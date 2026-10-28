"""Package an inventoried local candidate. Never execute, qualify or publish it."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('local_candidate_verifier',HERE/'verify-artifact.py')
verifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

MAX_ARCHIVE_BYTES=128*1024**2


class BoundedArchive:
    """Include ZIP headers/central directory in the same received-archive limit."""
    def __init__(self,stream):self.stream=stream
    def tell(self):return self.stream.tell()
    def seek(self,*args):return self.stream.seek(*args)
    def flush(self):return self.stream.flush()
    def write(self,data):
        if self.tell()+len(data)>MAX_ARCHIVE_BYTES:
            raise ValueError('Candidate ZIP exceeds runtime archive limit')
        return self.stream.write(data)


def pack(root, inventory, provenance, output):
    root,inventory,provenance,output=map(Path,(root,inventory,provenance,output))
    if output.exists() or output.is_symlink():
        raise FileExistsError('Candidate output already exists')
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError('Package output must be outside the inventoried tree')
    data=verifier.load_inventory(inventory,provenance)
    with inventory.open('rb') as stream:inventory_bytes=stream.read(8*1024**2+1)
    if len(inventory_bytes)>8*1024**2 or json.loads(inventory_bytes)!=data:
        raise ValueError('Inventory changed during packaging')
    verifier.inventory_data(data,provenance)
    # POSIX modes cannot be measured on a Windows copy. Encode the inventory's
    # modes, and explicitly report this limitation; native inspection remains due.
    verifier.verify_tree(root,data,enforce_modes=os.name!='nt')
    output.mkdir(mode=0o700,exist_ok=False)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=output,suffix='.part',delete=False) as stream:
            temporary=Path(stream.name)
            # Stored entries avoid zlib-version-dependent bytes. The ZIP is a
            # candidate only; its final size must still fit the runtime's limit.
            with zipfile.ZipFile(BoundedArchive(stream),'w',compression=zipfile.ZIP_STORED,allowZip64=False) as archive:
                for item in sorted(data['files'],key=lambda row:row['path']):
                    entry=zipfile.ZipInfo(item['path'],date_time=(1980,1,1,0,0,0))
                    entry.create_system=3
                    entry.external_attr=(stat.S_IFREG|item['mode'])<<16
                    entry.file_size=item['size']
                    observed=hashlib.sha256()
                    total=0
                    with (root/item['path']).open('rb') as incoming,archive.open(entry,'w') as outgoing:
                        while chunk:=incoming.read(65536):
                            total+=len(chunk)
                            if total>item['size']:raise ValueError('Source grew during ZIP copy')
                            observed.update(chunk)
                            outgoing.write(chunk)
                    if total!=item['size'] or observed.hexdigest()!=item['sha256']:
                        raise ValueError('Source changed during ZIP copy')
            stream.flush()
            os.fsync(stream.fileno())
        archive_sha=verifier.digest(temporary,maximum=MAX_ARCHIVE_BYTES)
        report=dict(kind='local-candidate-archive',qualified=False,
                    artifact_id=data['artifact_id'],platform=data['platform'],artifact_arch=data['artifact_arch'],abi=data['abi'],
                    archive='candidate.zip',archive_sha256=archive_sha,archive_bytes=temporary.stat().st_size,
                    inventory='inventory.json',inventory_sha256=hashlib.sha256(inventory_bytes).hexdigest(),
                    executable_sha256=next(item['sha256'] for item in data['files']
                                           if item['path']==data['executable_relative_path']),
                    provenance_sha256=data['provenance_sha256'],file_count=len(data['files']),
                    source_modes_checked=os.name!='nt',zip_modes='from-validated-inventory',compression='stored',
                    macos_signing_required=False,
                    pending=['dependency/license audit','binary inspection/ABI',
                             'real immutable distribution URL and runtime manifest','GitHub Actions ABI acceptance'])
        # No replace/copy fallback: an existing destination must remain untouched.
        os.link(temporary,output/'candidate.zip')
        with (output/'inventory.json').open('xb') as stream:stream.write(inventory_bytes)
        with (output/'candidate.json').open('x',encoding='utf-8') as stream:
            json.dump(report,stream,indent=2);stream.write('\n')
        return report
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','inventory','provenance','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    try:
        report=pack(args.root,args.inventory,args.provenance,args.output)
        print(json.dumps(report,indent=2))
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile,zipfile.LargeZipFile) as exc:
        parser.exit(1,'Candidate packaging failed ('+type(exc).__name__+'); no support qualified or published.\n')


if __name__=='__main__':main()
