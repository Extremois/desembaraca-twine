import gzip,hashlib,importlib.util,io,json,re,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REV='62489c84dfd4cf95a11f38877087b795f7d5274c'
BASE=ROOT/'specs/003-add-cross-platform-support/evidence/source-access-notices-2026-10-20'
RUNS=[39531303569,39531303576,39531303564,39531303568,39531303590]
sha=lambda raw:hashlib.sha256(raw).hexdigest()
ns={'__file__':str(ROOT/'.tmp/github-actions-003.py')}
exec(compile((ROOT/'.tmp/github-actions-003.py').read_text().split('mode=sys.argv[1]')[0],ns['__file__'],'exec'),ns)
request=ns['request']
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
check=load('source_access_integrity','tools/validation/check-distribution-integrity.py')
notice=load('source_access_notice','tools/runtime/prepare-draft-notices.py')
def write(path,value):
    with path.open('xb') as stream:stream.write(value)
def jsonwrite(path,value):write(path,(json.dumps(value,indent=2)+'\n').encode())
def state():
    records=[]
    for ident in RUNS:
        run=request('/actions/runs/'+str(ident));assert run['head_sha']==REV
        jobs=request('/actions/runs/'+str(ident)+'/jobs?per_page=100')['jobs']
        records.append(dict(id=ident,name=run['name'],url=run['html_url'],status=run['status'],
            conclusion=run['conclusion'],jobs=[dict(id=j['id'],name=j['name'],conclusion=j['conclusion'],
                active_steps=[s['name'] for s in j['steps'] if s['status']=='in_progress']) for j in jobs]))
    return records
records=state()
if sys.argv[1]=='status':
    print(json.dumps(records));raise SystemExit
assert sys.argv[1]=='capture'
assert all(r['conclusion']=='success' for r in records),records
assert not BASE.exists()
BASE.mkdir()
old=json.loads((ROOT/'specs/003-add-cross-platform-support/evidence/distribution-integrity-2026-10-20/final-check.json').read_bytes())
old_engines={b['artifact_id']:b['engine_sha256'] for b in old['bundles']}
rows=[]
for run in records[:-1]:
    artifacts=request('/actions/runs/'+str(run['id'])+'/artifacts')['artifacts']
    for artifact in artifacts:
        if '-unqualified-'+REV not in artifact['name']:continue
        assert not artifact['expired']
        path=ROOT/'.tmp'/('actions-artifact-'+str(artifact['id'])+'.zip')
        if not path.exists():write(path,request('/actions/artifacts/'+str(artifact['id'])+'/zip',raw=True))
        result=check.inspect_artifact(path)
        ident=result['artifact_id'];assert ident not in {r['artifact_id'] for r in rows}
        assert result['engine_sha256']==old_engines[ident]
        folder=BASE/ident;folder.mkdir()
        raw=path.read_bytes()
        with check.bounded_zip(raw) as outer:
            candidates=[e for e in outer.infolist() if e.filename.split('/')[-1]=='candidate.json']
            candidate_raw=outer.read(candidates[0]);candidate=json.loads(candidate_raw)
            prefix=candidates[0].filename.removesuffix('candidate.json')
            inventory_raw=outer.read(prefix+'inventory.json')
            prov=next(outer.read(e) for e in outer.infolist() if e.filename.split('/')[-1]=='provenance.json'
                and sha(outer.read(e))==candidate['provenance_sha256'])
            record=json.loads(prov)
            with check.bounded_zip(outer.read(prefix+'candidate.zip')) as bundle:
                source=bundle.read('third-party-notices/SOURCE-REFERENCES.txt')
                index=bundle.read('third-party-notices/NOTICE-ORIGINS.json')
                sdk=notice.sdk_archive_identity(record['sdk']['facts']) if ident.startswith('linux-') else None
                expected=notice.source_access_notice(record['source'],ident,sdk)
                assert source==expected if sdk else source.startswith(expected)
            payloads={'candidate.json':candidate_raw,'inventory.json':inventory_raw,'provenance.json.gz':gzip.compress(prov,mtime=0),
                'SOURCE-REFERENCES.txt':source,'NOTICE-ORIGINS.json.gz':gzip.compress(index,mtime=0)}
            for e in outer.infolist():
                name=Path(e.filename).name
                if re.fullmatch(r'(?:corpus|network|runtime|runtime-corpus|runtime-network)-(?:312|314)\.json',name):
                    data=outer.read(e);report=json.loads(data);assert report.get('passed') is True
                    assert name not in payloads;payloads[name]=data
        jsonwrite(folder/'archive-check.json',result)
        for name,data in payloads.items():write(folder/name,data)
        row=dict(artifact_id=ident,run_id=run['id'],actions_artifact_id=artifact['id'],
            artifact_sha256=sha(raw),engine_sha256=result['engine_sha256'],engine_unchanged=True,
            archive_sha256=candidate['archive_sha256'],provenance_sha256=candidate['provenance_sha256'],
            files_verified=result['files_verified'],notice_payloads_verified=result['notice_payloads_verified'],
            source_notice_matches_generator=True,glibc_section_6_notice=ident.startswith('linux-glibc-'),
            approved=False,qualified=False,
            retained_files={name:dict(sha256=sha(data),bytes=len(data)) for name,data in payloads.items()})
        row['retained_files']['archive-check.json']=dict(sha256=sha((folder/'archive-check.json').read_bytes()),bytes=(folder/'archive-check.json').stat().st_size)
        jsonwrite(folder/'summary.json',row);rows.append(row)
assert len(rows)==6
foundation=[]
for job in records[-1]['jobs']:
    if not job['name'].startswith('Pure contracts ('):continue
    raw=request('/actions/jobs/'+str(job['id'])+'/logs',raw=True)
    text=raw.decode('utf-8-sig');match=re.search(r'Ran (\d+) tests in ([0-9.]+)s',text)
    assert match and int(match[1])==251
    skip=re.search(r'OK \(skipped=(\d+)\)',text)
    foundation.append(dict(job_id=job['id'],name=job['name'],tests=int(match[1]),skipped=int(skip[1]) if skip else 0,raw_log_sha256=sha(raw)))
assert len(foundation)==6
summary=dict(kind='source-access-notice-native-package-review',revision=REV,task='T030/T052/T066',task_complete=False,
    passed=True,approved=False,qualified=False,runs=records,foundation=foundation,artifacts=rows,
    files_verified=sum(r['files_verified'] for r in rows),notice_payloads_verified=sum(r['notice_payloads_verified'] for r in rows),
    limitations=['No completed corresponding-source delivery or modified-library relink proof',
        'ISO/entity and remaining third-party compatibility reviews remain open',
        'No signature, release publication or complete support-cell qualification',
        'Existing cache snapshots refer to previous bundle hashes; not transferred to these archives'])
jsonwrite(BASE/'summary.json',summary)
write(BASE/'capture.py',Path(__file__).read_bytes())
print(json.dumps(dict(passed=True,artifacts=len(rows),files_verified=summary['files_verified'],foundation_slots=len(foundation))))
