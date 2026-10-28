"""Trusted packaged artifact selection and evidence-derived support state."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from .runtime_platform import HostEnvironment


PACKAGE = Path(__file__).resolve().parent
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
PYTHONS = ('3.12', '3.14')
GATES = frozenset(('installation', 'first_run', 'offline', 'preservation', 'repair', 'interruption', 'crash', 'concurrency', 'twine', 'licenses'))
COMMON_GATES = frozenset(('twine','licenses'))


class CatalogError(ValueError):
    """Invalid local metadata or no qualified artifact for the host."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError('chave JSON duplicada')
        result[key] = value
    return result


def read_json(path, maximum=8 * 1024**2):
    with Path(path).open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise CatalogError('metadados excedem limite')
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(CatalogError('constante JSON invÃ¡lida')))
    except (ValueError, UnicodeError) as exc:
        raise CatalogError('JSON invÃ¡lido') from exc


def local_manifest_path(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise CatalogError('caminho de manifesto invÃ¡lido')
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')):
        raise CatalogError('manifesto fora do pacote')
    return Path(*path.parts)


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d+)*', value):
        raise CatalogError('versÃ£o mÃ­nima invÃ¡lida')
    return tuple(int(part) for part in value.split('.'))


def _at_least(actual, minimum):
    try:
        first, second = version_tuple(actual), version_tuple(minimum)
        width = max(len(first), len(second))
        return first + (0,) * (width-len(first)) >= second + (0,) * (width-len(second))
    except CatalogError:
        return False


def validate_descriptor(item):
    try:
        if (not isinstance(item['id'], str) or not item['id'] or item['os'] not in ('windows', 'linux', 'darwin')
                or item['arch'] not in ('x86_64', 'aarch64') or type(item['priority']) is not int
                or not isinstance(item['qualification_evidence'], list) or not item['qualification_evidence']
                or any(not isinstance(value, str) or not value for value in item['qualification_evidence'])
                or not DIGEST.fullmatch(item['manifest_sha256'])):
            raise CatalogError('descritor nÃ£o qualificado')
        local_manifest_path(item['manifest_path'])
        version_tuple(item['minimum_os']) if item['os'] != 'linux' else None
        if item['os'] == 'linux':
            if item['abi'] not in ('glibc', 'musl'):
                raise CatalogError('ABI Linux invÃ¡lida')
            version_tuple(item['minimum_libc'])
            version_tuple(item['minimum_kernel'])
        if not isinstance(item.get('cpu_requirements', []), list) or any(not isinstance(value, str) or not value for value in item.get('cpu_requirements', [])):
            raise CatalogError('requisitos CPU invÃ¡lidos')
    except (KeyError, TypeError, AttributeError) as exc:
        raise CatalogError('descritor incompleto') from exc
    return item


def load_catalog(path=None):
    try:
        data = read_json(path or PACKAGE / 'runtime-catalog.json')
        if type(data['schema_version']) is not int or data['schema_version'] != 2 or data['engine'] != 'graphviz' or data['engine_version'] != '16.1.0':
            raise CatalogError('esquema ou motor invÃ¡lido')
        if not isinstance(data['artifacts'], list):
            raise CatalogError('catÃ¡logo invÃ¡lido')
        identities = set()
        for descriptor in data['artifacts']:
            validate_descriptor(descriptor)
            if descriptor['id'] in identities:
                raise CatalogError('identidade de artefato duplicada')
            identities.add(descriptor['id'])
        return data
    except (OSError, KeyError, TypeError) as exc:
        raise CatalogError('catÃ¡logo local ausente ou invÃ¡lido') from exc


def select_artifact(catalog, host):
    if host.translated or host.bits != 64 or host.python_implementation != 'CPython' or tuple(host.python_version) not in ((3, 12), (3, 14)):
        raise CatalogError('interpretador/arquitetura fora dos requisitos nativos')
    candidates = []
    for item in catalog['artifacts']:
        validate_descriptor(item)
        if item['os'] != host.os or item['arch'] != host.arch:
            continue
        if host.os == 'linux':
            kernel = host.kernel_version.split('-', 1)[0]
            if item['abi'] != host.libc_family or not _at_least(host.libc_version, item['minimum_libc']) or not _at_least(kernel, item['minimum_kernel']):
                continue
        elif not _at_least(host.os_version, item['minimum_os']):
            continue
        if not set(item.get('cpu_requirements', [])).issubset(host.cpu_features):
            continue
        candidates.append(item)
    if not candidates:
        raise CatalogError('NÃ£o hÃ¡ componente qualificado compatÃ­vel com o ambiente identificado')
    priority = max(item['priority'] for item in candidates)
    preferred = [item for item in candidates if item['priority'] == priority]
    if len(preferred) != 1:
        raise CatalogError('seleÃ§Ã£o de artefato ambÃ­gua')
    return preferred[0]


def verified_manifest(descriptor):
    path = PACKAGE / local_manifest_path(descriptor['manifest_path'])
    if hashlib.sha256(path.read_bytes()).hexdigest() != descriptor['manifest_sha256']:
        raise CatalogError('manifesto empacotado alterado')
    return path


def validate_manifest_identity(descriptor, data):
    """A descriptor must never redirect a host to a different ABI payload."""
    if data['schema_version'] == 1:
        if descriptor['os'] != 'windows' or descriptor['arch'] != 'x86_64' or descriptor['abi'] != 'windows':
            raise CatalogError('manifesto legado incompatÃ­vel com descritor')
        return
    for descriptor_key, manifest_key in (('os','platform'), ('arch','artifact_arch'), ('abi','abi'), ('build_variant','build_variant')):
        if descriptor.get(descriptor_key) != data.get(manifest_key):
            raise CatalogError('ABI/identidade do manifesto difere do catÃ¡logo')
    keys = ('minimum_libc','minimum_kernel') if descriptor['os']=='linux' else ('minimum_os',)
    if any(descriptor.get(key) != data.get(key) for key in keys):
        raise CatalogError('requisitos mÃ­nimos diferem do manifesto qualificado')


@dataclass(frozen=True)
class PythonQualification:
    target_id: str
    python_minor: str
    status: str
    evidence_ids: tuple


@dataclass(frozen=True)
class SupportTarget:
    data: dict

    @property
    def id(self):
        return self.data['id']


@dataclass(frozen=True)
class ArtifactDescriptor:
    data: dict

    def __post_init__(self):
        validate_descriptor(self.data)


@dataclass(frozen=True)
class EnvironmentSnapshot:
    data: dict

    @classmethod
    def from_probe(cls, result, *, label=None, image_digest=None, captured_at=None, evidence_ids=()):
        from .runtime_snapshot import fingerprint, inventory_digest
        if not result.known or not result.metadata or not result.records:
            raise CatalogError('snapshot desconhecido nÃ£o pode gerar evidÃªncia de referÃªncia')
        if (fingerprint(result.metadata,result.manager,result.records)!=result.snapshot_id
                or inventory_digest(result.manager,result.records)!=result.inventory_sha256):
            raise CatalogError('inventÃ¡rio/fingerprint de referÃªncia inconsistente')
        return cls(dict(result.metadata,schema='rolling-host-v1',inventory_schema='package-inventory-v1',
                        manager=result.manager,inventory_sha256=result.inventory_sha256,snapshot_id=result.snapshot_id,
                        records=result.records,label=label,image_digest=image_digest,captured_at=captured_at,
                        evidence_ids=list(evidence_ids)))


def support_status(target, evidence):
    """Derive status; a hand-edited status or repeated Python never grants support."""
    try:
        slots = target['python_qualifications']
        if (len(slots) != 2 or {slot['python_minor'] for slot in slots} != set(PYTHONS)
                or list(target['required_python_minors']) != list(PYTHONS)
                or any(slot['target_id'] != target['id'] for slot in slots)):
            raise CatalogError('qualificaÃ§Ãµes Python incompletas/duplicadas')
        for slot in slots:
            if slot['status'] not in ('pendente', 'em_qualificacao', 'validada'):
                raise CatalogError('estado de qualificaÃ§Ã£o invÃ¡lido')
        started = any(slot['status'] != 'pendente' or slot.get('evidence_ids') for slot in slots)
        revision, artifact = target.get('application_revision'), target.get('artifact_id')
        if not revision or not artifact or any(slot['status'] != 'validada' for slot in slots):
            return 'em_qualificacao' if started else 'pendente'
        if target.get('version') == 'rolling' and not DIGEST.fullmatch(target.get('snapshot_id') or ''):
            return 'em_qualificacao'
        for slot in slots:
            checks = set()
            if slot.get('application_revision') != revision or slot.get('artifact_id') != artifact:
                return 'em_qualificacao'
            for reference in (*target.get('evidence_ids', []), *slot.get('evidence_ids', [])):
                item = evidence.get(reference)
                if (not isinstance(item, dict) or item.get('target_id') != target['id']
                        or item.get('application_revision') != revision or item.get('artifact_id') != artifact
                        or item.get('snapshot_id') != target.get('snapshot_id')
                        or item.get('environment_kind') not in ('github-actions', 'native') or item.get('passed') is not True
                        or item.get('python_minor') not in (None, slot['python_minor'])):
                    return 'em_qualificacao'
                if any(item.get('checks', {}).get(gate) is False for gate in GATES):
                    return 'em_qualificacao'
                if item.get('python_minor') is None and not set(item.get('checks',{})).issubset(COMMON_GATES):
                    return 'em_qualificacao'
                checks.update(key for key, passed in item.get('checks', {}).items() if passed is True)
            if not GATES.issubset(checks):
                return 'em_qualificacao'
        return 'validada'
    except (KeyError, TypeError, AttributeError) as exc:
        raise CatalogError('alvo de suporte invÃ¡lido') from exc


def load_support_matrix(path=None):
    try:
        data = read_json(path or PACKAGE / 'support-matrix.json')
        if type(data['schema_version']) is not int or data['schema_version'] != 1 or not isinstance(data['targets'], list):
            raise CatalogError('matriz de suporte invÃ¡lida')
        identities = [target['id'] for target in data['targets']]
        if len(set(identities)) != len(identities) or not isinstance(data.get('evidence', {}), dict):
            raise CatalogError('identidade/evidÃªncia duplicada ou invÃ¡lida')
        return data
    except (OSError, KeyError, TypeError) as exc:
        raise CatalogError('matriz de suporte ausente ou invÃ¡lida') from exc


@dataclass(frozen=True)
class SupportDecision:
    level: str
    target_id: str | None = None
    reason: str = ''


def classify_support(host, descriptor, matrix, *, snapshot=None, application_revision=None):
    """Support classification never substitutes for ABI checks by select_artifact."""
    if not application_revision:
        return SupportDecision('best_effort', reason='Esta revisÃ£o ainda nÃ£o tem qualificaÃ§Ã£o oficial publicada para o ambiente.')
    if host.translated or host.bits!=64 or host.python_implementation!='CPython' or tuple(host.python_version) not in ((3,12),(3,14)):
        return SupportDecision('best_effort',reason='Interpretador sem slot nativo oficialmente qualificado.')
    distro = host.distribution_id if host.os == 'linux' else ('macos' if host.os == 'darwin' else 'windows')
    actual_version = host.distribution_version if host.os == 'linux' else host.os_version
    family=[target for target in matrix['targets'] if target['os']==host.os and target['arch']==host.arch
            and target['distribution_id']==distro and (target['version']=='rolling' or actual_version==target['version'] or actual_version.startswith(target['version']+'.'))]
    variants={target.get('cpu_variant') for target in family}
    matches = []
    for target in matrix['targets']:
        if target['os'] != host.os or target['arch'] != host.arch or target['distribution_id'] != distro:
            continue
        if target['application_revision'] != application_revision or target['artifact_id'] != descriptor['id']:
            continue
        if target['version']!='rolling' and host.channel and host.channel!=target['channel']:
            continue
        if target['version'] == 'rolling':
            if not snapshot or not snapshot.known or target.get('snapshot_id') != snapshot.snapshot_id or target['channel'] != snapshot.metadata['channel']:
                continue
        elif not (actual_version == target['version'] or actual_version.startswith(target['version'] + '.')):
            continue
        if host.cpu_variant and target.get('cpu_variant')!=host.cpu_variant:
            continue
        if not host.cpu_variant and (len(variants)>1 or target.get('cpu_variant')!='distribution-default'):
            # Unknown image variant cannot inherit a qualified default cell.
            continue
        if support_status(target, matrix.get('evidence', {})) == 'validada':
            matches.append(target)
    if len(matches) == 1:
        return SupportDecision('official', matches[0]['id'])
    return SupportDecision('best_effort', reason='Ambiente sem correspondÃªncia Ãºnica com uma combinaÃ§Ã£o oficialmente validada.')
