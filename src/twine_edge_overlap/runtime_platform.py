"""Host facts and local filesystem/process conventions, independent of layout."""
from contextlib import contextmanager
from dataclasses import dataclass
import errno
import os
from pathlib import Path
import platform
import re
import shlex
import stat
import struct
import sys
import time


def normalize_arch(value):
    return {'amd64': 'x86_64', 'x86_64': 'x86_64', 'arm64': 'aarch64', 'aarch64': 'aarch64'}.get(value.lower(), value.lower())


@dataclass(frozen=True)
class HostEnvironment:
    os: str
    arch: str
    os_version: str = ''
    python_version: tuple = (3, 14)
    python_implementation: str = 'CPython'
    bits: int = 64
    distribution_id: str = ''
    distribution_version: str = ''
    build_id: str | None = None
    channel: str = ''
    libc_family: str = ''
    libc_version: str = ''
    loader: str = ''
    cpu_features: frozenset = frozenset()
    kernel_version: str = ''
    translated: bool = False
    cpu_variant: str = ''


def read_bounded(path, maximum=65536):
    with Path(path).open('rb') as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('arquivo de identidade excedeu limite')
    return data.decode('utf-8', errors='strict')


def parse_os_release(text):
    """Parse shell-like quoted values as data; never evaluate substitutions."""
    if len(text.encode('utf-8')) > 65536:
        raise ValueError('identidade excessiva')
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, separator, value = line.partition('=')
        if not separator or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key) or key in result:
            raise ValueError('identidade inválida ou duplicada')
        tokens = shlex.split(value, comments=True, posix=True)
        if len(tokens) > 1:
            raise ValueError('valor de identidade inválido')
        result[key] = tokens[0] if tokens else ''
    return result


def os_release():
    try:
        text = read_bounded('/etc/os-release')
    except FileNotFoundError:
        text = read_bounded('/usr/lib/os-release')
    return parse_os_release(text)


def _elf_loader(path):
    """Read only bounded ELF64 program headers of the running interpreter."""
    try:
        with Path(path).open('rb') as stream:
            header = stream.read(64)
            if len(header) != 64 or header[:5] != b'\x7fELF\x02' or header[5] not in (1, 2):
                return ''
            endian = '<' if header[5] == 1 else '>'
            offset = struct.unpack_from(endian + 'Q', header, 32)[0]
            size, count = struct.unpack_from(endian + 'HH', header, 54)
            if size != 56 or count > 128 or offset > 1024**2:
                return ''
            for index in range(count):
                stream.seek(offset + index * size)
                entry = stream.read(size)
                if len(entry) != size:
                    return ''
                if struct.unpack_from(endian + 'I', entry)[0] == 3:
                    start, length = struct.unpack_from(endian + 'Q', entry, 8)[0], struct.unpack_from(endian + 'Q', entry, 32)[0]
                    if length > 4096 or start > 16 * 1024**2:
                        return ''
                    stream.seek(start)
                    value = stream.read(length).rstrip(b'\0').decode('utf-8')
                    return value if value.startswith('/') else ''
    except (OSError, ValueError, struct.error):
        pass
    return ''


def _mac_translated():
    import ctypes
    value = ctypes.c_int()
    size = ctypes.c_size_t(ctypes.sizeof(value))
    libc = ctypes.CDLL(None)
    return libc.sysctlbyname(b'sysctl.proc_translated', ctypes.byref(value), ctypes.byref(size), None, 0) == 0 and value.value == 1


def _windows_architecture():
    """Use native machine facts rather than an emulated process environment."""
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    query = kernel.IsWow64Process2
    query.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.USHORT), ctypes.POINTER(wintypes.USHORT))
    query.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    process, native = wintypes.USHORT(), wintypes.USHORT()
    if not query(kernel.GetCurrentProcess(), ctypes.byref(process), ctypes.byref(native)):
        return '', True
    names = {0x014c: 'x86', 0x8664: 'x86_64', 0xaa64: 'aarch64'}
    return names.get(process.value or native.value, ''), bool(process.value)


def _alma_cpu_variant(identity, arch, *, runner=None):
    """Recognize the installed release build, not the CPU's maximum instruction set."""
    version=identity.get('VERSION_ID','')
    if identity.get('ID')!='almalinux' or not re.fullmatch(r'10\.\d+',version) or arch!='x86_64':
        return ''
    from .engines.process import run_bounded, ProcessLimitError
    runner=runner or run_bounded
    try:
        result=runner(['/usr/bin/rpm','--query','--queryformat','%{ARCH}\t%{VERSION}\n','almalinux-release'],
                      timeout=1,max_output=65536,env={'LC_ALL':'C','LANG':'C','PATH':''},cwd='/')
        match=re.fullmatch(rb'(x86_64|x86_64_v2)\t(10\.\d+)\n?',result.stdout)
        if result.returncode or not match or match[2].decode('ascii')!=version:
            return ''
        return 'x86-64-v2' if match[1]==b'x86_64_v2' else 'distribution-default'
    except (OSError,ValueError,ProcessLimitError):
        return ''


def detect_host():
    system = {'win32': 'windows', 'darwin': 'darwin'}.get(sys.platform, 'linux' if sys.platform.startswith('linux') else sys.platform)
    facts = dict(os=system, arch=normalize_arch(platform.machine()),
                 python_version=tuple(sys.version_info[:2]), python_implementation=platform.python_implementation(),
                 bits=struct.calcsize('P') * 8, kernel_version=platform.release())
    if system == 'windows':
        version = sys.getwindowsversion()
        facts['os_version'] = ('11' if version.build >= 22000 else '10') if version.product_type == 1 else 'server'
        facts['build_id'] = str(version.build)
        facts['arch'], facts['translated'] = _windows_architecture()
    elif system == 'darwin':
        facts['os_version'] = platform.mac_ver()[0]
        facts['translated'] = _mac_translated()
    elif system == 'linux':
        try:
            identity = os_release()
        except (OSError, ValueError):
            identity = {}
        facts.update(distribution_id=identity.get('ID', ''), distribution_version=identity.get('VERSION_ID', ''),
                     os_version=identity.get('VERSION_ID', ''), build_id=identity.get('BUILD_ID'))
        facts['channel']={'lts':'stable'}.get(identity.get('RELEASE_TYPE'),identity.get('RELEASE_TYPE',''))
        facts['cpu_variant']=_alma_cpu_variant(identity,facts['arch'])
        loader = _elf_loader(sys.executable)
        family, version = platform.libc_ver()
        if family == 'glibc':
            facts.update(libc_family='glibc', libc_version=version)
        elif 'ld-musl-' in loader:
            from .engines.process import run_bounded, ProcessLimitError
            try:
                result = run_bounded([loader], timeout=1, max_output=65536, env={'LC_ALL': 'C', 'PATH': ''})
                match = re.search(rb'Version\s+(\d+\.\d+(?:\.\d+)?)', result.stdout + result.stderr)
                facts.update(libc_family='musl', libc_version=match[1].decode('ascii') if match else '')
            except (OSError, ProcessLimitError):
                facts.update(libc_family='musl')
        facts['loader'] = loader
        try:
            cpuinfo = read_bounded('/proc/cpuinfo', 1024**2)
            # Intersection prevents declaring a feature absent from another CPU core.
            groups = [frozenset(value.split()) for key, _, value in (line.partition(':') for line in cpuinfo.splitlines()) if key.strip() in ('flags', 'Features')]
            facts['cpu_features'] = frozenset.intersection(*groups) if groups else frozenset()
        except (OSError, ValueError):
            pass
    return HostEnvironment(**facts)


def cache_directory(host=None, *, environ=None, home=None):
    # Cache conventions need only the OS, not another classification/package query.
    host = host or HostEnvironment(os={'win32':'windows','darwin':'darwin'}.get(sys.platform,'linux'),arch='')
    env = os.environ if environ is None else environ
    home = Path.home() if home is None else Path(home)
    if host.os == 'windows':
        base = Path(env.get('LOCALAPPDATA') or home / 'AppData/Local')
    elif host.os == 'darwin':
        base = home / 'Library/Caches'
    else:
        candidate = Path(env.get('XDG_CACHE_HOME') or home / '.cache')
        base = candidate if candidate.is_absolute() else home / '.cache'
    base = base.absolute() if host.os == 'windows' else base.resolve()
    return base / 'DesembaracaTwine/runtimes/graphviz'


def assert_managed_path(path, root, *, private=True):
    """Check owned descendants, allowing a base canonicalized by its caller."""
    path, root = Path(path).absolute(), Path(root).absolute()
    if not path.is_relative_to(root):
        raise ValueError('caminho fora do cache gerenciado')
    current = path
    while True:
        try:
            info = current.lstat()
        except FileNotFoundError:
            info = None
        if info and (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError('link ou reparse point no cache gerenciado')
        if private and info and os.name != 'nt' and (info.st_uid != os.getuid() or info.st_mode & 0o022):
            raise ValueError('cache com proprietário/permissões inadequados')
        if current == root:
            return
        current = current.parent


def runtime_environment(executable, *, host_os=None, environ=None, plugin_directory=None):
    env = os.environ if environ is None else environ
    host_os = host_os or ('windows' if os.name == 'nt' else 'posix')
    keys = ('SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'USERPROFILE', 'LOCALAPPDATA') if host_os == 'windows' else ('HOME', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TMPDIR', 'TEMP', 'TMP')
    result = {key: env[key] for key in keys if key in env}
    result['PATH'] = str(Path(executable).parent)
    result['GVBINDIR'] = str(plugin_directory or Path(executable).parent)
    return result


class LockBusyError(TimeoutError):
    pass


@contextmanager
def preparation_lock(path, *, deadline, check):
    path = Path(path)
    flags = os.O_RDWR | os.O_CREAT
    if os.name != 'nt':
        flags |= getattr(os, 'O_NOFOLLOW', 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, 'r+b') as stream:
        if os.name == 'nt':
            import msvcrt
            # Windows permits locking beyond EOF. Initializing byte zero here
            # races another owner's byte-range lock and can fail before retry.
            def lock():
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            def unlock():
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            def lock(): fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            def unlock(): fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        until = min(deadline, time.monotonic() + 10)
        while True:
            check()
            try:
                lock()
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise
                if time.monotonic() >= until:
                    raise LockBusyError('outra preparação em andamento') from exc
                time.sleep(min(0.05, max(0, until - time.monotonic())))
        try:
            yield
        finally:
            unlock()
