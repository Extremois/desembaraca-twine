"""Prepare a new local notice candidate, never an approved audit or release.

Inputs are pinned archives, a completed private relink and its source evidence.
Existing candidates stay untouched. No download, compiler or global install.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('notice_source_audit',HERE/'audit-graphviz-sources.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
builder=audit.builder


def color_notice(data):
    lines=[]
    for line in data.splitlines(keepends=True):
        if line.strip() and not line.startswith(b'#'):break
        lines.append(line)
    prefix=b''.join(lines)
    if len(prefix)>65536 or not all(token in prefix for token in (b'Apache-Style Software License for ColorBrewer',b'Copyright',b'THIS SOFTWARE IS PROVIDED')):
        raise ValueError('ColorBrewer notice is missing or incomplete')
    return prefix


def bison_notice(data):
    data=data[:65536]
    if not data.startswith(b'/* A Bison parser, made by GNU Bison '):
        raise ValueError('Expected generated Bison prefix')
    end=0
    while match:=re.match(rb'\s*/\*.*?\*/',data[end:],re.DOTALL):
        end+=match.end()
        comment=match.group()
        if b'As a special exception' in comment and b'version 2.2 of Bison.' in comment:
            if b'Copyright' not in data[:end] or b'GNU General Public License' not in data[:end]:break
            return data[:end]
    raise ValueError('Complete Bison license and exception not found')


def source_notice_prefix(data):
    end=0
    while True:
        start=end+re.match(rb'\s*',data[end:]).end()
        if data[start:start+2]==b'/*':
            stop=data.find(b'*/',start+2)
            if stop<0:raise ValueError('Unterminated leading source comment')
            end=stop+2
        elif data[start:start+2]==b'//':
            stop=data.find(b'\n',start+2);end=len(data) if stop<0 else stop+1
        else:
            if end:end=start
            break
        if end>65536:raise ValueError('Leading source notice exceeds limit')
    if end>65536:raise ValueError('Leading source notice exceeds limit')
    return data[:end]


def object_notice_sources(record,linked_build,evidence,kind,prefixes):
    if evidence is None:return {},None
    data=json.loads(audit.bounded(evidence,8*1024**2))
    if (record['artifact_id']!='linux-musl-x86_64'
            or data.get('kind')!=kind
            or data.get('provenance_sha256')!=builder.digest(linked_build/'provenance.json')
            or data.get('executable_sha256')!=record['executable_sha256']
            or data.get('sdk_archive_sha256')!=record['sdk']['facts']['archive_sha256']):
        raise ValueError('Object evidence does not match this build and SDK')
    entries=data.get('sources')
    if not isinstance(entries,list) or not 0<len(entries)<=5000:raise ValueError('Invalid source evidence count')
    sources={}
    for item in entries:
        name=item['path'];path=PurePosixPath(name)
        if (not name.startswith(prefixes) or '..' in path.parts or path.as_posix()!=name
                or name in sources or not re.fullmatch(r'[0-9a-f]{64}',item.get('sha256',''))):
            raise ValueError('Invalid or duplicate source evidence')
        sources[name]=item
    return sources,builder.digest(evidence)


def musl_notice_sources(record,linked_build,evidence):
    return object_notice_sources(record,linked_build,evidence,
        'musl-object-source-observations-not-license-approval',('lib/libc/musl/',))


def zig_runtime_notice_sources(record,linked_build,evidence):
    return object_notice_sources(record,linked_build,evidence,
        'zig-startup-runtime-source-observations-not-approved',('lib/',))


def verified_source_prefix(data,item):
    if hashlib.sha256(data).hexdigest()!=item['sha256'] or len(data)!=item['size']:
        raise ValueError('Source differs from pinned archive')
    prefix=source_notice_prefix(data)
    if len(prefix)!=item['leading_comment_bytes'] or hashlib.sha256(prefix).hexdigest()!=item['leading_comment_sha256']:
        raise ValueError('Leading comment evidence differs from pinned source')
    return prefix


def archive_files(path,prefix,names):
    found={};count=expanded=0
    with tarfile.open(path) as archive:
        for member in archive:
            count+=1;expanded+=member.size
            if count>50000 or expanded>1024**3:raise ValueError('Archive exceeds notice preparation limits')
            parts=PurePosixPath(member.name)
            if parts.is_absolute() or '..' in parts.parts or parts.parts[0]!=prefix:raise ValueError('Unexpected archive path')
            relative=PurePosixPath(*parts.parts[1:]).as_posix()
            if relative not in names:continue
            if relative in found or not member.isfile() or member.size>1024**2:raise ValueError('Invalid or excessive notice/header entry')
            found[relative]=archive.extractfile(member).read(1024**2+1)
    if set(found)!=set(names):raise ValueError('Required notice/header absent from archive')
    return found


def sdk_notice_names(record,linked_build):
    artifact=record.get('artifact_id')
    if not record.get('completed') or artifact not in ('linux-glibc-x86_64','linux-musl-x86_64'):
        raise ValueError('Expected completed experimental Linux x86_64 build')
    common={'LICENSE','lib/libcxx/LICENSE.TXT','lib/libcxxabi/LICENSE.TXT','lib/libunwind/LICENSE.TXT'}
    if artifact=='linux-glibc-x86_64':return common|{'lib/libc/glibc/LICENSES'}
    measured=record.get('static_elf_inspection',{})
    if any(measured.get(key) is not True for key in
           ('no_interpreter','no_dynamic_section','no_needed_libraries','no_glibc_symbols')):
        raise ValueError('musl notices require a measured static candidate')
    facts=record.get('sdk',{}).get('facts',{})
    if (facts.get('target_os'),facts.get('target_arch'),facts.get('target_libc_family'),facts.get('static_linking'))!=('linux','x86_64','musl',True):
        raise ValueError('musl SDK target facts do not match artifact')
    report=linked_build/'static-elf-inspection.txt'
    data=audit.bounded(report,8*1024**2)
    if hashlib.sha256(data).hexdigest()!=measured.get('report_sha256'):
        raise ValueError('Static ELF report changed')
    builder.confirm_static_linkage(data.decode('utf-8'))
    return common|{'lib/libc/musl/COPYRIGHT'}


def prepare(linked_build,source_build,evidence,graphviz_archive,sdk_archive,sdk_root,output,
            musl_object_evidence=None,zig_runtime_evidence=None):
    record=json.loads(audit.bounded(linked_build/'provenance.json',8*1024**2))
    source=json.loads(audit.bounded(evidence,8*1024**2))
    sdk_names=sdk_notice_names(record,linked_build)
    if source['provenance_sha256']!=builder.digest(linked_build/'provenance.json') or source['executable_sha256']!=record['executable_sha256']:
        raise ValueError('Source evidence does not match linked build')
    if record['relink']['parent_provenance_sha256']!=builder.digest(source_build/'provenance.json'):
        raise ValueError('Source build changed')
    binary=linked_build/'candidate/bin/dot'
    if builder.digest(binary)!=record['executable_sha256']:raise ValueError('Executable changed')
    lock=json.loads((HERE/'source-lock.json').read_text())
    facts=record['sdk']['facts']
    if record['source']!=lock or builder.digest(graphviz_archive)!=lock['sha256'] or builder.digest(sdk_archive)!=facts['archive_sha256']:
        raise ValueError('Source archive differs from recorded bytes')
    if builder.digest(sdk_root/'zig')!=facts['zig_sha256']:raise ValueError('SDK root differs from build')
    musl_sources,musl_evidence_sha=musl_notice_sources(record,linked_build,musl_object_evidence)
    runtime_sources,runtime_evidence_sha=zig_runtime_notice_sources(record,linked_build,zig_runtime_evidence)
    dependencies=source['dependencies'].values() if isinstance(source['dependencies'],dict) else source['dependencies']
    dependencies=list(dependencies)
    external={}
    for item in dependencies:
        if item['origin']!='external':continue
        path=Path(item['path'])
        if not path.is_relative_to(sdk_root):raise ValueError('External input is outside the verified SDK')
        if builder.digest(path,maximum=1024**2)!=item['sha256']:raise ValueError('External header changed')
        external[path.relative_to(sdk_root).as_posix()]=item['sha256']
    generated={item['path']:item for item in dependencies if item['origin']=='generated-build'}
    for name,item in generated.items():
        if builder.digest(source_build/'build'/name,maximum=8*1024**2)!=item['sha256']:raise ValueError('Generated input changed')
    graphviz_names={'COPYING','AUTHORS','lib/rbtree/LICENSE','lib/common/brewer_colors'}
    graphviz=archive_files(graphviz_archive,'graphviz-16.1.0',graphviz_names)
    sdk=archive_files(sdk_archive,sdk_root.name,sdk_names|set(external)|set(musl_sources)|set(runtime_sources))
    for name,sha in external.items():
        if hashlib.sha256(sdk[name]).hexdigest()!=sha:raise ValueError('SDK header differs from pinned archive')
    materials=[]
    for name in sorted(graphviz_names):
        data=graphviz[name]
        materials.append((('ColorBrewer.txt' if name.endswith('brewer_colors') else 'Graphviz-'+name.replace('/','__')+'.txt'),
            color_notice(data) if name.endswith('brewer_colors') else data,
            dict(kind='graphviz-source-archive',path=name,archive_sha256=lock['sha256'],source_sha256=hashlib.sha256(data).hexdigest())))
    for name in sorted(sdk_names):
        materials.append(('SDK-'+name.replace('/','__')+'.txt',sdk[name],
                          dict(kind='sdk-source-archive',path=name,archive_sha256=facts['archive_sha256'],source_sha256=hashlib.sha256(sdk[name]).hexdigest())))
    for label,entries in (('musl-source',musl_sources),('zig-runtime-source',runtime_sources)):
        for name,item in sorted(entries.items()):
            prefix=verified_source_prefix(sdk[name],item)
            if prefix:
                materials.append((label+'-'+name.replace('/','__')+'.txt',prefix,
                    dict(kind='sdk-source-comment-prefix',path=name,archive_sha256=facts['archive_sha256'],
                         source_sha256=item['sha256'],offset=0,length=len(prefix))))
    for name in ('lib/cgraph/grammar.c','lib/cgraph/grammar.h','lib/common/htmlparse.c','lib/common/htmlparse.h'):
        if name not in generated:raise ValueError('Bison output is absent from compiler evidence')
        data=audit.bounded(source_build/'build'/name,8*1024**2)
        prefix=bison_notice(data)
        materials.append(('Bison-'+name.replace('/','__')+'.txt',prefix,
                          dict(kind='generated-file-prefix',path=name,source_sha256=generated[name]['sha256'],offset=0,length=len(prefix))))
    references=('Draft notice review material; approval and source offer remain incomplete.\n\n'
                'Graphviz 16.1.0 source:\n'+lock['url']+'\nSHA-256: '+lock['sha256']+'\n\n'
                'SDK archive used for source/header verification:\n'+facts['archive_url']+'\nSHA-256: '+facts['archive_sha256']+'\n').encode()
    materials.append(('SOURCE-REFERENCES.txt',references,dict(kind='maintainer-draft-reference')))
    output.mkdir(mode=0o700,parents=True,exist_ok=False)
    if record['artifact_id']=='linux-musl-x86_64':
        shutil.copyfile(linked_build/'static-elf-inspection.txt',output/'static-elf-inspection.txt')
        if builder.digest(output/'static-elf-inspection.txt')!=record['static_elf_inspection']['report_sha256']:
            raise ValueError('Static ELF report changed during copy')
    candidate=output/'candidate'
    (candidate/'bin').mkdir(parents=True)
    shutil.copyfile(binary,candidate/'bin/dot');(candidate/'bin/dot').chmod(0o755)
    if builder.digest(candidate/'bin/dot')!=record['executable_sha256']:raise ValueError('Executable changed during copy')
    notices=candidate/'third-party-notices';notices.mkdir()
    inventory=[]
    for name,data,origin in materials:
        path=notices/name
        with path.open('xb') as stream:stream.write(data)
        path.chmod(0o644)
        inventory.append(dict(path=path.relative_to(candidate).as_posix(),sha256=builder.digest(path),size=len(data),origin=origin))
    review=dict(kind='draft-notice-candidate-not-approved',approved=False,qualified=False,artifact_id=record['artifact_id'],
        executable_sha256=record['executable_sha256'],parent_provenance_sha256=builder.digest(linked_build/'provenance.json'),
        source_evidence_sha256=builder.digest(evidence),sdk_headers_verified=len(external),generated_files_verified=len(generated),notices=inventory,
        tool_sha256=builder.digest(Path(__file__)),
        pending=['Per-file license applicability and complete source offer','W3C/X11 data provenance and notice applicability',
                 'Flex generator provenance and canonical license texts as applicable','Final audited inventory and native baseline/cell qualification'])
    if musl_evidence_sha:
        review.update(musl_object_evidence_sha256=musl_evidence_sha,musl_sources_verified=len(musl_sources),
            musl_source_comment_files=sum(bool(i['leading_comment_bytes']) for i in musl_sources.values()))
    if runtime_evidence_sha:
        review.update(zig_runtime_evidence_sha256=runtime_evidence_sha,zig_runtime_sources_verified=len(runtime_sources),
            zig_runtime_comment_files=sum(bool(i['leading_comment_bytes']) for i in runtime_sources.values()))
        review['pending'].append('Generated builtin is separate review material; runtime source comments do not resolve third-party applicability')
    (output/'review.json').write_text(json.dumps(review,indent=2)+'\n')
    record.update(output=str(output),qualification='draft notices only; no approved audit or support',
                  notice_preparation=dict(review_sha256=builder.digest(output/'review.json'),approved=False))
    (output/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
    return review


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('linked-build','source-build','evidence','graphviz-archive','sdk-archive','sdk-root','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--musl-object-evidence',type=Path,help='Optional byte-bound musl object/source observations; comments rechecked against pinned SDK')
    parser.add_argument('--zig-runtime-evidence',type=Path,help='Optional startup/Zig source observations; only pinned SDK source prefixes are bundled')
    args=parser.parse_args()
    try:
        result=prepare(**{name:path.resolve() if path is not None else None for name,path in vars(args).items()})
        print(json.dumps(dict(notices=len(result['notices']),sdk_headers_verified=result['sdk_headers_verified'],qualified=False)))
    except (OSError,ValueError,KeyError,tarfile.TarError) as exc:parser.exit(1,type(exc).__name__+': '+str(exc)+'\n')


if __name__=='__main__':main()
