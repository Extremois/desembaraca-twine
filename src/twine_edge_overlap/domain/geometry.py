from .arcs import counts
from .model import Metrics

def measure(document,deadline=float('inf')):
    return Metrics(*counts(document.graph(),deadline))
