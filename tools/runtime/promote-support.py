"""Validate evidence and write an exclusive, reviewable per-cell proposal. Never publish."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import stat
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from twine_edge_overlap.runtime_catalog import GATES, COMMON_GATES, PYTHONS, CatalogError, read_json, support_status
from twine_edge_overlap.runtime_snapshot import META_KEYS, canonical_inventory, inventory_digest, fingerprint


def verified_log(item, root):
    name=item.get('path','')
    if (not isinstance(name,str) or not name or '\\' in name or ':' in name
            or Path(name).is_absolute() or any(part in ('','.','..') for part in name.split('/'))):
        raise ValueError('Log path must remain relative to the evidence root')
    path=root/name
    current=path
    while current!=root:
        if current.is_symlink():raise ValueError('Evidence logs cannot be links')
        current=current.parent
    if not stat.S_ISREG(path.stat().st_mode):raise ValueError('Evidence logs must be regular files')
    with path.open('rb') as stream:content=stream.read(8*1024**2+1)
    if len(content)>8*1024**2 or hashlib.sha256(content).hexdigest()!=item.get('sha256'):
        raise ValueError('Evidence log is absent, oversized or changed')


def validate_snapshot(snapshot, target):
    if not isinstance(snapshot,dict) or snapshot.get('schema')!='rolling-host-v1' or snapshot.get('inventory_schema')!='package-inventory-v1':
        raise ValueError('Canonical rolling reference required')
    manager=snapshot['manager']
    records=snapshot['records']
    if manager not in ('pacman','rpm') or not isinstance(records,list):raise ValueError('Invalid package inventory')
    # Round-trip through the same strict parser to check fields/order/duplicates/limits.
    separator=' ' if manager=='pacman' else '\t'
    payload=''.join(separator.join(row)+'\n' for row in records).encode('utf-8')
    canonical=canonical_inventory(manager,payload)
    metadata={key:snapshot[key] for key in META_KEYS}
    if (canonical!=records or inventory_digest(manager,records)!=snapshot['inventory_sha256']
            or fingerprint(metadata,manager,records)!=snapshot['snapshot_id']
            or snapshot['snapshot_id']!=target.get('snapshot_id')
            or metadata['distribution_id']!=target['distribution_id'] or metadata['channel']!=target['channel']
            or metadata['native_arch']!=target['arch']):
        raise ValueError('Rolling inventory/target fingerprint mismatch')


def validate_record(item,target,root):
    if not isinstance(item.get('checks'),dict) or any(type(value) is not bool for value in item['checks'].values()):
        raise ValueError('Gate results must be explicit booleans')
    audit_only=item.get('evidence_scope')=='artifact-license-audit'
    if audit_only and (item.get('python_minor') is not None or item['checks']!={'licenses':True}):
        raise ValueError('Shared artifact audit may grant only the license gate')
    if (item.get('environment_kind') not in ('github-actions','native') or item.get('passed') is not True
            or item.get('target_id')!=target['id'] or item.get('snapshot_id')!=target.get('snapshot_id')):
        raise ValueError('Evidence does not identify a supported CI environment for this cell')
    if not audit_only and (item.get('os')!=target['os'] or item.get('architecture')!=target['arch']
            or item.get('distribution_id')!=target['distribution_id'] or item.get('cpu_variant')!=target['cpu_variant']):
        raise ValueError('Execution environment differs from target')
    required=('id','artifact_id','recipe_revision','captured_at')+(() if audit_only else ('image_id','kernel','cpu'))
    for key in required:
        if not isinstance(item.get(key),str) or not item[key]:raise ValueError('Missing evidence field: '+key)
    if not re.fullmatch(r'[0-9a-f]{40,64}',item.get('application_revision','')) or not re.fullmatch(r'[0-9a-f]{64}',item.get('artifact_sha256','')):
        raise ValueError('Revision/artifact SHA is invalid')
    if not audit_only and any(not re.fullmatch(r'[0-9a-f]{64}',item.get(key,'')) for key in ('package_sha256','image_digest')):
        raise ValueError('Package and environment image hashes required')
    actual=item.get('os_version','')
    if not audit_only and ((target['version']!='rolling' and not (actual==target['version'] or actual.startswith(target['version']+'.'))) or item.get('channel')!=target['channel']):
        raise ValueError('Evidence version/channel differs from target')
    minor=item.get('python_minor')
    if minor is None and not set(item['checks']).issubset(COMMON_GATES):
        raise ValueError('Python-dependent trials cannot be shared across qualification slots')
    if minor is not None and (minor not in PYTHONS or not re.fullmatch(re.escape(minor)+r'\.\d+',item.get('python_patch','')) or not item.get('python_origin')):
        raise ValueError('Python patch/origin does not match its qualification slot')
    if not item.get('commands') or not item.get('logs'):raise ValueError('Commands and durable logs required')
    if not item.get('reviewer'):raise ValueError('Final evidence requires an identified reviewer')
    if item.get('source_state')!='committed':raise ValueError('Dirty or unverified candidate is not eligible for official support')
    for log in item['logs']:verified_log(log,root)
    if target['version']=='rolling' and not audit_only:
        validate_snapshot(item.get('environment_snapshot'),target)
        if item['kernel']!=item['environment_snapshot']['kernel_release']:
            raise ValueError('Evidence kernel differs from canonical rolling fingerprint')
    if item['checks'].get('installation'):
        installation=item.get('installation',{})
        if any(installation.get(key) is not True for key in ('wheel','sdist','remote','outside_checkout','console','module')):
            raise ValueError('Remote, wheel, sdist and external command installation evidence required')
    if item['checks'].get('licenses'):
        audit=item.get('license_audit',{})
        if (audit.get('approved') is not True or not audit.get('reviewer')
                or audit.get('artifact_sha256')!=item['artifact_sha256'] or not audit.get('components')):
            raise ValueError('Reviewed license/source audit for this artifact required')
        for component in audit['components']:
            if (not component.get('name') or not component.get('license_expression')
                    or not component.get('source_url','').startswith('https://')
                    or not re.fullmatch(r'[0-9a-f]{64}',component.get('source_sha256',''))):
                raise ValueError('Component source/license identity incomplete')
        verified_log(audit['log'],root)
    if item['checks'].get('offline'):
        network=item.get('network',{})
        if network.get('observation') not in ('github-actions-log','native-trace') or type(network.get('attempts')) is not int or network['attempts']!=0 or not network.get('reviewer'):
            raise ValueError('Offline gate requires reviewed GitHub Actions network logs')
        verified_log(network['log'],root)
    if item['checks'].get('preservation'):
        cases=read_json(ROOT/'tests/fixtures/cases.json')
        corpus=item.get('corpus',[])
        by_name={case.get('case'):case for case in corpus}
        if len(by_name)!=len(corpus) or set(by_name)!={case['case'] for case in cases}:
            raise ValueError('Full reference corpus required')
        for case in cases:
            row=by_name[case['case']]
            raw=(ROOT/'tests/fixtures'/case['file']).read_bytes().replace(b'\r\n',b'\n')
            accepted={hashlib.sha256(raw).hexdigest(),hashlib.sha256(raw.replace(b'\n',b'\r\n')).hexdigest()}
            if (row.get('input_sha256') not in accepted or not re.fullmatch(r'[0-9a-f]{64}',row.get('output_sha256',''))
                    or row.get('original_preserved') is not True or row.get('semantics_preserved') is not True):
                raise ValueError('Corpus hashes/invariants missing')
            before,after=row.get('before',[]),row.get('after',[])
            if len(before)!=3 or len(after)!=3 or any(type(n) is not int or n<0 for n in before+after) or any(a>b for a,b in zip(after,before)):
                raise ValueError('Corpus metrics regress or are incomplete')
            if before!=case['before']:raise ValueError('Corpus baseline differs from the known source fixture')
            if case['known_resolvable'] and after!=[0,0,0]:raise ValueError('Known reference is not clean')
    if item['checks'].get('twine'):
        twine=item.get('twine',{})
        cases=read_json(ROOT/'tests/fixtures/cases.json')
        required={case['case'] for case in cases if case['known_resolvable']}
        outputs=twine.get('outputs',[])
        if (not twine.get('version') or not twine.get('reviewer') or len(outputs)!=6
                or {row.get('case') for row in outputs}!=required
                or any(row.get('reopened') is not True or not re.fullmatch(r'[0-9a-f]{64}',row.get('sha256','')) for row in outputs)):
            raise ValueError('Six real Twine reopenings and reviewer are required')
        verified_log(twine['log'],root)


def propose(registry,target_id,records,evidence_root):
    result=copy.deepcopy(registry)
    targets=[target for target in result['targets'] if target['id']==target_id]
    if len(targets)!=1:raise ValueError('Target must be unique')
    target=targets[0]
    support_status(target,{})  # Detect duplicate/missing Python slots before changes.
    if not records:raise ValueError('No evidence supplied')
    if target['version']=='rolling' and target.get('snapshot_id') is None:
        captured={item.get('snapshot_id') for item in records}
        if len(captured)!=1 or not re.fullmatch(r'[0-9a-f]{64}',next(iter(captured)) or ''):
            raise ValueError('Both Python slots must reference one real rolling capture')
        target['snapshot_id']=captured.pop()
    root=Path(evidence_root).resolve()
    for item in records:validate_record(item,target,root)
    identities={(item['application_revision'],item['artifact_id'],item['artifact_sha256']) for item in records}
    if len(identities)!=1:raise ValueError('Evidence revisions/artifacts differ')
    execution_environments={(item['image_digest'],item['kernel']) for item in records if item.get('evidence_scope')!='artifact-license-audit'}
    if len(execution_environments)!=1:raise ValueError('Native execution baseline differs between records')
    revision,artifact,sha=identities.pop()
    ids=[item['id'] for item in records]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate evidence ID')
    evidence=result.setdefault('evidence',{})
    for item in records:
        record_sha=hashlib.sha256(json.dumps(item,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        # Full inventories/corpus remain in the reviewed evidence files, not in
        # every packaged Python slot. Runtime classification needs only summaries.
        summary={key:value for key,value in item.items() if key not in ('environment_snapshot','corpus','log_text')}
        summary['qualified_record_sha256']=record_sha
        if item['id'] in evidence and evidence[item['id']]!=summary:raise ValueError('Evidence ID already identifies different bytes')
        evidence[item['id']]=summary
    target.update(application_revision=revision,artifact_id=artifact,artifact_sha256=sha,
                  evidence_ids=[item['id'] for item in records if item.get('python_minor') is None])
    for slot in target['python_qualifications']:
        refs=[item['id'] for item in records if item.get('python_minor')==slot['python_minor']]
        if not refs:raise ValueError('Both Python slots require their own GitHub Actions evidence')
        slot.update(status='validada',application_revision=revision,artifact_id=artifact,evidence_ids=refs,pending_reason=None)
    if support_status(target,evidence)!='validada':raise ValueError('Required common/Python gates are incomplete or failed')
    required_cases={case['case'] for case in read_json(ROOT/'tests/fixtures/cases.json') if case['known_resolvable']}
    for minor in PYTHONS:
        outputs={name:set() for name in required_cases}
        for item in records:
            if item.get('python_minor')==minor and item['checks'].get('preservation'):
                for row in item.get('corpus',[]):
                    if row['case'] in outputs:outputs[row['case']].add(row['output_sha256'])
        reviews=[item['twine'] for item in records if item.get('python_minor') in (None,minor) and item['checks'].get('twine')]
        if not any(all(row['sha256'] in outputs[row['case']] for row in review['outputs']) for review in reviews):
            raise ValueError('Twine review hashes do not identify the verified outputs of Python '+minor)
    key=lambda item:tuple(item.get(name) for name in ('os','distribution_id','version','channel','arch','cpu_variant','snapshot_id'))
    if any(other['id']!=target_id and key(other)==key(target) for other in result['targets']):
        raise ValueError('Ambiguous duplicate cell identity')
    target.update(status='validada',pending_reason=None)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry',type=Path,default=ROOT/'tools/runtime/support-targets.json')
    parser.add_argument('--target',required=True)
    parser.add_argument('--evidence',type=Path,action='append',required=True)
    parser.add_argument('--evidence-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        records=[]
        for path in args.evidence:
            data=read_json(path,maximum=64*1024**2)
            records.extend(data if isinstance(data,list) else [data])
        proposal=propose(read_json(args.registry),args.target,records,args.evidence_root)
        with args.output.open('x',encoding='utf-8') as stream:json.dump(proposal,stream,indent=2,ensure_ascii=False);stream.write('\n')
        print('Proposal written for review; active catalog and registry unchanged.')
    except (OSError,ValueError,KeyError,TypeError,AttributeError) as exc:parser.exit(1,'Promotion refused: '+str(exc)+'\n')


if __name__=='__main__':main()
