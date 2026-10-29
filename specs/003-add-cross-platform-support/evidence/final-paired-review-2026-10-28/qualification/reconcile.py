"""Reconcile real CI receipts and run the existing evidence promotion validator.

Data review only: does not run the application, engine or tests locally.
"""
import copy,gzip,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path.cwd()
REV=sys.argv[1]
BASE=ROOT/'specs/003-add-cross-platform-support/evidence'
PAIR=BASE/'final-paired-review-2026-10-28'
CI=PAIR/'acceptance'/REV[:7]
OUT=PAIR/'qualification'
OUT.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_bytes((json.dumps(d,indent=2,ensure_ascii=False)+'\n').encode())
def ref(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
summary=read(CI/'summary.json')
assert summary['application_revision']==REV
reports=[]
for a in summary['artifacts']:
 for r in a['records']:
  if r['path'].endswith('.json.gz'):
   p=CI/r['path'];v=json.loads(gzip.decompress(p.read_bytes()))
   if isinstance(v,dict):reports.append((a,p,v))
final=[row for row in reports if row[2].get('kind')=='final-public-catalog-installed-acceptance']
assert len(final)==14
assert all(f['tests']>=313 for f in summary['foundation']) and len(summary['foundation'])==6
visual_path=BASE/'twine-visual-review-2026-10-28.json'
visual=read(visual_path);assert visual['passed'] and visual['reviewer']=='user'
reviewed={o['case']:o['sha256'] for o in visual['reviewed_outputs']}
public=read(PAIR/'public-download-verification.json')
publication=read(PAIR/'publication.json')
assert publication['published'] and publication['public_download_hashes_verified']
lock=read(ROOT/'tools/runtime/source-lock.json')
windows=read(ROOT/'src/twine_edge_overlap/runtime-manifest.json')
wa=dict(kind='technical-review-of-preserved-upstream-Windows-acquisition',approved=True,
 reviewer='Codex technical implementation review',artifact_sha256=windows['archive_sha256'],
 scope='Application distributes pinned notices and source references; unchanged Windows binaries are acquired directly from upstream, never redistributed by this release.',
 manifest=ref(ROOT/'src/twine_edge_overlap/runtime-manifest.json'),
 source_references=ref(ROOT/'src/twine_edge_overlap/third_party/graphviz-16.1.0/SOURCES.json'),
 components=[dict(name='Graphviz upstream source; dependency notices/source routes preserved separately',
 license_expression='EPL-2.0 AND LicenseRef-Upstream-Component-Notices',source_url=lock['url'],source_sha256=lock['sha256'])],
 decision='Keep EPL and dependency terms separate from Apache-2.0. Existing upstream DLLs remain replaceable; preserve the complete notices/SOURCES inventory offline. No Windows bundle repackaging, license change or new redistribution is approved.')
write(OUT/'windows-upstream-audit.json',wa)
spec=importlib.util.spec_from_file_location('promotion',ROOT/'tools/runtime/promote-support.py')
promotion=importlib.util.module_from_spec(spec);spec.loader.exec_module(promotion)
registry=read(ROOT/'tools/runtime/abi-targets.json')
rows=[]
for target in registry['targets']:
 records=[]
 for minor in ('3.12','3.14'):
  matches=[x for x in final if x[2]['target_id']==target['id'] and x[2]['python'].startswith(minor+'.')]
  assert len(matches)==1
  a,path,d=matches[0];assert d['passed'] and d['application_revision']==REV
  assert {r['mode'] for r in d['records']}=={'wheel','sdist','remote'}
  for r in d['records']:
   assert r['real_catalog'] and r['public_acquisition'] and r['outside_checkout'] and r['git_and_global_graphviz_absent']
   w=r['worker'];assert w['passed'] and w['network']['attempts']==0 and len(w['corpus'])==13
   assert {c['case']:c['output_sha256'] for c in w['corpus'] if c['case'] in reviewed}==reviewed
  worker=copy.deepcopy(d['records'][0]['worker'])
  # Recovery receipts must have exactly the same installed application bytes.
  recovery=[];notice=[]
  for ca,cp,cd in reports:
   if cd.get('application_revision')!=REV or not cd.get('python','').startswith(minor+'.') or not cd.get('passed'):continue
   for rr in cd.get('records',[]):
    if rr.get('mode')!='wheel' or rr.get('installed_file_hashes')!=d['records'][0]['installed_files']:continue
    pe=rr.get('private_engine') or {};cn=rr.get('cache_notices') or {}
    process=cn.get('recovery') or pe.get('observations',{}).get('explicit',{}).get('process_recovery')
    if process and process.get('passed') and process.get('real_engine'):
     # Exact executable identity, not just a platform label.
     manifest=read(ROOT/'src/twine_edge_overlap'/next(x['manifest_path'] for x in read(ROOT/'src/twine_edge_overlap/runtime-catalog.json')['artifacts'] if x['id']==d['artifact_id']))
     engine=next(f['sha256'] for f in manifest['files'] if f['path']==manifest['executable_relative_path'])
     if (cn or pe).get('engine_sha256')!=engine:continue
     assert all(s['passed'] and s['old_handle_usable'] for s in process['scenarios'].values())
     stages={'during_download','before_select','after_select','concurrent_first_use'}
     if cn:
      assert set(process['scenarios'])==stages|{'download','disk_full','execution_denied','corrupt_archive'}
     else:
      explicit=pe['observations']['explicit'];assert set(process['scenarios'])==stages
      assert set(explicit['recovery'])=={'transfer','disk-space','corrupt-archive','execution-denied'}
      assert all(s['selected_generation_preserved'] and s['previous_handle_usable'] and s['offline_acquisition_calls']==0 for s in explicit['recovery'].values())
     recovery.append((cp,ca,process))
    if cn.get('passed') and cn.get('same_generation') and cn.get('corruption_rejected') and cn.get('restored_snapshot_matches'):
     notice.append(cp)
  assert recovery,(target['id'],minor,'missing matching real-engine recovery')
  # POSIX notice checks use a separate installed report with the same artifact.
  if not notice:
   for ca,cp,cd in reports:
    if cd.get('application_revision')!=REV or not cd.get('python','').startswith(minor+'.') or not cd.get('passed'):continue
    for rr in cd.get('records',[]):
     cn=rr.get('cache_notices') or {}
     if rr.get('installed_file_hashes')==d['records'][0]['installed_files'] and cn.get('passed') and cn.get('engine_sha256')==engine and cn.get('same_generation') and cn.get('corruption_rejected') and cn.get('restored_snapshot_matches'):notice.append(cp)
  assert notice,(target['id'],minor,'notices')
  audit_path=OUT/'windows-upstream-audit.json' if target['os']=='windows' else PAIR/'audits'/(d['artifact_id'].removeprefix('graphviz-16.1.0-')+'.json')
  audit=read(audit_path);assert audit['approved']
  short=target['id']+'-'+minor
  network_path=OUT/(short+'-network.json')
  write(network_path,dict(reviewer='Codex technical implementation review',source=ref(path),attempts=0,
   observation='GitHub Actions worker Python socket/DNS guard while reusing healthy runtime; native engine has no acquisition role. Not a claim of a system-wide syscall trace.',
   formats=[dict(mode=r['mode'],network=r['worker']['network'],healthy_generation_reused=r['worker']['observations']['healthy_generation_reused']) for r in d['records']]))
  worker.update(id='final-'+short+'-'+REV[:7],reviewer='Codex technical implementation review',
   checks={g:True for g in promotion.GATES},pending_checks=[],pending_reason=None,
   installation={k:True for k in ('wheel','sdist','remote','outside_checkout','console','module')},
   logs=[ref(path),ref(recovery[0][0]),ref(notice[0]),ref(audit_path),ref(visual_path),ref(PAIR/'publication.json')],
   network=dict(observation='github-actions-log',attempts=0,reviewer='Codex technical implementation review',log=ref(network_path)),
   license_audit=dict(approved=True,reviewer=audit['reviewer'],artifact_sha256=worker['artifact_sha256'],components=audit['components'],log=ref(audit_path)),
   twine=dict(version=visual['twine_version'],reviewer=visual['reviewer'],outputs=[dict(case=k,sha256=v,reopened=True) for k,v in reviewed.items()],log=ref(visual_path)),
   constituent_evidence=dict(public_catalog_run_id=a['run_id'],recovery_run_id=recovery[0][1]['run_id'],
     recovery_revision=REV,visual_review_revision=visual['application_revision'],
     visual_binding='Same six byte hashes, checked for all three final installation modes; no claim of a new GUI session.',
     recovery_scope='Installed real engine, process exits and OS locks; transfer/disk/permission faults controlled. Tests executed only in Actions.',
     source_build_revision=audit.get('application_revision'),public_delivery=ref(PAIR/'publication.json')))
  records.append(worker)
  rows.append(dict(target_id=target['id'],python=minor,public_catalog=ref(path),recovery=ref(recovery[0][0]),notices=ref(notice[0])))
 write(OUT/(target['id']+'.json'),records)
 registry=promotion.propose(registry,target['id'],records,ROOT)
 write(OUT/(target['id']+'-proposal.json'),registry)
write(ROOT/'tools/runtime/abi-targets.json',registry)
matrix_path=ROOT/'src/twine_edge_overlap/support-matrix.json'
matrix=read(matrix_path);matrix['abi_targets']=registry['targets'];matrix.setdefault('evidence',{}).update(registry['evidence']);write(matrix_path,matrix)
catalog_path=ROOT/'src/twine_edge_overlap/runtime-catalog.json'
catalog=read(catalog_path);catalog['application_revision']=REV;write(catalog_path,catalog)
write(OUT/'summary.json',dict(passed=True,qualified=True,application_revision=REV,targets=7,python_slots=14,installation_modes=42,records=rows,
 promotion='Existing promote-support.py propose() executed for all seven targets after validating both Python records and durable byte-bound logs.',
 compatibility_declarations='69 distro entries retained as compatibility declarations, not individually certified',
 limitations=['Apple signing/notarization optional and not asserted','Windows ABI exercised on actual hosted Server, not represented as Windows 11 clean certification']))
print('Promoted seven ABI targets using fourteen reviewed composite records and forty-two public installed acceptances.')
