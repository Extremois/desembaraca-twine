"""Fixed argv bridge for configured native CI runners; no provisioning or secrets."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent


def main():
    env=os.environ
    candidates=list(Path('candidate').glob('*.whl'))
    if len(candidates)!=1:raise ValueError('Expected exactly one candidate wheel')
    package=candidates[0]
    if hashlib.sha256(package.read_bytes()).hexdigest()!=env['TWINE_PACKAGE_SHA256']:
        raise ValueError('Downloaded wheel differs from requested immutable candidate')
    target=env.get('TWINE_TARGET')
    if not target:
        registry=json.loads((HERE/'support-targets.json').read_text())
        matches=[item for item in registry['targets'] if item['os']=='darwin' and item['arch']==env['TWINE_ARCH'] and item['version']=='15']
        if len(matches)!=1:raise ValueError('Ambiguous macOS support target')
        target=matches[0]['id']
    Path('evidence').mkdir(exist_ok=True)
    command=[sys.executable,str(HERE/'qualify-target.py'),'--target',target,'--package',str(package.resolve()),
             '--artifact-id',env['TWINE_ARTIFACT_ID'],'--application-revision',env['TWINE_APPLICATION_REVISION'],
             '--package-sha256',env['TWINE_PACKAGE_SHA256'],'--python-312',env['TWINE_PYTHON312'],'--python-314',env['TWINE_PYTHON314'],
             '--python-minor',env['TWINE_PYTHON_MINOR'],'--python-origin','actions/setup-python (exact patch recorded)',
             '--source-state','committed',
             '--image-id',env['TWINE_IMAGE_ID'],'--image-digest',env['TWINE_IMAGE_DIGEST'],
             '--environment-kind','native','--output','evidence/result.json',
             '--review-output','evidence/twine-review']
    subprocess.run(command,check=True,shell=False)


if __name__=='__main__':main()
