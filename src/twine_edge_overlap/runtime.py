"""Pinned Graphviz preparation, isolated from stories and geometric processing."""
from dataclasses import dataclass, replace
import hashlib
import json
import ntpath
import os
from pathlib import Path
import re
import stat
import sys
import contextlib
import errno
import math
import tempfile
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from .engines.process import run_bounded, ProcessLimitError

from .errors import DependencyError, execution_diagnostic
from . import runtime_platform
from .runtime_catalog import CatalogError, load_catalog, select_artifact, verified_manifest, load_support_matrix, classify_support, validate_manifest_identity, version_tuple


PACKAGE = Path(__file__).resolve().parent
_DIGEST = re.compile(r'[0-9a-f]{64}\Z')
_RESERVED = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}


class _PreparationProblem(ValueError):
    """A controlled diagnostic, safe to present without remote payloads or credentials."""


def failure(reason, action='Repita --repair-runtime; se persistir, consulte a documentação do projeto.'):
    return DependencyError(f'{reason}. Componente de processamento indisponível; nenhuma cópia gerada. {action}')


def relative_path(value):
    """Accept only unambiguous Windows-safe, relative, forward-slash paths."""
    if not isinstance(value, str) or not value or '\\' in value or ntpath.isabs(value):
        raise _PreparationProblem('caminho relativo inválido')
    parts = value.split('/')
    for part in parts:
        if (not part or part in ('.', '..') or part[-1:] in (' ', '.')
                or any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                or part.split('.')[0].upper() in _RESERVED):
            raise _PreparationProblem('componente de caminho inválido')
    return Path(*parts)


def check_platform():
    try:
        return select_artifact(load_catalog(), runtime_platform.detect_host())
    except CatalogError as exc:
        raise failure(str(exc), 'Consulte a matriz de componentes disponíveis; use CPython 3.12 ou 3.14 nativo em ambiente compatível.') from exc


def _unique_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _PreparationProblem('chave JSON duplicada')
        result[key] = value
    return result


def _read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=_unique_json)


def _digest_file(path, check=lambda: None):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(65536):
            check()
            digest.update(chunk)
    return digest.hexdigest()


def _no_links(path, root=None):
    if os.name != 'nt':
        try:
            runtime_platform.assert_managed_path(path, root or PACKAGE, private=root is not None)
        except ValueError as exc:
            raise _PreparationProblem(str(exc)) from exc
        return
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise _PreparationProblem('link ou reparse point no cache')


@dataclass(frozen=True)
class Artifact:
    data: dict

    @property
    def identity(self):
        keys = ('engine', 'version', 'platform', 'artifact_arch', 'archive_sha256')
        if self.data.get('schema_version') == 2:
            keys = ('engine', 'version', 'platform', 'artifact_arch', 'abi', 'build_variant', 'archive_sha256', '_manifest_sha256')
        return '-'.join(str(self.data[key]) for key in keys)


@dataclass(frozen=True)
class RuntimeHandle:
    identity: str
    generation_id: str
    root: Path
    executable: Path
    cwd: Path
    env: dict
    classification_seconds: float = 0.0


def load_manifest(path=None):
    from urllib.parse import urlsplit
    try:
        manifest_path = Path(path or PACKAGE / 'runtime-manifest.json')
        if manifest_path.stat().st_size > 8 * 1024**2:
            raise _PreparationProblem('manifesto excede limite')
        data = _read_json(manifest_path)
        schema = data['schema_version']
        if (type(schema) is not int or schema not in (1, 2) or data['engine'] != 'graphviz'
                or data['version'] != '16.1.0' or not _DIGEST.fullmatch(data['archive_sha256'])):
            raise _PreparationProblem('identidade/esquema/hash inválido')
        if schema == 1:
            if data['platform'] != 'windows' or data['artifact_arch'] != 'win32':
                raise _PreparationProblem('identidade legada inválida')
        else:
            if (data['platform'] not in ('linux', 'darwin') or data['artifact_arch'] not in ('x86_64', 'aarch64')
                    or data['abi'] not in (('glibc', 'musl') if data['platform'] == 'linux' else ('darwin',))
                    or not re.fullmatch(r'[a-zA-Z0-9_.-]{1,80}', data['build_variant'])):
                raise _PreparationProblem('identidade nativa inválida')
            data['_manifest_sha256'] = _digest_file(manifest_path)
            for key in (('minimum_libc', 'minimum_kernel') if data['platform']=='linux' else ('minimum_os',)):
                version_tuple(data[key])
        url = urlsplit(data['url'])
        hosts = data['allowed_redirect_hosts']
        if (url.scheme != 'https' or url.username or url.password or url.port not in (None, 443)
                or not isinstance(hosts, list) or not hosts or url.hostname not in hosts
                or any(not isinstance(h, str) or not re.fullmatch(r'[a-z0-9.-]+', h) for h in hosts)):
            raise _PreparationProblem('origem inválida')
        for key, maximum in [('archive_bytes_limit', 128*1024**2), ('expanded_bytes_limit', 512*1024**2), ('entry_limit', 5000)]:
            if type(data[key]) is not int or not 0 < data[key] <= maximum:
                raise _PreparationProblem('limite inválido')
        seen = set()
        total = 0
        for entry in data['files']:
            name = relative_path(entry['path']).as_posix().casefold()
            if name in seen or not _DIGEST.fullmatch(entry['sha256']) or type(entry['size']) is not int or entry['size'] < 0:
                raise _PreparationProblem('inventário inválido')
            total += entry['size']
            seen.add(name)
            if schema == 2 and (type(entry.get('mode')) is not int or entry['mode'] not in (0o644, 0o755)):
                raise _PreparationProblem('modo POSIX não aprovado')
        if not seen or len(seen) > data['entry_limit'] or total > data['expanded_bytes_limit']:
            raise _PreparationProblem('limites do inventário')
        executable = relative_path(data['executable_relative_path'])
        if executable.as_posix().casefold() not in seen:
            raise _PreparationProblem('executável fora do inventário')
        if schema == 2:
            if next((entry['mode'] for entry in data['files'] if entry['path'] == executable.as_posix()), None) != 0o755:
                raise _PreparationProblem('executável sem modo aprovado')
            if 'plugin_relative_path' in data:
                plugin = relative_path(data['plugin_relative_path']).as_posix()
                if not any(entry['path'].startswith(plugin + '/') for entry in data['files']):
                    raise _PreparationProblem('plugins fora do inventário')
        # The qualified ZIP already contains a portable config8: no generated files are needed.
        if data['generated_files'] != []:
            raise _PreparationProblem('configuração gerada não qualificada')
        destinations = set()
        for notice in data['notices']:
            source = relative_path(notice['package_source'])
            destination = relative_path(notice['destination'])
            normalized = destination.as_posix().casefold()
            if (len(destination.parts) < 2 or destination.parts[0] != 'third-party-notices'
                    or normalized in destinations or normalized in seen
                    or not _DIGEST.fullmatch(notice['sha256'])):
                raise _PreparationProblem('aviso inválido')
            _no_links(PACKAGE / source)
            if _digest_file(PACKAGE / source) != notice['sha256']:
                raise _PreparationProblem('aviso do pacote alterado')
            destinations.add(normalized)
        all_files = seen | destinations
        for name in all_files:
            parts = name.split('/')
            if any('/'.join(parts[:index]) in all_files for index in range(1, len(parts))):
                raise _PreparationProblem('colisão entre arquivo e diretório no inventário')
        references = data['source_references']
        if not destinations or not isinstance(references, list) or not references:
            raise _PreparationProblem('avisos/fontes ausentes')
        for reference in references:
            if not isinstance(reference, str) or any(char.isspace() for char in reference):
                raise _PreparationProblem('referência de fonte inválida')
            source_url = urlsplit(reference)
            if source_url.scheme not in ('https', 'http') or not source_url.hostname or source_url.username or source_url.password:
                raise _PreparationProblem('referência de fonte inválida')
        return Artifact(data)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise failure('Manifesto ou avisos da aplicação ausentes ou inválidos', 'Obtenha novamente o projeto completo e repita o comando.') from exc


class _Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts):
        self.hosts = hosts
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        url = urllib.parse.urlsplit(newurl)
        if (self.count > 5 or url.scheme != 'https' or url.hostname not in self.hosts
                or url.username or url.password or url.port not in (None, 443)):
            raise _PreparationProblem('redirecionamento não autorizado')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def cache_directory():
    return runtime_platform.cache_directory()


class RuntimeManager:
    """One bounded preparation operation, with explicit seams for isolated tests."""

    def __init__(self, *, artifact=None, cache_root=None, opener=None, runner=run_bounded,
                 progress=None, checkpoint=None):
        self.artifact = artifact or load_manifest()
        self.data = self.artifact.data
        base = Path(cache_root or cache_directory()).absolute()
        anchor = base if cache_root is not None else base.parents[1]
        if os.name != 'nt':
            canonical_anchor = anchor.parent.resolve() / anchor.name
            base = canonical_anchor / base.relative_to(anchor)
            anchor = canonical_anchor
        self.anchor = anchor
        root = base / self.artifact.identity
        # Generations plus the pinned archive tree exceed MAX_PATH on ordinary profiles.
        # The extended namespace needs no registry change or user configuration.
        value = str(root)
        if os.name == 'nt' and not value.startswith('\\\\?\\'):
            value = ('\\\\?\\UNC\\' + value[2:]) if value.startswith('\\\\') else '\\\\?\\' + value
        self.root = Path(value)
        self.opener = opener
        self.runner = runner
        self.progress = progress or (lambda message: None)
        self.checkpoint = checkpoint or (lambda stage: None)
        self.deadline = 0.0

    def safe_path(self, path):
        _no_links(path, self.anchor)

    def make_directories(self, path):
        """Create owned descendants privately, without changing existing modes."""
        self.safe_path(path)
        if os.name == 'nt':
            path.mkdir(parents=True, exist_ok=True)
            return
        # A selected XDG/cache base need not exist on first use. Create only
        # missing ancestors, privately even with umask 000; never chmod existing
        # user directories. The anchor was canonicalized during construction.
        missing_parents = []
        parent = self.anchor.parent
        while not parent.exists():
            missing_parents.append(parent)
            parent = parent.parent
        for directory in reversed(missing_parents):
            self.check()
            directory.mkdir(mode=0o700, exist_ok=True)
            try:
                runtime_platform.assert_managed_path(directory, directory, private=True)
            except ValueError as exc:
                raise _PreparationProblem(str(exc)) from exc
        missing = []
        current = path
        while current.is_relative_to(self.anchor) and not current.exists():
            missing.append(current)
            current = current.parent
        for directory in reversed(missing):
            directory.mkdir(mode=0o700, exist_ok=True)
            self.safe_path(directory)

    def check(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError('prazo de preparação esgotado')

    @contextlib.contextmanager
    def locked(self):
        self.safe_path(self.root)
        self.make_directories(self.root)
        lock_path = self.root / 'prepare.lock'
        self.safe_path(lock_path)
        try:
            with runtime_platform.preparation_lock(lock_path, deadline=self.deadline, check=self.check):
                yield
        except runtime_platform.LockBusyError as exc:
            raise failure('Outra preparação está em andamento', 'Aguarde sua conclusão e repita o comando.') from exc

    def context(self, root, generation_id):
        executable = root / relative_path(self.data['executable_relative_path'])
        plugins = root / relative_path(self.data['plugin_relative_path']) if 'plugin_relative_path' in self.data else executable.parent
        env = runtime_platform.runtime_environment(executable, plugin_directory=plugins)
        # CreateProcess rejects a working directory beyond MAX_PATH even with the
        # extended namespace. Use the common runtime cache; executable and plugin
        # paths remain absolute and fixed to this generation.
        cwd = self.root.parent if os.name == 'nt' else root
        return RuntimeHandle(self.artifact.identity, generation_id, root, executable, cwd, env)

    def verify_files(self, root, *, ready):
        self.check()
        self.safe_path(root)
        expected = {entry['path']: entry for entry in self.data['files']}
        expected.update({entry['destination']: entry for entry in self.data['notices']})
        found = set()
        for folder, directories, filenames in os.walk(root, followlinks=False):
            self.check()
            for name in directories:
                self.safe_path(Path(folder) / name)
            for name in filenames:
                path = Path(folder) / name
                self.safe_path(path)
                relative = path.relative_to(root).as_posix()
                if relative == 'ready.json' and ready:
                    continue
                if relative not in expected:
                    raise _PreparationProblem('arquivo inesperado na geração')
                entry = expected[relative]
                if ('size' in entry and path.stat().st_size != entry['size']) or _digest_file(path, self.check) != entry['sha256']:
                    raise _PreparationProblem('arquivo da geração ausente ou alterado')
                if self.data['schema_version'] == 2 and os.name != 'nt' and stat.S_IMODE(path.stat().st_mode) != entry.get('mode', 0o644):
                    raise _PreparationProblem('modo instalado difere do inventário')
                found.add(relative)
        if found != set(expected):
            raise _PreparationProblem('geração incompleta')

    def probe(self, handle):
        def invoke(arguments):
            self.check()
            try:
                result = self.runner([str(handle.executable), *arguments], cwd=handle.cwd, env=handle.env,
                                     timeout=min(10, self.deadline-time.monotonic()), max_output=1024**2)
            except OSError as exc:
                raise execution_diagnostic(exc, self.data['platform']) from exc
            if result.returncode:
                raise _PreparationProblem('sondagem retornou erro')
            return result
        version = invoke(['-V'])
        if not re.search(rb'\b16\.1\.0\b', version.stdout + version.stderr):
            raise _PreparationProblem('versão do motor incompatível')
        with tempfile.TemporaryDirectory(prefix='twine-runtime-probe-') as folder:
            source = Path(folder) / 'probe.dot'
            source.write_text('digraph {node[shape=box,fixedsize=true,width=1,height=1,label=""]; n0 -> n1;}', encoding='ascii')
            result = invoke(['-Tjson0', str(source)])
        data = json.loads(result.stdout)
        bounds = [float(item) for item in data['bb'].split(',')]
        objects = data['objects']
        if (len(bounds) != 4 or not all(math.isfinite(value) and abs(value) <= 1e7 for value in bounds)
                or len(objects) != 2 or {item['name'] for item in objects} != {'n0', 'n1'}):
            raise _PreparationProblem('json0/identidades inválidos')
        for item in objects:
            position = [float(value) for value in item['pos'].split(',')]
            if len(position) != 2 or not all(math.isfinite(value) and abs(value) <= 1e7 for value in position):
                raise _PreparationProblem('posição de sondagem inválida')

    def current(self):
        try:
            selector = self.root / 'active.json'
            self.safe_path(selector)
            if selector.stat().st_size > 16384:
                return None
            active = _read_json(selector)
            generation_id = active['generation_id']
            if (active['artifact_identity'] != self.artifact.identity or not isinstance(generation_id, str)
                    or not re.fullmatch(r'[0-9a-f]{32}', generation_id)):
                return None
            root = self.root / 'generations' / generation_id
            self.verify_files(root, ready=True)
            self.safe_path(root / 'ready.json')
            if (root / 'ready.json').stat().st_size > 16384 or _read_json(root / 'ready.json') != active:
                return None
            handle = self.context(root, generation_id)
            self.probe(handle)
            return handle
        except (OSError, ValueError, KeyError, TypeError, AttributeError, ProcessLimitError):
            return None

    def download(self, target):
        self.check()
        self.progress('Preparando componente de processamento; a obtenção do pacote requer internet.')
        opener = self.opener or urllib.request.build_opener(_Redirects(self.data['allowed_redirect_hosts']))
        request = urllib.request.Request(self.data['url'], headers={'User-Agent': 'DesembaracaTwine/0.1'})
        digest = hashlib.sha256()
        total = 0
        try:
            with opener.open(request, timeout=min(30, self.deadline-time.monotonic())) as response, target.open('xb') as stream:
                url = urllib.parse.urlsplit(response.geturl())
                if (url.scheme != 'https' or url.hostname not in self.data['allowed_redirect_hosts']
                        or url.username or url.password or url.port not in (None, 443)):
                    raise _PreparationProblem('origem final não autorizada')
                if response.status != 200:
                    raise _PreparationProblem('resposta HTTP inválida')
                while True:
                    self.check()
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > self.data['archive_bytes_limit']:
                        raise _PreparationProblem('pacote excedeu o limite de transferência')
                    digest.update(chunk)
                    stream.write(chunk)
        except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
            # A cooperative preparation deadline is distinct from a socket failure.
            self.check()
            raise failure('Não foi possível obter o pacote pela internet', 'Restabeleça a conexão/acesso HTTPS e repita o comando.') from exc
        if digest.hexdigest() != self.data['archive_sha256']:
            raise _PreparationProblem('pacote não passou na verificação SHA-256')

    def extract(self, archive, staging):
        expected = {entry['path']: entry for entry in self.data['files']}
        seen = set()
        seen_normalized = set()
        total = 0
        with zipfile.ZipFile(archive) as source:
            entries = source.infolist()
            if len(entries) > self.data['entry_limit']:
                raise _PreparationProblem('excesso de entradas no ZIP')
            for entry in entries:
                self.check()
                relative = relative_path(entry.filename.rstrip('/'))
                key = relative.as_posix()
                normalized = key.casefold()
                mode = entry.external_attr >> 16
                if (normalized in seen_normalized or stat.S_ISLNK(mode)
                        or entry.external_attr & stat.FILE_ATTRIBUTE_REPARSE_POINT
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                        or entry.flag_bits & 1):
                    raise _PreparationProblem('entrada ZIP especial/duplicada/insegura')
                seen_normalized.add(normalized)
                destination = staging / relative
                self.safe_path(destination)
                if entry.is_dir():
                    self.make_directories(destination)
                    continue
                if key not in expected or entry.file_size != expected[key]['size']:
                    raise _PreparationProblem('estrutura ZIP diferente do inventário')
                if total + entry.file_size > self.data['expanded_bytes_limit']:
                    raise _PreparationProblem('expansão acima do limite')
                self.make_directories(destination.parent)
                actual = 0
                digest = hashlib.sha256()
                with source.open(entry) as incoming, destination.open('xb') as outgoing:
                    while chunk := incoming.read(65536):
                        self.check()
                        actual += len(chunk)
                        total += len(chunk)
                        if total > self.data['expanded_bytes_limit'] or actual > expected[key]['size']:
                            raise _PreparationProblem('expansão acima do limite real')
                        digest.update(chunk)
                        outgoing.write(chunk)
                if actual != expected[key]['size'] or digest.hexdigest() != expected[key]['sha256']:
                    raise _PreparationProblem('arquivo extraído inválido')
                if self.data['schema_version'] == 2 and os.name != 'nt':
                    destination.chmod(expected[key]['mode'])
                seen.add(key)
        if seen != set(expected):
            raise _PreparationProblem('ZIP incompleto')
        for notice in self.data['notices']:
            self.check()
            source = PACKAGE / relative_path(notice['package_source'])
            destination = staging / relative_path(notice['destination'])
            _no_links(source)
            if _digest_file(source, self.check) != notice['sha256']:
                raise _PreparationProblem('aviso da aplicação alterado')
            self.make_directories(destination.parent)
            with source.open('rb') as incoming, destination.open('xb') as outgoing:
                while chunk := incoming.read(65536):
                    self.check()
                    outgoing.write(chunk)
            if self.data['schema_version'] == 2 and os.name != 'nt':
                destination.chmod(0o644)

    @staticmethod
    def write_record(path, record):
        if os.name == 'nt':
            stream = path.open('x', encoding='utf-8')
        else:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
            try:
                stream = os.fdopen(descriptor, 'w', encoding='utf-8')
            except BaseException:
                os.close(descriptor)
                raise
        with stream:
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())

    @staticmethod
    def sync_directory(path):
        if os.name != 'nt':
            descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

    def ensure(self, *, force_repair=False, deadline=None):
        self.deadline = time.monotonic() + 300 if deadline is None else deadline
        try:
            self.safe_path(self.root)
            if not force_repair:
                current = self.current()
                if current:
                    return current
            with self.locked():
                if not force_repair:
                    current = self.current()
                    if current:
                        return current
                generation_id = uuid.uuid4().hex
                generations = self.root / 'generations'
                self.safe_path(generations)
                self.make_directories(generations)
                with tempfile.TemporaryDirectory(prefix='staging-', dir=self.root) as temporary:
                    temporary = Path(temporary)
                    archive = temporary / 'artifact.zip'
                    staging = temporary / 'tree'
                    staging.mkdir(mode=0o700)
                    self.download(archive)
                    self.extract(archive, staging)
                    generation = generations / generation_id
                    staging.rename(generation)
                    self.checkpoint('generation')
                    self.verify_files(generation, ready=False)
                    handle = self.context(generation, generation_id)
                    self.probe(handle)
                    record = dict(artifact_identity=self.artifact.identity, generation_id=generation_id)
                    self.write_record(generation / 'ready.json', record)
                    self.sync_directory(generation)
                    self.sync_directory(generations)
                    self.checkpoint('validated')
                    pending = self.root / ('.active-' + generation_id + '.tmp')
                    try:
                        self.write_record(pending, record)
                        self.check()
                        self.safe_path(self.root / 'active.json')
                        self.checkpoint('before_select')
                        os.replace(pending, self.root / 'active.json')
                        self.sync_directory(self.root)
                        self.checkpoint('after_select')
                    finally:
                        if pending.exists():
                            self.safe_path(pending)
                            pending.unlink()
                    return handle
        except DependencyError:
            raise
        except _PreparationProblem as exc:
            raise failure(str(exc)) from exc
        except TimeoutError as exc:
            raise failure('Prazo de preparação esgotado', 'Repita o comando; consulte a documentação se persistir.') from exc
        except ProcessLimitError as exc:
            raise failure('Sondagem excedeu seu limite de tempo ou saída') from exc
        except OSError as exc:
            if exc.errno == errno.ENOSPC:
                reason, action = 'Sem espaço para preparar o componente', 'Libere espaço na pasta do usuário e repita o comando.'
            elif isinstance(exc, PermissionError):
                reason, action = 'Acesso ao cache ou executável bloqueado', 'Verifique a permissão de acesso e repita o comando; consulte a documentação se persistir.'
            else:
                reason, action = 'Falha de acesso durante a preparação', 'Confira conexão, espaço e permissões e repita --repair-runtime.'
            raise failure(reason, action) from exc
        except (ValueError, KeyError, TypeError, AttributeError, TimeoutError, ProcessLimitError, zipfile.BadZipFile) as exc:
            raise failure('Pacote, integridade ou sondagem do componente inválidos') from exc


def ensure_runtime(*, force_repair=False, progress=None):
    started = time.monotonic()
    try:
        host = runtime_platform.detect_host()
        catalog = load_catalog()
        descriptor = select_artifact(catalog, host)
        artifact = load_manifest(verified_manifest(descriptor))
        validate_manifest_identity(descriptor, artifact.data)
        if host.os != 'windows':
            from .runtime_snapshot import snapshot_for_host
            snapshot = snapshot_for_host(host)
            decision = classify_support(host, descriptor, load_support_matrix(), snapshot=snapshot,
                                        application_revision=catalog.get('application_revision'))
            if decision.level != 'official' and progress:
                progress('Aviso: ambiente não validado; uso de melhor esforço, sem garantia de suporte completo. ' + decision.reason)
    except (OSError, CatalogError) as exc:
        raise failure(str(exc), 'Consulte a matriz e os pré-requisitos; obtenha novamente o pacote completo se os metadados estiverem alterados.') from exc
    classification_seconds = time.monotonic() - started
    handle = RuntimeManager(artifact=artifact, progress=progress).ensure(force_repair=force_repair, deadline=started + 300)
    return replace(handle, classification_seconds=classification_seconds)
