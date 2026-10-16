"""Lossless parser for the explicit static Twee profile; never executes story code."""
import json
import re
import time
from dataclasses import replace
from ..domain.model import Document,Node,MAX_BYTES,MAX_NODES,MAX_EDGES
from ..errors import FormatError,IntegrityError,BudgetError

HEADER=re.compile(rb'^(?:\xef\xbb\xbf)?::[ \t]+([^\r\n]*)\r?$',re.M)
LABEL=re.compile(rb'(?P<name>[^{}\[\]\\]+?)(?:[ \t]+\[(?P<tags>[^\[\]\\]*)\])?(?:[ \t]+(?P<meta>\{.*\}))?[ \t]*$')


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise FormatError('Chave JSON duplicada; exporte novamente pelo Twine')
        result[key]=value
    return result


def reject_constant(value):
    raise FormatError('JSON contém NaN ou infinito; esses valores não são aceitos pelo Twine')


def position_span(raw):
    """Locate the top-level JSON position value without confusing nested metadata."""
    text=raw.decode('utf-8')
    decoder=json.JSONDecoder()
    i=1
    while True:
        while text[i].isspace() or text[i]==',': i+=1
        if text[i]=='}': break
        key,end=decoder.raw_decode(text,i)
        i=end
        while text[i].isspace(): i+=1
        i+=1  # colon; syntax already checked by strict JSON parsing
        while text[i].isspace(): i+=1
        value,end=decoder.raw_decode(text,i)
        if key=='position':
            if not isinstance(value,str): raise FormatError('position deve ser uma string x,y')
            return len(text[:i+1].encode('utf-8')),len(text[:end-1].encode('utf-8'))
        i=end
    raise FormatError('Metadado position ausente')


def initialize_layout(data,headers,deadline):
    """Supply Twine importer defaults, editing only visual header metadata."""
    passages=[]
    for h in headers:
        if time.monotonic()>=deadline: raise BudgetError('Prazo global esgotado durante a leitura do perfil')
        if len(h.group(1))>8192: raise FormatError('Cabeçalho excede o limite de 8 KiB do perfil')
        m=LABEL.fullmatch(h.group(1))
        if m is None: raise FormatError('Cabeçalho fora do perfil: nomes escapados não são suportados')
        name=m.group('name').strip().decode('utf-8')
        tags=set((m.group('tags') or b'').decode('utf-8').split())
        if name in ('StoryTitle','StoryData') or tags & {'script','stylesheet'}: continue
        raw=m.group('meta')
        meta={} if raw is None else json.loads(raw,object_pairs_hook=unique_object,parse_constant=reject_constant)
        x,y=map(float,meta.get('position','0,0').split(','))
        w,ht=map(float,meta.get('size','100,100').split(','))
        Node(name,x,y,w,ht)  # Explicit invalid values must never be replaced by defaults.
        passages.append((h,m,raw,meta,x,y))
        if len(passages)>MAX_NODES: raise FormatError('Limite do perfil: até 100 nós e 300 ocorrências de links')
    grid=bool(passages) and all(x==0 and y==0 for _,_,_,_,x,y in passages)
    patches=[]
    for index,(h,m,raw,meta,x,y) in enumerate(passages):
        position=f'{25+125*(index%10)},{25+125*(index//10)}' if grid else '0,0'
        additions={}
        if 'position' not in meta: additions['position']=position
        if 'size' not in meta: additions['size']='100,100'
        if raw is None:
            patches.append((h.end(1),h.end(1),b' '+json.dumps(additions).encode('ascii')))
        else:
            base=h.start(1)+m.start('meta')
            if grid and 'position' in meta:
                lo,hi=position_span(raw)
                patches.append((base+lo,base+hi,position.encode('ascii')))
            if additions:
                extra=json.dumps(additions).encode('ascii')[1:-1]
                patches.append((base+len(raw)-1,base+len(raw)-1,(b',' if meta else b'')+extra))
    for lo,hi,value in sorted(patches,reverse=True): data=data[:lo]+value+data[hi:]
    return data,bool(patches)


def link_target(content):
    """Interpret static Twee destinations without executing optional setters."""
    content=content.split('][',1)[0]
    if '->' in content: target=content.rsplit('->',1)[1]
    elif '<-' in content: target=content.split('<-',1)[0]
    elif '|' in content: target=content.rsplit('|',1)[1]
    else: target=content
    if not target or '[' in target or ']' in target:
        raise FormatError('Destino de link vazio ou delimitadores não suportados')
    return target


def parse(data,deadline=float('inf')):
    if time.monotonic()>=deadline:
        raise BudgetError('Prazo global esgotado durante a leitura do perfil')
    if len(data)>MAX_BYTES: raise FormatError('Arquivo excede o limite de 10 MiB')
    try:
        data.decode('utf-8-sig',errors='strict')
        headers=list(HEADER.finditer(data))
        if not headers or data[:headers[0].start()].replace(b'\xef\xbb\xbf',b'',1).strip():
            raise FormatError('Esperada fonte Twee UTF-8 com cabeçalhos ::')
        # Every unescaped header must be recognized; malformed headers cannot hide in a body.
        if len(re.findall(rb'^(?:\xef\xbb\xbf)?::',data,re.M))!=len(headers): raise FormatError('Cabeçalho Twee incompleto')
        initialized,changed=initialize_layout(data,headers,deadline)
        if changed: return replace(parse(initialized,deadline),layout_initialized=True)
        nodes,edges,spans=[],[],[]
        names=set(); specials={}; opaque=False
        for index,h in enumerate(headers):
            if time.monotonic()>=deadline:
                raise BudgetError('Prazo global esgotado durante a leitura do perfil')
            if len(h.group(1))>8192:
                raise FormatError('Cabeçalho excede o limite de 8 KiB do perfil')
            if h.start()>0 and data[h.start():].startswith(b'\xef\xbb\xbf'):
                raise FormatError('BOM permitido somente no início do arquivo')
            m=LABEL.fullmatch(h.group(1))
            if m is None: raise FormatError('Cabeçalho fora do perfil: nomes escapados não são suportados')
            name=m.group('name').strip().decode('utf-8')
            if not name or name in names: raise FormatError('Nome de passagem vazio ou duplicado')
            names.add(name)
            end=headers[index+1].start() if index+1<len(headers) else len(data)
            body=data[h.end():end].decode('utf-8')
            tags=set((m.group('tags') or b'').decode('utf-8').split())
            if name in ('StoryTitle','StoryData'):
                if tags or m.group('meta'): raise FormatError('Passagem especial com cabeçalho incompatível')
                specials[name]=body
                continue
            if 'script' in tags and 'stylesheet' in tags: raise FormatError('Tags script e stylesheet simultâneas não suportadas')
            if tags & {'script','stylesheet'}:
                opaque=True
                continue
            raw=m.group('meta')
            if raw is None: raise FormatError('Posição/tamanho ausentes; exporte a história com metadados de layout')
            meta=json.loads(raw,object_pairs_hook=unique_object,parse_constant=reject_constant)
            x,y=map(float,meta['position'].split(','))
            w,ht=map(float,meta['size'].split(','))
            nodes.append(Node(name,x,y,w,ht))
            lo,hi=position_span(raw)
            base=h.start(1)+m.start('meta')
            spans.append((base+lo,base+hi))
            if body.count('[[')!=body.count(']]'):
                raise FormatError('Link incompleto ou delimitadores não suportados')
            links=list(re.finditer(r'\[\[(.*?)\]\]',body))
            if body.count('[[')!=len(links): raise FormatError('Link incompleto ou multilinha fora do perfil')
            if re.search(r'\((?:goto|link-goto|display|include)\s*:|<<',body,re.I):
                raise FormatError('Navegação por macros não suportada pelo perfil estático')
            opaque |= bool(re.search(r'\([\w-]+\s*:|<script\b',body,re.I))
            for link in links:
                target=link_target(link.group(1))
                if re.match(r'\w+://',target): continue
                edges.append((name,target))
            if len(nodes)>MAX_NODES or len(edges)>MAX_EDGES:
                raise FormatError('Limite do perfil: até 100 nós e 300 ocorrências de links')
        if 'StoryTitle' in specials and not specials['StoryTitle'].strip():
            raise FormatError('StoryTitle deve conter um título')
        story=json.loads(specials['StoryData'],object_pairs_hook=unique_object,parse_constant=reject_constant) if 'StoryData' in specials else {}
        if not isinstance(story,dict): raise FormatError('StoryData deve ser um objeto JSON')
        ids={n.id for n in nodes}
        missing=sorted({b for a,b in edges if b not in ids})
        if missing:
            raise FormatError('Links apontam para passagens inexistentes ou não narrativas: '+', '.join(missing))
        if 'start' in story and story['start'] not in ids: raise FormatError('Passagem inicial de StoryData não existe')
        return Document(data,tuple(nodes),tuple(edges),tuple(spans),opaque)
    except (UnicodeError,ValueError,KeyError,TypeError,AttributeError,IndexError,RecursionError) as exc:
        if isinstance(exc,FormatError): raise
        raise FormatError('UTF-8, JSON, coordenadas ou dimensões inválidas no perfil Twee') from exc


def neutralize(document):
    result=[]; previous=0
    for lo,hi in document.spans:
        result.extend((document.raw[previous:lo],b'<position>')); previous=hi
    result.append(document.raw[previous:])
    return b''.join(result)


def verify(original,candidate):
    if neutralize(original)!=neutralize(candidate) or original.edges!=candidate.edges or tuple((n.id,n.w,n.h) for n in original.nodes)!=tuple((n.id,n.w,n.h) for n in candidate.nodes):
        raise IntegrityError('Conteúdo, metadados ou conexões alterados fora das posições')


def serialize(document,positions):
    if set(positions)!={n.id for n in document.nodes}: raise IntegrityError('Identidades diferentes no layout candidato')
    result=document.raw
    for n,(lo,hi) in reversed(list(zip(document.nodes,document.spans))):
        x,y=positions[n.id]
        Node(n.id,x,y,n.w,n.h)
        if (x,y)!=(n.x,n.y):
            result=result[:lo]+f'{x:.6f},{y:.6f}'.encode('ascii')+result[hi:]
    verify(document,parse(result))
    return result
