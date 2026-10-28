"""Real installed-engine recovery in disposable CI caches; acquisition/errors are controlled."""
import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


def worker(args):
    from runtime_support import ControlledTransport,blocked_network
    from twine_edge_overlap.runtime import RuntimeManager,load_manifest
    class Transport(ControlledTransport):
        def open(self,*argv,**kwargs):
            if args.stage=='during_download':os._exit(77)
            if args.stage=='normal':
                descriptor=os.open(str(args.archive)+'.calls',os.O_CREAT|os.O_WRONLY|os.O_APPEND,0o600)
                with os.fdopen(descriptor,'ab') as stream:stream.write(b'acquisition\n')
                time.sleep(.2)
            return super().open(*argv,**kwargs)
    def checkpoint(stage):
        if stage==args.stage:os._exit(77)
    if args.stage=='normal':
        Path(str(args.result)+'.ready').write_text('ready',encoding='ascii')
        deadline=time.monotonic()+10
        while not args.start.exists():
            if time.monotonic()>deadline:raise TimeoutError('Worker start barrier expired')
            time.sleep(.02)
    with blocked_network():
        manager=RuntimeManager(artifact=load_manifest(args.manifest),cache_root=args.cache,
            opener=Transport(args.archive.read_bytes()),checkpoint=checkpoint)
        handle=manager.ensure(force_repair=args.stage!='normal')
        args.result.write_text(handle.generation_id,encoding='ascii')


def exercise(args,bundle,*,process_only=False,artifact=None):
    from runtime_support import ControlledTransport,blocked_network
    from twine_edge_overlap.runtime import RuntimeManager,load_manifest
    from twine_edge_overlap.errors import DependencyError
    from twine_edge_overlap.application import run
    from twine_edge_overlap.formats.profile import parse,verify
    from twine_edge_overlap.engines.process import run_bounded
    digest=lambda data:hashlib.sha256(data).hexdigest()
    fixtures=args.driver/'tests/fixtures'
    selected=[row for row in json.loads((fixtures/'cases.json').read_bytes()) if row['known_resolvable']]
    if len(selected)!=6:raise ValueError('Expected six public recovery references')
    scenarios={}
    with tempfile.TemporaryDirectory(prefix='native-private-recovery-') as folder,blocked_network():
        root=Path(folder);archive=root/'candidate.zip';archive.write_bytes(bundle.payload)
        data=dict((artifact or load_manifest()).data)
        if artifact is None:
            data.update(schema_version=2,platform=bundle.platform_name,artifact_arch=bundle.record['native_arch'],
                abi=bundle.record['recipe']['abi'],build_variant='private-recovery-only',
                minimum_libc='0',minimum_kernel='0',minimum_os='15',files=bundle.inventory['files'],
                executable_relative_path='bin/dot',generated_files=[])
            data['notices']=[dict(data['notices'][0],destination='third-party-notices/private-recovery-application.txt')]
            data.pop('plugin_relative_path',None)
        data.update(url='https://runtime.invalid/artifact.zip',allowed_redirect_hosts=['runtime.invalid'],
                    archive_sha256=digest(bundle.payload))
        manifest=root/'private-manifest.json';manifest.write_text(json.dumps(data),encoding='utf-8')
        artifact=load_manifest(manifest)
        def manager(cache,**kwargs):return RuntimeManager(artifact=artifact,cache_root=cache,opener=ControlledTransport(bundle.payload),**kwargs)
        def offline_refs(current,work):
            current.opener=ControlledTransport(error=AssertionError('Offline recovery attempted acquisition'))
            rows=[]
            for case in selected:
                raw=(fixtures/case['file']).read_bytes();path=work/case['file'];path.write_bytes(raw)
                result=run(path,runtime_provider=current.ensure);output=result.path.read_bytes()
                if result.after.values!=(0,0,0) or path.read_bytes()!=raw:raise AssertionError('Recovery reference failed')
                verify(parse(raw),parse(output))
                rows.append(dict(case=case['case'],input_sha256=digest(raw),output_sha256=digest(output),after=result.after.values))
            if current.opener.calls:raise AssertionError('Healthy recovery cache attempted acquisition')
            return rows
        def old_handle(old,work):
            path=work/'old-handle.twee';path.write_bytes((fixtures/'crossing.twee').read_bytes())
            result=run(path,runtime_provider=lambda:old)
            if result.after.values!=(0,0,0) or digest(old.executable.read_bytes())!=bundle.record['executable_sha256']:
                raise AssertionError('Previously returned handle became unusable')
            return True
        def command(cache,stage,result,start):
            return [sys.executable,'-I',str(Path(__file__).resolve()),'--worker','--driver',str(args.driver),
                '--cache',str(cache),'--manifest',str(manifest),'--archive',str(archive),
                '--stage',stage,'--result',str(result),'--start',str(start)]
        for name in (() if process_only else ('download','disk_full','execution_denied','corrupt_archive')):
            work=root/name;work.mkdir();current=manager(work/'cache');old=current.ensure()
            active=(current.root/'active.json').read_bytes()
            if name=='download':current.opener=ControlledTransport(error=ConnectionError('injected transfer failure'))
            elif name=='corrupt_archive':current.opener=ControlledTransport(b'not-the-pinned-archive')
            elif name=='execution_denied':
                def denied_runner(argv,**kwargs):
                    if os.name=='nt':raise PermissionError(errno.EACCES,'injected Windows execution denial')
                    Path(argv[0]).chmod(0o644)
                    return run_bounded(argv,**kwargs)
                current.runner=denied_runner
            else:
                def checkpoint(stage):
                    if stage!='generation':return
                    raise OSError(errno.ENOSPC,'injected filesystem full')
                current.checkpoint=checkpoint
            try:current.ensure(force_repair=True)
            except DependencyError:pass
            else:raise AssertionError('Failed repair was accepted: '+name)
            if (current.root/'active.json').read_bytes()!=active:raise AssertionError('Failed repair changed selected generation')
            current.checkpoint=lambda stage:None
            current.runner=run_bounded
            rows=offline_refs(current,work)
            usable=old_handle(old,work)
            current.opener=ControlledTransport(bundle.payload);replacement=current.ensure(force_repair=True)
            if replacement.generation_id==old.generation_id:raise AssertionError('Repair retry did not publish a new generation')
            scenarios[name]=dict(passed=True,offline_references=len(rows),cases=rows,old_handle_usable=usable,
                selection_preserved=True,retry_succeeded=True,
                failure_kind=('Injected Windows execution denial' if os.name=='nt' else 'Real executable permission denial')
                    if name=='execution_denied' else 'Explicit controlled error/bytes injection')
        for stage in ('during_download','before_select','after_select'):
            work=root/stage;work.mkdir();cache=work/'cache';current=manager(cache);old=current.ensure()
            active=(current.root/'active.json').read_bytes()
            child=subprocess.run(command(cache,stage,work/'unused',work/'start'),capture_output=True,timeout=30)
            if child.returncode!=77:raise AssertionError('Crash worker did not exit at checkpoint: '+child.stderr.decode(errors='replace'))
            orphans=set(current.root.glob('staging-*'))
            if stage=='during_download' and len(orphans)!=1:raise AssertionError('Crash did not leave expected staging orphan')
            def orphan_snapshot():
                return {str(path.relative_to(current.root)):
                        (path.stat().st_mode&0o777, digest(path.read_bytes()) if path.is_file() else None)
                        for orphan in orphans for path in [orphan,*orphan.rglob('*')]}
            orphan_before=orphan_snapshot()
            current.opener=ControlledTransport(error=AssertionError('Offline crash recovery attempted acquisition'))
            resumed=current.ensure()
            if (resumed.generation_id==old.generation_id)!=(stage!='after_select'):raise AssertionError('Crash selected wrong generation')
            if stage!='after_select' and (current.root/'active.json').read_bytes()!=active:raise AssertionError('Pre-selection crash changed selector')
            rows=offline_refs(current,work);usable=old_handle(old,work)
            current.opener=ControlledTransport(bundle.payload);replacement=current.ensure(force_repair=True)
            if replacement.generation_id==resumed.generation_id:raise AssertionError('Crash retry did not publish a new generation')
            if any(not path.is_dir() for path in orphans) or orphan_snapshot()!=orphan_before:
                raise AssertionError('Unowned staging orphan was removed or changed')
            scenarios[stage]=dict(passed=True,exitcode=child.returncode,lock_reacquired=True,
                offline_references=len(rows),cases=rows,old_handle_usable=usable,orphan_untouched=True,
                selection='new' if stage=='after_select' else 'previous')
        work=root/'concurrent_first_use';work.mkdir();cache=work/'cache';start=work/'start'
        outputs=[work/'one.txt',work/'two.txt'];children=[]
        try:
            for path in outputs:
                children.append(subprocess.Popen(command(cache,'normal',path,start),stdout=subprocess.PIPE,stderr=subprocess.PIPE))
            deadline=time.monotonic()+10
            while not all(Path(str(path)+'.ready').exists() for path in outputs):
                if any(child.poll() is not None for child in children):
                    raise AssertionError('Concurrent worker exited before readiness barrier')
                if time.monotonic()>deadline:raise TimeoutError('Concurrent readiness barrier expired')
                time.sleep(.02)
            start.write_text('start',encoding='ascii')
            for child in children:
                stdout,stderr=child.communicate(timeout=30)
                if child.returncode:raise AssertionError('Concurrent worker failed: '+stderr.decode(errors='replace'))
            generations=[path.read_text(encoding='ascii') for path in outputs]
            calls=Path(str(archive)+'.calls').read_bytes().splitlines()
            if generations[0]!=generations[1] or len(calls)!=1:raise AssertionError('Concurrent first use duplicated acquisition or generation')
            current=manager(cache);old=current.ensure()
            if old.generation_id!=generations[0] or current.opener.calls:raise AssertionError('Concurrent generation was not reusable offline')
            rows=offline_refs(current,work)
            scenarios['concurrent_first_use']=dict(passed=True,acquisition_calls=len(calls),same_generation=True,
                offline_references=len(rows),cases=rows,old_handle_usable=old_handle(old,work),workers=2,
                workers_ready=2,start_barrier=True)
        finally:
            for child in children:
                if child.poll() is None:child.kill();child.communicate(timeout=5)
    return dict(passed=True,real_engine=True,scenarios=scenarios,
        scope='Private installed-engine recovery: real process exits, permissions and OS locking; acquisition/disk-full errors controlled; not full-cell acceptance')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--driver',type=Path,required=True);parser.add_argument('--worker',action='store_true')
    for name in ('package','provenance','report','cache','manifest','archive','result','start'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--stage');parser.add_argument('--environment-kind')
    args=parser.parse_args();args.driver=args.driver.resolve(strict=True)
    sys.path[:0]=[str(args.driver/'tests'),str(args.driver/'tests/integration')]
    import common  # Bootstrap the existing fixture helpers before runtime_support.
    if args.worker:worker(args)
    else:
        from test_linux_runtime import LinuxPrivateBundleIntegrationTests as Bundle
        Bundle.configuration=(args.package.resolve(strict=True),args.provenance.resolve(strict=True))
        result=unittest.TextTestRunner(stream=sys.stdout).run(unittest.defaultTestLoader.loadTestsFromTestCase(Bundle))
        if not result.wasSuccessful():raise SystemExit(1)
        recovery=exercise(args,Bundle)
        import platform
        report=dict(kind='linux-private-bundle-runtime-and-recovery-integration',passed=True,qualified=False,
            environment_kind=args.environment_kind,python=platform.python_version(),arch=platform.machine(),
            engine_sha256=Bundle.record['executable_sha256'],provenance_sha256=hashlib.sha256(args.provenance.read_bytes()).hexdigest(),
            observations=Bundle.observations,cases=Bundle.observations['explicit']['cases'],recovery=recovery)
        args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
