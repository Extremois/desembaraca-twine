"""Isolated acquisition fixtures; helpers never access the real network."""
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile
import copy
import hashlib
import json
from twine_edge_overlap.engines.process import ProcessResult
from common import ROOT, fixture  # Reuse the existing synthetic story reader.


def archive_bytes(files):
    """Build a small controlled ZIP from relative names and byte contents."""
    output = BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()


class ControlledResponse(BytesIO):
    """Minimal urllib-like response for deterministic transfer tests."""

    def __init__(self, content, *, url='https://runtime.invalid/artifact.zip', headers=None):
        super().__init__(content)
        self.url = url
        self.headers = headers or {}
        self.status = 200

    def geturl(self):
        return self.url


class ControlledTransport:
    """Record requests and return a fresh controlled response per call."""

    def __init__(self, content=b'', *, error=None):
        self.content = content
        self.error = error
        self.calls = []

    def open(self, request, timeout=None):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return ControlledResponse(self.content)


@contextmanager
def isolated_cache():
    with tempfile.TemporaryDirectory(prefix='twine-runtime-test-') as directory:
        yield Path(directory)


@contextmanager
def blocked_network():
    """Fail visibly if a test attempts DNS or a socket connection."""
    with patch('socket.getaddrinfo', side_effect=AssertionError('unexpected DNS')), \
         patch('socket.socket.connect', side_effect=AssertionError('unexpected network')), \
         patch('socket.create_connection', side_effect=AssertionError('unexpected network')):
        yield


def synthetic_artifact(platform_name=None):
    from twine_edge_overlap import runtime
    content = {'bin/dot.exe': b'controlled executable', 'bin/config8': b'controlled config'}
    archive = archive_bytes(content)
    data = copy.deepcopy(runtime.load_manifest().data)
    data.update(url='https://runtime.invalid/artifact.zip', allowed_redirect_hosts=['runtime.invalid'],
                archive_sha256=hashlib.sha256(archive).hexdigest(), executable_relative_path='bin/dot.exe',
                files=[dict(path=name, size=len(value), sha256=hashlib.sha256(value).hexdigest()) for name,value in content.items()])
    data['notices'] = data['notices'][:1]
    if platform_name in ('linux', 'darwin'):
        # Controlled bytes only: this fixture never qualifies a native bundle.
        data.update(schema_version=2, platform=platform_name, artifact_arch='x86_64',
                    abi='glibc' if platform_name=='linux' else 'darwin', build_variant='controlled-test',
                    minimum_os='15' if platform_name=='darwin' else '0', minimum_libc='2.27', minimum_kernel='4.15')
        for entry in data['files']:
            entry['mode'] = 0o755 if entry['path']==data['executable_relative_path'] else 0o644
        data['_manifest_sha256'] = hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
    return runtime.Artifact(data), archive


def synthetic_runner(command, **kwargs):
    if '-V' in command:
        return ProcessResult(0,b'',b'dot - graphviz version 16.1.0')
    return ProcessResult(0,json.dumps({'bb':'0,0,100,200','objects':[{'name':'n0','pos':'50,150'},{'name':'n1','pos':'50,50'}]}).encode(),b'')


def active_artifact():
    """Metadata of the host's real qualified component, without another acquisition."""
    from twine_edge_overlap.runtime import load_manifest
    from twine_edge_overlap.runtime_catalog import load_catalog,select_artifact,verified_manifest
    from twine_edge_overlap.runtime_platform import detect_host
    return load_manifest(verified_manifest(select_artifact(load_catalog(),detect_host())))


def controlled_runtime():
    """Explicit context for fake engines/runners; its executable must never run."""
    from twine_edge_overlap.runtime import RuntimeHandle
    return RuntimeHandle('controlled-test-runtime','0'*32,ROOT,ROOT/'not-executed-dot.exe',ROOT,{'PATH':str(ROOT)})
