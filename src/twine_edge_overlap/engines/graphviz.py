"""Geometry-only Graphviz interface; story text never reaches DOT or a shell."""
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
import time
from .process import run_bounded,ProcessLimitError
from ..domain.model import Node
from ..errors import DependencyError,EngineError,BudgetError


def locate():
    explicit=os.environ.get('TWINE_GRAPHVIZ_DOT')
    if explicit:
        if Path(explicit).is_file(): return explicit
        raise DependencyError('TWINE_GRAPHVIZ_DOT não aponta para um executável existente')
    found=shutil.which('dot')
    if found: return found
    if os.name=='nt':
        for root in (os.environ.get('ProgramFiles',r'C:\Program Files'),os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)')):
            path=Path(root)/'Graphviz/bin/dot.exe'
            if path.is_file(): return str(path)
    raise DependencyError('Graphviz dot não encontrado; instale Graphviz ou defina TWINE_GRAPHVIZ_DOT')


def build_dot(document):
    ids={n.id:f'n{i}' for i,n in enumerate(document.nodes)}
    lines=['digraph G {','graph [rankdir=TB,nodesep=0.7,ranksep=1,splines=line];',
           'node [shape=box,fixedsize=true,label=""];']
    for n in document.nodes:
        lines.append(f'{ids[n.id]} [width={n.w/72:.12g},height={n.h/72:.12g}];')
    lines.extend(f'{ids[a]} -> {ids[b]};' for a,b in document.edges)
    return '\n'.join([*lines,'}'])


def decode_layout(data,document):
    try:
        graph=json.loads(data)
        bb=list(map(float,graph['bb'].split(',')))
        if len(bb)!=4 or not all(math.isfinite(v) and abs(v)<=1e7 for v in bb) or bb[2]<bb[0] or bb[3]<bb[1]:
            raise ValueError('bounding box')
        items=graph.get('objects',[])
        if len(items)!=len(document.nodes): raise ValueError('node count')
        objects={obj['name']:obj for obj in items}
        if len(objects)!=len(items) or set(objects)!={f'n{i}' for i in range(len(document.nodes))}: raise ValueError('identities')
        positions={}
        for i,n in enumerate(document.nodes):
            x,y=map(float,objects[f'n{i}']['pos'].split(','))
            node=Node(n.id,round(x-n.w/2,6),round(bb[3]-y-n.h/2,6),n.w,n.h)
            positions[n.id]=(node.x,node.y)
        return positions
    except (ValueError,KeyError,TypeError,AttributeError,RecursionError) as exc:
        raise EngineError('Saída JSON/IDs/coordenadas inválidos de Graphviz') from exc


def layout(document,deadline):
    executable=locate()
    if not document.nodes: return {}
    remaining=min(30,deadline-time.monotonic())
    if remaining<=0: raise BudgetError('Prazo global esgotado antes do motor')
    try:
        with tempfile.TemporaryDirectory(prefix='twine-graphviz-') as folder:
            source=Path(folder)/'graph.dot'
            source.write_text(build_dot(document),encoding='ascii')
            result=run_bounded([executable,'-Tjson0',str(source)],timeout=remaining)
        if result.returncode: raise EngineError('Graphviz falhou; confira instalação completa e plugins json0')
        return decode_layout(result.stdout,document)
    except ProcessLimitError as exc: raise BudgetError('Motor excedeu o limite de tempo ou de 8 MiB de saída') from exc
    except OSError as exc: raise EngineError('Não foi possível executar Graphviz ou seus temporários') from exc
