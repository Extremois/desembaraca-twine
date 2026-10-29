"""Security contracts using isolated caches and real bounded child processes.

Controlled transports/probes never qualify a native Graphviz artifact.
"""
from dataclasses import replace
from pathlib import Path
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from common import fixture
from runtime_support import (
    ControlledTransport, blocked_network, isolated_cache,
    synthetic_artifact, synthetic_runner,
)
from twine_edge_overlap import runtime
from twine_edge_overlap.engines.graphviz import build_dot
from twine_edge_overlap.engines.process import ProcessLimitError, run_bounded
from twine_edge_overlap.errors import DependencyError
from twine_edge_overlap.formats.profile import parse
from twine_edge_overlap.runtime_platform import read_bounded, runtime_environment
from twine_edge_overlap.runtime_snapshot import collect_snapshot


class SecurityLimitsTests(unittest.TestCase):
    def test_acquisition_request_and_probe_do_not_include_story_or_parent_secrets(self):
        artifact, archive = synthetic_artifact()
        transport = ControlledTransport(archive)
        calls = []
        def probe(command, **kwargs):
            calls.append((command, kwargs))
            return synthetic_runner(command, **kwargs)
        # The canary is synthetic and must never become a request header/env var.
        with patch.dict(os.environ, {'TWINE_PRIVATE_CANARY': 'private-test-value'}):
            before, cwd = dict(os.environ), Path.cwd()
            with isolated_cache() as root, blocked_network():
                manager = runtime.RuntimeManager(
                    artifact=artifact, cache_root=root, opener=transport, runner=probe)
                started = time.monotonic()
                first = manager.ensure()
                self.assertLessEqual(manager.deadline - started, 300.1)
                self.assertGreater(manager.deadline - started, 299)
                second = manager.ensure()
                self.assertEqual(first.generation_id, second.generation_id)
                self.assertEqual(len(transport.calls), 1)
                request, timeout = transport.calls[0]
                self.assertEqual(request.full_url, artifact.data['url'])
                self.assertEqual(request.get_method(), 'GET')
                self.assertIsNone(request.data)
                self.assertEqual(dict(request.header_items()), {'User-agent': 'DesembaracaTwine/0.1'})
                self.assertTrue(0 < timeout <= 30)
                for command, options in calls:
                    self.assertTrue(Path(command[0]).is_absolute())
                    self.assertTrue(0 < options['timeout'] <= 10)
                    self.assertEqual(options['max_output'], 1024**2)
                    self.assertNotIn('TWINE_PRIVATE_CANARY', options['env'])
            self.assertEqual(os.environ, before)
            self.assertEqual(Path.cwd(), cwd)

    def test_expired_preparation_cannot_acquire_or_select_a_generation(self):
        artifact, archive = synthetic_artifact()
        transport = ControlledTransport(archive)
        with isolated_cache() as root, blocked_network():
            manager = runtime.RuntimeManager(
                artifact=artifact, cache_root=root, opener=transport, runner=synthetic_runner)
            with self.assertRaisesRegex(DependencyError, 'Prazo'):
                manager.ensure(deadline=time.monotonic() - 1)
            self.assertEqual(transport.calls, [])
            self.assertFalse((manager.root / 'active.json').exists())

    def test_dot_contains_only_generated_ids_dimensions_and_edges(self):
        document = parse(fixture('crossing'))
        names = {node.id: 'PRIVATE_TITLE_' + str(index) + '";system(command)'
                 for index, node in enumerate(document.nodes)}
        private = replace(document,
                          nodes=tuple(replace(node, id=names[node.id]) for node in document.nodes),
                          edges=tuple((names[a], names[b]) for a, b in document.edges))
        dot = build_dot(private)
        self.assertEqual(dot, build_dot(document))
        self.assertNotIn('PRIVATE_TITLE', dot)
        self.assertNotIn('Synthetic passage', dot)
        self.assertNotIn('system(', dot)

    def test_loader_and_graphviz_overrides_are_not_inherited_on_any_os(self):
        parent = {name: 'private-test-value' for name in (
            'LD_PRELOAD', 'LD_LIBRARY_PATH', 'LD_AUDIT', 'DYLD_INSERT_LIBRARIES',
            'DYLD_LIBRARY_PATH', 'GVBINDIR', 'GV_FILE_PATH', 'DOTFONTPATH',
            'PYTHONPATH', 'HTTP_PROXY', 'HTTPS_PROXY', 'TWINE_PRIVATE_CANARY')}
        before = parent.copy()
        for system in ('windows', 'linux', 'darwin'):
            with self.subTest(system=system):
                env = runtime_environment(Path('/private/bin/dot'), host_os=system, environ=parent)
                self.assertEqual(set(env), {'PATH', 'GVBINDIR'})
                self.assertEqual(env['PATH'], str(Path('/private/bin')))
                self.assertEqual(env['GVBINDIR'], str(Path('/private/bin')))
        self.assertEqual(parent, before)

    def test_identity_file_is_bounded_and_rolling_never_receives_parent_env(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'identity'
            path.write_bytes(b'x' * 65536)
            self.assertEqual(len(read_bounded(path)), 65536)
            path.write_bytes(b'x' * 65537)
            with self.assertRaises(ValueError):
                read_bounded(path)
        meta = dict(distribution_id='arch', version_id=None, build_id=None,
                    channel='rolling', native_arch='x86_64', kernel_release='test')
        calls = []
        def query(command, **options):
            from twine_edge_overlap.engines.process import ProcessResult
            calls.append((command, options))
            return ProcessResult(0, b'public-test-package 1\n', b'')
        with blocked_network():
            result = collect_snapshot('pacman', lambda: meta, runner=query)
        self.assertTrue(result.known)
        self.assertEqual(len(calls), 2)
        for command, options in calls:
            self.assertEqual(command, ('/usr/bin/pacman', '--query', '--color', 'never'))
            self.assertEqual(options['env'], {'LC_ALL': 'C', 'LANG': 'C', 'PATH': ''})
            self.assertEqual(options['cwd'], '/')
            self.assertTrue(0 < options['timeout'] <= 5)
        self.assertEqual(calls[1][1]['max_output'], 8 * 1024**2 - len(b'public-test-package 1\n'))

    def test_production_runner_enforces_combined_default_output_limit(self):
        with self.assertRaisesRegex(ProcessLimitError, 'output'):
            run_bounded([sys.executable, '-I', '-c',
                         'import sys; sys.stdout.buffer.write(b"x"*(4*1024**2)); '
                         'sys.stdout.flush(); sys.stderr.buffer.write(b"y"*(4*1024**2+1))'])

    def test_production_runner_stops_a_real_child_at_deadline(self):
        started = time.monotonic()
        with self.assertRaisesRegex(ProcessLimitError, 'time'):
            run_bounded([sys.executable, '-I', '-c', 'import time; time.sleep(20)'], timeout=.2)
        self.assertLess(time.monotonic() - started, 4)
