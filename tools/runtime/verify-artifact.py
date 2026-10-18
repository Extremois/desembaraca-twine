"""Inspect a pinned candidate without promoting or publishing it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from twine_edge_overlap.runtime import load_manifest, relative_path
from twine_edge_overlap.runtime_catalog import read_json, version_tuple
from twine_edge_overlap.runtime_platform import detect_host
from twine_edge_overlap.engines.process import run_bounded


def linux_dependencies(text, allowed, minimum_libc, *, require_static=False):
    libraries = re.findall(r'\(NEEDED\).*?\[([^]]+)\]', text)
    if require_static:
        if ('There is no dynamic section in this file.' not in text
                or any(marker in text for marker in ('INTERP','Requesting program interpreter','(NEEDED)','GLIBC_'))):
            raise ValueError('Expected standalone static ELF without loader, dynamic dependencies or GLIBC symbols')
        return []
    if not allowed or not set(libraries).issubset(set(allowed)):
        raise ValueError('Unapproved native dependency')
    for search in re.findall(r'\((?:RPATH|RUNPATH)\).*?\[([^]]+)\]', text):
        if any(not value.startswith('$ORIGIN') or '/..' in value.replace('$ORIGIN/..', '', 1) for value in search.split(':')):
            raise ValueError('Non-relocatable library search path')
    versions = [tuple(map(int, value.split('.'))) for value in re.findall(r'\bGLIBC_(\d+(?:\.\d+)+)', text)]
    if versions and max(versions) > tuple(map(int, minimum_libc.split('.'))):
        raise ValueError('Observed GLIBC symbols exceed declared baseline')
    return libraries


def darwin_dependencies(text, allowed):
    libraries = []
    for line in text.splitlines()[1:]:
        if not line.strip(): continue
        name = line.strip().split(' (',1)[0]
        if name not in allowed:
            raise ValueError('Unapproved Darwin dependency; dynamic private closure needs explicit qualification')
        libraries.append(name)
    if not libraries:
        raise ValueError('No Darwin system dependencies observed')
    return libraries


def digest(path, *, maximum=None):
    value = hashlib.sha256()
    total=0
    with Path(path).open('rb') as stream:
        while chunk := stream.read(65536):
            total+=len(chunk)
            if maximum is not None and total>maximum:
                raise ValueError('Candidate content exceeds its inventory bound')
            value.update(chunk)
    return value.hexdigest()


def static_inventory_evidence(record,provenance):
    """Bind a local no-libc-baseline inventory to the completed static experiment."""
    recipe=record['recipe']
    facts=record.get('sdk',{}).get('facts',{})
    measured=record.get('static_elf_inspection',{})
    if (recipe.get('os')!='linux' or recipe.get('abi')!='musl'
            or '-static' not in shlex.split(recipe.get('cmake',{}).get('CMAKE_EXE_LINKER_FLAGS',''))
            or facts.get('target_os')!='linux' or facts.get('target_arch')!=recipe['arch']
            or facts.get('target_libc_family')!='musl' or facts.get('static_linking') is not True
            or any(measured.get(key) is not True for key in
                   ('no_interpreter','no_dynamic_section','no_needed_libraries','no_glibc_symbols'))):
        raise ValueError('Static local inventory requires measured musl recipe and SDK')
    report=Path(provenance).parent/'static-elf-inspection.txt'
    if digest(report,maximum=8*1024**2)!=measured.get('report_sha256'):
        raise ValueError('Static local inventory report differs from provenance')
    linux_dependencies(report.read_text(encoding='utf-8'),[],None,require_static=True)


def inventory_data(data, provenance):
    """Validate local inspection metadata; it is deliberately not a runtime manifest."""
    record=read_json(provenance)
    if (data.get('kind')!='local-candidate-inventory' or data.get('schema_version')!=1
            or data.get('qualification')!='inventory-only-not-qualified'
            or data.get('provenance_sha256')!=digest(provenance)
            or record.get('completed') is not True
            or not re.fullmatch(r'[0-9a-f]{64}',record.get('recipe_sha256',''))
            or not re.fullmatch(r'[0-9a-f]{64}',record.get('sdk',{}).get('environment_digest',''))):
        raise ValueError('Local inventory requires exact completed build provenance')
    recipe=record['recipe']
    if (data['artifact_id']!=record['artifact_id'] or recipe['id']!=data['artifact_id']
            or data['platform']!=recipe['os'] or data['artifact_arch']!=recipe['arch']
            or data['abi']!=recipe['abi'] or data['platform'] not in ('linux','darwin')
            or data['artifact_arch'] not in ('x86_64','aarch64')
            or data['abi'] not in (('glibc','musl') if data['platform']=='linux' else ('darwin',))):
        raise ValueError('Inventory differs from build recipe identity')
    if data.get('native_linkage') is not None:
        if data['native_linkage']!='static-elf' or data.get('minimum_libc') is not None:
            raise ValueError('Static local inventory cannot declare a host libc baseline')
        static_inventory_evidence(record,provenance)
    elif data['platform']=='linux':version_tuple(data['minimum_libc'])
    files=data['files']
    if not isinstance(files,list) or not 0<len(files)<=5000:
        raise ValueError('Candidate inventory count exceeds limit')
    seen=set()
    total=0
    for item in files:
        name=relative_path(item['path']).as_posix().casefold()
        if (name in seen or type(item['size']) is not int or item['size']<0
                or type(item['mode']) is not int or item['mode'] not in (0o644,0o755)
                or not re.fullmatch(r'[0-9a-f]{64}',item['sha256'])):
            raise ValueError('Invalid local inventory entry')
        seen.add(name)
        total+=item['size']
    if total>512*1024**2:
        raise ValueError('Candidate expansion exceeds limit')
    for name in seen:
        parts=name.split('/')
        if any('/'.join(parts[:index]) in seen for index in range(1,len(parts))):
            raise ValueError('Candidate file/directory collision')
    executable=data['executable_relative_path']
    if executable!='bin/dot' or not any(item['path']==executable and item['mode']==0o755
            and item['sha256']==record.get('executable_sha256') for item in files):
        raise ValueError('Executable differs from provenance or lacks approved mode')
    # Local inventory includes notices as ordinary inventoried files. The reviewed
    # audit below independently requires exact component source/license/notice hashes.
    if data.get('notices')!=[]:
        raise ValueError('Local inventory cannot resolve package notice sources')
    return data


def load_inventory(path, provenance):
    return inventory_data(read_json(path),provenance)


def create_inventory(root, provenance, *, minimum_libc=None, static_elf=False):
    record=read_json(provenance)
    recipe=record['recipe']
    host=detect_host()
    if host.os!=recipe['os'] or host.arch!=recipe['arch'] or host.translated or os.name=='nt':
        raise ValueError('Inventory creation requires matching native POSIX OS/architecture')
    root=Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Candidate root must be a real directory')
    if root.stat().st_mode & 0o7022:
        raise ValueError('Candidate root has unsafe permissions')
    files=[]
    total=0
    count=0
    for folder,directories,names in os.walk(root,followlinks=False):
        for name in sorted(directories+names):
            path=Path(folder)/name
            info=path.lstat()
            count+=1
            if count>5000 or stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise ValueError('Candidate contains excessive entries, links or special files')
            if stat.S_ISDIR(info.st_mode):
                if info.st_mode & 0o7022:
                    raise ValueError('Candidate directory has unsafe permissions')
                continue
            mode=stat.S_IMODE(info.st_mode)
            total+=info.st_size
            if mode not in (0o644,0o755) or total>512*1024**2:
                raise ValueError('Candidate mode or expansion exceeds approved limits')
            files.append(dict(path=path.relative_to(root).as_posix(),size=info.st_size,
                              mode=mode,sha256=digest(path)))
    data=dict(kind='local-candidate-inventory',schema_version=1,
              qualification='inventory-only-not-qualified',artifact_id=record['artifact_id'],
              platform=recipe['os'],artifact_arch=recipe['arch'],abi=recipe['abi'],
              provenance_sha256=digest(provenance),executable_relative_path='bin/dot',
              files=sorted(files,key=lambda item:item['path']),notices=[])
    if static_elf:
        if minimum_libc is not None:raise ValueError('Choose static ELF evidence or a libc baseline')
        data.update(native_linkage='static-elf',minimum_libc=None)
    elif host.os=='linux':
        if not minimum_libc:raise ValueError('Explicit inspection libc baseline required')
        data['minimum_libc']=minimum_libc
    return inventory_data(data,provenance)


def validate_audit(reviewed, provenance, root, record, *, require_linkage=False):
    """A reviewer approves exact provenance, sources and bundled notices."""
    if (reviewed.get('approved') is not True or not reviewed.get('reviewer')
            or reviewed.get('provenance_sha256') != digest(provenance)
            or not reviewed.get('components') or not reviewed.get('source_references')):
        raise ValueError('Reviewed audit must bind the exact build provenance')
    names = set()
    covered=set()
    for component in reviewed['components']:
        name = component.get('name')
        source = component.get('source_url', '')
        source_sha = component.get('source_sha256', '')
        notice = component.get('notice_path', '')
        path = Path(notice)
        if (not name or name in names or not component.get('license_expression')
                or not source.startswith('https://') or source not in reviewed['source_references']
                or not re.fullmatch(r'[0-9a-f]{64}', source_sha)
                or not notice or path.is_absolute() or '\\' in notice or ':' in notice
                or any(part in ('', '.', '..') for part in notice.split('/'))):
            raise ValueError('Component source/license/notice audit is incomplete')
        names.add(name)
        if digest(root / path) != component.get('notice_sha256'):
            raise ValueError('Component notice differs from reviewed bytes')
        hashes=component.get('link_input_sha256',[])
        if not isinstance(hashes,list) or any(not isinstance(value,str) or not re.fullmatch(r'[0-9a-f]{64}',value) for value in hashes):
            raise ValueError('Invalid component linkage coverage')
        covered.update(hashes)
    source = record.get('source', {})
    if not any(component.get('source_url') == source.get('url')
               and component.get('source_sha256') == source.get('sha256')
               for component in reviewed['components']):
        raise ValueError('Pinned Graphviz source is absent from the component audit')
    linkage=record.get('linkage',{})
    if require_linkage or linkage.get('recorded') is True:
        if (linkage.get('recorded') is not True or not linkage.get('inputs')
                or linkage.get('executable_sha256')!=record.get('executable_sha256')
                or any(not re.fullmatch(r'[0-9a-f]{64}',linkage.get(key,'')) for key in ('link_command_sha256','dependency_file_sha256'))):
            raise ValueError('Reviewed linkage evidence bound to this executable is required')
        required=set()
        observed=set()
        for item in linkage['inputs']:
            if (not isinstance(item.get('path'),str) or not item['path'] or item.get('scope') not in ('build','sdk')
                    or not re.fullmatch(r'[0-9a-f]{64}',item.get('sha256',''))):
                raise ValueError('Incomplete linkage inventory')
            observed.add(item['sha256'])
            if Path(item['path']).suffix in ('.a','.o'):required.add(item['sha256'])
        if not required or not required.issubset(covered) or not covered.issubset(observed):
            raise ValueError('Static archive/object inputs lack reviewed source/license coverage')


def elf_architecture(path, expected):
    with Path(path).open('rb') as stream:
        header = stream.read(20)
    if len(header) < 20 or header[:5] != b'\x7fELF\x02' or header[5] not in (1, 2):
        raise ValueError('Expected an ELF64 native object')
    machine = struct.unpack_from('<H' if header[5] == 1 else '>H', header, 18)[0]
    if machine != {'x86_64': 62, 'aarch64': 183}.get(expected):
        raise ValueError('Native object architecture differs from manifest')


def macho_architecture(path, expected):
    with Path(path).open('rb') as stream:
        header = stream.read(8)
    if len(header) != 8 or header[:4] != b'\xcf\xfa\xed\xfe':
        raise ValueError('Expected one thin little-endian Mach-O64 object')
    machine = struct.unpack_from('<I', header, 4)[0]
    if machine != {'x86_64': 0x01000007, 'aarch64': 0x0100000c}.get(expected):
        raise ValueError('Mach-O architecture differs from manifest')


def verify_tree(root, data, *, enforce_modes=True):
    """Check an exact file tree without executing it or granting audit approval."""
    root=Path(root).absolute()
    expected = {item['path']: item for item in data['files']}
    expected.update({item['destination']: item for item in data['notices']})
    actual = set()
    if root.is_symlink():
        raise ValueError('Candidate root cannot be a link')
    for folder, directories, names in os.walk(root, followlinks=False):
        for name in directories + names:
            path = Path(folder) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise ValueError('Candidate contains a link/special file')
        for name in names:
            path = Path(folder) / name
            relative = path.relative_to(root).as_posix()
            if relative not in expected:
                raise ValueError('Uninventoried candidate file')
            entry = expected[relative]
            if ('size' in entry and path.stat().st_size != entry['size']) or digest(path,maximum=entry.get('size',512*1024**2)) != entry['sha256']:
                raise ValueError('Candidate content differs from inventory')
            if enforce_modes and stat.S_IMODE(path.stat().st_mode) != entry.get('mode', 0o644):
                raise ValueError('Candidate mode differs from inventory')
            actual.add(relative)
    if actual != set(expected):
        raise ValueError('Candidate inventory incomplete')
    return expected


def inspect(root, manifest, provenance, audit, *, inventory=None):
    root = Path(root).absolute()
    if inventory is not None:
        if manifest is not None:raise ValueError('Choose local inventory or runtime manifest')
        data=load_inventory(inventory,provenance)
        identity='local-inventory-'+digest(inventory)
    else:
        artifact = load_manifest(manifest)
        data = artifact.data
        identity=artifact.identity
    host = detect_host()
    if host.os != data['platform'] or host.arch != data['artifact_arch'] or host.translated:
        raise ValueError('Native candidate inspection requires matching OS/architecture')
    record = json.loads(Path(provenance).read_text(encoding='utf-8'))
    reviewed = json.loads(Path(audit).read_text(encoding='utf-8'))
    if record.get('completed') is not True or not record.get('recipe_sha256') or not record.get('sdk', {}).get('environment_digest'):
        raise ValueError('Build provenance is incomplete')
    expected=verify_tree(root,data)
    validate_audit(reviewed, provenance, root, record,require_linkage=host.os=='linux')
    executable = root / data['executable_relative_path']
    if digest(executable) != record.get('executable_sha256'):
        raise ValueError('Build executable differs from candidate')
    inspector = shutil.which('readelf' if host.os == 'linux' else 'otool')
    if not inspector:
        raise ValueError('SDK dependency inspector is unavailable')
    command = [inspector, '--program-headers', '--dynamic', '--version-info', str(executable)] if host.os == 'linux' else [inspector, '-L', str(executable)]
    report = run_bounded(command, timeout=30, max_output=8 * 1024**2)
    if report.returncode:
        raise ValueError('Dependency inspector failed')
    text = report.stdout.decode('utf-8', errors='strict')
    if host.os == 'linux':
        elf_architecture(executable, host.arch)
        # Inspect every inventoried ELF, including private libraries, rather than
        # trusting a successful probe of just the main executable.
        native_objects = []
        for name in expected:
            path = root / name
            with path.open('rb') as stream:
                magic = stream.read(4)
            if magic == b'\x7fELF':
                native_objects.append(path)
        allowed = reviewed.get('system_libraries', []) + [path.name for path in native_objects if path != executable]
        require_static=(data['abi']=='musl' and '-static' in shlex.split(record.get('recipe',{}).get('cmake',{}).get('CMAKE_EXE_LINKER_FLAGS','')))
        libraries = []
        for path in native_objects:
            elf_architecture(path, host.arch)
            result = run_bounded([inspector, '--program-headers', '--dynamic', '--version-info', str(path)], timeout=30, max_output=8*1024**2)
            if result.returncode:
                raise ValueError('Private ELF dependency inspection failed')
            libraries.extend(linux_dependencies(result.stdout.decode('utf-8'), allowed, data['minimum_libc'],require_static=require_static))
    else:
        # The base recipe statically links Graphviz; only reviewed OS dylibs are allowed.
        macho_architecture(executable, host.arch)
        for name in expected:
            path = root / name
            with path.open('rb') as stream:
                magic = stream.read(4)
            if path != executable and magic in (b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):
                raise ValueError('Base Darwin recipe does not qualify additional Mach-O objects')
        libraries = darwin_dependencies(text, reviewed.get('system_libraries', []))
        signature = run_bounded(['/usr/bin/codesign','--verify','--deep','--strict',str(executable)],timeout=30,max_output=1024**2)
        if signature.returncode or reviewed.get('notarization_verified') is not True:
            raise ValueError('Darwin signature/notarization evidence required; no security bypass is permitted')
    # Static inspection passed; bounded smoke probe executes only the verified bytes.
    env = {'PATH': str(executable.parent), 'LC_ALL': 'C', 'GVBINDIR': str(executable.parent)}
    version = run_bounded([str(executable), '-V'], cwd=root, env=env, timeout=10, max_output=1024**2)
    if version.returncode or not re.search(rb'\b16\.1\.0\b', version.stdout + version.stderr):
        raise ValueError('Candidate version probe failed')
    return dict(artifact_identity=identity, inventory_verified=True, system_libraries=sorted(set(libraries)),
                components=reviewed['components'], provenance_sha256=digest(provenance),
                inspector_sha256=hashlib.sha256(report.stdout).hexdigest(),
                qualification='inspection-only; corpus, relocation, signatures and cell acceptance still required')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'provenance'):
        parser.add_argument('--' + name, type=Path, required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--manifest',type=Path,help='Existing runtime manifest (requires real distribution URL)')
    mode.add_argument('--inventory',type=Path,help='Local inventory, no URL or catalog entry needed')
    mode.add_argument('--write-inventory',type=Path,help='Create new local inventory only; no inspection approval')
    parser.add_argument('--minimum-libc',help='Explicit Linux inspection baseline for --write-inventory')
    parser.add_argument('--static-elf',action='store_true',help='Local measured static musl inventory without a host libc baseline; not support qualification')
    parser.add_argument('--audit',type=Path)
    args = parser.parse_args()
    try:
        if args.write_inventory:
            if args.audit:raise ValueError('--write-inventory does not perform or approve an audit')
            if args.write_inventory.resolve().is_relative_to(args.root.resolve()):
                raise ValueError('Inventory output must be outside the inventoried tree')
            if args.write_inventory.exists():raise ValueError('Inventory output already exists')
            data=create_inventory(args.root,args.provenance,minimum_libc=args.minimum_libc,static_elf=args.static_elf)
            with args.write_inventory.open('x',encoding='utf-8') as stream:
                json.dump(data,stream,indent=2);stream.write('\n')
            print('Local inventory written; no artifact inspected, qualified or published.')
        else:
            if args.minimum_libc or args.static_elf:raise ValueError('Baseline/linkage flags are only for inventory creation; inspection uses recorded metadata')
            if not args.audit:raise ValueError('Inspection requires --audit; inventory never replaces a reviewed audit')
            print(json.dumps(inspect(args.root,args.manifest,args.provenance,args.audit,inventory=args.inventory), indent=2))
    except Exception as exc:
        parser.exit(1, type(exc).__name__ + ': ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
