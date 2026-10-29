"""Inspect an exact reviewed bundle on its native CI CPU, without publishing."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


packages = load('reviewed_packages', 'tools/validation/check-built-packages.py')
distribution = load('reviewed_distribution', 'tools/validation/check-distribution-integrity.py')
native = load('reviewed_native', 'tools/runtime/verify-artifact.py')


def inspect(artifact, artifact_id, audit):
    reviewed = json.loads(Path(audit).read_bytes())
    decision = (ROOT / reviewed['decision_document']).resolve()
    if not decision.is_relative_to(ROOT) or native.digest(decision, maximum=1024**2) != reviewed['decision_sha256']:
        raise ValueError('Bound technical decision changed')
    with tempfile.TemporaryDirectory(prefix='reviewed-bundle-') as temporary:
        work = Path(temporary)
        package = work / 'package'
        packages.prepare_engine_fixture(Path(artifact), package, artifact_id)
        candidate_raw, inventory_raw, provenance_raw, archive_raw = (
            (package / name).read_bytes() for name in
            ('candidate.json', 'inventory.json', 'provenance.json', 'candidate.zip'))
        candidate = json.loads(candidate_raw)
        if (reviewed.get('artifact_id') != artifact_id
                or reviewed['source_pair']['candidate_sha256'] != candidate['archive_sha256']):
            raise ValueError('Review does not identify this exact candidate')
        sources = list(Path(artifact).rglob('sources.json'))
        if len(sources) != 1:
            raise ValueError('One paired source receipt is required')
        source = json.loads(sources[0].read_bytes())
        if (source['archive_sha256'] != reviewed['source_pair']['sources_sha256']
                or source['executable_sha256'] != candidate['executable_sha256']
                or source['provenance_sha256'] != candidate['provenance_sha256']):
            raise ValueError('Reviewed corresponding-source pair differs')
        provenance = json.loads(provenance_raw)
        if provenance.get('static_elf_inspection'):
            expected = provenance['static_elf_inspection']['report_sha256']
            reports = [p for p in Path(artifact).rglob('*static-elf-inspection.txt')
                       if native.digest(p, maximum=8*1024**2) == expected]
            if not reports:
                raise ValueError('Bound static ELF inspection is missing')
            (package / 'static-elf-inspection.txt').write_bytes(reports[0].read_bytes())
        checked = distribution.inspect_candidate(candidate_raw, inventory_raw, provenance_raw, archive_raw)
        root = work / 'candidate'
        root.mkdir()
        # The existing inventory checker has validated every member name, type,
        # size, hash and encoded mode before any extraction or native execution.
        with zipfile.ZipFile(package / 'candidate.zip') as archive:
            archive.extractall(root)
        for row in json.loads(inventory_raw)['files']:
            (root / row['path']).chmod(row['mode'])
        result = native.inspect(root, None, package / 'provenance.json', audit,
                                inventory=package / 'inventory.json')
        return dict(passed=True, qualified=False, artifact_id=artifact_id,
            archive_sha256=candidate['archive_sha256'], executable_sha256=candidate['executable_sha256'],
            audit_sha256=native.digest(audit), files_verified=checked['files_verified'], inspection=result,
            scope='Exact bundle technical audit and native inspection; public paired delivery and final catalog acceptance remain gates')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('artifact', 'audit', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--artifact-id', required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Preserve existing reports; choose a new path')
    result = inspect(args.artifact, args.artifact_id, args.audit)
    with args.report.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
