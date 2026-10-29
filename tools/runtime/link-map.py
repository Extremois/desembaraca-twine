"""Bind LLD allocated input-section observations to an ELF and hashed link inputs.

This records retained allocations, not complete source-to-instruction provenance
or license approval. Debug sections and DWARF imports do not count as allocations.
"""
import hashlib
from pathlib import Path, PurePosixPath
import re
import struct

MAX_BYTES=8*1024**2


def bounded(path,limit):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Expected regular link-map input')
    with path.open('rb') as stream:raw=stream.read(limit+1)
    if len(raw)>limit:raise ValueError('Link-map input exceeds bound')
    return raw


def allocated_sections(raw):
    if (len(raw)<64 or raw[:7]!=b'\x7fELF\x02\x01\x01'
            or struct.unpack_from('<H',raw,18)[0] not in (62,183)):
        raise ValueError('Expected bounded native Linux ELF64 little-endian metadata')
    header=struct.unpack_from('<HHIQQQIHHHHHH',raw,16)
    offset,entry_size,count,strings=header[5],header[10],header[11],header[12]
    if (header[0] not in (2,3) or header[2]!=1 or header[7]!=64 or entry_size!=64
            or not 0<count<=4096 or not 0<strings<count or offset<64 or offset+count*64>len(raw)):
        raise ValueError('Invalid ELF section table')
    sections=[struct.unpack_from('<IIQQQQIIQQ',raw,offset+index*64) for index in range(count)]
    for section in sections:
        if section[1]!=8 and section[4]+section[5]>len(raw):raise ValueError('ELF section outside file')
    table=sections[strings]
    if table[1]!=3 or table[5]>1024**2:raise ValueError('Invalid ELF section names')
    names=raw[table[4]:table[4]+table[5]];result={}
    for section in sections:
        start=section[0];end=names.find(b'\0',start)
        if start>=len(names) or end<start or end-start>4096:raise ValueError('Invalid ELF section name')
        name=names[start:end].decode('utf-8',errors='strict')
        if section[2]&2 and section[5]:
            if not name or name in result or section[3]+section[5]>2**64:raise ValueError('Ambiguous ELF allocation')
            result[name]=dict(address=section[3],bytes=section[5],executable=bool(section[2]&4))
    if not result:raise ValueError('No allocated ELF sections')
    return result


def capture(path,binary,linkage,build_root):
    payload=bounded(path,MAX_BYTES);elf=bounded(binary,64*1024**2)
    digest=lambda raw:hashlib.sha256(raw).hexdigest()
    if digest(elf)!=linkage['executable_sha256']:raise ValueError('Mapped ELF differs from link provenance')
    allocations=allocated_sections(elf)
    inputs={}
    for item in linkage['inputs']:
        name=str(PurePosixPath(build_root)/item['path']) if item['scope']=='build' else item['path']
        if name in inputs or not re.fullmatch('[0-9a-f]{64}',item['sha256']):raise ValueError('Ambiguous hashed link input')
        inputs[name]=item
    extracted={(row['archive_sha256'],row['member']) for row in linkage['archive_extractions']['rows']}
    lines=payload.decode('utf-8',errors='strict').splitlines()
    if not lines or lines[0].split()!=['VMA','LMA','Size','Align','Out','In','Symbol'] or len(lines)>100001:
        raise ValueError('Invalid or excessive LLD map')
    rows=[];seen=set();parent=None;internal=0
    for line in lines[1:]:
        match=re.fullmatch(r'\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+) (.*)',line)
        if not match or len(line)>16384 or '\0' in line:raise ValueError('Malformed LLD map row')
        address,load,size=(int(match[i],16) for i in (1,2,3))
        if max(address,load,size)>=2**64 or address+size>2**64:raise ValueError('LLD address exceeds ELF64')
        tail=match[5];indent=len(tail)-len(tail.lstrip());name=tail.strip()
        if indent==0:
            parent=None
            if name in allocations:
                actual=allocations[name]
                if name in seen or (address,size)!=(actual['address'],actual['bytes']):
                    raise ValueError('LLD output allocation differs from ELF')
                seen.add(name);parent=name
            continue
        if indent not in (8,16):raise ValueError('Unsupported LLD map row level')
        if parent is None:
            if indent==8 and size and any(section['address']<=address< section['address']+section['bytes']
                                         for section in allocations.values()):
                raise ValueError('Allocated input lacks its mapped ELF output')
            continue
        if indent==16:continue  # Symbol labels are not input-section contributions.
        actual=allocations[parent]
        if not actual['address']<=address<=address+size<=actual['address']+actual['bytes']:
            raise ValueError('Input section outside ELF output allocation')
        source=re.fullmatch(r'(.+):\(([^()\0]+)\)',name)
        if not source:raise ValueError('Unsupported LLD input section')
        if source[1]=='<internal>':internal+=1;continue
        input_name=source[1];member=None
        if input_name.endswith(')'):
            input_name,separator,member=input_name.rpartition('(')
            if not separator or not member[:-1]:raise ValueError('Invalid mapped archive member')
            member=member[:-1]
        if input_name not in inputs:raise ValueError('Mapped section lacks a hashed link input')
        item=inputs[input_name]
        if member is not None and (item['sha256'],member) not in extracted:
            raise ValueError('Mapped archive member lacks extraction evidence')
        if size:
            rows.append(dict(input_sha256=item['sha256'],input_path=item['path'],scope=item['scope'],
                member=member,input_section=source[2],output_section=parent,address=address,bytes=size,
                executable=actual['executable']))
    if seen!=set(allocations) or not rows:raise ValueError('Incomplete allocated-section map')
    return dict(kind='lld-allocated-input-sections-not-source-closure',approved=False,qualified=False,
        executable_sha256=digest(elf),map_sha256=digest(payload),map_bytes=len(payload),
        allocated_output_sections=len(seen),internal_rows=internal,sections=rows,
        limitations=['Linker allocations only; debug imports and symbol labels are excluded',
            'Not an exhaustive source-to-instruction audit, license decision or platform qualification'])
