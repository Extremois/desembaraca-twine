"""Prepare byte-bound macOS draft notices; never approve, sign or publish them."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tarfile

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


common = load('prepare-draft-notices')
link_audit = load('audit-macos-link')
builder = common.builder
HEADER_REVIEW_SHA256 = {
    # Xcode 16.4 / macOS SDK 15.5 inputs recorded in the current review dossier.
    'float.h': '4346c126d6f51ea8b63ea394f609f2474b26fdb9257c65cf3d2b43aaef36cd3e',
    'math.h': '00606d7b27eb5db0a3b93c575a7084f432d1e783cfca2eedcdc234c01cb15134',
}


def data_reference_materials(source_archive, lock):
    """Preserve upstream data notices without asserting generated-table equivalence."""
    if builder.digest(source_archive) != lock['sha256']:
        raise ValueError('Graphviz archive differs from pinned source')
    data_audit = load('audit-graphviz-data')
    materials, _ = data_audit.w3c_reference_materials()
    names = {'lib/common/entities.html', 'lib/common/svgcolor_names', 'lib/common/color_names'}
    sources = common.archive_files(source_archive, 'graphviz-16.1.0', names)
    for name, raw in sorted(sources.items()):
        sha = hashlib.sha256(raw).hexdigest()
        if name.endswith('entities.html'):
            materials.append(data_audit.entity_declaration_notice(raw, sha))
        # Keep raw inputs as text review material, alongside their notices.
        materials.append(('Graphviz-data-' + Path(name).name + '.txt', raw,
            dict(kind='pinned-graphviz-data-reference', path=name, archive_sha256=lock['sha256'],
                 source_sha256=sha, scope='Conservative source reference; generated-table equivalence and applicability pending')))
    raw = data_audit.reference_material('xorg-rgb-1.1.0-COPYING')
    reference = json.loads(common.audit.bounded(data_audit.REFERENCES / 'sources.json', 65536))[
        'references']['xorg-rgb-1.1.0-COPYING']
    materials.append(('Xorg-rgb-1.1.0-COPYING.txt', raw,
        dict(kind='pinned-reference-license-material', source_sha256=hashlib.sha256(raw).hexdigest(),
             source_url=reference['url'], archive_sha256=reference['archive_sha256'],
             archive_member=reference['archive_member'],
             scope='Reference material; historical copying and applicability pending')))
    return materials


def canonical_references(materials):
    # These are references to explicit declarations, not a license classifier.
    rules = (
        ('apsl_1_1_copying', 'APSL-1.1-COPYING.txt',
         lambda name, raw: b'Apple Public Source License' in raw and b'Version 1.1' in raw),
        ('apsl_2_copying', 'APSL-2.0-COPYING.txt',
         lambda name, raw: b'Apple Public Source License' in raw and b'Version 2.0' in raw),
        ('llvm_17_license_reference', 'LLVM-license-reference-COPYING.txt',
         lambda name, raw: b'Apache-2.0 WITH LLVM-exception' in raw),
        ('gpl_3_copying', 'GPL-3.0-COPYING.txt',
         lambda name, raw: name.startswith('Bison-') and b'GNU General Public License' in raw and b'version 3' in raw),
    )
    result = []
    for key, filename, matches in rules:
        referenced_by = sorted(name for name, raw, _ in materials if matches(name, raw))
        if referenced_by:
            raw, origin = common.license_material(key)
            origin.update(referenced_by=referenced_by,
                applicability='Per-file applicability pending; reference text does not identify compiler sources or approve redistribution')
            result.append((filename, raw, origin))
    return result


def origin_index(materials, parent_sha256, evidence_sha256):
    report = dict(kind='macos-offline-notice-origins', schema_version=1, approved=False, qualified=False,
        parent_provenance_sha256=parent_sha256, source_evidence_sha256=evidence_sha256,
        scope='Payload notices excluding this index; complete applicability/source review remains pending',
        notices=[dict(path=name, size=len(raw), sha256=hashlib.sha256(raw).hexdigest(), origin=origin)
                 for name, raw, origin in materials])
    return (json.dumps(report, indent=2, sort_keys=True) + '\n').encode('utf-8')


def header_notice(row, developer):
    developer = Path(developer).resolve(strict=True)
    path = Path(row['path']).resolve(strict=True)
    if not path.is_relative_to(developer):
        raise ValueError('Compiler header outside recorded Xcode')
    raw = common.audit.bounded(path, 8 * 1024**2)
    if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError('Compiler header changed after source observation')
    prefix = common.source_notice_prefix(raw)
    return prefix, dict(kind='recorded-xcode-header-prefix', path=path.relative_to(developer).as_posix(),
        source_sha256=row['sha256'], offset=0, length=len(prefix),
        qualification='Leading comment material only; applicability and complete text remain under review')


def sdk_header_review_materials(dependencies, developer):
    selected = {}
    for row in dependencies:
        path = Path(row['path'])
        name = path.name
        if (row['origin'] != 'external' or name not in HEADER_REVIEW_SHA256
                or not path.as_posix().endswith('/usr/include/' + name)):
            continue
        prefix, origin = header_notice(row, developer)
        raw = common.audit.bounded(path, 1024**2)
        if (name in selected or row['sha256'] != HEADER_REVIEW_SHA256[name]
                or hashlib.sha256(raw).hexdigest() != HEADER_REVIEW_SHA256[name]
                or b'Apple Public Source License Version 1.1' not in prefix):
            raise ValueError('SDK header differs from the pinned APSL source review')
        selected[name] = (name, raw, dict(origin, kind='recorded-xcode-header-source',
            length=len(raw), qualification='Complete unmodified input for review; applicability pending'))
    if set(selected) != set(HEADER_REVIEW_SHA256):
        raise ValueError('Missing pinned SDK header source for review')
    license_raw, license_origin = common.license_material('apsl_1_1_copying')
    return [selected[name] for name in sorted(selected)] + [
        ('APSL-1.1-COPYING.txt', license_raw, license_origin)]


def prepare(build, evidence, source_archive, map_path, output):
    build, evidence, source_archive, map_path, output = map(Path, (build, evidence, source_archive, map_path, output))
    if output.exists() or output.is_symlink():
        raise FileExistsError('Notice output already exists')
    record = json.loads(common.audit.bounded(build / 'provenance.json', 8 * 1024**2))
    if record['artifact_id'] not in ('macos-arm64', 'macos-x86_64'):
        raise ValueError('Completed native macOS candidate required')
    observed = json.loads(common.audit.bounded(evidence, 8 * 1024**2))
    # Recompute the observation against objects, headers, map and pinned source.
    if observed != link_audit.collect(build, map_path, source_archive):
        raise ValueError('Source observation differs from this native build')
    dependencies = list(observed['dependencies'].values())
    header_sources = sdk_header_review_materials(dependencies, record['sdk']['facts']['developer_dir'])
    generated = {}
    for row in dependencies:
        if row['origin'] != 'generated':
            continue
        path = Path(row['path'])
        if not path.is_relative_to(build / 'build'):
            raise ValueError('Generated input outside build')
        raw = common.audit.bounded(path, 8 * 1024**2)
        if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Generated input changed')
        generated[path.relative_to(build / 'build').as_posix()] = (raw, row)
    graphviz_names = {'COPYING', 'AUTHORS', 'lib/rbtree/LICENSE', 'lib/common/brewer_colors'}
    files = common.archive_files(source_archive, 'graphviz-16.1.0', graphviz_names)
    source_rows, materials = common.graphviz_source_materials(dependencies, source_archive, record['source'])
    materials.extend(data_reference_materials(source_archive, record['source']))
    for name in sorted(graphviz_names):
        raw = files[name]
        filename = 'ColorBrewer.txt' if name.endswith('brewer_colors') else 'Graphviz-' + name.replace('/', '__') + '.txt'
        materials.append((filename, common.color_notice(raw) if name.endswith('brewer_colors') else raw,
            dict(kind='pinned-graphviz-source', path=name, source_sha256=hashlib.sha256(raw).hexdigest(),
                 archive_sha256=record['source']['sha256'])))
    color_path = 'lib/common/brewer_colors'
    materials.append(('ColorBrewer-ACKNOWLEDGMENT.txt', common.color_acknowledgment(files[color_path]),
        dict(kind='maintainer-colorbrewer-acknowledgment', path=color_path,
             archive_sha256=record['source']['sha256'], source_sha256=hashlib.sha256(files[color_path]).hexdigest())))
    for name in ('lib/cgraph/grammar.c', 'lib/cgraph/grammar.h', 'lib/common/htmlparse.c', 'lib/common/htmlparse.h'):
        raw, row = generated[name]
        prefix = common.bison_notice(raw)
        materials.append(('Bison-' + name.replace('/', '__') + '.txt', prefix,
            dict(kind='generated-parser-prefix', path=name, source_sha256=row['sha256'], offset=0, length=len(prefix))))
    scanner, scanner_row = generated['lib/cgraph/scan.c']
    generator = record['sdk']['facts']['host_tools']['flex']
    generator_path = Path(generator['path']).resolve(strict=True)
    developer = Path(record['sdk']['facts']['developer_dir']).resolve(strict=True)
    if not generator_path.is_relative_to(developer) or builder.digest(generator_path) != generator['sha256']:
        raise ValueError('Recorded Apple Flex generator missing or changed')
    flex, flex_origin = common.flex_scanner_notice(scanner, generator, apple=True)
    flex_origin.update(generated_path='lib/cgraph/scan.c', generated_sha256=scanner_row['sha256'],
                       recorded_generator_version=generator['version'])
    materials.append(('Flex-Apple-35-COPYING.txt', flex, flex_origin))
    headers = []
    for row in sorted((row for row in dependencies if row['origin'] == 'external'), key=lambda row: row['path']):
        prefix, origin = header_notice(row, developer)
        headers.append(dict(**origin, prefix_sha256=hashlib.sha256(prefix).hexdigest(),
                            status='prefix-preserved-review-pending' if prefix else 'no-leading-comment-review-pending'))
        if prefix:
            filename = 'SDK-header-' + hashlib.sha256(origin['path'].encode()).hexdigest()[:24] + '.txt'
            materials.append((filename, prefix, origin))
    references = common.source_access_notice(record['source'], record['artifact_id']) + (
        'Xcode: ' + record['sdk']['facts']['xcode'].replace('\n', '; ') + '\n'
        'SDK tree SHA-256: ' + record['sdk']['facts']['sdk_tree_sha256'] + '\n'
        'Header notices are leading comments, not a redistribution of the Apple SDK.\n'
        'Referenced license texts and byte-bound NOTICE-ORIGINS.json are included offline.\n'
        'LLVM reference text does not identify the sources of the Apple compiler.\n'
        'Additional texts, applicability, generated data and corresponding-source offer remain under review.\n').encode()
    materials.append(('SOURCE-REFERENCES.txt', references, dict(kind='maintainer-source-review-reference')))
    materials.extend(canonical_references(materials))
    materials.append(('NOTICE-ORIGINS.json', origin_index(materials,
        builder.digest(build / 'provenance.json'), builder.digest(evidence)),
        dict(kind='maintainer-offline-notice-origin-index', scope='Other notice payloads only; no self hash')))
    if len(materials) > 5000 or sum(len(raw) for _, raw, _ in materials) > 16 * 1024**2:
        raise ValueError('Notice material exceeds budget')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    (output / 'header-review').mkdir()
    header_source_records = []
    for name, raw, origin in header_sources:
        target = output / 'header-review' / name
        target.write_bytes(raw)
        header_source_records.append(dict(path=target.relative_to(output).as_posix(), size=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(), origin=origin))
    candidate = output / 'candidate'
    (candidate / 'bin').mkdir(parents=True)
    binary = candidate / 'bin/dot'
    shutil.copyfile(build / 'candidate/bin/dot', binary)
    binary.chmod(0o755)
    if builder.digest(binary) != record['executable_sha256']:
        raise ValueError('Engine changed during notice copy')
    notices = candidate / 'third-party-notices'
    notices.mkdir()
    inventory = []
    for name, raw, origin in materials:
        target = notices / name
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(0o644)
        inventory.append(dict(path=target.relative_to(candidate).as_posix(), size=len(raw),
                              sha256=hashlib.sha256(raw).hexdigest(), origin=origin))
    review = dict(kind='macos-draft-notice-review', approved=False, qualified=False,
        artifact_id=record['artifact_id'], executable_sha256=record['executable_sha256'],
        parent_provenance_sha256=builder.digest(build / 'provenance.json'), source_evidence_sha256=builder.digest(evidence),
        notices=inventory, headers=headers, graphviz_sources=source_rows,
        sdk_header_source_review=header_source_records,
        generated_inputs_verified=len(generated),macos_signing_required=False,
        pending=['Per-file applicability and any additional required texts', 'Generated data provenance/notices',
                 'Unnamed linker-map slots and SDK contribution review', 'Complete corresponding-source offer',
                 'Approved audit and installed ABI acceptance in GitHub Actions'])
    (output / 'review.json').write_text(json.dumps(review, indent=2) + '\n', encoding='utf-8')
    record.update(output=str(output), qualification='draft macOS notices only; no approved audit or support',
        notice_preparation=dict(approved=False, review_sha256=builder.digest(output / 'review.json')))
    (output / 'provenance.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build', 'evidence', 'source-archive', 'map-path', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = prepare(**{key: value.resolve() for key, value in vars(args).items()})
        print(json.dumps(dict(notices=len(report['notices']), headers=len(report['headers']), approved=False)))
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
