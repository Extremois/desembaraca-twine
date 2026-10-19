"""Isolated worker: imports the candidate installed in its venv, not checkout src."""
from contextlib import ExitStack,redirect_stdout,redirect_stderr
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
from unittest.mock import patch


def invalid_input_trial(cli,work):
    """An invalid first file must fail before acquisition, even if errors are caught."""
    from twine_edge_overlap import application
    source=work/'invalid-first-input.twee'
    with source.open('xb') as stream:stream.write(b'\xff')
    acquired=[];network=[]
    def acquisition(*args,**kwargs):
        acquired.append(True)
        raise AssertionError('Invalid input attempted runtime acquisition')
    def connection(*args,**kwargs):
        network.append(True)
        raise AssertionError('Invalid input attempted Python network')
    with ExitStack() as stack:
        stack.enter_context(patch.object(application,'ensure_runtime',side_effect=acquisition))
        for name in ('socket.getaddrinfo','socket.socket.connect','socket.create_connection'):
            stack.enter_context(patch(name,side_effect=connection))
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            try:code=cli([str(source)])
            except AssertionError as exc:raise ValueError('Invalid first input attempted acquisition/network') from exc
    if code!=1 or acquired or network or source.read_bytes()!=b'\xff':
        raise ValueError('Invalid first input was not refused before acquisition/network')
    return dict(exit_code=code,acquisition_attempts=0,python_network_attempts=0)


def collect(request):
    from twine_edge_overlap.runtime import ensure_runtime
    from twine_edge_overlap.runtime_catalog import load_catalog,select_artifact,verified_manifest
    from twine_edge_overlap.runtime_platform import detect_host,cache_directory
    from twine_edge_overlap.runtime_snapshot import snapshot_for_host
    from twine_edge_overlap.runtime_catalog import EnvironmentSnapshot
    from twine_edge_overlap.application import run
    from twine_edge_overlap.formats.profile import parse,verify
    from twine_edge_overlap.cli import main as cli
    import twine_edge_overlap
    work=Path(request['work'])
    if not Path(twine_edge_overlap.__file__).resolve().is_relative_to((work/'venv').resolve()):
        raise ValueError('Worker did not load the external venv installation')
    host=detect_host()
    if host.translated:raise ValueError('Translated interpreter cannot qualify')
    target=request['target']
    distro=host.distribution_id if host.os=='linux' else ('macos' if host.os=='darwin' else 'windows')
    version=host.distribution_version if host.os=='linux' else host.os_version
    if (host.os!=target['os'] or host.arch!=target['arch'] or distro!=target['distribution_id']
            or (target['version']!='rolling' and not (version==target['version'] or version.startswith(target['version']+'.')))
            or (target['version']!='rolling' and host.channel and host.channel!=target['channel'])
            or (host.cpu_variant and host.cpu_variant!=target['cpu_variant'])):
        raise ValueError('Installed worker environment differs from requested cell')
    if request['variant_required'] and host.cpu_variant!=target['cpu_variant']:
        raise ValueError('Installed worker cannot identify the image variant')
    catalog=load_catalog()
    descriptor=select_artifact(catalog,host)
    if descriptor['id']!=request['artifact_id'] or catalog.get('application_revision',request['application_revision'])!=request['application_revision']:
        raise ValueError('Installed catalog/revision differs from request')
    from twine_edge_overlap.runtime import load_manifest
    artifact=load_manifest(verified_manifest(descriptor))
    fixture_root=Path(request['fixture_root'])
    cases=json.loads((fixture_root/'cases.json').read_text())
    invalid_trial=invalid_input_trial(cli,work)
    source=work/cases[0]['file']
    source.write_bytes((fixture_root/cases[0]['file']).read_bytes())
    output,errors=io.StringIO(),io.StringIO()
    with redirect_stdout(output),redirect_stderr(errors):
        first_code=cli([str(source)])  # Automatic first preparation with normal acquisition.
        if first_code!=0:raise ValueError('First known reference CLI use failed')
        if cli(['--prepare-runtime'])!=0:raise ValueError('Explicit preparation failed')
    handle=ensure_runtime()
    security_assessed=False
    if host.os=='darwin':
        security_env=dict(os.environ,LC_ALL='C',LANG='C')
        status=subprocess.run(['/usr/sbin/spctl','--status'],check=True,capture_output=True,env=security_env,timeout=10)
        if b'assessments enabled' not in status.stdout+status.stderr:raise ValueError('Normal macOS assessments are not enabled')
        signature=subprocess.run(['/usr/bin/codesign','-dvv',str(handle.executable)],check=True,capture_output=True,env=security_env,timeout=10)
        if b'Authority=Developer ID Application:' not in signature.stderr or b'Timestamp=' not in signature.stderr or b'runtime' not in signature.stderr:
            raise ValueError('Developer ID, timestamp and hardened runtime are required')
        subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(handle.executable)],check=True,capture_output=True,env=security_env,timeout=30)
        subprocess.run(['/usr/sbin/spctl','--assess','--type','execute',str(handle.executable)],check=True,capture_output=True,env=security_env,timeout=30)
        security_assessed=True
    attempts=[]
    def denied(*a,**k):
        attempts.append('python-network-call')
        raise AssertionError('Unexpected network during offline processing')
    corpus=[]
    review=work/'review'
    if request.get('retain_review'):review.mkdir(exist_ok=False)
    with ExitStack() as stack:
        for name in ('socket.getaddrinfo','socket.socket.connect','socket.create_connection'):
            stack.enter_context(patch(name,side_effect=denied))
        with redirect_stdout(output),redirect_stderr(errors):
            if cli(['--prepare-runtime'])!=0:raise ValueError('Offline cached preparation failed')
        snapshot=snapshot_for_host(host)
        if target['version']=='rolling' and (not snapshot.known or snapshot.metadata['channel']!=target['channel']
                or (target.get('snapshot_id') is not None and snapshot.snapshot_id!=target['snapshot_id'])):
            raise ValueError('Rolling identity/channel differs from requested cell')
        for case in cases:
            source=work/case['file']
            original=(fixture_root/case['file']).read_bytes()
            source.write_bytes(original)
            result=run(source)  # Normal cache path, classification and fresh handle resolution.
            generated=result.path.read_bytes()
            verify(parse(original),parse(generated))
            if source.read_bytes()!=original or any(a>b for a,b in zip(result.after.values,result.before.values)):
                raise ValueError('Corpus preservation/non-regression failed')
            if list(result.before.values)!=case['before']:raise ValueError('Reference baseline metrics changed')
            if case['known_resolvable'] and result.after.values!=(0,0,0):raise ValueError('Known reference failed')
            if request.get('retain_review') and case['known_resolvable']:
                # This directory contains public fixtures only, never the work/cache tree.
                if case['case'] not in ('crossing','coincident','isolated_overlap','connected_overlap','through_isolated','through_connected'):
                    raise ValueError('Unexpected public review case')
                with (review/(case['case']+'.twee')).open('xb') as stream:stream.write(generated)
            corpus.append(dict(case=case['case'],input_sha256=hashlib.sha256(original).hexdigest(),output_sha256=hashlib.sha256(generated).hexdigest(),before=list(result.before.values),after=list(result.after.values),original_preserved=True,semantics_preserved=True,status=result.status))
        after_host=detect_host()
        identity=lambda value:(value.os,value.arch,value.os_version,value.distribution_version,value.cpu_variant,value.channel,value.kernel_version)
        if identity(after_host)!=identity(host):
            raise ValueError('Host identity changed during acceptance')
        if request['target']['version']=='rolling':
            after_snapshot=snapshot_for_host(after_host)
            if not snapshot.known or not after_snapshot.known or after_snapshot.snapshot_id!=snapshot.snapshot_id:
                raise ValueError('Rolling capture changed during acceptance')
        if ensure_runtime().generation_id!=handle.generation_id:raise ValueError('Healthy cache generation was unexpectedly replaced')
    if attempts:raise ValueError('Offline Python network attempt observed')
    from twine_edge_overlap.runtime_catalog import GATES
    checks=dict(first_run=True,preservation=True)
    # Offline needs native syscall tracing; installation needs wheel+sdist+remote.
    # Twine, audited licenses and native failure/crash trials need separate evidence.
    captured=datetime.now(timezone.utc).isoformat()
    record=dict(id=target['id']+'-'+request['python_minor']+'-'+captured.replace(':',''),target_id=target['id'],
                python_minor=request['python_minor'],python_patch=platform.python_version(),python_origin=request['python_origin'],
                application_revision=request['application_revision'],artifact_id=descriptor['id'],artifact_sha256=artifact.data['archive_sha256'],
                source_state=request['source_state'],
                recipe_revision=artifact.data.get('build_variant','legacy-upstream-16.1.0'),package_sha256=request['package_sha256'],
                os=host.os,os_version=host.distribution_version if host.os=='linux' else host.os_version,
                distribution_id=target['distribution_id'],channel=target['channel'],cpu_variant=target['cpu_variant'],
                architecture=host.arch,kernel=host.kernel_version,cpu=platform.processor() or host.arch,
                image_id=request['image_id'],image_digest=request['image_digest'],captured_at=captured,environment_kind=request['environment_kind'],
                snapshot_id=snapshot.snapshot_id if snapshot.known else None,checks=checks,passed=True,
                pending_checks=sorted(GATES-set(checks)),
                observations=dict(cache_matches_platform=handle.root.resolve().is_relative_to(cache_directory(host).resolve()),
                                  invalid_input_refused_without_acquisition=invalid_trial['exit_code']==1,
                                  executable_mode=stat.S_IMODE(handle.executable.stat().st_mode),runtime_schema=artifact.data['schema_version'],
                                  healthy_generation_reused=True,macos_security_assessed=security_assessed,
                                  paths_with_spaces_and_accents=' ' in str(work) and chr(0xe7) in str(work)),
                commands=['external venv installation --no-index','console script --help','python -m twine_edge_overlap --help','CLI invalid first input without acquisition','CLI first valid file','CLI --prepare-runtime','public corpus using normal installed runtime'],
                corpus=corpus,network=dict(observation='python-only',attempts=0),
                log_text=output.getvalue()+'\n'+errors.getvalue(),
                installation={request['package_mode']:True,'outside_checkout':True},
                pending_reason='Native network trace, remaining installation modes, failures/crash/concurrency, license audit and actual Twine review required.')
    if target['version']=='rolling':
        if not snapshot.known:raise ValueError('Rolling identity unknown; no truncated reference is accepted')
        record['environment_snapshot']=EnvironmentSnapshot.from_probe(snapshot,captured_at=captured,image_digest=request['image_digest']).data
    return record


if __name__=='__main__':
    request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    result=collect(request)
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
