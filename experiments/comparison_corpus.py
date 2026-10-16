"""Synthetic, narrative-free cases fixed before the first motor comparison."""
from __future__ import annotations
import json
from validate_twee_sample import HEADER, NARRATIVE, inspect


def graph(points, edges):
    return {'nodes':[{'id':str(i),'x':x,'y':y,'w':100,'h':100}
                     for i,(x,y) in enumerate(points)],
            'edges':[(str(a),str(b)) for a,b in edges]}


def cases():
    return {
        'crossing':graph([(0,0),(300,0),(0,300),(300,300)],[(0,3),(1,2)]),
        'coincident':graph([(0,0),(0,200),(0,400),(0,600)],[(0,3),(1,2)]),
        'clean':graph([(0,0),(0,200)],[(0,1)]),
        'isolated_overlap':graph([(0,0),(50,50)],[]),
        'connected_overlap':graph([(0,0),(50,50),(0,300)],[(0,2),(1,2)]),
        'through_isolated':graph([(0,0),(0,400),(0,200)],[(0,1)]),
        'through_connected':graph([(0,0),(0,400),(0,200),(300,200)],[(0,1),(2,3)]),
        'border_only':graph([(0,0),(0,400),(50,200)],[(0,1)]),
        'cycle':graph([(0,0),(300,0),(150,300)],[(0,1),(1,2),(2,0)]),
        'parallel_occurrences':graph([(0,0),(0,300)],[(0,1),(0,1)]),
        'self_loop':graph([(0,0)],[(0,0)]),
        'reciprocal':graph([(0,0),(0,300)],[(0,1),(1,0)]),
    }


def from_sample(data):
    inspect(data)  # reject unsupported experimental input before extracting
    headers = list(HEADER.finditer(data))
    nodes, edges, names = [], [], {}
    import re
    for i,h in enumerate(headers):
        match = NARRATIVE.fullmatch(h.group(1))
        if match:
            names[match.group('name').decode('utf-8')] = str(len(names))
    for i,h in enumerate(headers):
        match = NARRATIVE.fullmatch(h.group(1))
        if not match:
            continue
        name = match.group('name').decode('utf-8')
        meta = json.loads(match.group('meta'))
        x,y = map(float,meta['position'].split(','))
        w,ht = map(float,meta['size'].split(','))
        nodes.append({'id':names[name],'x':x,'y':y,'w':w,'h':ht})
        end = headers[i+1].start() if i+1<len(headers) else len(data)
        for target in re.findall(rb'\[\[([^\]\r\n]+)\]\]',data[h.end():end]):
            edges.append((names[name],names[target.decode('utf-8')]))
    return {'nodes':nodes,'edges':edges}


def curved_cases():
    result=cases()
    result['coincident']=graph([(0,0),(300,0),(0,0),(300,0)],[(0,1),(2,3)])
    # Rectangle above an arc, touching only its topmost point.
    result['border_only']=graph([(0,0),(500,0),(295,0)],[(0,1)])
    result['border_only']['nodes'][2].update(w=10,h=10,y=50-300*(1-3**.5/2)-10)
    return result
