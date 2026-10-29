"""Read notices from a private Windows cache prepared from the pinned public ZIP."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import tempfile
import urllib.request
from types import SimpleNamespace


def digest(raw):return hashlib.sha256(raw).hexdigest()


def collect(driver,review_directory=None):
    if sys.platform!='win32':raise ValueError('Windows cache check requires Windows')
    sys.path.insert(0,str(driver/'tests'))
    import common
    from runtime_support import ControlledTransport,blocked_network,archive_bytes
    from twine_edge_overlap.application import run
    from twine_edge_overlap.formats.profile import parse,verify
    import twine_edge_overlap
    from twine_edge_overlap.runtime import RuntimeManager,load_manifest,_Redirects
    spec=importlib.util.spec_from_file_location('private_cache_notices',driver/'.github/scripts/probe-cache-notices.py')
    notices=importlib.util.module_from_spec(spec);spec.loader.exec_module(notices)
    artifact=load_manifest()
    if artifact.data['platform']!='windows':raise ValueError('Expected pinned Windows manifest')
    manifest_raw=(Path(twine_edge_overlap.__file__).parent/'runtime-manifest.json').read_bytes()
    upstream=urllib.request.build_opener(_Redirects(artifact.data['allowed_redirect_hosts']))
    class Download:
        calls=0
        def open(self,request,timeout):
            self.calls+=1
            return upstream.open(request,timeout=timeout)
    download=Download()
    with tempfile.TemporaryDirectory(prefix='windows-cache-notices-') as folder:
        manager=RuntimeManager(artifact=artifact,cache_root=Path(folder)/'cache com espaços ação',opener=download)
        handle=manager.ensure()
        expected={row['destination']:dict(row,size=(handle.root/row['destination']).stat().st_size)
                  for row in artifact.data['notices']}
        before=notices.snapshot(handle.root,expected)
        manager.opener=ControlledTransport(error=AssertionError('Windows notice cache attempted acquisition offline'))
        with blocked_network():
            reused=manager.ensure()
            after=notices.snapshot(reused.root,expected)
            target=handle.root/next(iter(sorted(expected)))
            original=target.read_bytes();rejected=False
            try:
                target.write_bytes(original+b'corrupted')
                try:notices.snapshot(handle.root,expected)
                except ValueError:rejected=True
            finally:target.write_bytes(original)
            restored=notices.snapshot(handle.root,expected)
            cases=[]
            fixtures=driver/'tests/fixtures'
            for case in json.loads((fixtures/'cases.json').read_bytes()):
                raw=(fixtures/case['file']).read_bytes();story=Path(folder)/case['file'];story.write_bytes(raw)
                result=run(story,runtime_provider=manager.ensure);output=result.path.read_bytes()
                verify(parse(raw),parse(output))
                if story.read_bytes()!=raw or any(a>b for a,b in zip(result.after.values,result.before.values)):
                    raise ValueError('Windows corpus changed input bytes or regressed geometry')
                if case['known_resolvable'] and result.after.values!=(0,0,0):
                    raise ValueError('Windows reference did not reach zero overlaps')
                if case['known_resolvable'] and review_directory is not None:
                    with (review_directory/case['file']).open('xb') as exported:exported.write(output)
                cases.append(dict(case=case['case'],input_sha256=digest(raw),output_sha256=digest(output),
                    before=result.before.values,after=result.after.values,original_preserved=True,semantics_preserved=True))
        if (download.calls!=1 or manager.opener.calls or handle.generation_id!=reused.generation_id
                or before!=after or restored!=before or not rejected):
            raise ValueError('Windows notice cache failed offline integrity or restoration')
        executable=next(row for row in artifact.data['files'] if row['path']==artifact.data['executable_relative_path'])
        # Reuse verified installed bytes; recovery never downloads or relies on a system Graphviz.
        payload=archive_bytes({row['path']:(handle.root/row['path']).read_bytes() for row in artifact.data['files']})
        spec=importlib.util.spec_from_file_location('installed_recovery',driver/'.github/scripts/probe-installed-recovery.py')
        recovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(recovery)
        recovered=recovery.exercise(SimpleNamespace(driver=driver),
            SimpleNamespace(payload=payload,record=dict(executable_sha256=executable['sha256'])),artifact=artifact)
        return dict(kind='windows-installed-cache-notice-integrity',passed=True,qualified=False,
            system='Windows',python=platform.python_version(),arch=platform.machine(),os_version=platform.version(),
            manifest_sha256=digest(manifest_raw),archive_sha256=artifact.data['archive_sha256'],
            engine_sha256=executable['sha256'],source_acquisition='pinned-upstream-https',
            initial_download_operations=download.calls,offline_acquisition_calls=len(manager.opener.calls),
            before=before,after=after,notice_files=len(expected),same_generation=True,
            corruption_rejected=rejected,restored_snapshot_matches=restored==before,modes_checked=False,
            cases=cases,recovery=recovered,
            scope='Windows ABI on hosted CI; real pinned engine and process exits/locking; controlled repair errors, including injected Windows EACCES; no Windows 11 certification')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('driver','report'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--review-directory',type=Path)
    args=parser.parse_args()
    if args.report.exists() or args.report.is_symlink():parser.error('Choose a new report')
    result=collect(args.driver.resolve(),args.review_directory)
    with args.report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
