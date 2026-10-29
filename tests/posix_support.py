"""Simulated POSIX metadata/transport, never native engine qualification."""
from contextlib import contextmanager, ExitStack
from pathlib import Path
import os
import tempfile
from unittest.mock import patch
from runtime_support import synthetic_artifact, synthetic_runner, ControlledTransport, blocked_network
from twine_edge_overlap import runtime
from twine_edge_overlap.runtime_platform import HostEnvironment


@contextmanager
def private_test_directory():
    base=tempfile.gettempdir()
    if os.name=='nt' and not base.startswith('\\\\?\\'):
        base='\\\\?\\'+base
    with tempfile.TemporaryDirectory(dir=base) as folder:
        yield Path(folder)


@contextmanager
def simulated_runtime(system, **facts):
    artifact, payload = synthetic_artifact(system)
    descriptor = dict(id='simulated-'+system, os=system, arch='x86_64', abi=artifact.data['abi'],
                      minimum_os='15', minimum_libc='2.27', minimum_kernel='4.15',
                      build_variant=artifact.data['build_variant'], priority=100, cpu_requirements=[],
                      manifest_path='controlled.json', manifest_sha256='0'*64, qualification_evidence=['simulation'])
    values=dict(os=system, arch='x86_64', os_version='15.7' if system=='darwin' else '26.04',
                distribution_id='ubuntu' if system=='linux' else '', distribution_version='26.04',
                libc_family='glibc', libc_version='2.43', kernel_version='6.18')
    values.update(facts)
    host=HostEnvironment(**values)
    transport = ControlledTransport(payload)
    manager_type = runtime.RuntimeManager
    with private_test_directory() as root, ExitStack() as stack, blocked_network():
        def manager(**kwargs):
            return manager_type(cache_root=root/'cache', opener=transport, runner=synthetic_runner, **kwargs)
        for name, value in [('load_catalog', lambda:dict(artifacts=[descriptor])),
                            ('verified_manifest', lambda item:root/'controlled.json'),
                            ('load_manifest', lambda path=None:artifact),
                            ('load_support_matrix', lambda:dict(targets=[],evidence={})),
                            ('RuntimeManager', manager)]:
            stack.enter_context(patch.object(runtime,name,value))
        stack.enter_context(patch.object(runtime.runtime_platform,'detect_host',return_value=host))
        yield root, transport, host
