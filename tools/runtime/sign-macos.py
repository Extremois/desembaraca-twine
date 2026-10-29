"""Prepare a signed/notarized copy on native macOS; never publish or disable protections."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'src'))
from twine_edge_overlap.runtime_platform import detect_host


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sign(build,output,audit,identity,profile):
    host=detect_host()
    if host.os!='darwin' or host.translated:raise ValueError('Native macOS without translation required')
    if not identity.startswith('Developer ID Application:') or not profile:
        raise ValueError('Developer ID Application identity and existing Keychain profile required')
    build=Path(build).resolve()
    record=json.loads((build/'provenance.json').read_text())
    if not record.get('completed') or record.get('native_arch')!=host.arch or record.get('native_os')!='darwin':
        raise ValueError('Completed matching native build required')
    candidate=build/'candidate'
    binary=candidate/'bin/dot'
    if digest(binary)!=record['executable_sha256']:raise ValueError('Unsigned binary differs from provenance')
    for path in (candidate,*candidate.rglob('*')):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):raise ValueError('Candidate contains links or special files')
        if path.is_file() and path!=binary:
            with path.open('rb') as stream:magic=stream.read(4)
            if magic in (b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xca\xfe\xba\xbe'):
                raise ValueError('Base signing recipe only qualifies the single static Graphviz Mach-O')
    spec=importlib.util.spec_from_file_location('candidate_verifier',HERE/'verify-artifact.py')
    verifier=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    verifier.macho_architecture(binary,host.arch)
    verifier.validate_audit(json.loads(Path(audit).read_text()),build/'provenance.json',candidate,record)
    output=Path(output).absolute()
    output.mkdir(mode=0o700,parents=False,exist_ok=False)
    signed_root=output/'candidate'
    shutil.copytree(candidate,signed_root)
    executable=signed_root/'bin/dot'
    def run(argv,timeout=120):
        return subprocess.run(argv,check=True,shell=False,stdin=subprocess.DEVNULL,capture_output=True,timeout=timeout)
    run(['/usr/bin/codesign','--force','--timestamp','--options','runtime','--sign',identity,str(executable)])
    run(['/usr/bin/codesign','--verify','--deep','--strict',str(executable)])
    archive=output/'notarization-candidate.zip'
    run(['/usr/bin/ditto','-c','-k','--keepParent',str(signed_root),str(archive)])
    submitted=run(['/usr/bin/xcrun','notarytool','submit',str(archive),'--keychain-profile',profile,'--wait','--output-format','json'],timeout=1800)
    result=json.loads(submitted.stdout)
    (output/'notarization-result.json').write_text(json.dumps(result,indent=2)+'\n')
    if result.get('status')!='Accepted' or not result.get('id'):raise ValueError('Notarization was not accepted')
    details=run(['/usr/bin/xcrun','notarytool','log',result['id'],'--keychain-profile',profile])
    (output/'notarization-log.json').write_bytes(details.stdout)
    # Assess normally. A denial is a failed gate, never a request to disable Gatekeeper.
    run(['/usr/sbin/spctl','--assess','--type','execute','--verbose=4',str(executable)])
    unsigned_sha=record['executable_sha256']
    record.update(executable_sha256=digest(executable),unsigned_executable_sha256=unsigned_sha,
                  unsigned_provenance_sha256=digest(build/'provenance.json'),
                  notarization_submission_id=result['id'],notarization_log_sha256=digest(output/'notarization-log.json'),
                  notarization_archive_sha256=digest(archive),
                  qualification='signed and notarized copy; final bundle, updated audit and native distribution/offline acceptance still required')
    (output/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    return dict(signed_executable_sha256=record['executable_sha256'],notarization_submission_id=result['id'],published=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('build-output','output','audit'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--identity',default=os.environ.get('TWINE_SIGN_IDENTITY',''))
    parser.add_argument('--notary-profile',default=os.environ.get('TWINE_NOTARY_PROFILE',''))
    args=parser.parse_args()
    try:print(json.dumps(sign(args.build_output,args.output,args.audit,args.identity,args.notary_profile),indent=2))
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as exc:parser.exit(1,'Signing/notarization incomplete ('+type(exc).__name__+'); no artifact published.\n')


if __name__=='__main__':main()
