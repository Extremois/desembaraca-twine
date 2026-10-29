"""Bind generated Graphviz tables to pinned inputs and public reference values.

Runs only two pinned upstream Python generators, with bounded resources, in a
new temporary directory. Reference matching is not a complete license audit or
proof of historical copying. No download, catalog mutation or publication.
"""
import argparse
import gzip
import hashlib
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import tarfile
import tempfile
from urllib.parse import urljoin

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('data_source_audit',HERE/'audit-graphviz-sources.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
builder=audit.builder
REFERENCES=HERE/'licenses/data-references'
W3C_REFERENCES=REFERENCES/'w3c'


class PolicyText(HTMLParser):
    """Render policy text as data, preserving visible words and link targets."""
    def __init__(self,url):
        super().__init__(convert_charrefs=True)
        self.url=url;self.chunks=[];self.ignored=0;self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('head','script','style'):self.ignored+=1
        if self.ignored:return
        if tag in ('p','div','li','h1','h2','h3','h4','br','hr'):self.chunks.append('\n')
        if tag=='a':self.links.append(dict(attrs).get('href'))
    def handle_endtag(self,tag):
        if tag in ('head','script','style'):
            self.ignored=max(0,self.ignored-1);return
        if self.ignored:return
        if tag=='a' and self.links:
            href=self.links.pop()
            if href:self.chunks.append(' ('+urljoin(self.url,href)+') ')
        if tag in ('p','div','li','h1','h2','h3','h4'):self.chunks.append('\n')
    def handle_data(self,data):
        if not self.ignored:self.chunks.append(data)


def policy_text(data,encoding,url):
    if encoding not in ('utf-8','iso-8859-1','us-ascii'):raise ValueError('Unsupported policy encoding')
    parser=PolicyText(url);parser.feed(data.decode(encoding));parser.close()
    return '\n'.join(line for part in ''.join(parser.chunks).splitlines() if (line:=' '.join(part.split())))+'\n'


def w3c_reference_materials(*, include_legacy_entities=True):
    """Preserve dated policies and original publication headers, without approval."""
    lock=json.loads(audit.bounded(W3C_REFERENCES/'sources.json',65536))
    expected={'document-1999','software-1998','document-2002','document-2023','html401-index','svg11-index'}
    if set(lock['references'])!=expected:raise ValueError('Incomplete W3C policy reference set')
    raw_files={};materials=[]
    for name in sorted(expected):
        if not include_legacy_entities and name in ('html401-index', 'document-1999', 'software-1998'):
            continue
        item=lock['references'][name];filename=item['file'];path=Path(filename)
        if (path.name!=filename or '\\' in filename or ':' in filename
                or not item['url'].startswith('https://www.w3.org/')):
            raise ValueError('Invalid W3C reference identity')
        stored=audit.bounded(W3C_REFERENCES/path,1024**2)
        if hashlib.sha256(stored).hexdigest()!=item['stored_sha256']:raise ValueError('Stored W3C reference changed')
        with gzip.GzipFile(fileobj=io.BytesIO(stored)) as stream:raw=stream.read(1024**2+1)
        if len(raw)!=item['size'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
            raise ValueError('W3C reference size/hash mismatch')
        raw_files[name]=raw
        material=raw
        if name.endswith('-index'):
            copyright=re.search(rb'<p\s+class="copyright">.*?</p>',raw,re.IGNORECASE|re.DOTALL)
            if copyright is None:raise ValueError('Original publication copyright missing')
            separator=re.search(rb'<hr\b',raw[copyright.end():],re.IGNORECASE)
            if separator is None:raise ValueError('Publication header separator missing')
            material=raw[:copyright.end()+separator.start()]
        text=policy_text(material,item['encoding'],item['resolved_url'])
        if name.endswith('-index') and 'W3C Recommendation' not in text:
            raise ValueError('Original publication status missing')
        content=('W3C reference review material; license applicability remains pending.\n'
            'Source: '+item['url']+'\nObserved destination: '+item['resolved_url']+
            '\nRaw source SHA-256: '+item['sha256']+'\n\n'+text).encode('utf-8')
        materials.append(('W3C-'+name+'.txt',content,dict(kind='pinned-w3c-reference-text',approved=False,
            source_url=item['url'],resolved_url=item['resolved_url'],source_sha256=item['sha256'],
            stored_sha256=item['stored_sha256'],raw_offset=0,raw_length=len(material),encoding=item['encoding'],
            scope='Publication header' if name.endswith('-index') else 'Full policy text; no retroactive license assignment')))
    routing=lock['policy_routing']
    for name in routing['html401']['policy_references'] if include_legacy_entities else ():
        if lock['references'][name]['url'].encode() not in raw_files['html401-index']:
            raise ValueError('Dated HTML policy link differs from publication')
    if routing['svg11']['observed_policy_url'].encode() not in raw_files['svg11-index']:
        raise ValueError('SVG generic policy link differs from publication')
    return materials,routing if include_legacy_entities else {'svg11': routing['svg11']}


def reference_material(name):
    lock=json.loads(audit.bounded(REFERENCES/'sources.json',65536))['references'][name]
    path=Path(lock['file'])
    if path.name!=str(path):raise ValueError('Reference filename must be local')
    stored=audit.bounded(REFERENCES/path,1024**2)
    if hashlib.sha256(stored).hexdigest()!=lock['stored_sha256']:raise ValueError('Stored reference changed')
    if str(path).endswith('.gz'):
        with gzip.GzipFile(fileobj=io.BytesIO(stored)) as stream:raw=stream.read(1024**2+1)
    else:raw=stored
    if len(raw)!=lock['size'] or hashlib.sha256(raw).hexdigest()!=lock['sha256']:
        raise ValueError('Reference size/hash differs from pinned origin')
    return raw


def put(values,name,value):
    if name in values and values[name]!=value:raise ValueError('Conflicting reference alias: '+name)
    values[name]=value
    if len(values)>5000:raise ValueError('Excessive reference records')


def rgb(numbers):
    values=tuple(map(int,numbers))
    if any(v<0 or v>255 for v in values):raise ValueError('Color channel out of range')
    return values


def xorg_colors(data):
    values={}
    for line in data.decode('ascii').splitlines():
        if not line.strip() or line.startswith('!'):continue
        match=re.fullmatch(r'\s*(\d+)\s+(\d+)\s+(\d+)\s+([A-Za-z0-9 ]+)\s*',line)
        if not match:raise ValueError('Unrecognized X.Org color record')
        put(values,re.sub(r'\s+','',match[4]).lower(),rgb(match.groups()[:3]))
    if not values:raise ValueError('Empty X.Org reference')
    return values


class Text(HTMLParser):
    def __init__(self):super().__init__();self.chunks=[]
    def handle_data(self,data):self.chunks.append(data)


def svg_colors(data):
    parser=Text();parser.feed(data.decode('utf-8'));values={}
    for name,r,g,b in re.findall(r'\b([a-z]+)\s+rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',' '.join(parser.chunks)):
        put(values,name,rgb((r,g,b)))
    if not values:raise ValueError('Empty SVG reference')
    return values


def entities(data):
    values={}
    for name,value in re.findall(rb'&lt;!ENTITY\s+(\S+)\s+CDATA\s+"&amp;#(\d+);"\s+--',data):
        number=int(value)
        if number>0x10ffff:raise ValueError('Entity code point out of range')
        put(values,name.decode('ascii'),number)
    if not values:raise ValueError('Empty entity reference')
    return values


def entity_declaration_notice(data,expected_sha256):
    """Retain the SGML declaration notices, including ISO's stated conditions."""
    if len(data)>1024**2 or hashlib.sha256(data).hexdigest()!=expected_sha256:
        raise ValueError('Entity document differs from bound source bytes')
    source_lock=json.loads((HERE/'source-lock.json').read_text())
    replacement=builder.source_inputs.replacements(source_lock).get('graphviz-16.1.0/lib/common/entities.html')
    if replacement is not None and data == replacement:
        notice = data.split(b'-->\n', 1)[0].removeprefix(b'<!--\n') + b'\n'
        return ('ENTITY-DATA-LICENSES.txt', notice, dict(kind='reviewed-replacement-entity-notices',
            approved=False, path='lib/common/entities.html', source_sha256=expected_sha256,
            source_tree_sha256=source_lock['entity_replacement']['source_tree_sha256'],
            declaration_notices=0, license_route='WHATWG BSD-3-Clause; W3C software/document 2002',
            scope='Replacement data and compatibility changes; no whole-artifact approval'))
    reference=reference_material('html401-entities.html')
    def notices(raw):
        parser=Text();parser.feed(raw.decode('iso-8859-1'));parser.close()
        return [text for text in re.findall(r'<!--.*?-->', ''.join(parser.chunks),re.DOTALL)
                if re.search(r'copyright|permission|portions',text,re.IGNORECASE)]
    observed=notices(data);expected=notices(reference)
    if len(expected)!=3 or observed!=expected:
        raise ValueError('SGML declaration notices differ from pinned reference')
    source_lock=json.loads((HERE/'source-lock.json').read_text())
    reference_lock=json.loads(audit.bounded(REFERENCES/'sources.json',65536))['references']['html401-entities.html']
    raw=('Entity declaration notice review; conditions and applicability remain under review.\n'
         'Graphviz source: '+source_lock['url']+'\nPath: lib/common/entities.html\n'
         'Source SHA-256: '+expected_sha256+'\nReference: '+reference_lock['url']+'\n\n'+
         '\n\n'.join(observed)+'\n').encode('utf-8')
    return ('W3C-HTML401-ENTITY-DECLARATION-NOTICES.txt',raw,
        dict(kind='bound-entity-declaration-notices',approved=False,path='lib/common/entities.html',
            archive_sha256=source_lock['sha256'],source_sha256=expected_sha256,
            reference_url=reference_lock['url'],reference_sha256=reference_lock['sha256'],declaration_notices=3,
            scope='ISO attribution and conditions preserved; no claim about conformity, applicability or compatibility'))


def graphviz_colors(data):
    values={}
    for line in data.decode('ascii').splitlines():
        if not line.strip() or line.startswith('#'):continue
        fields=line.split()
        if len(fields)!=5:raise ValueError('Malformed Graphviz color')
        put(values,fields[0],rgb(fields[1:]))
    return values


def compare_xorg(graphviz,reference):
    differences={name:dict(graphviz=list(value),reference=list(reference[name]) if name in reference else None)
                 for name,value in graphviz.items() if value[:3]!=reference.get(name) or value[3]!=255}
    expected={name:dict(graphviz=[192,192,192,255],reference=[190,190,190]) for name in ('gray','grey')}
    expected.update({name:dict(graphviz=[255,255,254,0],reference=None) for name in ('invis','none','transparent')})
    if differences!=expected:raise ValueError('Unexpected Graphviz/X.Org data differences')
    return dict(matched=len(graphviz)-len(differences),differences=differences)


def collect(source_build,linked_build,source_archive,compiler_evidence):
    record=json.loads(audit.bounded(linked_build/'provenance.json',8*1024**2))
    evidence=json.loads(audit.bounded(compiler_evidence,8*1024**2))
    if (not record.get('completed') or evidence['executable_sha256']!=record['executable_sha256']
            or evidence['provenance_sha256']!=builder.digest(linked_build/'provenance.json')
            or builder.digest(linked_build/'candidate/bin/dot')!=record['executable_sha256']
            or record['relink']['parent_provenance_sha256']!=builder.digest(source_build/'provenance.json')):
        raise ValueError('Data audit requires exact completed build and compiler evidence')
    lock=json.loads((HERE/'source-lock.json').read_text())
    if record['source']!=lock:
        raise ValueError('Graphviz source archive changed')
    builder.source_inputs.verify(source_archive, lock)
    names=('make_colortbl.py','entities.py','brewer_colors','svgcolor_names','color_names','entities.html')
    inputs={};source_dir=source_build/'source/graphviz-16.1.0/lib/common'
    with tarfile.open(source_archive) as archive:
        for name in names:
            member=archive.getmember('graphviz-16.1.0/lib/common/'+name)
            if not member.isfile() or member.size>1024**2:raise ValueError('Invalid pinned data source')
            raw=builder.source_inputs.member_bytes(archive, member, lock)
            if raw!=audit.bounded(source_dir/name,1024**2):raise ValueError('Generator or data differs from pinned archive')
            inputs[name]=raw
    svg=graphviz_colors(inputs['svgcolor_names'])
    expected_svg=svg_colors(reference_material('svg11-types.html'))
    if len(svg)!=147 or {k.removeprefix('/svg/'):v for k,v in svg.items()}!={k:(*v,255) for k,v in expected_svg.items()}:
        raise ValueError('SVG reference values differ')
    actual_entities=entities(inputs['entities.html'])
    reference_entities=(builder.source_inputs.replacements(lock)['graphviz-16.1.0/lib/common/entities.html']
                        if 'entity_replacement' in lock else reference_material('html401-entities.html'))
    if len(actual_entities)!=252 or actual_entities!=entities(reference_entities):
        raise ValueError('HTML entity values differ')
    xorg=compare_xorg(graphviz_colors(inputs['color_names']),xorg_colors(reference_material('xorg-rgb-1.1.0-rgb.txt')))
    generated={item['path']:item for item in evidence['dependencies'].values() if item['origin']=='generated-build'}
    outputs=[]
    with tempfile.TemporaryDirectory(prefix='graphviz-data-rebuild-') as folder:
        work=Path(folder)
        for generator,target,arguments in (
                ('make_colortbl.py','lib/common/common/colortbl.h',[source_dir/n for n in ('brewer_colors','svgcolor_names','color_names')]),
                ('entities.py','lib/common/common/entities.h',[])):
            output=work/Path(target).name
            result=builder.run_bounded([sys.executable,'-I','-B',str(source_dir/generator),*map(str,arguments),str(output)],
                cwd=work,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'},timeout=10,max_output=1024**2)
            if result.returncode:raise ValueError('Pinned table generator failed')
            raw=audit.bounded(source_build/'build'/target,8*1024**2)
            sha=hashlib.sha256(raw).hexdigest()
            if sha!=generated[target]['sha256'] or raw!=audit.bounded(output,8*1024**2):
                raise ValueError('Rebuilt data table differs from compiled input')
            outputs.append(dict(path=target,sha256=sha,size=len(raw),generator=generator,reproduced=True))
    references=json.loads(audit.bounded(REFERENCES/'sources.json',65536))
    return dict(kind='graphviz-generated-data-evidence-not-license-approval',approved=False,qualified=False,
        executable_sha256=record['executable_sha256'],provenance_sha256=builder.digest(linked_build/'provenance.json'),
        compiler_evidence_sha256=builder.digest(compiler_evidence),source=lock,
        inputs=[dict(path='lib/common/'+name,size=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for name,raw in inputs.items()],
        outputs=outputs,references=references,
        comparison=dict(svg_colors_matched=147,html_entities_matched=252,xorg=xorg),
        historical_copying_proven=False,
        limits=dict(generator_seconds=10,generator_output_bytes=1024**2,reference_bytes=1024**2),
        pending=['Reference value equality does not establish the historical copying chain or decide license applicability',
                 'Corresponding-source offer, per-file SDK notices and complete reviewed audit remain pending'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-build','linked-build','source-archive','compiler-evidence','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise ValueError('Data report must be new')
    report=collect(args.source_build.resolve(),args.linked_build.resolve(),args.source_archive.resolve(),args.compiler_evidence.resolve())
    with args.report.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report['comparison']))
