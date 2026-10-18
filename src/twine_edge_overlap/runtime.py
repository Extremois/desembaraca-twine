"""Pinned Graphviz preparation, isolated from stories and geometric processing."""
from dataclasses import dataclass
import hashlib
import json
import ntpath
import os
from pathlib import Path
import platform
import re
import stat
import struct
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

from .errors import DependencyError


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
    if (sys.platform != 'win32' or platform.machine().upper() not in ('AMD64', 'X86_64')
            or platform.python_implementation() != 'CPython' or struct.calcsize('P') != 8
            or sys.version_info[:2] not in ((3, 12), (3, 14))
            or sys.getwindowsversion().build < 22000):
        raise failure('Ambiente fora da matriz suportada', 'Use Windows 11 x64 com CPython 3.12 x64 ou 3.14 x64.')


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


def _no_links(path):
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
        return '-'.join(str(self.data[key]) for key in ('engine', 'version', 'platform', 'artifact_arch', 'archive_sha256'))


@dataclass(frozen=True)
class RuntimeHandle:
    identity: str
    generation_id: str
    root: Path
    executable: Path
    cwd: Path
    env: dict


def load_manifest(path=None):
    from urllib.parse import urlsplit
    try:
        data = _read_json(path or PACKAGE / 'runtime-manifest.json')
        if (type(data['schema_version']) is not int or data['schema_version'] != 1 or data['engine'] != 'graphviz'
                or data['version'] != '16.1.0' or data['platform'] != 'windows'
                or data['artifact_arch'] != 'win32' or not _DIGEST.fullmatch(data['archive_sha256'])):
            raise _PreparationProblem('identidade/esquema/hash inválido')
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
        if not seen or len(seen) > data['entry_limit'] or total > data['expanded_bytes_limit']:
            raise _PreparationProblem('limites do inventário')
        executable = relative_path(data['executable_relative_path'])
        if executable.as_posix().casefold() not in seen:
            raise _PreparationProblem('executável fora do inventário')
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
    base = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData/Local')
    return base.absolute() / 'DesembaracaTwine/runtimes/graphviz'


class RuntimeManager:
    """One bounded preparation operation, with explicit seams for isolated tests."""

    def __init__(self, *, artifact=None, cache_root=None, opener=None, runner=run_bounded,
                 progress=None, checkpoint=None):
        self.artifact = artifact or load_manifest()
        self.data = self.artifact.data
        root = Path(cache_root or cache_directory()).absolute() / self.artifact.identity
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

    def check(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError('prazo de preparação esgotado')

    @contextlib.contextmanager
    def locked(self):
        import msvcrt
        _no_links(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = self.root / 'prepare.lock'
        _no_links(lock_path)
        acquired = False
        with lock_path.open('a+b') as stream:
            if stream.tell() == 0:
                stream.write(b'\0')
                stream.flush()
            until = min(self.deadline, time.monotonic() + 10)
            while not acquired:
                self.check()
                try:
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    acquired = True
                except OSError:
                    if time.monotonic() >= until:
                        raise failure('Outra preparação está em andamento', 'Aguarde sua conclusão e repita o comando.')
                    time.sleep(min(0.05, max(0, until - time.monotonic())))
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)

    def context(self, root, generation_id):
        executable = root / relative_path(self.data['executable_relative_path'])
        env = {key: os.environ[key] for key in ('SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA') if key in os.environ}
        env['PATH'] = str(executable.parent)
        env['GVBINDIR'] = str(executable.parent)
        # CreateProcess rejects a working directory beyond MAX_PATH even with the
        # extended namespace. Use the common runtime cache; executable and plugin
        # paths remain absolute and fixed to this generation.
        return RuntimeHandle(self.artifact.identity, generation_id, root, executable, self.root.parent, env)

    def verify_files(self, root, *, ready):
        self.check()
        _no_links(root)
        expected = {entry['path']: entry for entry in self.data['files']}
        expected.update({entry['destination']: entry for entry in self.data['notices']})
        found = set()
        for folder, directories, filenames in os.walk(root, followlinks=False):
            self.check()
            for name in directories:
                _no_links(Path(folder) / name)
            for name in filenames:
                path = Path(folder) / name
                _no_links(path)
                relative = path.relative_to(root).as_posix()
                if relative == 'ready.json' and ready:
                    continue
                if relative not in expected:
                    raise _PreparationProblem('arquivo inesperado na geração')
                entry = expected[relative]
                if ('size' in entry and path.stat().st_size != entry['size']) or _digest_file(path, self.check) != entry['sha256']:
                    raise _PreparationProblem('arquivo da geração ausente ou alterado')
                found.add(relative)
        if found != set(expected):
            raise _PreparationProblem('geração incompleta')

    def probe(self, handle):
        def invoke(arguments):
            self.check()
            result = self.runner([str(handle.executable), *arguments], cwd=handle.cwd, env=handle.env,
                                 timeout=min(10, self.deadline-time.monotonic()), max_output=1024**2)
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
            _no_links(selector)
            if selector.stat().st_size > 16384:
                return None
            active = _read_json(selector)
            generation_id = active['generation_id']
            if (active['artifact_identity'] != self.artifact.identity or not isinstance(generation_id, str)
                    or not re.fullmatch(r'[0-9a-f]{32}', generation_id)):
                return None
            root = self.root / 'generations' / generation_id
            self.verify_files(root, ready=True)
            _no_links(root / 'ready.json')
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
                _no_links(destination)
                if entry.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if key not in expected or entry.file_size != expected[key]['size']:
                    raise _PreparationProblem('estrutura ZIP diferente do inventário')
                if total + entry.file_size > self.data['expanded_bytes_limit']:
                    raise _PreparationProblem('expansão acima do limite')
                destination.parent.mkdir(parents=True, exist_ok=True)
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
            destination.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as incoming, destination.open('xb') as outgoing:
                while chunk := incoming.read(65536):
                    self.check()
                    outgoing.write(chunk)

    @staticmethod
    def write_record(path, record):
        with path.open('x', encoding='utf-8') as stream:
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())

    def ensure(self, *, force_repair=False):
        self.deadline = time.monotonic() + 300
        try:
            _no_links(self.root)
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
                _no_links(generations)
                generations.mkdir(exist_ok=True)
                with tempfile.TemporaryDirectory(prefix='staging-', dir=self.root) as temporary:
                    temporary = Path(temporary)
                    archive = temporary / 'artifact.zip'
                    staging = temporary / 'tree'
                    staging.mkdir()
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
                    self.checkpoint('validated')
                    pending = self.root / ('.active-' + generation_id + '.tmp')
                    try:
                        self.write_record(pending, record)
                        self.check()
                        _no_links(self.root / 'active.json')
                        self.checkpoint('before_select')
                        os.replace(pending, self.root / 'active.json')
                        self.checkpoint('after_select')
                    finally:
                        if pending.exists():
                            _no_links(pending)
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
    check_platform()
    return RuntimeManager(progress=progress).ensure(force_repair=force_repair)
