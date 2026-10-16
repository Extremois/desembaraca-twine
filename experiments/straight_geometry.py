"""Independent experimental model: rectangle-clipped straight connections.

This is a hypothesis to verify against the user's editor, not a Twine renderer.
Arrowheads, stroke width, loops and reciprocal-connection offsets are not modeled.
"""
from __future__ import annotations

import itertools
import time

EPS = 1e-7


def check(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError('Experimental geometry deadline exceeded')


def center(n):
    return (n['x'] + n['w'] / 2, n['y'] + n['h'] / 2)


def segment(a, b):
    p, q = center(a), center(b)
    dx, dy = q[0] - p[0], q[1] - p[1]
    if abs(dx) + abs(dy) < EPS:
        return p, q
    def extent(n):
        return min(n['w'] / (2 * abs(dx)) if dx else float('inf'),
                   n['h'] / (2 * abs(dy)) if dy else float('inf'))
    ta, tb = extent(a), extent(b)
    if ta + tb >= 1:
        return p, q  # overlapping endpoints are measured separately as nodes
    return ((p[0] + ta * dx, p[1] + ta * dy),
            (q[0] - tb * dx, q[1] - tb * dy))


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def sub(a, b):
    return a[0] - b[0], a[1] - b[1]


def intersection(first, second):
    """Return none, a contact point, or a positive-length collinear overlap."""
    a, b = first
    c, d = second
    r, s, ca = sub(b, a), sub(d, c), sub(c, a)
    den = cross(r, s)
    if abs(den) > EPS:
        t, u = cross(ca, s) / den, cross(ca, r) / den
        if -EPS <= t <= 1 + EPS and -EPS <= u <= 1 + EPS:
            return ('point', (a[0] + t * r[0], a[1] + t * r[1]))
        return None
    if abs(cross(ca, r)) > EPS:
        return None
    rr = r[0] ** 2 + r[1] ** 2
    if rr < EPS ** 2:
        return None
    t = (ca[0] * r[0] + ca[1] * r[1]) / rr
    da = sub(d, a)
    u = (da[0] * r[0] + da[1] * r[1]) / rr
    lo, hi = max(0, min(t, u)), min(1, max(t, u))
    if hi < lo - EPS:
        return None
    if hi - lo > EPS:
        return ('overlap', None)
    return ('point', (a[0] + lo * r[0], a[1] + lo * r[1]))


def interior(line, n):
    a, b = line
    lo, hi = 0., 1.
    for dim, start, size in ((0, n['x'], n['w']), (1, n['y'], n['h'])):
        delta = b[dim] - a[dim]
        if abs(delta) < EPS:
            if not start + EPS < a[dim] < start + size - EPS:
                return False
        else:
            t, u = (start + EPS - a[dim]) / delta, (start + size - EPS - a[dim]) / delta
            lo, hi = max(lo, min(t, u)), min(hi, max(t, u))
    return hi > lo + EPS


def counts(graph, deadline=float('inf')):
    nodes = {n['id']: n for n in graph['nodes']}
    edges = list(dict.fromkeys(tuple(e) for e in graph['edges']))
    if any(a == b for a, b in edges):
        raise ValueError('Self-loop geometry is not characterized')
    if any((b, a) in edges for a, b in edges):
        raise ValueError('Reciprocal-connection geometry is not characterized')
    lines = [segment(nodes[a], nodes[b]) for a, b in edges]
    ee = nn = en = 0
    for a, b in itertools.combinations(nodes.values(), 2):
        check(deadline)
        nn += (min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > EPS
               and min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > EPS)
    for i, j in itertools.combinations(range(len(edges)), 2):
        check(deadline)
        hit = intersection(lines[i], lines[j])
        if hit:
            shared = set(edges[i]) & set(edges[j])
            normal = (hit[0] == 'point' and any(
                nodes[n]['x'] - EPS <= hit[1][0] <= nodes[n]['x'] + nodes[n]['w'] + EPS
                and nodes[n]['y'] - EPS <= hit[1][1] <= nodes[n]['y'] + nodes[n]['h'] + EPS
                for n in shared))
            ee += not normal
    for edge, line in zip(edges, lines):
        for name, n in nodes.items():
            check(deadline)
            if name not in edge:
                en += interior(line, n)
    return [ee, nn, en]
