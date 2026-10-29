"""Independently inspect downloaded CI archives and their native pairing receipts.

Offline only. No engine execution, extraction of unvalidated paths, publication,
catalog update or license/support approval. Payloads remain under ignored .tmp.
"""
import hashlib
import gzip
import importlib.util
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().parent
REVISION = 'a825f0d80bd7892de0e307656d28070885a9d1ed'


def tool(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


integrity = tool('native_pair_integrity', 'tools/validation/check-distribution-integrity.py')
sources = tool('native_pair_sources', 'tools/runtime/verify-public-sources.py')
pairing = tool('native_pair_verify', 'tools/runtime/verify-source-pairing.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)


def write(path, data):
    save(path, (json.dumps(data, indent=2) + '\n').encode())


def member(archive, name, maximum=8 * 1024**2):
    matches = [entry for entry in archive.infolist() if entry.filename.split('/')[-1] == name]
    require(len(matches) == 1, 'Missing or ambiguous ' + name)
    require(matches[0].file_size <= maximum, 'Oversized ' + name)
    return archive.read(matches[0]), matches[0].filename


def checked_archive(row):
    require(re.fullmatch(r'actions-artifact-[0-9]+\.zip', row['file']) is not None, 'Invalid download filename')
    path = ROOT / '.tmp' / row['file']
    raw = integrity.read_bounded(path)
    require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'Downloaded archive changed')
    return raw


def source_pair(binary, source, work):
    source_raw = checked_archive(source)
    binary_raw = checked_archive(binary)
    with integrity.bounded_zip(binary_raw) as archive:
        candidate_raw, candidate_name = member(archive, 'candidate.json')
        prefix = candidate_name.removesuffix('candidate.json')
        candidate = json.loads(candidate_raw)
        inventory_raw = archive.read(prefix + 'inventory.json')
        payload = archive.read(prefix + 'candidate.zip')
        provenance_matches = [archive.read(entry) for entry in archive.infolist()
                              if entry.filename.split('/')[-1] == 'provenance.json' and entry.file_size <= 8 * 1024**2]
        provenance_matches = [raw for raw in provenance_matches if sha(raw) == candidate['provenance_sha256']]
        require(bool(provenance_matches), 'Binary provenance missing')
        provenance_raw = provenance_matches[0]
        inspected = integrity.inspect_candidate(candidate_raw, inventory_raw, provenance_raw, payload)
        native_pair_raw, _ = member(archive, 'source-pairing.json')
    with integrity.bounded_zip(source_raw) as archive:
        source_receipt_raw, _ = member(archive, 'sources.json')
        source_payload, _ = member(archive, 'sources.tar.gz', 128 * 1024**2)
        source_pair_raw, _ = member(archive, 'source-pairing.json')
    require(native_pair_raw == source_pair_raw, 'Binary and source artifacts carry different pairing receipts')
    source_receipt = json.loads(source_receipt_raw)
    work.mkdir()
    for name, raw in (('candidate.json', candidate_raw), ('inventory.json', inventory_raw),
                      ('candidate.zip', payload), ('sources.json', source_receipt_raw),
                      ('sources.tar.gz', source_payload)):
        save(work / name, raw)
    local_pair = pairing.verify_pairing(work / 'candidate.json', work / 'sources.json',
                                       work / 'candidate.zip', work / 'sources.tar.gz', application_revision=REVISION)
    native_pair = json.loads(native_pair_raw)
    require(local_pair == native_pair, 'Independent local verification differs from native pairing receipt')
    files, manifest, provenance = sources.source_inventory(work / 'sources.tar.gz', source_receipt)
    require(sha(provenance_raw) == manifest['provenance_sha256'], 'Source and binary provenance hashes differ')
    require(provenance == json.loads(provenance_raw), 'Source and binary provenance content differs')
    require(native_pair['archive_verification'] == {'candidate': True, 'sources': True}, 'Native files were not verified')
    require(native_pair['delivery_binding']['active_catalog_promoted'] is False, 'Pairing must not promote catalog')
    require(native_pair['delivery_binding']['status'] == 'unpromoted_pending_authorized_distribution', 'Unexpected delivery approval')
    require(candidate['source_modes_checked'] is True, 'Native candidate did not measure modes')
    destination = OUTPUT / candidate['artifact_id']
    destination.mkdir()
    for name, raw in (('candidate.json', candidate_raw), ('inventory.json', inventory_raw),
                      ('sources.json', source_receipt_raw), ('pairing.json', native_pair_raw)):
        save(destination / name, raw)
    # Preserve exact native provenance bytes compressed, without changing them.
    save(destination / 'provenance.json.gz', gzip.compress(provenance_raw, mtime=0))
    return dict(artifact_id=candidate['artifact_id'], candidate_revision=REVISION,
                binary_actions_artifact_id=binary['id'], binary_actions_archive_sha256=binary['sha256'],
                source_actions_artifact_id=source['id'], source_actions_archive_sha256=source['sha256'],
                binary_run_id=binary['run_id'], source_run_id=source['run_id'],
                binary_files=inspected['files_verified'], notices=inspected['notice_payloads_verified'],
                source_files=len(files), sdk_files=source_receipt['sdk_files'],
                executable_sha256=candidate['executable_sha256'], provenance_sha256=candidate['provenance_sha256'],
                candidate_archive_sha256=candidate['archive_sha256'], source_archive_sha256=source_receipt['archive_sha256'],
                native_pair_receipts_byte_identical=True, independent_pairing_matches_native=True,
                source_manifest_checked=True, source_provenance_matches_binary=True,
                encoded_modes_checked=True, native_modes_measured=True,
                pairing_receipt=candidate['artifact_id'] + '/pairing.json', pairing_receipt_sha256=sha(native_pair_raw))


def main():
    require(len(sys.argv) == 3, 'Usage: python capture.py DOWNLOAD_RECEIPT NEW_SCRATCH_DIRECTORY')
    index = json.loads(Path(sys.argv[1]).read_bytes())
    require(index['revision'] == REVISION, 'Download revision differs')
    require(all(run['revision'] == REVISION and run['conclusion'] == 'success' for run in index['runs']), 'Checkpoint workflows must pass')
    require(not (OUTPUT / 'summary.json').exists(), 'Do not overwrite review receipts')
    work = Path(sys.argv[2]).resolve()
    require(work.is_relative_to((ROOT / '.tmp').resolve()), 'Scratch must be inside ignored .tmp')
    work.mkdir(exist_ok=False)
    pairs, other = [], []
    downloads = index['downloads']
    for binary in downloads:
        if '-unqualified-' not in binary['name']:
            continue
        if binary['name'].startswith('macos-'):
            inspected = integrity.inspect_artifact(ROOT / '.tmp' / binary['file'])
            require(inspected['artifact_sha256'] == binary['sha256'], 'macOS Actions archive changed')
            other.append({key: inspected[key] for key in ('artifact_id', 'artifact_sha256', 'archive_sha256',
                          'engine_sha256', 'provenance_sha256', 'files_verified', 'notice_payloads_verified')})
            continue
        identifier = binary['name'].removesuffix('-' + REVISION).removesuffix('-unqualified').removesuffix('-container')
        source_matches = [row for row in downloads if row['name'] == identifier + '-source-review-' + REVISION]
        require(len(source_matches) == 1, 'Corresponding source Actions artifact missing')
        pairs.append(source_pair(binary, source_matches[0], work / identifier))
    require(len(pairs) == 4 and len(other) == 2, 'Expected four Linux pairs and two macOS bundles')
    require(len({row['artifact_id'] for row in pairs}) == 4, 'Duplicate Linux artifact')
    foundation = OUTPUT / 'foundation'
    foundation.mkdir()
    require(len(index['foundation']) == 6, 'Expected six foundation logs')
    for record in index['foundation']:
        require(re.fullmatch(r'actions-job-[0-9]+\.log', record['file']) is not None, 'Invalid foundation log path')
        raw = integrity.read_bounded(ROOT / '.tmp' / record['file'], 8 * 1024**2)
        require(sha(raw) == record['sha256'], 'Foundation log changed')
        save(foundation / (record['file'] + '.gz'), gzip.compress(raw, mtime=0))
    summary = dict(kind='native-ci-linux-source-pairing-review', candidate_revision=REVISION,
                   source_state='working-tree-review-of-committed-candidate', reviewed_on='2026-10-27',
                   qualified=False, approved=False, task_complete=False, tasks=['T030', 'T066'],
                   runs=index['runs'], downloads=downloads, foundation=index['foundation'],
                   linux_pairs=pairs, macos_bundles=other,
                   capture_sha256=sha(Path(__file__).read_bytes()),
                   verification_tools={name: sha((ROOT / name).read_bytes()) for name in (
                       'tools/runtime/verify-source-pairing.py', 'tools/runtime/verify-public-sources.py',
                       'tools/validation/check-distribution-integrity.py')},
                   limitations=['Linux glibc built on native Ubuntu CPU; musl built in Alpine containers on matching CPU',
                                'macOS bundles remain unsigned; no source pairing or signing approval for macOS',
                                'Source files/manifests/provenance checked; source completeness and final distribution remain separate',
                                'CI artifacts are temporary review material, not permanent public source delivery',
                                'No catalog promotion or complete support-cell qualification'])
    write(OUTPUT / 'summary.json', summary)
    print(json.dumps(dict(linux_pairs=len(pairs), macos_bundles=len(other),
                          binary_files=sum(row['binary_files'] for row in pairs),
                          source_files=sum(row['source_files'] for row in pairs), passed=True)))


if __name__ == '__main__':
    main()
