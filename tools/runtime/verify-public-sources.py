"""Compare an exported source package with pinned public source archives offline.

No extraction, network, compiler execution, publication or license approval.
Generated candidate metadata is explicitly separate from recoverable sources.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import zipfile

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('public_source_packer',HERE/'pack-sources.py')
PACKER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(PACKER)
PROJECT_LOCK=json.loads((HERE/'public-recipe-source-lock.json').read_bytes())
GRAPHVIZ_LOCK=PACKER.SOURCE_LOCK
SDK_LOCKS={'x86_64':PACKER.SDK_LOCK,'aarch64':PACKER.SDK_LOCK_ARM64}
MAX_FILES=PACKER.MAX_FILES
MAX_FILE=PACKER.MAX_FILE
MAX_EXPANDED=PACKER.MAX_EXPANDED
digest=PACKER.digest


def hash_bytes(data):return hashlib.sha256(data).hexdigest()


def project_pin(path=None):
    lock=PROJECT_LOCK if path is None else json.loads(PACKER.bounded(Path(path),65536))
    if not isinstance(lock,dict):raise ValueError('Invalid public project pin')
    revision=lock.get('revision')
    if (lock.get('kind')!='public-recipe-source-review-pin' or lock.get('approved') is not False
            or not isinstance(revision,str) or not re.fullmatch('[0-9a-f]{40}',revision)
            or lock.get('url')!='https://github.com/Extremois/desembaraca-twine/archive/'+revision+'.zip'
            or lock.get('root')!='desembaraca-twine-'+revision
            or type(lock.get('size')) is not int or not 0<lock['size']<=128*1024**2
            or not isinstance(lock.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',lock['sha256'])):
        raise ValueError('Invalid public project pin')
    # Copy before verification so the complete comparison and report use the same pin.
    return dict(lock)


def safe_name(name):
    if (not isinstance(name,str) or not name or len(name)>4096 or '\\' in name or ':' in name
            or '\0' in name or PurePosixPath(name).is_absolute()
            or any(part in ('','.','..') for part in name.split('/'))):
        raise ValueError('Unsafe source path')
    return name


def stream_identity(stream,expected_size):
    total=0;hasher=hashlib.sha256()
    while data:=stream.read(65536):
        total+=len(data)
        if total>MAX_FILE or total>expected_size:raise ValueError('Source file exceeds bounds')
        hasher.update(data)
    if total!=expected_size:raise ValueError('Truncated source file')
    return dict(size=total,sha256=hasher.hexdigest())


def project_inventory(archive,root):
    safe_name(root)
    if '/' in root:raise ValueError('Project archive root must be one component')
    files={};seen=set();total=0
    for index,item in enumerate(archive.infolist()):
        name=safe_name(item.filename.removesuffix('/'))
        mode=item.external_attr>>16
        if (index>=MAX_FILES or name in seen or not (name==root or name.startswith(root+'/'))
                or stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR)
                or item.flag_bits&1 or item.file_size<0 or item.file_size>MAX_FILE):
            raise ValueError('Unsafe or duplicate project archive entry')
        seen.add(name);total+=item.file_size
        if total>MAX_EXPANDED:raise ValueError('Project archive exceeds expansion budget')
        if item.is_dir():continue
        relative=name[len(root)+1:]
        safe_name(relative);files[relative]=item
    return files


def source_inventory(path,receipt):
    PACKER.pinned(path,dict(size=receipt['archive_bytes'],sha256=receipt['archive_sha256']))
    files={};metadata={};total=0
    with tarfile.open(path,'r:*') as archive:
        for index,item in enumerate(archive):
            name=safe_name(item.name)
            if (index>=MAX_FILES or name in files or not item.isfile() or item.size<0 or item.size>MAX_FILE):
                raise ValueError('Unsafe or duplicate source package entry')
            total+=item.size
            if total>MAX_EXPANDED:raise ValueError('Source package exceeds expansion budget')
            with archive.extractfile(item) as stream:
                if name in ('manifest.json','candidate-provenance.json'):
                    if item.size>8*1024**2:raise ValueError('Source metadata exceeds budget')
                    raw=stream.read(item.size+1)
                    if len(raw)!=item.size:raise ValueError('Truncated source metadata')
                    metadata[name]=raw;files[name]=dict(size=len(raw),sha256=hash_bytes(raw))
                else:files[name]=stream_identity(stream,item.size)
    if len(files)!=receipt['file_count'] or set(metadata)!= {'manifest.json','candidate-provenance.json'}:
        raise ValueError('Source package inventory or metadata is incomplete')
    manifest=json.loads(metadata['manifest.json']);provenance=json.loads(metadata['candidate-provenance.json'])
    declared={}
    for row in manifest['files']:
        name=safe_name(row['path'])
        if (name in declared or type(row['size']) is not int or row['size']<0
                or not isinstance(row['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',row['sha256'])):
            raise ValueError('Invalid manifest source entry')
        declared[name]=dict(size=row['size'],sha256=row['sha256'])
    if declared!={name:row for name,row in files.items() if name!='manifest.json'}:
        raise ValueError('Exported source manifest differs from bytes')
    for record in (manifest,provenance):
        if (record['artifact_id']!=receipt['artifact_id'] or record['executable_sha256']!=receipt['executable_sha256']):
            raise ValueError('Source metadata does not match candidate receipt')
    if (manifest['provenance_sha256']!=receipt['provenance_sha256']
            or files['candidate-provenance.json']['sha256']!=receipt['provenance_sha256']
            or provenance.get('completed') is not True):
        raise ValueError('Source provenance binding is incomplete')
    return files,manifest,provenance


def verify(source_package,receipt,project,graphviz,sdk,project_lock=None):
    selected_project_lock=project_pin(project_lock)
    source_package,receipt,project,graphviz,sdk=map(Path,(source_package,receipt,project,graphviz,sdk))
    record=json.loads(PACKER.bounded(receipt,65536))
    artifact=record['artifact_id']
    if artifact not in ('linux-glibc-x86_64','linux-glibc-aarch64','linux-musl-x86_64','linux-musl-aarch64'):
        raise ValueError('Unsupported Linux source artifact')
    arch='aarch64' if artifact.endswith('aarch64') else 'x86_64'
    sdk_lock=SDK_LOCKS[arch]
    for path,lock in ((project,selected_project_lock),(graphviz,GRAPHVIZ_LOCK),(sdk,sdk_lock)):PACKER.pinned(path,lock)
    files,manifest,provenance=source_inventory(source_package,record)
    if (manifest['graphviz_archive_sha256']!=GRAPHVIZ_LOCK['sha256']
            or provenance['source']['sha256']!=GRAPHVIZ_LOCK['sha256']
            or manifest['sdk_archive_sha256']!=sdk_lock['sha256']
            or provenance['sdk']['facts']['archive']['sha256']!=sdk_lock['sha256']
            or files.get('graphviz.tar.gz')!=dict(size=GRAPHVIZ_LOCK['size'],sha256=GRAPHVIZ_LOCK['sha256'])):
        raise ValueError('Exported upstream source pins differ')
    sdk_files={name:row for name,row in files.items() if name.startswith('sdk/')}
    with tarfile.open(sdk,'r:*') as archive:
        members=PACKER.sdk_members(archive)
        if {name for name,item in members}!=set(sdk_files) or len(members)!=record['sdk_files']:
            raise ValueError('Public SDK source inventory differs')
        for name,item in members:
            with archive.extractfile(item) as stream:identity=stream_identity(stream,item.size)
            if identity!=sdk_files[name]:raise ValueError('Public SDK source differs from export')
    project_files={name:row for name,row in files.items() if name not in sdk_files
                   and name not in ('graphviz.tar.gz','candidate-provenance.json','manifest.json')}
    recipe='tools/runtime/'+artifact+'.json'
    if not project_files or project_files.get(recipe,{}).get('sha256')!=provenance['recipe_sha256']:
        raise ValueError('Public recipe binding is missing')
    with zipfile.ZipFile(project) as archive:
        available=project_inventory(archive,selected_project_lock['root'])
        for name,identity in project_files.items():
            if name not in available:raise ValueError('Public project source is missing')
            item=available[name]
            with archive.open(item) as stream:actual=stream_identity(stream,item.file_size)
            if actual!=identity:raise ValueError('Public project source differs from export')
    for path,lock in ((project,selected_project_lock),(graphviz,GRAPHVIZ_LOCK),(sdk,sdk_lock)):PACKER.pinned(path,lock)
    PACKER.pinned(source_package,dict(size=record['archive_bytes'],sha256=record['archive_sha256']))
    return dict(kind='public-source-recovery-verification',approved=False,qualified=False,
        artifact_id=artifact,executable_sha256=record['executable_sha256'],project_revision=selected_project_lock['revision'],
        project_pin=selected_project_lock,
        source_package_sha256=record['archive_sha256'],source_files_recovered=len(files)-2,
        project_files=len(project_files),sdk_files=len(sdk_files),generated_metadata_files=['candidate-provenance.json','manifest.json'],
        public_sources=[dict(url=lock['url'],size=lock['size'],sha256=lock['sha256'])
                        for lock in (selected_project_lock,GRAPHVIZ_LOCK,sdk_lock)],
        limitations=['Byte recovery only; no new compiler execution or byte-identical rebuild claim',
            'Generated candidate provenance and export index are review metadata, not upstream program sources',
            'Public upstream availability is not a guarantee of future hosting or an approved corresponding-source offer',
            'Per-file license applicability and distribution qualification remain separate gates'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-package','receipt','project','graphviz','sdk','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--project-lock',type=Path,
        help='Explicit reviewed public revision pin; defaults to public-recipe-source-lock.json')
    args=vars(parser.parse_args());report=args.pop('report')
    try:
        if report.exists() or report.is_symlink():raise ValueError('Report already exists')
        result=verify(**args)
        with report.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        print(json.dumps(result,indent=2))
    except (OSError,ValueError,KeyError,TypeError,tarfile.TarError,zipfile.BadZipFile) as exc:
        parser.exit(1,'Source recovery verification failed ('+type(exc).__name__+'); no offer approved.\n')


if __name__=='__main__':main()
