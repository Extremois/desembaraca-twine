"""Read pinned Graphviz sources with the two reviewed entity replacements.

The downloaded archive stays an upstream input. Source exports contain only
the modified archive; its logical tree is authenticated independently of gzip.
"""
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

HERE = Path(__file__).resolve().parent
PREFIX = 'graphviz-16.1.0/'


def replacements(lock):
    result = {}
    for name, row in lock.get('entity_replacement', {}).get('files', {}).items():
        path = HERE / row['file']
        if not path.resolve().is_relative_to(HERE.resolve()) or path.is_symlink():
            raise ValueError('Unsafe replacement source path')
        with path.open('rb') as stream:
            raw = stream.read(1024**2 + 1)
        if len(raw) != row['size'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Entity replacement source changed')
        result[PREFIX + name] = raw
    return result


def member_bytes(archive, member, lock):
    if not member.isfile() or member.size > 64 * 1024**2 or member.size < 0:
        raise ValueError('Invalid Graphviz source member')
    raw = archive.extractfile(member).read(member.size + 1)
    if len(raw) != member.size:
        raise ValueError('Truncated Graphviz source member')
    replacement = (replacements(lock).get(member.name)
                   if member.name.removeprefix(PREFIX) in lock.get('entity_replacement', {}).get('files', {}) else None)
    if replacement is not None:
        row = lock['entity_replacement']['files'][member.name[len(PREFIX):]]
        if hashlib.sha256(raw).hexdigest() not in (row['upstream_sha256'], row['sha256']):
            raise ValueError('Unexpected entity source before replacement')
        return replacement
    return raw


def tree_identity(path, lock):
    rows, seen, total = [], set(), 0
    with tarfile.open(path) as archive:
        if archive.pax_headers.get('comment') != lock['git_revision']:
            raise ValueError('Source archive revision differs')
        for member in archive:
            name = member.name
            relative = PurePosixPath(name)
            total += member.size
            if (name in seen or not relative.parts or relative.is_absolute() or '..' in relative.parts
                    or '\\' in name or ':' in name or relative.parts[0] != PREFIX[:-1]
                    or len(seen) >= 50000 or total > 1024**3 or member.size < 0):
                raise ValueError('Unsafe or excessive Graphviz source tree')
            seen.add(name)
            row = dict(path=name, mode=member.mode)
            if member.isfile():
                raw = member_bytes(archive, member, lock)
                row.update(type='file', size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            elif member.isdir():
                row.update(type='directory')
            elif member.issym():
                target = PurePosixPath(member.linkname)
                if target.is_absolute() or '..' in target.parts or '\\' in member.linkname:
                    raise ValueError('Unsafe Graphviz source link')
                row.update(type='symlink', target=member.linkname)
            else:
                raise ValueError('Unsupported Graphviz source member')
            rows.append(row)
    if not set(replacements(lock)).issubset(seen):
        raise ValueError('Entity source missing from archive')
    return hashlib.sha256(json.dumps(sorted(rows, key=lambda row: row['path']),
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def verify(path, lock):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 64 * 1024**2:
        raise ValueError('Source archive exceeds bounds or is not a regular file')
    with path.open('rb') as stream:
        original = ('size' not in lock or path.stat().st_size == lock['size']) and hashlib.file_digest(stream, 'sha256').hexdigest() == lock['sha256']
    if 'entity_replacement' not in lock:
        if not original:
            raise ValueError('Source archive differs from pinned upstream')
        return
    try:
        identity = tree_identity(path, lock)
    except tarfile.TarError as exc:
        raise ValueError('Source archive is not a valid reviewed tar archive') from exc
    if identity != lock['entity_replacement']['source_tree_sha256']:
        raise ValueError('Source archive differs from reviewed modified tree')


def apply(directory, lock):
    for name, raw in replacements(lock).items():
        path = Path(directory) / name
        row = lock['entity_replacement']['files'][name[len(PREFIX):]]
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() not in (row['upstream_sha256'], row['sha256']):
            raise ValueError('Extracted entity source differs from reviewed input')
        path.write_bytes(raw)


def export(path, lock):
    """Return a compressed modified archive, excluding both old entity files."""
    verify(path, lock)
    if 'entity_replacement' not in lock:
        return Path(path).read_bytes()
    result = io.BytesIO()
    with tarfile.open(path) as incoming, gzip.GzipFile(fileobj=result, mode='wb', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w|', format=tarfile.PAX_FORMAT,
                          pax_headers=incoming.pax_headers) as outgoing:
            for member in incoming:
                entry = copy.copy(member)
                raw = member_bytes(incoming, member, lock) if member.isfile() else None
                if raw is not None:
                    entry.size = len(raw)
                outgoing.addfile(entry, io.BytesIO(raw) if raw is not None else None)
    if result.tell() > 64 * 1024**2:
        raise ValueError('Modified source archive exceeds budget')
    return result.getvalue()
