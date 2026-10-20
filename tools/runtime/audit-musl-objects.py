"""Collect byte-bound musl object/source observations; never approve a license.

Read private linker metadata and pinned SDK bytes. Only the recorded readelf
is executed, with bounded output/deadlines. No compiler, candidate, shell or network.
DWARF observations do not prove reproducible compilation or section retention.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('musl_notice_inputs',HERE/'prepare-draft-notices.py')
notices=importlib.util.module_from_spec(spec);spec.loader.exec_module(notices)
audit=notices.audit
builder=audit.builder


def compilation_units(text):
    if len(text.encode('utf-8'))>8*1024**2:raise ValueError('DWARF output exceeds limit')
    units=[];current=None;top=False
    for line in text.splitlines():
        tag=re.match(r'\s*<(\d+)><[0-9a-f]+>:',line)
        if tag:
            top=tag[1]=='0' and '(DW_TAG_compile_unit)' in line
            if top:
                current={};units.append(current)
                if len(units)>1000:raise ValueError('Excessive compilation units')
            continue
        if not top:continue
        attribute=re.search(r'\bDW_AT_(name|comp_dir)\s*:\s*(.*)$',line)
        if attribute:
            key,value=attribute.groups()
            if key in current:raise ValueError('Ambiguous compilation unit attribute')
            value=re.sub(r'^\([^)]*\):\s*','',value)
            if not value or '\0' in value or len(value)>16384:raise ValueError('Invalid compilation unit attribute')
            current[key]=value
    return units


def sdk_source(unit,sdk):
    name=unit.get('name')
    if not name:raise ValueError('Compilation unit lacks source name')
    path=Path(name)
    if not path.is_absolute():
        directory=unit.get('comp_dir')
        if not directory or not Path(directory).is_absolute():raise ValueError('Relative source lacks absolute compilation directory')
        path=Path(directory)/path
    if path.is_symlink():raise ValueError('Source cannot be a symlink')
    sdk=sdk.resolve(strict=True)
    resolved=path.resolve()
    if not resolved.is_relative_to(sdk):raise ValueError('Compilation unit source is outside pinned SDK')
    if not resolved.is_file():raise ValueError('SDK source is absent')
    return resolved.relative_to(sdk).as_posix()


def notice_prefix(data):
    return notices.source_notice_prefix(data)


def collect(linked_build,sdk_root,sdk_archive):
    started=time.monotonic()
    record=json.loads(audit.bounded(linked_build/'provenance.json',8*1024**2))
    if record.get('artifact_id') not in ('linux-musl-x86_64','linux-musl-aarch64'):raise ValueError('Expected supported musl experimental relink')
    notices.sdk_notice_names(record,linked_build)
    if builder.digest(linked_build/'candidate/bin/dot')!=record['executable_sha256']:raise ValueError('Executable changed')
    facts=record['sdk']['facts']
    identity=notices.sdk_archive_identity(facts)
    if builder.digest(sdk_archive)!=identity['sha256'] or builder.digest(sdk_root/'zig')!=facts['zig_sha256']:
        raise ValueError('SDK differs from pinned build inputs')
    inspector=record['sdk']['elf_inspector']
    inspector_path=Path(inspector['path'])
    if not inspector_path.is_absolute() or builder.digest(inspector_path)!=inspector['sha256']:
        raise ValueError('Recorded ELF inspector changed')
    extraction=record['linkage']['archive_extractions']
    metadata=linked_build/'build/cmd/dot/CMakeFiles/dot.dir/why-extract.tsv'
    measured=audit.relinker.capture_extractions(metadata,record['linkage'],Path(record['relink']['parent_output'])/'build')
    if measured!=extraction:raise ValueError('Extraction observations changed')
    archives=[i for i in record['linkage']['inputs'] if i['scope']=='sdk' and Path(i['path']).name=='libc.a']
    if len(archives)!=1:raise ValueError('Expected one recorded musl archive')
    library=archives[0]
    payload=audit.bounded(Path(library['path']),64*1024**2)
    if hashlib.sha256(payload).hexdigest()!=library['sha256']:raise ValueError('musl archive changed')
    members=audit.ar_members(payload)
    observed=sorted({row['member'] for row in extraction['rows'] if row['archive_sha256']==library['sha256']})
    if not observed or len(observed)>5000:raise ValueError('Invalid musl extraction count')
    objects=[];sources={};source_bytes=0
    cache=Path(library['path']).parents[1].resolve(strict=True)
    for name in observed:
        path=Path(name)
        if not path.is_absolute() or not path.resolve().is_relative_to(cache):raise ValueError('Object outside recorded SDK cache')
        data=audit.bounded(path,64*1024**2)
        member=members.get(name)
        if member is None or hashlib.sha256(data).hexdigest()!=member['sha256']:raise ValueError('Cached object differs from archive member')
        remaining=120-(time.monotonic()-started)
        if remaining<=0:raise ValueError('Object audit exceeded aggregate deadline')
        result=builder.run_bounded([str(inspector_path),'--debug-dump=info','--dwarf-depth=1',str(path)],
            timeout=min(10,remaining),max_output=8*1024**2,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
        if result.returncode:raise ValueError('Object DWARF inspector failed')
        units=compilation_units(result.stdout.decode('utf-8'))
        names=[]
        for unit in units:
            relative=sdk_source(unit,sdk_root)
            if not relative.startswith('lib/libc/musl/'):raise ValueError('musl member refers to an unexpected source tree')
            source=audit.bounded(sdk_root/relative,1024**2)
            if relative not in sources:source_bytes+=len(source)
            if len(sources)>=5000 or source_bytes>64*1024**2:raise ValueError('Source observations exceed aggregate bound')
            sources[relative]=dict(path=relative,sha256=hashlib.sha256(source).hexdigest(),size=len(source))
            names.append(relative)
        objects.append(dict(member=path.name,object_sha256=member['sha256'],object_size=member['size'],
            dwarf_report_sha256=hashlib.sha256(result.stdout).hexdigest(),sources=names,
            unresolved_reason=None if names else 'No compilation unit source in DWARF; separate source review required'))
    pinned=notices.archive_files(sdk_archive,sdk_root.name,set(sources))
    for name,item in sources.items():
        if hashlib.sha256(pinned[name]).hexdigest()!=item['sha256']:raise ValueError('Source differs from pinned SDK archive')
        prefix=notice_prefix(pinned[name])
        item.update(leading_comment_bytes=len(prefix),leading_comment_sha256=hashlib.sha256(prefix).hexdigest(),
                    leading_comments=prefix.decode('utf-8'))
    if time.monotonic()-started>120:raise ValueError('Object audit exceeded aggregate deadline')
    return dict(kind='musl-object-source-observations-not-license-approval',approved=False,qualified=False,
        source_to_binary_complete=False,artifact_id=record['artifact_id'],executable_sha256=record['executable_sha256'],
        provenance_sha256=builder.digest(linked_build/'provenance.json'),sdk_archive_sha256=identity['sha256'],
        archive_sha256=library['sha256'],extraction_report_sha256=extraction['report_sha256'],inspector_sha256=inspector['sha256'],
        tool_sha256=builder.digest(Path(__file__)),objects=objects,sources=sorted(sources.values(),key=lambda i:i['path']),
        summary=dict(observed_members=len(objects),members_with_source=sum(bool(i['sources']) for i in objects),
            sources_verified=len(sources),sources_with_leading_comments=sum(bool(i['leading_comment_bytes']) for i in sources.values())),
        pending=['DWARF is compiler metadata, not reproducible source-to-binary proof or section-retention evidence',
            'Transitive headers, assembly without DWARF, direct crt1.o, libzigc/compiler_rt and LLVM sources remain separate review',
            'Per-file notice applicability, complete corresponding sources and approved audit remain pending',
            'No native Alpine/kernel/CPU qualification, candidate changes, catalog admission or publication'])


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
