"""Observe glibc startup/archive sources in an exact experimental Linux relink.

Only pinned readelf runs. Debug metadata is source evidence, not an exhaustive
transitive-source proof or license approval. No download or candidate mutation.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('glibc_source_observer',HERE/'audit-musl-objects.py')
musl=importlib.util.module_from_spec(spec);spec.loader.exec_module(musl)
audit=musl.audit;builder=musl.builder;notices=musl.notices


def sdk_inputs(record):
    if record.get('completed') is not True or record.get('artifact_id') not in ('linux-glibc-x86_64','linux-glibc-aarch64'):
        raise ValueError('Expected completed glibc experimental relink')
    if record['artifact_id']=='linux-glibc-aarch64':
        recipe=record.get('recipe',{})
        if ((record.get('native_os'),record.get('native_arch'))!=('linux','aarch64')
                or (recipe.get('os'),recipe.get('arch'),recipe.get('abi'))!=('linux','aarch64','glibc')):
            raise ValueError('ARM64 glibc provenance must match its native recipe')
    inputs={}
    for item in record['linkage']['inputs']:
        if item['scope']!='sdk':continue
        name=Path(item['path']).name
        if name in inputs:raise ValueError('Ambiguous SDK input basename')
        inputs[name]=item
    if not {'crt1.o','libc_nonshared.a'}.issubset(inputs):raise ValueError('Missing glibc startup/archive')
    return inputs


def archive_source_scope(artifact,name):
    if name=='libc_nonshared.a':return 'glibc'
    if artifact=='linux-glibc-aarch64' and name=='libcompiler_rt.a':return 'separate-runtime-review'
    raise ValueError('New SDK archive extraction requires separate source review')


def observed_member(name,members,cache):
    path=Path(name)
    if not path.is_absolute() or path.is_symlink() or not path.resolve().is_relative_to(cache.resolve()/'o'):
        raise ValueError('Archive member outside recorded object cache')
    payload=audit.bounded(path,64*1024**2)
    member=members.get(name)
    if member is None or hashlib.sha256(payload).hexdigest()!=member['sha256']:
        raise ValueError('Object differs from recorded archive member')
    return path.resolve()


def collect(linked_build,sdk_root,sdk_archive):
    started=time.monotonic()
    record=json.loads(audit.bounded(linked_build/'provenance.json',8*1024**2))
    inputs=sdk_inputs(record)
    if builder.digest(linked_build/'candidate/bin/dot')!=record['executable_sha256']:
        raise ValueError('Executable differs from provenance')
    identity=notices.sdk_archive_identity(record['sdk']['facts'])
    if (builder.digest(sdk_archive)!=identity['sha256']
            or builder.digest(sdk_root/'zig')!=record['sdk']['facts']['zig_sha256']):
        raise ValueError('SDK differs from recorded archive/compiler')
    inspector=record['sdk']['elf_inspector'];inspector_path=Path(inspector['path'])
    if not inspector_path.is_absolute() or builder.digest(inspector_path)!=inspector['sha256']:
        raise ValueError('Recorded ELF inspector changed')
    extraction=record['linkage']['archive_extractions']
    metadata=linked_build/'build/cmd/dot/CMakeFiles/dot.dir/why-extract.tsv'
    if audit.relinker.capture_extractions(metadata,record['linkage'],Path(record['relink']['parent_output'])/'build')!=extraction:
        raise ValueError('Linker extraction report changed')
    cache=Path(inputs['crt1.o']['path']).parents[2].resolve(strict=True)
    selected=[];input_observations=[]
    for name,item in sorted(inputs.items()):
        path=Path(item['path']);payload=audit.bounded(path,64*1024**2)
        if hashlib.sha256(payload).hexdigest()!=item['sha256']:raise ValueError('SDK link input changed')
        rows=[r for r in extraction['rows'] if r['archive_sha256']==item['sha256']]
        if name.endswith('.o'):
            if name!='crt1.o' or not path.resolve().is_relative_to(cache/'o'):
                raise ValueError('Unexpected direct SDK object')
            selected.append(dict(input=name,input_sha256=item['sha256'],path=path,member=None))
            kind='direct-object'
        elif name.endswith('.a'):
            kind='static-archive'
            if rows:
                scope=archive_source_scope(record['artifact_id'],name)
                if scope=='separate-runtime-review':
                    kind='static-archive-requires-separate-runtime-source-review'
                else:
                    members=audit.ar_members(payload)
                    for member in sorted({r['member'] for r in rows}):
                        selected.append(dict(input=name,input_sha256=item['sha256'],
                            path=observed_member(member,members,cache),member=Path(member).name))
        elif '.so.' in name:
            if rows:raise ValueError('Shared SDK input unexpectedly has archive extractions')
            kind='link-time-shared-input-not-bundled'
        else:raise ValueError('Unknown SDK link input kind')
        input_observations.append(dict(name=name,sha256=item['sha256'],size=len(payload),kind=kind,
            reported_extraction_rows=len(rows),absence_of_incorporated_code_proven=False))
    objects=[];sources={};total=0
    for item in selected:
        remaining=120-(time.monotonic()-started)
        if remaining<=0:raise ValueError('glibc object audit exceeded aggregate deadline')
        result=builder.run_bounded([str(inspector_path),'--debug-dump=info','--dwarf-depth=1',str(item['path'])],
            timeout=min(10,remaining),max_output=8*1024**2,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
        if result.returncode:raise ValueError('glibc object inspection failed')
        units=musl.compilation_units(result.stdout.decode('utf-8'))
        if not units:raise ValueError('No startup/archive compilation unit; explicit review required')
        names=[]
        for unit in units:
            relative=musl.sdk_source(unit,sdk_root)
            if not relative.startswith('lib/libc/glibc/'):raise ValueError('Observed source outside glibc SDK tree')
            raw=audit.bounded(sdk_root/relative,1024**2)
            if relative not in sources:total+=len(raw)
            if len(sources)>=5000 or total>64*1024**2:raise ValueError('Source observation budget exceeded')
            sources[relative]=dict(path=relative,size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                                   role='observed-compilation-unit')
            names.append(relative)
        objects.append(dict(input=item['input'],input_sha256=item['input_sha256'],member=item['member'],
            object_sha256=builder.digest(item['path']),dwarf_report_sha256=hashlib.sha256(result.stdout).hexdigest(),sources=names))
    # Source material associated with the startup recipe, explicitly distinguished
    # from DWARF observations (assembly may lack compilation-unit metadata).
    additional='lib/libc/glibc/csu/abi-note.S'
    raw=audit.bounded(sdk_root/additional,1024**2)
    sources.setdefault(additional,dict(path=additional,size=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                                      role='additional-startup-source-material-not-object-observation'))
    pinned=notices.archive_files(sdk_archive,sdk_root.name,set(sources))
    for name,item in sources.items():
        if hashlib.sha256(pinned[name]).hexdigest()!=item['sha256']:raise ValueError('glibc source differs from pinned SDK')
        prefix=notices.source_notice_prefix(pinned[name])
        item.update(leading_comment_bytes=len(prefix),leading_comment_sha256=hashlib.sha256(prefix).hexdigest(),
                    leading_comments=prefix.decode('utf-8'))
    if time.monotonic()-started>120:raise ValueError('glibc object audit exceeded aggregate deadline')
    return dict(kind='glibc-object-source-observations-not-license-approval',approved=False,qualified=False,
        source_to_binary_complete=False,artifact_id=record['artifact_id'],executable_sha256=record['executable_sha256'],
        provenance_sha256=builder.digest(linked_build/'provenance.json'),sdk_archive_sha256=identity['sha256'],
        inspector_sha256=inspector['sha256'],tool_sha256=builder.digest(Path(__file__)),
        input_observations=input_observations,objects=objects,sources=sorted(sources.values(),key=lambda i:i['path']),
        summary=dict(objects=len(objects),observed_source_units=sum(len(i['sources']) for i in objects),
            sources_verified=len(sources),sources_with_leading_comments=sum(bool(i['leading_comment_bytes']) for i in sources.values()),
            sdk_inputs=len(input_observations)),
        pending=['DWARF compilation units do not cover all transitive headers, assembly or retained sections',
                 'Zero extraction rows are observations, not proof that an input contributes no code',
                 'abi-note.S is additional pinned material, not an observed compilation-unit binding',
                 'Inputs marked separate-runtime-source-review are not covered by this glibc source observation',
                 'Per-file applicability, complete source offer and reviewed audit remain pending'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('linked-build','sdk-root','sdk-archive','report'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise ValueError('Object report must be new')
    result=collect(args.linked_build.resolve(),args.sdk_root.resolve(),args.sdk_archive.resolve())
    with args.report.open('x',encoding='utf-8') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result['summary']))
