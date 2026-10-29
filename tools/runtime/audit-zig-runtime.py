"""Observe selected startup/Zig runtime sources in a private Linux relink.

Only the pinned readelf is executed. Line-table presence does not establish
retained code, an exhaustive dependency graph or an approved license audit.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runtime_musl_objects',HERE/'audit-musl-objects.py')
musl=importlib.util.module_from_spec(spec);spec.loader.exec_module(musl)
audit=musl.audit;builder=musl.builder;notices=musl.notices


def line_table_files(text,comp_dir):
    """Parse exactly one GNU readelf DWARF4 table as data; fail on ambiguity."""
    if len(text.encode('utf-8'))>8*1024**2 or re.findall(r'DWARF Version:\s*(\d+)',text)!=['4']:
        raise ValueError('Expected one bounded DWARF4 line table')
    match=re.search(r'The Directory Table[^\n]*:\n(.*?)\n\s*The File Name Table[^\n]*:\n(.*?)\n\s*Line Number Statements:',text,re.DOTALL)
    if not match or not Path(comp_dir).is_absolute():raise ValueError('Line table structure or compilation directory is invalid')
    directories={0:Path(comp_dir)}
    for line in match[1].splitlines():
        if not line.strip():continue
        entry=re.fullmatch(r'\s*(\d+)\s+(.+?)\s*',line)
        if not entry or int(entry[1]) in directories:raise ValueError('Invalid or duplicate line directory')
        path=Path(entry[2]);directories[int(entry[1])]=path if path.is_absolute() else Path(comp_dir)/path
        if len(directories)>5001:raise ValueError('Excessive line directories')
    files=[];ids=set();header=False
    for line in match[2].splitlines():
        if not line.strip():continue
        if line.split()==['Entry','Dir','Time','Size','Name'] and not header:
            header=True;continue
        entry=re.fullmatch(r'\s*(\d+)\s+(\d+)\s+\d+\s+\d+\s+(.+?)\s*',line)
        if not header or not entry:raise ValueError('Malformed line file entry')
        index,directory,name=int(entry[1]),int(entry[2]),entry[3]
        filename=Path(name)
        if (index<1 or index in ids or directory not in directories or filename.is_absolute()
                or '..' in filename.parts or '\0' in name or len(name)>16384):
            raise ValueError('Invalid, ambiguous or escaping line file entry')
        ids.add(index);files.append(dict(file_id=index,path=directories[directory]/filename))
        if len(files)>5000:raise ValueError('Excessive line file entries')
    if not files:raise ValueError('Empty line file table')
    return files


def source_identity(path,sdk,cache):
    if path.is_symlink():raise ValueError('Runtime source cannot be a symlink')
    resolved=path.resolve(strict=True);sdk=sdk.resolve(strict=True);cache=cache.resolve(strict=True)
    if not resolved.is_file():raise ValueError('Runtime source is not a regular file')
    if resolved.is_relative_to(sdk):return 'sdk',resolved.relative_to(sdk).as_posix()
    if resolved.is_relative_to(cache/'b') and resolved.name=='builtin.zig':
        return 'generated',resolved.relative_to(cache).as_posix()
    raise ValueError('Runtime source outside pinned SDK or generated builtin cache')


def license_indicators(data):
    """Flag review locations throughout source; regex matches are not license decisions."""
    if len(data)>1024**2:raise ValueError('Source exceeds indicator scan bound')
    prefix=notices.source_notice_prefix(data)
    offset=0;items=[]
    for number,line in enumerate(data.splitlines(keepends=True),1):
        if re.search(rb'copyright|SPDX-License-Identifier|licen[cs]e|public domain|golang\.org',line,re.IGNORECASE):
            if len(items)>=256 or len(line)>4096:raise ValueError('Source indicator output exceeds bound')
            items.append(dict(line=number,text=line.decode('utf-8').rstrip('\r\n'),within_leading_comments=offset<len(prefix)))
        offset+=len(line)
    return items


def runtime_profile(record):
    if record.get('artifact_id')=='linux-musl-x86_64':
        return {'crt1.o','libzigc.a','libcompiler_rt.a'},('lib/c.zig','lib/compiler_rt.zig')
    recipe=record.get('recipe',{})
    if (record.get('artifact_id')=='linux-musl-aarch64' and record.get('completed') is True
            and (record.get('native_os'),record.get('native_arch'))==('linux','aarch64')
            and (recipe.get('os'),recipe.get('arch'),recipe.get('abi'))==('linux','aarch64','musl')):
        return {'crt1.o','libzigc.a','libcompiler_rt.a'},('lib/c.zig','lib/compiler_rt.zig')
    if (record.get('artifact_id')=='linux-glibc-aarch64' and record.get('completed') is True
            and (record.get('native_os'),record.get('native_arch'))==('linux','aarch64')
            and (recipe.get('os'),recipe.get('arch'),recipe.get('abi'))==('linux','aarch64','glibc')):
        return {'libcompiler_rt.a'},('lib/compiler_rt.zig',)
    raise ValueError('Expected supported musl startup or native ARM64 glibc runtime record')


def collect(linked_build,sdk_root,sdk_archive):
    started=time.monotonic()
    record=json.loads(audit.bounded(linked_build/'provenance.json',8*1024**2))
    required,entrypoints=runtime_profile(record)
    if record['artifact_id'] in ('linux-musl-x86_64','linux-musl-aarch64'):notices.sdk_notice_names(record,linked_build)
    if builder.digest(linked_build/'candidate/bin/dot')!=record['executable_sha256']:raise ValueError('Executable changed')
    facts=record['sdk']['facts']
    identity=notices.sdk_archive_identity(facts)
    if builder.digest(sdk_archive)!=identity['sha256'] or builder.digest(sdk_root/'zig')!=facts['zig_sha256']:
        raise ValueError('SDK differs from pinned build')
    inspector=record['sdk']['elf_inspector'];inspector_path=Path(inspector['path'])
    if not inspector_path.is_absolute() or builder.digest(inspector_path)!=inspector['sha256']:raise ValueError('ELF inspector changed')
    extraction=record['linkage']['archive_extractions']
    metadata=linked_build/'build/cmd/dot/CMakeFiles/dot.dir/why-extract.tsv'
    if audit.relinker.capture_extractions(metadata,record['linkage'],Path(record['relink']['parent_output'])/'build')!=extraction:
        raise ValueError('Extraction observations changed')
    entries={}
    for item in record['linkage']['inputs']:
        name=Path(item['path']).name
        if item['scope']=='sdk' and name in required:
            if name in entries:raise ValueError('Ambiguous runtime input')
            entries[name]=item
    if set(entries)!=required:raise ValueError('Runtime inputs incomplete')
    cache=Path(entries['libcompiler_rt.a']['path']).parents[2].resolve(strict=True)
    sources={};generated={};objects=[];total=0
    for name,item in sorted(entries.items()):
        path=Path(item['path']);payload=audit.bounded(path,64*1024**2)
        if hashlib.sha256(payload).hexdigest()!=item['sha256']:raise ValueError('Runtime input changed')
        member_name=None
        if name.endswith('.a'):
            observed={r['member'] for r in extraction['rows'] if r['archive_sha256']==item['sha256']}
            if len(observed)!=1:raise ValueError('Expected one runtime member observation')
            member_name=observed.pop();members=audit.ar_members(payload);path=Path(member_name)
            if not path.is_absolute() or not path.resolve().is_relative_to(cache/'o'):raise ValueError('Runtime member outside recorded cache')
            payload=audit.bounded(path,64*1024**2)
            member=members.get(member_name)
            if member is None or hashlib.sha256(payload).hexdigest()!=member['sha256']:raise ValueError('Runtime object differs from archive member')
        reports=[]
        for mode in ('info','rawline'):
            remaining=120-(time.monotonic()-started)
            if remaining<=0:raise ValueError('Runtime source audit exceeded deadline')
            argv=[str(inspector_path),'--debug-dump='+mode]
            if mode=='info':argv.append('--dwarf-depth=1')
            result=builder.run_bounded(argv+[str(path)],timeout=min(10,remaining),max_output=8*1024**2,
                env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
            if result.returncode:raise ValueError('Runtime DWARF inspection failed')
            reports.append(result.stdout)
        units=musl.compilation_units(reports[0].decode('utf-8'))
        if len(units)!=1:raise ValueError('Expected one runtime compilation unit')
        unit=units[0]
        expected={'libzigc.a':'zigc','libcompiler_rt.a':'compiler_rt'}
        if name in expected and unit.get('name')!=expected[name]:raise ValueError('Unexpected virtual runtime unit')
        table=line_table_files(reports[1].decode('utf-8'),unit.get('comp_dir',''))
        observed_sources=[]
        for file in table:
            origin,relative=source_identity(file['path'],sdk_root,cache)
            collection=sources if origin=='sdk' else generated
            data=audit.bounded(file['path'],1024**2)
            if relative not in collection:total+=len(data)
            if len(sources)+len(generated)>=5000 or total>64*1024**2:raise ValueError('Runtime source aggregate exceeds bound')
            collection[relative]=dict(path=relative,size=len(data),sha256=hashlib.sha256(data).hexdigest())
            observed_sources.append(dict(file_id=file['file_id'],origin=origin,path=relative))
        if name=='crt1.o':
            source=musl.sdk_source(unit,sdk_root)
            if source not in {f['path'] for f in observed_sources if f['origin']=='sdk'}:raise ValueError('Startup unit and line table differ')
        unit_name=source if name=='crt1.o' else expected[name]
        objects.append(dict(input=name,input_sha256=item['sha256'],member=Path(member_name).name if member_name else None,
            object_sha256=hashlib.sha256(payload).hexdigest(),object_size=len(payload),
            compilation_unit=unit_name,
            info_report_sha256=hashlib.sha256(reports[0]).hexdigest(),line_report_sha256=hashlib.sha256(reports[1]).hexdigest(),
            line_table_files=observed_sources))
    # Explicit entrypoints are additional source material, never inferred from virtual CU names.
    for name in entrypoints:
        data=audit.bounded(sdk_root/name,1024**2)
        sources[name]=dict(path=name,size=len(data),sha256=hashlib.sha256(data).hexdigest(),role='explicit-source-entrypoint-not-line-table-observation')
    pinned=notices.archive_files(sdk_archive,sdk_root.name,set(sources))
    for name,item in sources.items():
        if hashlib.sha256(pinned[name]).hexdigest()!=item['sha256']:raise ValueError('Runtime source differs from pinned SDK archive')
        prefix=notices.source_notice_prefix(pinned[name])
        item.update(leading_comment_bytes=len(prefix),leading_comment_sha256=hashlib.sha256(prefix).hexdigest(),
            leading_comments=prefix.decode('utf-8'),license_indicators=license_indicators(pinned[name]))
    if time.monotonic()-started>120:raise ValueError('Runtime source audit exceeded deadline')
    return dict(kind='zig-startup-runtime-source-observations-not-approved',approved=False,qualified=False,source_to_binary_complete=False,
        artifact_id=record['artifact_id'],executable_sha256=record['executable_sha256'],provenance_sha256=builder.digest(linked_build/'provenance.json'),
        sdk_archive_sha256=identity['sha256'],inspector_sha256=inspector['sha256'],tool_sha256=builder.digest(Path(__file__)),
        objects=objects,sources=sorted(sources.values(),key=lambda i:i['path']),generated_files=sorted(generated.values(),key=lambda i:i['path']),
        summary=dict(objects=len(objects),sdk_sources_verified=len(sources),generated_files_hashed=len(generated),
            sources_with_leading_comments=sum(bool(i['leading_comment_bytes']) for i in sources.values()),
            sources_with_license_indicators=sum(bool(i['license_indicators']) for i in sources.values()),
            sources_with_indicators_outside_prefix=sum(any(not line['within_leading_comments'] for line in i['license_indicators']) for i in sources.values())),
        pending=['File tables overapproximate source presence; not retained-section or exhaustive transitive-source evidence',
            'Generated builtin current-file hashes are not pinned SDK sources or proof of their build-time bytes',
            'Per-file Zig/LLVM/third-party applicability, complete source offer and reviewed audit remain pending',
            'Other headers/components, native Alpine/ARM64/kernel/CPU qualification and distribution remain pending'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('linked-build','sdk-root','sdk-archive','report'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    try:
        if args.report.exists():raise ValueError('Report already exists')
        result=collect(args.linked_build.resolve(),args.sdk_root.resolve(),args.sdk_archive.resolve())
        with args.report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        print(json.dumps(result['summary']))
    except (OSError,ValueError,KeyError) as exc:parser.exit(1,type(exc).__name__+': '+str(exc)+'\n')


if __name__=='__main__':main()
