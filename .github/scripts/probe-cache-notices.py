"""Independently read notices in a real private native-engine cache."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile


def digest(raw):return hashlib.sha256(raw).hexdigest()


def snapshot(root,expected):
    root=Path(root).resolve()
    parent=root/'third-party-notices'
    if parent.is_symlink() or not parent.is_dir():raise ValueError('Missing or linked notice directory')
    found={};total=0
    for path in parent.rglob('*'):
        if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):
            raise ValueError('Notice path is a link')
        if path.is_dir():continue
        name=path.relative_to(root).as_posix()
        if not path.is_file() or name not in expected:raise ValueError('Uninventoried cached notice')
        entry=expected[name]
        with path.open('rb') as stream:raw=stream.read(16*1024**2+1)
        total+=len(raw)
        if total>16*1024**2 or len(raw)!=entry['size'] or digest(raw)!=entry['sha256']:
            raise ValueError('Cached notice is missing or altered')
        if os.name!='nt' and path.stat().st_mode&0o777!=entry.get('mode',0o644):
            raise ValueError('Cached notice mode differs from inventory')
        found[name]=digest(raw)
    if set(found)!=set(expected):raise ValueError('Cached notice inventory is incomplete')
    return found


def collect(driver,package,provenance):
    sys.path.insert(0,str(driver/'tests'))
    import common
    from runtime_support import ControlledTransport,blocked_network
    from twine_edge_overlap.runtime import RuntimeManager,load_manifest
    record=json.loads(provenance.read_bytes())
    candidate=json.loads((package/'candidate.json').read_bytes())
    inventory_raw=(package/'inventory.json').read_bytes();inventory=json.loads(inventory_raw)
    payload=(package/'candidate.zip').read_bytes()
    arch={'arm64':'aarch64','AMD64':'x86_64'}.get(platform.machine(),platform.machine())
    if (sys.platform not in ('linux','darwin') or record.get('completed') is not True
            or record.get('native_os')!=sys.platform or record.get('native_arch')!=arch
            or digest(payload)!=candidate['archive_sha256']
            or digest(inventory_raw)!=candidate['inventory_sha256']
            or digest(provenance.read_bytes())!=candidate['provenance_sha256']
            or inventory['provenance_sha256']!=candidate['provenance_sha256']):
        raise ValueError('Private bundle does not match native host and build')
    with tempfile.TemporaryDirectory(prefix='native-cache-notices-') as folder,blocked_network():
        work=Path(folder)
        data=dict(load_manifest().data)
        data.update(schema_version=2,platform=sys.platform,artifact_arch=arch,
            abi=record['recipe']['abi'],build_variant='private-cache-notices-only',
            minimum_libc='0',minimum_kernel='0',minimum_os='15',files=inventory['files'],
            executable_relative_path='bin/dot',generated_files=[],
            url='https://runtime.invalid/artifact.zip',allowed_redirect_hosts=['runtime.invalid'],
            archive_sha256=digest(payload))
        data['notices']=[dict(data['notices'][0],destination='third-party-notices/private-integration-application.txt')]
        data.pop('plugin_relative_path',None)
        manifest=work/'fixture.json';manifest.write_text(json.dumps(data),encoding='utf-8')
        transport=ControlledTransport(payload)
        manager=RuntimeManager(artifact=load_manifest(manifest),cache_root=work/'cache com espaços ação',opener=transport)
        handle=manager.ensure()
        expected={r['path']:r for r in inventory['files'] if r['path'].startswith('third-party-notices/')}
        expected.update({r['destination']:dict(r,size=(handle.root/r['destination']).stat().st_size)
                         for r in data['notices']})
        before=snapshot(handle.root,expected)
        manager.opener=ControlledTransport(error=AssertionError('Notice check attempted offline acquisition'))
        reused=manager.ensure()
        after=snapshot(reused.root,expected)
        if reused.generation_id!=handle.generation_id or manager.opener.calls or len(transport.calls)!=1:
            raise ValueError('Notice cache did not reuse the original generation offline')
        # Alter only a test-owned notice, then restore its exact bytes in finally.
        target=handle.root/next(iter(sorted(expected)))
        original=target.read_bytes()
        rejected=False
        try:
            target.write_bytes(original+b'corrupted')
            try:snapshot(handle.root,expected)
            except ValueError:rejected=True
        finally:target.write_bytes(original)
        restored=snapshot(handle.root,expected)
        if not rejected or restored!=before:raise ValueError('Corrupted notice was accepted or not restored')
        return dict(kind='private-installed-cache-notice-integrity',passed=True,qualified=False,
            engine_sha256=record['executable_sha256'],provenance_sha256=digest(provenance.read_bytes()),
            python=platform.python_version(),system=platform.system(),arch=platform.machine(),
            before=before,after=after,notice_files=len(expected),initial_acquisition_calls=len(transport.calls),
            offline_acquisition_calls=len(manager.opener.calls),same_generation=True,
            corruption_rejected=rejected,restored_snapshot_matches=restored==before,modes_checked=os.name!='nt',
            scope='Real native engine probes and private manager cache; fixture acquisition, Python-only network guard; no license/signature/support approval')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('driver','package','provenance','report'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists() or args.report.is_symlink():parser.error('Choose a new report')
    result=collect(args.driver.resolve(),args.package.resolve(),args.provenance.resolve())
    with args.report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
