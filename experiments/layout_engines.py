"""Standalone T006 adapters. No production package is imported."""
from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import time

from process_budget import run_bounded

DOT_OPTIONS = {'rankdir': 'TB', 'nodesep': '0.7', 'ranksep': '1', 'splines': 'line'}
ELK_OPTIONS = {'elk.algorithm': 'layered', 'elk.direction': 'DOWN',
               'elk.edgeRouting': 'POLYLINE', 'elk.spacing.nodeNode': '50',
               'elk.layered.spacing.nodeNodeBetweenLayers': '72', 'elk.randomSeed': '1'}


def validate_positions(graph, positions):
    if set(positions) != {n['id'] for n in graph['nodes']}:
        raise ValueError('Engine returned different node identities')
    for pair in positions.values():
        if len(pair) != 2 or not all(isinstance(v,(float,int)) and math.isfinite(v) and abs(v)<=1e7 for v in pair):
            raise ValueError('Engine returned invalid or excessive coordinates')
    return {'nodes':[dict(n,x=round(positions[n['id']][0],6),y=round(positions[n['id']][1],6))
                     for n in graph['nodes']], 'edges':graph['edges']}


def candidate(graph, engine, executable, elk_root, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('No time remains for layout')
    with tempfile.TemporaryDirectory(prefix='twine-layout-') as folder:
        root = Path(folder)
        if engine == 'graphviz':
            # Numeric IDs prevent passage names or body text reaching DOT.
            ids = {n['id']: f'n{i}' for i, n in enumerate(graph['nodes'])}
            lines = ['digraph G {', 'graph [' + ','.join(f'{k}="{v}"' for k,v in DOT_OPTIONS.items()) + '];',
                     'node [shape=box,fixedsize=true,label=""];']
            for n in graph['nodes']:
                lines.append(f'{ids[n["id"]]} [width={n["w"]/72:.12g},height={n["h"]/72:.12g}];')
            lines += [f'{ids[a]} -> {ids[b]};' for a,b in graph['edges']]
            lines.append('}')
            source = root / 'graph.dot'
            source.write_text('\n'.join(lines), encoding='utf-8')
            result = run_bounded([executable, '-Tjson0', str(source)], timeout=min(30,remaining))
            if result.returncode:
                raise ValueError('Graphviz rejected experimental graph')
            output = json.loads(result.stdout)
            height = float(output['bb'].split(',')[3])
            objects = {obj['name']: obj for obj in output.get('objects', [])}
            positions = {}
            for n in graph['nodes']:
                x,y = map(float, objects[ids[n['id']]]['pos'].split(','))
                positions[n['id']] = (x-n['w']/2, height-y-n['h']/2)
        else:
            source = root / 'graph.json'
            source.write_text(json.dumps({'id':'root','layoutOptions':ELK_OPTIONS,
                'children':[{'id':n['id'],'width':n['w'],'height':n['h']} for n in graph['nodes']],
                'edges':[{'id':f'e{i}','sources':[a],'targets':[b]} for i,(a,b) in enumerate(graph['edges'])]}),encoding='utf-8')
            script = root / 'layout.cjs'
            script.write_text("const fs=require('fs');const ELK=require(process.argv[2]);"
                "const elk=new ELK();elk.layout(JSON.parse(fs.readFileSync(process.argv[3],'utf8')))"
                ".then(g=>{console.log(JSON.stringify(g));})"
                ".catch(e=>{console.error(String(e));process.exit(1);});",encoding='utf-8')
            result = run_bounded([executable,str(script),str(Path(elk_root)/'lib/elk.bundled.js'),str(source)],
                                 timeout=min(30,remaining))
            if result.returncode:
                raise ValueError('ELK rejected experimental graph: ' + result.stderr.decode('utf-8',errors='replace')[:1000])
            output = json.loads(result.stdout)
            positions = {n['id']:(n['x'],n['y']) for n in output['children']}
        return validate_positions(graph,positions)
