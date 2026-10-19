"""Collect pinned source material for review, separately from the runtime ZIP.

This is not an approved corresponding-source offer or a public release.
The SDK compiler executable, caches and checkout secrets are never collected.
"""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE_LOCK = json.loads((HERE / 'source-lock.json').read_bytes())
SPEC = importlib.util.spec_from_file_location('source_sdk_preparer', HERE / 'prepare-linux-ci.py')
PREPARER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREPARER)
SDK_LOCK = PREPARER.ZIG
SDK_LOCK_ARM64 = PREPARER.ZIG_ARM64
MAX_EXPANDED = 512 * 1024**2
MAX_FILE = 64 * 1024**2
MAX_FILES = 30000


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pinned(path, lock):
    if path.is_symlink() or path.stat().st_size != lock['size'] or digest(path) != lock['sha256']:
        raise ValueError('Pinned source archive size/hash mismatch')


def bounded(path, limit=MAX_FILE):
    if path.is_symlink() or not path.is_file():
        raise ValueError('Source material must be a regular file')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Source material exceeds budget')
    return data


def sdk_members(archive):
    selected, seen, total = [], set(), 0
    for index, member in enumerate(archive):
        if index >= MAX_FILES:
            raise ValueError('SDK member count exceeds budget')
        path = PurePosixPath(member.name)
        if (path.is_absolute() or '..' in path.parts or '\\' in member.name
                or ':' in member.name or not (member.isfile() or member.isdir())):
            raise ValueError('Unsafe SDK member')
        if len(path.parts) < 2:
            continue
        relative = PurePosixPath(*path.parts[1:])
        if member.isdir() or not (relative.parts[0] == 'lib' or str(relative) == 'LICENSE'):
            continue
        name = 'sdk/' + str(relative)
        if name in seen or member.size > MAX_FILE or member.size < 0:
            raise ValueError('Invalid SDK source member')
        total += member.size
        if total > MAX_EXPANDED:
            raise ValueError('SDK expansion exceeds budget')
        seen.add(name)
        selected.append((name, member))
    if 'sdk/LICENSE' not in seen or not any(name.startswith('sdk/lib/') for name in seen):
        raise ValueError('SDK sources or root license missing')
    return selected


def pack(graphviz, sdk, provenance, output):
    graphviz, sdk, provenance, output = map(Path, (graphviz, sdk, provenance, output))
    if output.exists() or output.is_symlink():
        raise FileExistsError('Source output already exists')
    pinned(graphviz, SOURCE_LOCK)
    provenance_bytes = bounded(provenance, 8 * 1024**2)
    record = json.loads(provenance_bytes)
    artifact=record['artifact_id']
    if artifact not in ('linux-glibc-x86_64','linux-glibc-aarch64'):
        raise ValueError('Unsupported source material artifact')
    sdk_lock=SDK_LOCK if artifact=='linux-glibc-x86_64' else SDK_LOCK_ARM64
    if artifact=='linux-glibc-aarch64' and (record.get('native_os'),record.get('native_arch'))!=('linux','aarch64'):
        raise ValueError('ARM64 source material requires matching native provenance')
    pinned(sdk, sdk_lock)
    recipe = HERE / (artifact+'.json')
    if (record.get('completed') is not True
            or record['source']['sha256'] != SOURCE_LOCK['sha256']
            or record['sdk']['facts']['archive']['sha256'] != sdk_lock['sha256']
            or record['recipe_sha256'] != digest(recipe)):
        raise ValueError('Source material does not match candidate provenance')
    # Enumerate only maintainer recipes, scripts, notices and reference data.
    # Never walk the checkout, artifacts/, private SDK or compiler cache.
    paths = sorted([path for path in HERE.iterdir() if path.suffix in ('.py', '.json', '.sh', '.md')]
                   + [path for path in (HERE / 'licenses').rglob('*') if path.is_file()])
    local = [('tools/runtime/' + path.relative_to(HERE).as_posix(), bounded(path)) for path in paths]
    # build-common imports host detection and bounded process execution. Preserve
    # their exact source dependencies so the exported recipe works independently.
    for name in ('LICENSE', 'src/twine_edge_overlap/__init__.py',
                 'src/twine_edge_overlap/runtime_platform.py',
                 'src/twine_edge_overlap/engines/__init__.py',
                 'src/twine_edge_overlap/engines/process.py'):
        local.append((name, bounded(HERE.parents[1] / name)))
    local += [('graphviz.tar.gz', bounded(graphviz)), ('candidate-provenance.json', provenance_bytes)]
    rows, total = [], 0

    def add(archive, name, data):
        nonlocal total
        total += len(data)
        if total > MAX_EXPANDED or len(rows) >= MAX_FILES:
            raise ValueError('Source package exceeds budget')
        entry = tarfile.TarInfo(name)
        entry.size, entry.mode = len(data), 0o644
        archive.addfile(entry, io.BytesIO(data))
        rows.append(dict(path=name, size=len(data), sha256=hashlib.sha256(data).hexdigest()))

    with tarfile.open(sdk, 'r:xz') as incoming:
        members = sdk_members(incoming)
        output.mkdir(mode=0o700, parents=True, exist_ok=False)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=output, suffix='.part', delete=False) as stream:
                temporary = Path(stream.name)
                with gzip.GzipFile(filename='', mode='wb', fileobj=stream, mtime=0) as compressed:
                    with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.USTAR_FORMAT) as archive:
                        for name, data in local:
                            add(archive, name, data)
                        for name, member in sorted(members):
                            with incoming.extractfile(member) as source:
                                data = source.read(member.size + 1)
                            if len(data) != member.size:
                                raise ValueError('Incomplete SDK source member')
                            add(archive, name, data)
                        manifest = dict(kind='candidate-source-review-material', approved=False,
                            artifact_id=record['artifact_id'], executable_sha256=record['executable_sha256'],
                            provenance_sha256=hashlib.sha256(provenance_bytes).hexdigest(),
                            graphviz_archive_sha256=SOURCE_LOCK['sha256'], sdk_archive_sha256=sdk_lock['sha256'],
                            sdk_scope='Complete lib/ tree and root LICENSE; compiler executable excluded',
                            files=rows.copy(), pending=['per-file applicability and complete source offer review',
                            'rebuild/relink execution from exported sources', 'immutable public source distribution'])
                        add(archive, 'manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())
                stream.flush()
                os.fsync(stream.fileno())
            # Recheck archives after reading; never certify changed input bytes.
            pinned(graphviz, SOURCE_LOCK)
            pinned(sdk, sdk_lock)
            report = dict(kind=manifest['kind'], approved=False, artifact_id=record['artifact_id'],
                executable_sha256=record['executable_sha256'], provenance_sha256=manifest['provenance_sha256'],
                archive='sources.tar.gz', archive_sha256=digest(temporary), archive_bytes=temporary.stat().st_size,
                sdk_files=len(members), file_count=len(rows), expanded_bytes=total, pending=manifest['pending'])
            os.link(temporary, output / 'sources.tar.gz')
            with (output / 'sources.json').open('x', encoding='utf-8') as stream:
                json.dump(report, stream, indent=2)
                stream.write('\n')
            return report
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('graphviz', 'sdk', 'provenance', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(pack(args.graphviz, args.sdk, args.provenance, args.output), indent=2))
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as exc:
        parser.exit(1, 'Source collection failed (' + type(exc).__name__ + '); no source offer approved.\n')


if __name__ == '__main__':
    main()
