"""Offline byte/origin checks for development distributions; never approve licenses."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import stat
import zipfile

ROOT=Path(__file__).resolve().parents[2]
MAXIMUM=128*1024**2


def digest(raw):return hashlib.sha256(raw).hexdigest()


def read_bounded(path,maximum=MAXIMUM):
    with Path(path).open('rb') as stream:raw=stream.read(maximum+1)
    if len(raw)>maximum:raise ValueError('Distribution input exceeds byte limit')
    return raw


def safe_name(name):
    if (not isinstance(name,str) or not name or '\\' in name or ':' in name
            or '\x00' in name or any(part in ('','.','..') for part in name.split('/'))):
        raise ValueError('Unsafe distribution member')
    return name


def bounded_zip(raw):
    if not 0<len(raw)<=MAXIMUM:raise ValueError('Invalid ZIP size')
    archive=zipfile.ZipFile(io.BytesIO(raw))
    entries=archive.infolist()
    if (len(entries)>10000 or sum(i.file_size for i in entries)>MAXIMUM
            or len({i.filename for i in entries})!=len(entries)):
        archive.close()
        raise ValueError('Duplicate or excessive distribution ZIP')
    return archive


def inspect_candidate(candidate_raw,inventory_raw,provenance_raw,archive_raw):
    candidate,inventory,provenance=map(json.loads,(candidate_raw,inventory_raw,provenance_raw))
    if (candidate.get('archive_bytes')!=len(archive_raw)
            or candidate.get('archive_sha256')!=digest(archive_raw)
            or candidate.get('inventory_sha256')!=digest(inventory_raw)
            or candidate.get('provenance_sha256')!=digest(provenance_raw)
            or inventory.get('provenance_sha256')!=digest(provenance_raw)
            or provenance.get('completed') is not True
            or not candidate.get('artifact_id')
            or candidate['artifact_id']!=inventory.get('artifact_id')
            or candidate['artifact_id']!=provenance.get('artifact_id')):
        raise ValueError('Unbound candidate/inventory/build bytes')
    expected={}
    if inventory.get('notices') not in (None,[]):
        raise ValueError('Native bundle notices must be inventoried files')
    for row in inventory['files']:
        name=safe_name(row['path'])
        if (name in expected or type(row.get('size')) is not int or row['size']<0
                or row.get('mode') not in (0o644,0o755)
                or not re.fullmatch(r'[0-9a-f]{64}',row.get('sha256',''))):
            raise ValueError('Incomplete or ambiguous native file inventory')
        expected[name]=row
    with bounded_zip(archive_raw) as archive:
        if set(archive.namelist())!=set(expected):
            raise ValueError('Archive contains omitted or uninventoried files')
        payloads={}
        for entry in archive.infolist():
            row=expected[safe_name(entry.filename)]
            mode=entry.external_attr>>16
            if (entry.is_dir() or entry.create_system!=3 or stat.S_IFMT(mode)!=stat.S_IFREG
                    or mode&0o7777!=row['mode'] or entry.file_size!=row['size']):
                raise ValueError('Archive size/type/mode differs from native inventory')
            raw=archive.read(entry)
            if digest(raw)!=row['sha256']:raise ValueError('Archive bytes differ from inventory')
            payloads[entry.filename]=raw
    executable=inventory.get('executable_relative_path','bin/dot')
    if executable not in expected or expected[executable]['sha256']!=provenance.get('executable_sha256'):
        raise ValueError('Executable differs from completed build')
    index_name='third-party-notices/NOTICE-ORIGINS.json'
    origins=json.loads(payloads[index_name])
    indexed=set()
    for row in origins['notices']:
        name='third-party-notices/'+safe_name(row['path'])
        if (name in indexed or name not in payloads or name==index_name
                or digest(payloads[name])!=row.get('sha256') or len(payloads[name])!=row.get('size')
                or not isinstance(row.get('origin'),dict) or not isinstance(row['origin'].get('kind'),str)
                or not row['origin']['kind']):
            raise ValueError('Offline notice origin is missing, duplicated or changed')
        indexed.add(name)
    notices={name for name in payloads if name.startswith('third-party-notices/')}
    if indexed!=notices-{index_name} or not indexed:
        raise ValueError('Offline origin index does not cover every bundled notice')
    source=provenance.get('source',{})
    if (not source.get('url','').startswith('https://')
            or not re.fullmatch(r'[0-9a-f]{64}',source.get('sha256',''))
            or not source.get('license')
            or source.get('license_sha256') not in {expected[name]['sha256'] for name in indexed}):
        raise ValueError('Pinned upstream source/license text missing from bundled notices')
    return dict(artifact_id=candidate['artifact_id'],passed=True,qualified=False,
        license_compatibility_approved=False,archive_sha256=digest(archive_raw),
        provenance_sha256=digest(provenance_raw),inventory_sha256=digest(inventory_raw),
        engine_sha256=provenance['executable_sha256'],files_verified=len(expected),
        notice_payloads_verified=len(indexed),notice_index_sha256=digest(payloads[index_name]),
        offline_notice_origins=origins,source=source,
        checks=['Exact inventory, file bytes, sizes and encoded POSIX modes',
            'Every bundled notice has an offline origin entry and matching bytes',
            'Pinned upstream license text present; no compatibility approval inferred'])


def inspect_artifact(path):
    raw=read_bounded(path)
    with bounded_zip(raw) as archive:
        def read(entry,maximum=8*1024**2):
            if entry.file_size>maximum:raise ValueError('Excessive artifact member')
            return archive.read(entry)
        candidates=[entry for entry in archive.infolist() if entry.filename.split('/')[-1]=='candidate.json']
        if len(candidates)!=1:raise ValueError('Missing or ambiguous candidate artifact')
        candidate_raw=read(candidates[0]);candidate=json.loads(candidate_raw)
        prefix=candidates[0].filename.removesuffix('candidate.json')
        inventory_raw=read(archive.getinfo(prefix+'inventory.json'))
        archive_raw=read(archive.getinfo(prefix+'candidate.zip'),MAXIMUM)
        matching=[payload for entry in archive.infolist() if entry.filename.split('/')[-1]=='provenance.json'
                  for payload in [read(entry)] if digest(payload)==candidate['provenance_sha256']]
        if not matching:raise ValueError('Candidate provenance missing from artifact')
        result=inspect_candidate(candidate_raw,inventory_raw,matching[0],archive_raw)
    return dict(result,artifact_file=Path(path).name,artifact_sha256=digest(raw))


def collect(wheel,sdist,bundles,runtime_summary=None):
    wheel_raw,sdist_raw=read_bounded(wheel),read_bounded(sdist)
    spec=importlib.util.spec_from_file_location('package_checks',ROOT/'tools/validation/check-built-packages.py')
    packages=importlib.util.module_from_spec(spec);spec.loader.exec_module(packages)
    package=packages.package_inventory(wheel,sdist)
    if b'Apache License' not in (ROOT/'LICENSE').read_bytes():raise ValueError('Project license text missing')
    rows=[inspect_artifact(path) for path in bundles]
    if len({row['artifact_id'] for row in rows})!=len(rows):raise ValueError('Duplicate bundle ID')
    runtime=[]
    if runtime_summary is not None:
        summary=json.loads(read_bounded(runtime_summary,8*1024**2))
        if summary.get('passed') is not True:raise ValueError('Referenced runtime checks did not pass')
        for row in summary['reports']:
            parent=Path(runtime_summary).resolve().parent
            path=(parent/safe_name(row['file'])).resolve()
            if not path.is_relative_to(parent):raise ValueError('Runtime receipt escapes its evidence directory')
            raw=read_bounded(path,8*1024**2)
            if digest(raw)!=row['sha256']:raise ValueError('Runtime receipt changed')
            report=json.loads(raw)
            fixture=report['private_engine_fixture']
            bound=next((item for item in rows if item['artifact_id']==fixture['artifact_id']),None)
            if (bound is None or fixture['candidate_archive_sha256']!=bound['archive_sha256']
                    or fixture['provenance_sha256']!=bound['provenance_sha256']):
                raise ValueError('Runtime/cache receipt refers to another native bundle')
            for record in report['records']:
                packages.validate_engine_result(record['private_engine'],fixture,
                    json.loads((ROOT/'tests/fixtures/cases.json').read_bytes()),
                    'darwin' if report['system']=='Darwin' else 'linux')
            runtime.append(dict(file=row['file'],sha256=digest(raw),artifact_id=bound['artifact_id'],
                installed_modes=[r['mode'] for r in report['records']],
                independent_cache_notice_snapshot=False))
    return dict(kind='partial-offline-distribution-integrity',task='T066',task_complete=False,
        passed=True,qualified=False,license_compatibility_approved=False,
        captured_at=datetime.now(timezone.utc).isoformat(),tool_sha256=digest(Path(__file__).read_bytes()),
        package=dict(files_verified=len(package['files']),licenses=package['licenses'],
            wheel_sha256=digest(wheel_raw),sdist_sha256=digest(sdist_raw),
            source_state='Current source/data bytes; development archives, not final distributions'),
        bundles=rows,referenced_runtime_reports=runtime,
        limitations=['Byte/origin checks only; no per-component license compatibility approval',
            'No source hosting/retention offer or native signature/notarization approval',
            'Archive modes inspected offline; no new execution or filesystem mode measurement',
            'Referenced manager offline tests do not independently capture every cached notice',
            'Final bundles, Windows cache and complete support matrix remain pending'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('wheel','sdist','report'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--bundle',type=Path,action='append',required=True)
    parser.add_argument('--runtime-summary',type=Path)
    args=parser.parse_args()
    if args.report.exists() or args.report.is_symlink():parser.error('Choose a new report')
    result=collect(args.wheel,args.sdist,args.bundle,args.runtime_summary)
    with args.report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print('Offline byte/origin checks passed; license compatibility and T066 remain pending.')
