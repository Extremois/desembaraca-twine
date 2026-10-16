"""Immutable semantic and visual models; no filesystem access."""
from dataclasses import dataclass
import math
from pathlib import Path

MAX_BYTES=10*1024*1024
MAX_NODES=100
MAX_EDGES=300
GLOBAL_SECONDS=60


@dataclass(frozen=True)
class Node:
    id: str
    x: float
    y: float
    w: float
    h: float

    def __post_init__(self):
        if not self.id or not all(math.isfinite(v) for v in (self.x,self.y,self.w,self.h)):
            raise ValueError('Identidade vazia ou coordenadas não finitas')
        if max(abs(self.x),abs(self.y))>1e7 or not (.001<=self.w<=1e6 and .001<=self.h<=1e6):
            raise ValueError('Coordenadas ou dimensões fora dos limites do perfil')


@dataclass(frozen=True)
class Document:
    raw: bytes
    nodes: tuple[Node,...]
    edges: tuple[tuple[str,str],...]
    spans: tuple[tuple[int,int],...]
    opaque: bool=False
    layout_initialized: bool=False

    def __post_init__(self):
        identities={node.id for node in self.nodes}
        if len(identities)!=len(self.nodes) or len(self.nodes)>MAX_NODES or len(self.edges)>MAX_EDGES:
            raise ValueError('Identidades duplicadas ou grafo excede os limites')
        if any(a not in identities or b not in identities for a,b in self.edges):
            raise ValueError('Relação com identidade ausente')
        if not isinstance(self.raw,bytes) or len(self.raw)>MAX_BYTES or len(self.spans)!=len(self.nodes):
            raise ValueError('Snapshot ou intervalos incompatíveis com os nós')
        previous=0
        for lo,hi in self.spans:
            if not (previous<=lo<hi<=len(self.raw)):
                raise ValueError('Intervalo de posição inválido ou sobreposto')
            previous=hi

    def graph(self):
        return {'nodes':[vars(n).copy() for n in self.nodes],'edges':list(self.edges)}


@dataclass(frozen=True)
class Metrics:
    edges: int
    nodes: int
    traversals: int

    def __post_init__(self):
        if any(type(v) is not int or v<0 for v in self.values):
            raise ValueError('Contagens devem ser inteiros não negativos')

    @property
    def values(self): return (self.edges,self.nodes,self.traversals)

    @property
    def clean(self): return self.values==(0,0,0)


@dataclass(frozen=True)
class Result:
    status: str
    path: Path|None
    before: Metrics|None
    after: Metrics|None
    reason: str

    def __post_init__(self):
        if self.status not in ('sucesso','limitações','falha'):
            raise ValueError('Estado desconhecido')
        if self.status=='falha':
            if self.path is not None: raise ValueError('Falha não pode anunciar arquivo válido')
        elif self.path is None or self.before is None or self.after is None:
            raise ValueError('Resultado válido exige arquivo e contagens')
