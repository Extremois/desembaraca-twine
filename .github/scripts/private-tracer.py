"""Prepare pinned Debian tracing tools in the test user's private input tree."""
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[2]


def unpack_deb(raw,selected):
    if len(raw)>4*1024**2 or not raw.startswith(b'!<arch>\n'):
        raise ValueError('Invalid or excessive Debian tool archive')
    if any(not re.fullmatch(r'[a-zA-Z0-9_.-]+',name) for name in selected.values()):
        raise ValueError('Private tracer output must be a basename')
    position=8;payload=None;names=set()
    while position<len(raw):
        header=raw[position:position+60]
        if len(header)!=60 or header[58:60]!=b'`\n':raise ValueError('Invalid Debian ar header')
        name=header[:16].decode('ascii').strip().rstrip('/')
        try:size=int(header[48:58])
        except ValueError:raise ValueError('Invalid Debian ar size') from None
        position+=60
        if name in names or len(names)>=10 or size<0 or position+size>len(raw):raise ValueError('Ambiguous or truncated Debian archive')
        names.add(name)
        if name=='debian-binary' and raw[position:position+size]!=b'2.0\n':raise ValueError('Unknown Debian archive version')
        if name in ('data.tar.xz','data.tar.gz'):
            if payload is not None:raise ValueError('Duplicate Debian payload')
            payload=raw[position:position+size]
        position+=size+size%2
    if payload is None or 'debian-binary' not in names:raise ValueError('Missing Debian archive payload/version')
    result={};seen=set();total=0
    with tarfile.open(fileobj=io.BytesIO(payload),mode='r:*') as archive:
        for member in archive:
            path=PurePosixPath(member.name)
            total+=member.size
            if (path.is_absolute() or '..' in path.parts or '\\' in member.name or member.name in seen
                    or len(seen)>=1000 or member.size<0 or total>32*1024**2):
                raise ValueError('Unsafe or excessive Debian payload')
            seen.add(member.name)
            if member.name not in selected:continue
            if not member.isfile() or member.mode & 0o6000:raise ValueError('Tracer input must be a regular unprivileged ELF')
            content=archive.extractfile(member).read(4*1024**2+1)
            if (len(content)>4*1024**2 or len(content)<64 or content[:6]!=b'\x7fELF\x02\x01'
                    or struct.unpack_from('<H',content,18)[0]!=62):raise ValueError('Expected x86_64 ELF tracer/library')
            destination=selected[member.name]
            if destination in result:raise ValueError('Duplicate private tool destination')
            result[destination]=content
    if set(result)!=set(selected.values()):raise ValueError('Missing reviewed tracer files')
    return result


def prepare(work,packages=None):
    pin_path=ROOT/'.github/native-images/private-tracer-debian-x64.json'
    pin_raw=pin_path.read_bytes();pins=json.loads(pin_raw)
    payloads={};receipts=[]
    for pin in pins['packages']:
        if packages is None:
            if not pin['url'].startswith('https://deb.debian.org/debian/pool/main/'):
                raise ValueError('Unexpected private tracer origin')
            with urllib.request.urlopen(pin['url'],timeout=30) as response:
                if response.url!=pin['url']:raise ValueError('Private tracer origin redirected')
                raw=response.read(4*1024**2+1)
        else:raw=(packages/pin['name']).read_bytes()
        if len(raw)!=pin['size'] or hashlib.sha256(raw).hexdigest()!=pin['sha256']:
            raise ValueError('Private tracer package changed')
        selected=unpack_deb(raw,pin['selected'])
        if set(payloads)&set(selected):raise ValueError('Duplicate tracer package destination')
        payloads.update(selected);receipts.append({k:pin[k] for k in ('url','name','size','sha256')})
    folder=work/'input/private-tracer';folder.mkdir(exist_ok=False)
    rows=[]
    for name,raw in sorted(payloads.items()):
        path=folder/name
        with path.open('xb') as stream:stream.write(raw)
        path.chmod(0o755)
        rows.append(dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),size=len(raw)))
    report=dict(version=pins['version'],files=rows,packages=receipts,pin_sha256=hashlib.sha256(pin_raw).hexdigest())
    content=(json.dumps(report,indent=2)+'\n').encode()
    (work/'input/tracer.json').write_bytes(content)
    (work/'evidence/private-tracer.json').write_bytes(content)
