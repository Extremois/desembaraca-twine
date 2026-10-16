"""T006 probes and comparisons under an explicitly unverified straight-edge model.

No graph quality, relative performance or preservation result is inferred from a probe.
Run with --probe to check Graphviz and ELK.js without accessing the network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import time

from process_budget import ProcessLimitError, run_bounded


ROOT = Path(__file__).resolve().parents[1]


def compare(args):
    if args.geometry not in ('straight-hypothesis','twine-2.12.1'):
        raise ValueError('Unsupported geometry: the editor uses curves; only an explicitly requested straight-hypothesis experiment is available')
    from comparison_corpus import cases, curved_cases, from_sample
    from layout_engines import candidate, DOT_OPTIONS, ELK_OPTIONS
    if args.geometry=='twine-2.12.1':
        from twine_geometry import counts,check
    else:
        from straight_geometry import counts, check
    from validate_twee_sample import inspect, neutralize
    import hashlib
    deadline = time.monotonic() + 300
    if not args.dot or not args.node or not (args.elk_root/'lib/elk.bundled.js').is_file():
        raise ValueError('Both engines must be available before comparison')
    if args.report.exists():
        raise FileExistsError('Choose a new report path; existing reports are preserved')
    if args.direction=='LR':
        DOT_OPTIONS['rankdir']='LR'
        ELK_OPTIONS['elk.direction']='RIGHT'
    corpus = curved_cases() if args.geometry=='twine-2.12.1' else cases()
    original = None
    if args.sample:
        if args.sample.stat().st_size > 10 * 1024 * 1024:
            raise ValueError('Sample exceeds experimental input allowance')
        original = args.sample.read_bytes()
        corpus['local_sample'] = from_sample(original)
    report = {'geometry':args.geometry,
              'target_editor_observation':'curves or bends, confirmed by user (option B)',
              'eligible_for_motor_selection':args.geometry=='twine-2.12.1',
              'options':{'graphviz':DOT_OPTIONS,'elkjs':ELK_OPTIONS},
              'coordinate_limit':10000000, 'rounding_decimal_places':6,
              'graphviz_version':probe('graphviz',[args.dot,'-V'],deadline),
              'elkjs_package':json.loads((args.elk_root/'package.json').read_text(encoding='utf-8'))['version'],
              'cases':[]}
    for name, graph in corpus.items():
        start = time.monotonic()
        case_deadline = min(deadline,start+120)
        row = {'case':name,'nodes':len(graph['nodes']),'semantic_edges':len(graph['edges'])}
        report['cases'].append(row)
        try:
            check(case_deadline)
            if len(graph['nodes'])>1000 or len(graph['edges'])>5000:
                raise ValueError('Experimental graph allowance exceeded')
            row['original'] = counts(graph,case_deadline)
            if case_deadline-time.monotonic()<60:
                raise TimeoutError('Insufficient equal motor allowance')
            for engine, exe in [('graphviz',args.dot),('elkjs',args.node)]:
                t = time.monotonic()
                output = candidate(graph,engine,exe,args.elk_root,case_deadline)
                metrics = counts(output,case_deadline)
                row[engine] = {'counts':metrics,'seconds':round(time.monotonic()-t,4),
                               'positions':{n['id']:[n['x'],n['y']] for n in output['nodes']},
                               'non_regression':all(a<=b for a,b in zip(metrics,row['original']))}
                if name=='local_sample':
                    spans,names,targets = inspect(original)
                    patched = original
                    for n,(lo,hi) in reversed(list(zip(output['nodes'],spans))):
                        patched = patched[:lo] + f'{n["x"]:.6f},{n["y"]:.6f}'.encode('ascii') + patched[hi:]
                    other_spans,other_names,other_targets = inspect(patched)
                    if neutralize(original,spans)!=neutralize(patched,other_spans) or (names,targets)!=(other_names,other_targets):
                        raise ValueError('Experimental preservation failed')
                    row[engine]['preserved'] = True
                    # Local review artifacts are ignored and are never published results.
                    dest = args.report.parent / f'{args.report.stem}-{engine}-review.twee'
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    with dest.open('xb') as f:
                        f.write(patched)
                    row[engine]['review_copy'] = str(dest)
            row['status']='measured_from_source_profile' if args.geometry=='twine-2.12.1' else 'measured_under_hypothesis'
        except (ValueError,TimeoutError,OSError,ProcessLimitError) as exc:
            row.update(status='not_compared',reason=str(exc))
        row['seconds'] = round(time.monotonic()-start,4)
    if original is not None:
        report['source_unchanged']=args.sample.read_bytes()==original
        report['source_sha256']=hashlib.sha256(original).hexdigest()
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0


def probe(label: str, command: list[str], deadline: float) -> dict:
    start = time.monotonic()
    remaining = deadline - start
    if remaining < 30:
        return {"engine": label, "status": "not_compared", "reason": "session_budget"}
    try:
        result = run_bounded(command, timeout=30, max_output=8 * 1024 * 1024)
        return {
            "engine": label, "status": "ready" if result.returncode == 0 else "error",
            "returncode": result.returncode,
            "diagnostic": (result.stdout + result.stderr).decode("utf-8", errors="replace").strip(),
            "probe_seconds": round(time.monotonic() - start, 4),
        }
    except (OSError, ProcessLimitError) as exc:
        return {"engine": label, "status": "unavailable", "reason": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probe", action="store_true")
    mode.add_argument("--compare", action="store_true")
    parser.add_argument('--geometry', choices=['straight-hypothesis','twine-2.12.1'],
                        help='Explicit hypothetical model only; incompatible with the user-reported curved editor')
    parser.add_argument('--sample',type=Path)
    parser.add_argument('--direction',choices=['TB','LR'],default='TB')
    parser.add_argument('--report',type=Path,default=ROOT/'.tmp/layout-comparison/results.json')
    parser.add_argument("--dot", default=shutil.which("dot"))
    parser.add_argument("--node", default=shutil.which("node"))
    parser.add_argument("--elk-root", type=Path,
                        default=ROOT / ".tmp/layout-engines/node_modules/elkjs")
    args = parser.parse_args()
    if args.compare:
        if args.geometry is None:
            parser.error('geometry is unverified: --compare requires explicit --geometry straight-hypothesis; this does not validate the curved Twine editor')
        return compare(args)
    deadline = time.monotonic() + 300
    results = []
    if args.dot:
        results.append(probe("graphviz", [args.dot, "-V"], deadline))
    else:
        results.append({"engine": "graphviz", "status": "unavailable", "reason": "dot_not_found"})
    module = args.elk_root / "lib/elk.bundled.js"
    package = args.elk_root / "package.json"
    if args.node and module.is_file() and package.is_file():
        # The module path is an argument, not JavaScript code interpolated from a path.
        code = (
            "const E=require(process.argv[1]);"
            "const p=require(process.argv[2]);"
            "if(typeof E!=='function')process.exit(3);"
            "console.log(JSON.stringify({version:p.version,license:p.license}));"
        )
        results.append(probe("elkjs", [args.node, "-e", code, str(module), str(package)], deadline))
    else:
        results.append({"engine": "elkjs", "status": "unavailable", "reason": "node_or_elkjs_not_found"})
    ready = all(result["status"] == "ready" for result in results)
    print(json.dumps({
        "phase": "dependency_probe", "layout_comparison_executed": False,
        "dependencies_ready": ready, "results": results,
    }, ensure_ascii=False, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    sys.exit(main())
