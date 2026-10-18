"""Collect Graphviz object/source evidence without approving licenses or support.

Read pinned archives and compiler/linker metadata as bounded data. No compiler,
shell, network access, extraction to disk, installation or runtime admission.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('graphviz_builder', HERE / 'build-common.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
spec = importlib.util.spec_from_file_location('graphviz_relinker', HERE / 'relink-zig.py')
relinker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relinker)


def bounded(path, limit):
    if path.is_symlink():
        raise ValueError('Symlink is not an audit input')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Audit input exceeds limit')
    return data


def ar_members(data):
    """Hash regular ar payloads, including GNU/BSD long names; never follow names."""
    if len(data) > 64 * 1024**2 or not data.startswith(b'!<arch>\n'):
        raise ValueError('Expected bounded regular ar archive; thin archives need a separate audit')
    offset = 8
    long_names = b''
    members = {}
    count = 0
    while offset < len(data):
        count += 1
        header = data[offset:offset+60]
        if count > 10000 or len(header) != 60 or header[58:] != b'`\n':
            raise ValueError('Malformed or excessive archive members')
        size_text = header[48:58].strip()
        if not size_text.isdigit():
            raise ValueError('Invalid archive member size')
        size = int(size_text)
        start = offset + 60
        end = start + size
        if end > len(data) or end + size % 2 > len(data):
            raise ValueError('Truncated archive member')
        payload = data[start:end]
        offset = end + size % 2
        name = header[:16].decode('utf-8').strip()
        if name == '//':
            long_names = payload
            continue
        if name in ('/', '/SYM64/'):
            continue
        if name.startswith('#1/'):
            length = int(name[3:])
            if length < 1 or length > len(payload):
                raise ValueError('Invalid BSD member name')
            name = payload[:length].rstrip(b'\0').decode('utf-8')
            payload = payload[length:]
        elif name.startswith('/'):
            position = int(name[1:])
            stop = long_names.find(b'/\n', position)
            if position < 0 or stop < position or (position and long_names[position-2:position] != b'/\n'):
                raise ValueError('Invalid GNU member name')
            name = long_names[position:stop].decode('utf-8')
        else:
            name = name.removesuffix('/')
        if not name or '\0' in name or name in members:
            raise ValueError('Empty, invalid or ambiguous member name')
        members[name] = dict(sha256=hashlib.sha256(payload).hexdigest(), size=len(payload))
    return members


def object_dependencies(text, target):
    prefix = target + ':'
    if not text.startswith(prefix):
        raise ValueError('Compiler dependency target does not match object')
    return builder.parse_link_dependencies('dot:' + text[len(prefix):])


def match_member_object(member, candidates):
    matches = [path for path in candidates if builder.digest(path, maximum=64*1024**2)==member['sha256']]
    if len(matches) != 1:
        raise ValueError('Archive member has no unique byte-identical compiled object')
    return matches[0]


def collect(source_build, linked_build, archive):
    source_build = source_build.resolve(strict=True)
    linked_build = linked_build.resolve(strict=True)
    parent_path = source_build / 'provenance.json'
    linked_path = linked_build / 'provenance.json'
    parent = json.loads(bounded(parent_path, 8*1024**2))
    record = json.loads(bounded(linked_path, 8*1024**2))
    if not parent.get('completed') or not record.get('completed'):
        raise ValueError('Both builds must be completed')
    if record['relink']['parent_provenance_sha256'] != builder.digest(parent_path):
        raise ValueError('Relink is not bound to this source build')
    if builder.digest(linked_build/'candidate/bin/dot') != record['executable_sha256']:
        raise ValueError('Linked executable changed')
    source_lock = json.loads((HERE/'source-lock.json').read_text(encoding='utf-8'))
    if parent['source'] != source_lock or record['source'] != source_lock or builder.digest(archive) != source_lock['sha256']:
        raise ValueError('Source archive or provenance differs from source lock')
    build = source_build/'build'
    source = source_build/'source/graphviz-16.1.0'
    linkage = record['linkage']
    if not linkage.get('recorded') or not linkage.get('archive_extractions', {}).get('recorded'):
        raise ValueError('Real linker inputs and extraction observations required')
    if linkage['executable_sha256'] != record['executable_sha256']:
        raise ValueError('Linker evidence does not match executable')
    metadata = linked_build/'build/cmd/dot/CMakeFiles/dot.dir'
    for name, field in (('link.txt','link_command_sha256'),('link.d','dependency_file_sha256')):
        if builder.digest(metadata/name, maximum=8*1024**2) != linkage[field]:
            raise ValueError('Linker metadata changed')
    if relinker.capture_extractions(metadata/'why-extract.tsv',linkage,build) != linkage['archive_extractions']:
        raise ValueError('Extraction metadata does not match the linker report')
    depfiles = list(build.rglob('*.o.d'))
    if len(depfiles) > 10000:
        raise ValueError('Too many object dependency files')
    by_name = {}
    for path in depfiles:
        by_name.setdefault(path.name.removesuffix('.d'), []).append(path.with_suffix(''))
    inputs = [entry for entry in linkage['inputs'] if entry['scope']=='build']
    by_hash = {}
    for entry in inputs:
        by_hash.setdefault(entry['sha256'],[]).append(entry)
    objects = {}
    archive_cache = {}
    for entry in inputs:
        path = build/entry['path']
        if builder.digest(path, maximum=64*1024**2) != entry['sha256']:
            raise ValueError('Link input changed')
        if path.suffix == '.o':
            objects[str(path)] = dict(object_sha256=entry['sha256'], origin='direct-link-input')
    for row in linkage['archive_extractions']['rows']:
        matches = by_hash.get(row['archive_sha256'],[])
        if not matches:
            continue  # SDK extraction evidence is separate from this Graphviz collector.
        if len(matches) != 1:
            raise ValueError('Ambiguous archive hash in build inputs')
        entry = matches[0]
        path = build/entry['path']
        if path not in archive_cache:
            archive_cache[path] = ar_members(bounded(path, 64*1024**2))
        member = archive_cache[path].get(row['member'])
        if member is None:
            raise ValueError('Extracted member is absent from the hashed archive')
        object_path = match_member_object(member, by_name.get(Path(row['member']).name, []))
        objects[str(object_path)] = dict(object_sha256=member['sha256'], origin='archive-extraction',
                                        archive_sha256=entry['sha256'], member=row['member'])
    dependencies = {}
    source_bytes = {}
    total = 0
    for object_path, entry in sorted(objects.items()):
        path = Path(object_path)
        depfile = path.with_suffix(path.suffix+'.d')
        declared = object_dependencies(bounded(depfile, 8*1024**2).decode('utf-8'), path.relative_to(build).as_posix())
        keys = []
        for name in declared:
            dependency = Path(name)
            dependency = (dependency if dependency.is_absolute() else build/dependency).resolve(strict=True)
            origin = 'source' if dependency.is_relative_to(source) else 'generated-build' if dependency.is_relative_to(build) else 'external'
            label = dependency.relative_to(source).as_posix() if origin=='source' else dependency.relative_to(build).as_posix() if origin=='generated-build' else str(dependency)
            key = origin+':'+label
            keys.append(key)
            if key in dependencies:
                continue
            if len(dependencies) >= 5000:
                raise ValueError('Too many compiler inputs')
            payload = bounded(dependency, 8*1024**2)
            total += len(payload)
            if total > 256*1024**2:
                raise ValueError('Compiler inputs exceed total limit')
            text = payload[:8192].decode('utf-8', errors='replace')
            dependencies[key] = dict(path=label, origin=origin, sha256=hashlib.sha256(payload).hexdigest(),size=len(payload),
                spdx_indicators=re.findall(r'SPDX-License-Identifier:\s*([^\r\n*]+)', text),
                generated_bison_indicator='Bison' in text and 'parser' in text,
                license_review='pending')
            if origin=='source':
                source_bytes[label] = dependencies[key]['sha256']
        entry.update(object_path=path.relative_to(build).as_posix(), dependency_file_sha256=builder.digest(depfile),dependencies=sorted(set(keys)))
    verified = set()
    notices = []
    count = expanded = 0
    with tarfile.open(archive) as incoming:
        if incoming.pax_headers.get('comment') != source_lock['git_revision']:
            raise ValueError('Source archive revision differs')
        for member in incoming:
            count += 1
            expanded += member.size
            if count > 50000 or expanded > 1024**3:
                raise ValueError('Source archive exceeds limits')
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or '..' in relative.parts or relative.parts[0]!='graphviz-16.1.0':
                raise ValueError('Unexpected source archive path')
            relative = PurePosixPath(*relative.parts[1:]).as_posix()
            notice = PurePosixPath(relative).name.lower().startswith(('copying','license','notice','authors'))
            if not member.isfile() or (relative not in source_bytes and not notice):
                continue
            if member.size > 8*1024**2:
                raise ValueError('Source entry exceeds limit')
            payload = incoming.extractfile(member).read(8*1024**2+1)
            sha = hashlib.sha256(payload).hexdigest()
            if relative in source_bytes:
                if sha != source_bytes[relative]:
                    raise ValueError('Installed Graphviz source differs from archive')
                verified.add(relative)
            if notice:
                notices.append(dict(path=relative,sha256=sha,size=len(payload),review='pending'))
    if verified != set(source_bytes):
        raise ValueError('Compiler source input missing from pinned archive')
    return dict(kind='graphviz-object-source-evidence-not-license-approval',approved=False,qualified=False,
        executable_sha256=record['executable_sha256'],provenance_sha256=builder.digest(linked_path),
        parent_provenance_sha256=builder.digest(parent_path),source=source_lock,
        objects=list(objects.values()),dependencies=dependencies,notice_candidates=sorted(notices,key=lambda x:x['path']),
        summary=dict(objects=len(objects),verified_graphviz_source_files=len(verified),
                     generated_files=sum(i['origin']=='generated-build' for i in dependencies.values()),
                     external_files=sum(i['origin']=='external' for i in dependencies.values())),
        tool_sha256=builder.digest(Path(__file__)),
        limitations=['Compiler declarations and object-byte equality do not prove section retention or complete source-to-binary correspondence',
                     'Generated parsers/configuration and external headers require separate source/license review',
                     'Notice filenames and SPDX/Bison indicators are evidence, not license decisions',
                     'No approved audit, catalog change, publication or native support qualification'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-build', type=Path, required=True)
    parser.add_argument('--linked-build', type=Path, required=True)
    parser.add_argument('--source-archive', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.report.exists():
            raise ValueError('Report already exists')
        result = collect(args.source_build,args.linked_build,args.source_archive)
        with args.report.open('x',encoding='utf-8') as stream:
            json.dump(result,stream,indent=2);stream.write('\n')
        print(json.dumps(result['summary']))
    except (OSError, ValueError, KeyError, tarfile.TarError) as exc:
        parser.exit(1,type(exc).__name__+': '+str(exc)+'\n')


if __name__=='__main__':main()
