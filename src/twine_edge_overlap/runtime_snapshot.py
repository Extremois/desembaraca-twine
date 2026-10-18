"""Read-only, bounded recognition of the exact rolling environment tested."""
from dataclasses import dataclass
import hashlib
import json
import os
import platform
import re
import time
import unicodedata

from .engines.process import run_bounded, ProcessLimitError
from .runtime_platform import os_release, read_bounded


MAX_OUTPUT = 8 * 1024**2
MAX_RECORDS = 100_000
SECONDS = 5
META_KEYS = ('distribution_id', 'version_id', 'build_id', 'channel', 'native_arch', 'kernel_release')
COMMANDS = {
    'pacman': ('/usr/bin/pacman', '--query', '--color', 'never'),
    'rpm': ('/usr/bin/rpm', '--query', '--all', '--queryformat', '%{NAME}\t%{EPOCHNUM}\t%{VERSION}\t%{RELEASE}\t%{ARCH}\n'),
}


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def canonical_inventory(manager, payload, *, max_records=MAX_RECORDS):
    if manager not in COMMANDS or len(payload) > MAX_OUTPUT:
        raise ValueError('inventário excessivo ou gerenciador desconhecido')
    text = payload.decode('utf-8', errors='strict')
    records = []
    seen = set()
    lines = text.split('\n')
    if lines[-1] == '':
        lines.pop()
    for line in lines:
        # Only the final newline may create an empty record.
        if not line:
            raise ValueError('linha vazia no inventário')
        fields = line.split(' ' if manager == 'pacman' else '\t')
        if len(fields) != (2 if manager == 'pacman' else 5):
            raise ValueError('registro incompleto no inventário')
        if any(not field or any(c.isspace() or unicodedata.category(c).startswith('C') for c in field) for field in fields):
            raise ValueError('campo inválido no inventário')
        if manager == 'rpm':
            if not re.fullmatch(r'[0-9]+', fields[1]) or len(fields[1]) > 20:
                raise ValueError('epoch inválido')
            fields[1] = str(int(fields[1]))
        record = tuple(fields)
        if record in seen:
            raise ValueError('registro duplicado no inventário')
        seen.add(record)
        records.append(fields)
        if len(records) > max_records:
            raise ValueError('excesso de registros no inventário')
    if not records:
        raise ValueError('inventário vazio')
    return sorted(records, key=lambda row: tuple(field.encode('utf-8') for field in row))


def inventory_digest(manager, records):
    return hashlib.sha256(canonical_json(dict(schema='package-inventory-v1', manager=manager, records=records))).hexdigest()


def fingerprint(metadata, manager, records):
    if set(metadata) != set(META_KEYS):
        raise ValueError('metadados de snapshot incompletos')
    if any(not isinstance(metadata[key], str) or not metadata[key] for key in META_KEYS if key not in ('version_id', 'build_id')):
        raise ValueError('identidade de snapshot desconhecida')
    if any(metadata[key] is not None and not isinstance(metadata[key], str) for key in ('version_id', 'build_id')):
        raise ValueError('versão/build inválido')
    payload = dict(metadata, schema='rolling-host-v1', inventory_schema='package-inventory-v1', manager=manager,
                   inventory_sha256=inventory_digest(manager, records))
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def manjaro_branch(text):
    values = []
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        key, separator, value = line.partition('=')
        if separator and key.strip() == 'Branch':
            values.append(value.strip())
    if len(values) != 1 or values[0] not in ('stable', 'testing', 'unstable', 'stable-staging'):
        raise ValueError('canal Manjaro desconhecido')
    return values[0]


@dataclass(frozen=True)
class SnapshotResult:
    known: bool
    snapshot_id: str | None = None
    inventory_sha256: str | None = None
    metadata: dict | None = None
    records: list | None = None
    reason: str = ''
    manager: str | None = None


def collect_snapshot(manager, identity_reader, *, runner=run_bounded, clock=time.monotonic):
    """No persistence, network, updates or interpretation of user commands."""
    deadline = clock() + SECONDS
    total = 0
    captures = []
    try:
        command = COMMANDS[manager]
        for _ in range(2):
            metadata = identity_reader()
            remaining = deadline - clock()
            if remaining <= 0:
                raise TimeoutError()
            result = runner(command, timeout=remaining, max_output=MAX_OUTPUT - total,
                            env={'LC_ALL': 'C', 'LANG': 'C', 'PATH': ''}, cwd='/')
            total += len(result.stdout) + len(result.stderr)
            if result.returncode or total > MAX_OUTPUT or clock() >= deadline:
                raise ValueError('consulta falhou ou excedeu limite')
            records = canonical_inventory(manager, result.stdout)
            captures.append((fingerprint(metadata, manager, records), metadata, records))
            if clock() >= deadline:
                raise TimeoutError()
        if captures[0][0] != captures[1][0]:
            raise ValueError('ambiente mudou durante a coleta')
        identity, metadata, records = captures[0]
        return SnapshotResult(True, identity, inventory_digest(manager, records), metadata, records, manager=manager)
    except (OSError, ValueError, KeyError, TimeoutError, ProcessLimitError):
        # Do not include package inventory, config contents or personal paths in diagnostics.
        return SnapshotResult(False, reason='Não foi possível reconhecer um snapshot local estável dentro dos limites.')


def snapshot_for_host(host, *, runner=run_bounded):
    if host.os != 'linux' or host.distribution_id not in ('arch', 'archarm', 'manjaro', 'opensuse-tumbleweed'):
        return SnapshotResult(False, reason='Ambiente sem identificação rolling cadastrada.')
    manager = 'rpm' if host.distribution_id == 'opensuse-tumbleweed' else 'pacman'
    def identity():
        data = os_release()
        distro = data.get('ID')
        if distro != host.distribution_id:
            raise ValueError('distribuição mudou durante a coleta')
        channel = 'tumbleweed' if manager == 'rpm' else 'rolling'
        if distro == 'manjaro':
            channel = manjaro_branch(read_bounded('/etc/pacman-mirrors.conf'))
        return dict(distribution_id=distro, version_id=data.get('VERSION_ID') or None,
                    build_id=data.get('BUILD_ID') or None, channel=channel,
                    native_arch=host.arch, kernel_release=platform.release())
    return collect_snapshot(manager, identity, runner=runner)
