"""Revalidate four preserved historical Linux pairs offline; never execute engines.

Repackage verified payloads to obtain current producer receipts, requiring ZIP
bytes identical to the historical candidates. Historical receipts stay untouched.
All binary/source payloads remain in ignored .tmp; only review receipts are saved.
"""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[4]
OUTPUT = Path(__file__).resolve().parent
HISTORICAL = ROOT / 'specs/003-add-cross-platform-support/evidence/linux-component-obligations-ci-2026-10-20'
SOURCES = ROOT / '.tmp/public-source-review-current'
REVISION = '47844106ff072cad005a8a1c795153c658b2bc89'
VARIANTS = ('glibc-x86_64', 'glibc-aarch64', 'musl-x86_64', 'musl-aarch64')


def tool(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


integrity = tool('pair_review_integrity', 'tools/validation/check-distribution-integrity.py')
packer = tool('pair_review_packer', 'tools/runtime/pack-candidate.py')
pairing = tool('pair_review_pairing', 'tools/runtime/verify-source-pairing.py')
sources = tool('pair_review_sources', 'tools/runtime/verify-public-sources.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, value):
    with path.open('xb') as stream:
        stream.write(value)


def write(path, value):
    save(path, (json.dumps(value, indent=2) + '\n').encode())


def capture_variant(variant, work):
    previous = HISTORICAL / variant
    original_summary = json.loads((previous / 'summary.json').read_bytes())
    artifact = ROOT / '.tmp' / ('actions-artifact-' + str(original_summary['actions_artifact_id']) + '.zip')
    original_candidate = integrity.read_bounded(previous / 'candidate.json', 8 * 1024**2)
    inventory_raw = integrity.read_bounded(previous / 'inventory.json', 8 * 1024**2)
    provenance_raw = gzip.decompress(integrity.read_bounded(previous / 'provenance.json.gz', 8 * 1024**2))
    inventory, provenance = map(json.loads, (inventory_raw, provenance_raw))
    candidate = json.loads(original_candidate)
    archive_raw = integrity.read_bounded(artifact)
    require(sha(archive_raw) == original_summary['actions_archive_sha256'], 'Historical Actions archive changed')
    require(original_summary['revision'] == REVISION, 'Historical revision differs')
    with integrity.bounded_zip(archive_raw) as archive:
        entries = [entry for entry in archive.infolist() if entry.filename.split('/')[-1] == 'candidate.json']
        require(len(entries) == 1, 'Ambiguous candidate receipt')
        require(archive.read(entries[0]) == original_candidate, 'Historical candidate receipt differs')
        prefix = entries[0].filename.removesuffix('candidate.json')
        require(archive.read(prefix + 'inventory.json') == inventory_raw, 'Historical inventory differs')
        binary_raw = archive.read(prefix + 'candidate.zip')
        inspection = integrity.inspect_candidate(original_candidate, inventory_raw, provenance_raw, binary_raw)
        require(inspection['engine_sha256'] == original_summary['executable_sha256'], 'Engine differs from historical review')
        work.mkdir(mode=0o700)
        save(work / 'inventory.json', inventory_raw)
        save(work / 'provenance.json', provenance_raw)
        if inventory.get('native_linkage') == 'static-elf':
            expected = provenance['static_elf_inspection']['report_sha256']
            reports = [archive.read(entry) for entry in archive.infolist()
                       if entry.filename.endswith('/static-elf-inspection.txt')]
            reports = [raw for raw in reports if sha(raw) == expected]
            require(len(reports) == 1, 'Exact static ELF report missing')
            save(work / 'static-elf-inspection.txt', reports[0])

    # The existing inspector checked every member, byte, size, mode and notice.
    # Resolve each inventoried path before any local write; never use extractall.
    tree = work / 'candidate'
    tree.mkdir(mode=0o700)
    with integrity.bounded_zip(binary_raw) as archive:
        for row in inventory['files']:
            name = packer.verifier.relative_path(row['path']).as_posix()
            target = tree / name
            require(target.resolve().is_relative_to(tree.resolve()), 'Candidate path escapes scratch tree')
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            save(target, archive.read(name))
            target.chmod(row['mode'])

    repacked = packer.pack(tree, work / 'inventory.json', work / 'provenance.json', work / 'repacked')
    require(repacked['archive_sha256'] == candidate['archive_sha256'], 'Repacked ZIP differs from historical candidate')
    require(repacked['archive_bytes'] == candidate['archive_bytes'], 'Repacked ZIP size differs')
    source_receipt_path = SOURCES / variant / 'sources.json'
    source_archive = SOURCES / variant / 'sources.tar.gz'
    source_receipt_raw = integrity.read_bounded(source_receipt_path, 65536)
    source_receipt = json.loads(source_receipt_raw)
    files, manifest, source_provenance = sources.source_inventory(source_archive, source_receipt)
    require(source_provenance == provenance, 'Embedded source provenance differs from binary build')
    result = pairing.verify_pairing(work / 'repacked/candidate.json', source_receipt_path,
                                   work / 'repacked/candidate.zip', source_archive,
                                   application_revision=REVISION)

    destination = OUTPUT / variant
    destination.mkdir()
    save(destination / 'candidate-original.json', original_candidate)
    save(destination / 'candidate-repacked.json', (work / 'repacked/candidate.json').read_bytes())
    save(destination / 'sources.json', source_receipt_raw)
    write(destination / 'pairing.json', result)
    # Demonstrate that a different archive cannot inherit this pair's proof.
    altered = dict(source_receipt, provenance_sha256='0' * 64)
    try:
        pairing.pair_records(repacked, altered)
    except ValueError:
        mismatch_rejected = True
    else:
        raise ValueError('Changed provenance unexpectedly paired')

    return dict(artifact_id=result['artifact_id'], historical_revision=REVISION,
                actions_artifact_id=original_summary['actions_artifact_id'],
                actions_archive_sha256=sha(archive_raw),
                historical_summary_sha256=sha((previous / 'summary.json').read_bytes()),
                original_candidate_receipt_sha256=sha(original_candidate),
                repacked_candidate_receipt_sha256=sha((work / 'repacked/candidate.json').read_bytes()),
                candidate_zip_byte_identical=True, candidate_zip_sha256=repacked['archive_sha256'],
                source_archive_sha256=source_receipt['archive_sha256'],
                executable_sha256=result['executable_sha256'], provenance_sha256=result['provenance_sha256'],
                binary_files_verified=inspection['files_verified'],
                notice_payloads_verified=inspection['notice_payloads_verified'],
                source_files_verified=len(files), sdk_files=source_receipt['sdk_files'],
                source_manifest_matches_bytes=True, source_provenance_matches_binary=True,
                mismatched_provenance_rejected=mismatch_rejected,
                archive_verification=result['archive_verification'],
                source_modes_checked=repacked['source_modes_checked'],
                pairing_receipt=variant + '/pairing.json',
                pairing_receipt_sha256=sha((destination / 'pairing.json').read_bytes()))


def main():
    require(len(sys.argv) == 2, 'Usage: python capture.py NEW_SCRATCH_DIRECTORY')
    work = Path(sys.argv[1]).resolve()
    require(work.is_relative_to((ROOT / '.tmp').resolve()), 'Scratch must be inside ignored .tmp')
    require(not any((OUTPUT / name).exists() for name in (*VARIANTS, 'summary.json')), 'Choose new review outputs')
    work.mkdir(mode=0o700, exist_ok=False)
    rows = [capture_variant(variant, work / variant) for variant in VARIANTS]
    tool_paths = ['tools/runtime/pack-candidate.py', 'tools/runtime/verify-source-pairing.py',
                  'tools/runtime/verify-public-sources.py', 'tools/validation/check-distribution-integrity.py']
    summary = dict(kind='historical-linux-source-pairing-local-review', reviewed_on='2026-10-27',
                   source_state='working-tree', approved=False, qualified=False, task_complete=False,
                   tasks=['T030', 'T066'], historical_revision=REVISION,
                   tools={name: sha((ROOT / name).read_bytes()) for name in tool_paths},
                   capture_sha256=sha(Path(__file__).read_bytes()), pairs=rows,
                   limitations=['Historical development packages only; not the latest or final candidates',
                                'No engine/compiler execution or native qualification in this review',
                                'POSIX modes checked from ZIP/inventory; locally repacked on Windows',
                                'Source manifest/bytes/provenance checked; no new source completeness or license approval',
                                'No public delivery URLs or release; active catalog remains unchanged'])
    write(OUTPUT / 'summary.json', summary)
    print(json.dumps(dict(pairs=len(rows), binary_files=sum(row['binary_files_verified'] for row in rows),
                          source_files=sum(row['source_files_verified'] for row in rows), passed=True)))


if __name__ == '__main__':
    main()
