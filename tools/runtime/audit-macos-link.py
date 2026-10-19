"""Bind Apple linker-map objects and compiler inputs; never approve a license."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tarfile

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('macos_graphviz_sources', HERE / 'audit-graphviz-sources.py')
SOURCES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCES)
builder = SOURCES.builder


def parse_map(text):
    if len(text.encode()) > 16 * 1024**2:
        raise ValueError('Linker map exceeds budget')
    paths = re.findall(r'^# Path: (.+)$', text, re.M)
    arch = re.findall(r'^# Arch: (.+)$', text, re.M)
    if len(paths) != 1 or len(arch) != 1 or text.count('# Object files:') != 1:
        raise ValueError('Missing or ambiguous map header')
    section = text.split('# Object files:\n', 1)
    if len(section) != 2 or '# Sections:\n' not in section[1]:
        raise ValueError('Incomplete linker map object section')
    rows, indices = [], set()
    for line in section[1].split('# Sections:\n', 1)[0].splitlines():
        match = re.fullmatch(r'\[\s*(\d+)\]\s+(.+)', line)
        if not match or int(match[1]) in indices or len(indices) >= 10000:
            raise ValueError('Invalid, duplicate or excessive map object')
        index, value = int(match[1]), match[2]
        indices.add(index)
        if value == 'linker synthesized':
            continue
        member = re.fullmatch(r'(.+\.a)\(([^()/]+)\)', value)
        if value.endswith(')') and not member:
            raise ValueError('Unrecognized archive member notation')
        rows.append(dict(index=index, path=member[1] if member else value,
                         member=member[2] if member else None))
    if not rows:
        raise ValueError('No observed object inputs')
    return dict(path=paths[0], arch=arch[0], objects=rows)


def collect(output, map_path, archive):
    output, map_path, archive = map(lambda p: Path(p).resolve(strict=True), (output, map_path, archive))
    provenance = output / 'provenance.json'
    record = json.loads(SOURCES.bounded(provenance, 8 * 1024**2))
    host = builder.detect_host()
    if (host.os != 'darwin' or host.arch != record['native_arch'] or host.translated
            or record['native_os'] != 'darwin' or record['completed'] is not True):
        raise ValueError('Matching completed native Darwin build required')
    binary = output / 'candidate/bin/dot'
    if builder.digest(binary) != record['executable_sha256']:
        raise ValueError('Candidate changed after build')
    plan = builder.plan(record['artifact_id'], archive, output)
    if record['source'] != plan['source'] or record['recipe_sha256'] != plan['recipe_sha256']:
        raise ValueError('Source or recipe differs from pinned build')
    if str(map_path) != record['sdk']['facts']['link_map']:
        raise ValueError('Map differs from recorded compiler configuration')
    raw = SOURCES.bounded(map_path, 16 * 1024**2)
    parsed = parse_map(raw.decode())
    expected_arch = 'arm64' if host.arch == 'aarch64' else 'x86_64'
    build, source = output / 'build', output / 'source/graphviz-16.1.0'
    original = Path(parsed['path']).resolve(strict=True)
    if (parsed['arch'] != expected_arch or not original.is_relative_to(build)
            or builder.digest(original) != record['executable_sha256']):
        raise ValueError('Map output is not the completed native candidate')
    sdk = Path(record['sdk']['facts']['developer_dir']).resolve(strict=True)
    objects, inputs, archive_cache, dependencies = [], {}, {}, {}
    compiled = list(build.rglob('*.o'))
    total = dependency_bytes = 0
    for row in parsed['objects']:
        # macOS system dylibs can live only in the shared cache. A map spelling
        # is a runtime-library reference, not proof of independently read bytes.
        if row['member'] is None and row['path'] in ('/usr/lib/libSystem.B.dylib', '/usr/lib/libc++.1.dylib'):
            objects.append(dict(**row, scope='system-library-reference', input_bytes_available=False))
            continue
        path = Path(row['path'])
        path = (path if path.is_absolute() else build / 'cmd/dot' / path).resolve(strict=True)
        scope = 'build' if path.is_relative_to(build) else 'sdk' if path.is_relative_to(sdk) else None
        if scope is None:
            raise ValueError('Unexpected linker input outside build/selected Xcode')
        if str(path) not in inputs:
            payload = SOURCES.bounded(path, 64 * 1024**2)
            total += len(payload)
            if total > 1024**3:
                raise ValueError('Link inputs exceed budget')
            inputs[str(path)] = dict(path=str(path), scope=scope, size=len(payload), sha256=hashlib.sha256(payload).hexdigest())
            if row['member']:
                archive_cache[str(path)] = SOURCES.ar_members(payload)
        item = dict(**row, input_sha256=inputs[str(path)]['sha256'], scope=scope)
        if row['member']:
            member = archive_cache[str(path)].get(row['member'])
            if member is None:
                raise ValueError('Map member absent from hashed archive')
            item.update(object_sha256=member['sha256'], object_size=member['size'])
            object_path = SOURCES.match_member_object(member, compiled) if scope == 'build' else None
        else:
            item['object_sha256'] = inputs[str(path)]['sha256']
            object_path = path if scope == 'build' and path.suffix == '.o' else None
        if object_path is not None:
            depfile = object_path.with_suffix(object_path.suffix + '.d')
            declared = SOURCES.object_dependencies(SOURCES.bounded(depfile, 8 * 1024**2).decode(),
                                                   object_path.relative_to(build).as_posix())
            keys = []
            for name in declared:
                dependency = Path(name)
                dependency = (dependency if dependency.is_absolute() else build / dependency).resolve(strict=True)
                origin = 'source' if dependency.is_relative_to(source) else 'generated' if dependency.is_relative_to(build) else 'external'
                label = dependency.relative_to(source).as_posix() if origin == 'source' else str(dependency)
                key = origin + ':' + label
                keys.append(key)
                if key not in dependencies:
                    data = SOURCES.bounded(dependency, 8 * 1024**2)
                    dependency_bytes += len(data)
                    if len(dependencies) >= 10000 or dependency_bytes > 256 * 1024**2:
                        raise ValueError('Compiler inputs exceed budget')
                    dependencies[key] = dict(path=label, origin=origin, size=len(data), sha256=hashlib.sha256(data).hexdigest())
            item.update(object_path=object_path.relative_to(build).as_posix(),
                        dependency_file_sha256=builder.digest(depfile), dependencies=sorted(set(keys)))
        objects.append(item)
    expected = {row['path']: row['sha256'] for row in dependencies.values() if row['origin'] == 'source'}
    verified = set()
    with tarfile.open(archive) as incoming:
        for member in incoming:
            name = member.name.removeprefix('graphviz-16.1.0/')
            if member.isfile() and name in expected:
                if member.size > 8 * 1024**2:
                    raise ValueError('Source member exceeds budget')
                if hashlib.sha256(incoming.extractfile(member).read()).hexdigest() != expected[name]:
                    raise ValueError('Compiled source differs from pinned archive')
                verified.add(name)
    if not verified or verified != set(expected):
        raise ValueError('Compiled source missing from archive')
    return dict(kind='macos-link-object-source-observation', approved=False, qualified=False,
        artifact_id=record['artifact_id'], executable_sha256=record['executable_sha256'],
        provenance_sha256=builder.digest(provenance), map_sha256=hashlib.sha256(raw).hexdigest(),
        source=record['source'], inputs=list(inputs.values()), objects=objects, dependencies=dependencies,
        summary=dict(objects=len(objects), verified_graphviz_sources=len(verified),
                     generated_inputs=sum(v['origin'] == 'generated' for v in dependencies.values()),
                     external_inputs=sum(v['origin'] == 'external' for v in dependencies.values())),
        pending=['Map membership and compiler declarations do not prove retained sections or complete source closure',
                 'SDK objects, generated material and all per-file notices/licenses require review',
                 'No signing, notarization, release or support qualification'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('build-output', 'map', 'source-archive', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        report = collect(args.build_output, args.map, args.source_archive)
        with args.report.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
