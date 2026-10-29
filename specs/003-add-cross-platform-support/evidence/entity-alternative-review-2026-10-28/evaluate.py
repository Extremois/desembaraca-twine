"""Evaluate replacement entity inputs in Actions; never change a production build."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def evaluate(output):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Run this evaluation in GitHub Actions')
    lock = json.loads((HERE/'inputs.json').read_bytes())
    inputs = {}
    for name, item in lock['inputs'].items():
        stored = (HERE/'inputs'/name).read_bytes()
        if len(stored) > 1024**2 or sha(stored) != item.get('stored_sha256', item['sha256']):
            raise ValueError('Evaluation input changed')
        raw = gzip.decompress(stored) if item.get('encoding') == 'gzip' else stored
        if len(raw) != item['size'] or sha(raw) != item['sha256']:
            raise ValueError('Evaluation input differs from its lock')
        inputs[name] = raw
    names = {'amp'}  # XML's predefined name is not repeated in the three selector files.
    for suffix in ('lat1', 'special', 'symbol'):
        raw = inputs['xhtml1-'+suffix+'.ent']
        if b'conforming SGML systems' in raw or b'W3C Software Notice and License' not in raw:
            raise ValueError('Expected the modern permissively licensed selector')
        names.update(n.decode() for n in re.findall(rb'^<!ENTITY\s+([A-Za-z][A-Za-z0-9]+)\s+"', raw, re.M))
    modern = json.loads(inputs['entities.json'])
    values = {}
    for name in sorted(names):
        row = modern['&'+name+';']
        if len(row['codepoints']) != 1 or row['characters'] != chr(row['codepoints'][0]):
            raise ValueError('Legacy selector must resolve to one Unicode scalar')
        values[name] = row['codepoints'][0]
    for name, change in lock['compatibility_overrides'].items():
        if values[name] != change['modern']:
            raise ValueError('Modern compatibility value changed')
        values[name] = change['legacy']
    if len(values) != 252:
        raise ValueError('Expected exactly the original 252 names')
    whatwg = inputs['WHATWG-LICENSE.txt'].decode()
    bsd = whatwg.split('BSD 3-Clause License\n', 1)[1].split('- - - -', 1)[0].strip()
    notice = ('Copyright © WHATWG (Apple, Google, Mozilla, Microsoft).\n'
        'Copyright 1998 - 2011 W3C.\n'
        'WHATWG portions incorporated into source code: BSD 3-Clause License.\n'
        + bsd + '\n\nW3C selector portions: W3C Software and Document License 2002.\n'
        + inputs['W3C-software-2002.txt'].decode()
        + '\nChanges, 2026-10-28: select 252 names; preserve Graphviz legacy lang/rang values.\n'
        'Data: https://html.spec.whatwg.org/entities.json\n'
        'Selectors: https://www.w3.org/2003/entities/2007/xhtml1-{lat1,special,symbol}.ent\n')
    if '-->' in notice or '*/' in notice:
        raise ValueError('Unexpected notice delimiter')
    proposed_html = ('<!--\n'+notice+'-->\n'+''.join(
        '&lt;!ENTITY '+name+' CDATA "&amp;#'+str(value)+';" -- generated --&gt;\n'
        for name, value in sorted(values.items()))).encode()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = json.loads((ROOT/'tools/runtime/source-lock.json').read_bytes())
    with tempfile.TemporaryDirectory(dir=os.environ['RUNNER_TEMP']) as temporary:
        work = Path(temporary)
        archive = work/'graphviz.tar.gz'
        with urllib.request.urlopen(source['url'], timeout=30) as incoming, archive.open('xb') as stream:
            total = 0
            while chunk := incoming.read(65536):
                total += len(chunk)
                if total > source['size']:
                    raise ValueError('Upstream archive exceeds pinned size')
                stream.write(chunk)
        if total != source['size'] or sha(archive.read_bytes()) != source['sha256']:
            raise ValueError('Upstream archive differs from the source lock')
        with tarfile.open(archive) as incoming:
            def member(name):
                item = incoming.getmember('graphviz-16.1.0/'+name)
                if not item.isfile() or item.size > 1024**2:
                    raise ValueError('Unexpected upstream evaluation input')
                return incoming.extractfile(item).read()
            original_py = member('lib/common/entities.py')
            original_html = member('lib/common/entities.html')
            copying = member('COPYING')
            if sha(copying) != source['license_sha256']:
                raise ValueError('Graphviz license differs from the source lock')
            original_values = {n.decode(): int(v) for n, v in re.findall(
                rb'&lt;!ENTITY\s+([^\s]*)\s+CDATA\s+"&amp;#(\d+);"\s+--', original_html)}
            if values != original_values:
                raise ValueError('Candidate changes entity names or code points')
            old_url = b'http://www.w3.org/TR/REC-html40/sgml/entities.html'
            if original_py.count(old_url) != 2:
                raise ValueError('Unexpected upstream provenance comment')
            proposed_py = original_py.replace(old_url, b'https://html.spec.whatwg.org/entities.json')
            comment = '    /*\n'+''.join('     * '+line+'\n' for line in notice.splitlines())+'     */\n'
            comment = comment.replace('{', '{{').replace('}', '}}').encode()
            if proposed_py.count(b'    /// @file') != 1:
                raise ValueError('Unexpected upstream header template')
            proposed_py = proposed_py.replace(b'    /// @file', comment+b'    /// @file')
            baseline = work/'baseline'
            baseline.mkdir()
            for directory, script, data in ((baseline, original_py, original_html), (output, proposed_py, proposed_html)):
                (directory/'entities.py').write_bytes(script)
                (directory/'entities.html').write_bytes(data)
                subprocess.run([sys.executable, str(directory/'entities.py'), str(directory/'entities.h')],
                    check=True, timeout=10, cwd=directory)
            def declarations(raw):
                raw = re.sub(rb'/\*.*?\*/|//[^\n]*', b'', raw, flags=re.S)
                return re.sub(rb'\s+', b' ', raw).strip()
            baseline_header = (baseline/'entities.h').read_bytes()
            candidate_header = (output/'entities.h').read_bytes()
            if declarations(baseline_header) != declarations(candidate_header):
                raise ValueError('Candidate changes generated C declarations')
            replacements = {'graphviz-16.1.0/lib/common/entities.html': proposed_html,
                            'graphviz-16.1.0/lib/common/entities.py': proposed_py}
            tree, seen, size = [], set(), 0
            for item in incoming:
                path = PurePosixPath(item.name).as_posix()
                if path in seen or '..' in PurePosixPath(path).parts or PurePosixPath(path).is_absolute():
                    raise ValueError('Unsafe or duplicate upstream member')
                seen.add(path)
                row = dict(path=path, mode=item.mode)
                if item.isfile():
                    size += item.size
                    if item.size > 64*1024**2 or size > 1024**3 or len(seen) > 50000:
                        raise ValueError('Source tree exceeds budget')
                    raw = replacements.get(path)
                    if raw is None:
                        with incoming.extractfile(item) as stream:
                            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                        length = item.size
                    else:
                        digest, length = sha(raw), len(raw)
                    row.update(type='file', size=length, sha256=digest)
                elif item.isdir():
                    row.update(type='directory')
                elif item.issym():
                    row.update(type='symlink', target=item.linkname)
                else:
                    raise ValueError('Unsupported source-tree member')
                tree.append(row)
        (output/'COPYING-Graphviz-EPL-2.0.txt').write_bytes(copying)
        integration = source.get('entity_replacement')
        if integration is not None:
            spec = importlib.util.spec_from_file_location('integrated_entity_source', ROOT/'tools/runtime/graphviz-source.py')
            integrated = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(integrated)
            if integrated.replacements(source) != replacements:
                raise ValueError('Integrated replacement bytes differ from reproduced proposal')
            modified = output/'modified-graphviz.tar.gz'
            modified.write_bytes(integrated.export(archive, source))
            integrated.verify(modified, source)
            with tarfile.open(modified) as exported:
                for name, raw in replacements.items():
                    if exported.extractfile(name).read() != raw:
                        raise ValueError('Source export retains a legacy entity file')
            # An exported source archive must remain usable without historical inputs.
            with tempfile.TemporaryDirectory(dir=os.environ['RUNNER_TEMP']) as replay:
                with tarfile.open(modified) as exported:
                    exported.extractall(replay, filter='data')
                integrated.apply(replay, source)
        report = dict(kind='entity-alternative-prototype-not-production-qualification', passed=True,
            approved=False, qualified=False, application_revision=os.environ['GITHUB_SHA'],
            source_lock_sha256=sha((ROOT/'tools/runtime/source-lock.json').read_bytes()),
            whatwg_repository_revision=lock['whatwg_repository_revision'], entity_count=len(values),
            modern_values_unchanged=250, compatibility_overrides=lock['compatibility_overrides'],
            candidate_names_and_values_match_original=True, generated_c_declarations_identical=True,
            original_header_sha256=sha(baseline_header), candidate_header_sha256=sha(candidate_header),
            generated_c_declarations_sha256=sha(declarations(candidate_header)),
            replacements={name: dict(sha256=sha(raw), size=len(raw)) for name, raw in replacements.items()},
            proposed_source_tree_sha256=sha(json.dumps(sorted(tree, key=lambda r: r['path']),
                sort_keys=True, separators=(',', ':')).encode()), source_tree_entries=len(tree),
            source_tree_identity_format='sorted path/mode/type/size/content-sha256 or symlink-target records; JSON sort_keys, compact separators',
            production_changed=integration is not None, integrated_source_export_verified=integration is not None,
            native_engine_executed=False,
            remaining=['Integrate and record the two source replacements',
                       'Export the modified source tree, excluding legacy ISO reference data',
                       'Update per-artifact notices/provenance and run ABI/package acceptance in Actions'])
        (output/'summary.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    evaluate(parser.parse_args().output)
