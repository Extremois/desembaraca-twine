"""Reproduce the glibc object/source join without compiling or executing ELF.

Pass the pinned zig-x86_64-linux-0.15.2.tar.xz as --sdk-archive.
This archive contains both architecture sources. Existing output is compared,
never overwritten. Inputs remain the original evidence, including its limits.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EVIDENCE = HERE.parent


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk-archive', type=Path, required=True)
    args = parser.parse_args()
    if sha(args.sdk_archive.read_bytes()) != '02aa270f183da276e5b5920b1dac44a63f1a49e55050ebde3aecc9eb82f93239':
        raise ValueError('Expected pinned x86_64 SDK archive')
    module_spec = importlib.util.spec_from_file_location('glibc_join', ROOT / 'tools/runtime/audit-glibc-objects.py')
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    variants = []
    requested = {}
    prefixes = {}
    for arch, relative in [
            ('x86_64', 'linux-native-glibc-license-package-2026-10-19/glibc-object-evidence.json'),
            ('aarch64', 'linux-arm64-sdk-sources-2026-10-19/glibc-object-evidence.json.gz')]:
        observations_path = EVIDENCE / relative
        allocations_path = EVIDENCE / 'linux-allocated-sections-ci-2026-10-20' / ('glibc-' + arch) / 'allocated-sections.json.gz'
        observations, allocations = read(observations_path), read(allocations_path)
        result = module.allocated_source_observations(observations, allocations)
        result['inputs'] = [dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p.read_bytes()))
                            for p in (observations_path, allocations_path)]
        for source in observations['sources']:
            previous = requested.setdefault(source['path'], source['sha256'])
            if previous != source['sha256']:
                raise ValueError('Architecture sources disagree')
            prefixes.setdefault(source['path'], set()).add(source['leading_comments'].encode('utf-8'))
        variants.append(result)
    found = {}
    with tarfile.open(args.sdk_archive, 'r:xz') as archive:
        for member in archive:
            relative = member.name.removeprefix('zig-x86_64-linux-0.15.2/')
            if relative not in requested:
                continue
            if relative in found or not member.isfile() or member.size > 1024 ** 2:
                raise ValueError('Ambiguous or invalid SDK source')
            raw = archive.extractfile(member).read()
            if sha(raw) != requested[relative]:
                raise ValueError('Source differs from pinned SDK')
            if prefixes[relative] != {module.notices.source_notice_prefix(raw)}:
                raise ValueError('Observed notice differs from pinned source prefix')
            found[relative] = dict(path=relative, sha256=sha(raw), size=len(raw))
    if found.keys() != requested.keys():
        raise ValueError('Missing source in pinned SDK')
    ledger = read(ROOT / 'tools/runtime/licenses/linux.json')['glibc_retained_source_reviews']
    for variant in variants:
        matches = [item for item in ledger if item['artifact_id'] == variant['artifact_id']]
        if len(matches) != 1:
            raise ValueError('Expected unique artifact review in license ledger')
        item = matches[0]
        without_phrase = sorted({source['path'] for obj in variant['objects']
            for source in obj['compilation_units'] if not source['linking_exception_phrase_present']})
        if (item['executable_sha256'] != variant['executable_sha256']
                or item['retained_objects_joined'] != len(variant['objects'])
                or item['allocated_bytes'] != sum(obj['allocated_bytes'] for obj in variant['objects'])
                or item['executable_bytes'] != sum(obj['executable_bytes'] for obj in variant['objects'])
                or sorted(item['observed_sources_without_link_exception_phrase']) != without_phrase
                or item['approved'] is not False or item['qualified'] is not False
                or item['per_source_retention_established'] is not False):
            raise ValueError('License ledger differs from observed artifact facts')
    report = dict(kind='glibc-retained-source-review', approved=False, qualified=False,
        sdk_archive_sha256=sha(args.sdk_archive.read_bytes()),
        tool_sha256=sha((ROOT / 'tools/runtime/audit-glibc-objects.py').read_bytes()),
        sources_verified=sorted(found.values(), key=lambda item: item['path']), variants=variants)
    raw = (json.dumps(report, indent=2) + '\n').encode()
    destination = HERE / 'summary.json'
    if destination.exists():
        if destination.read_bytes() != raw:
            raise ValueError('Existing review differs; preserve it and review the changes')
    else:
        destination.write_bytes(raw)
    print(json.dumps(dict(variants=len(variants), sources_verified=len(found),
        retained_objects=sum(len(item['objects']) for item in variants), approved=False)))


if __name__ == '__main__':
    main()
