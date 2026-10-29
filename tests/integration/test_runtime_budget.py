from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import fixture
from runtime_support import blocked_network,controlled_runtime
from twine_edge_overlap.application import run
from twine_edge_overlap.errors import DependencyError


class RuntimeBudgetTests(unittest.TestCase):
    def test_snapshot_classification_consumes_processing_allowance(self):
        from dataclasses import replace
        clock=[100.0]
        seen=[]
        def prepare():
            clock[0]+=50
            return replace(controlled_runtime(),classification_seconds=5)
        def engine(document,deadline):
            seen.append(deadline)
            return {node.id:(node.x,node.y) for node in document.nodes}
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee'
            source.write_bytes(fixture('crossing'))
            with patch('twine_edge_overlap.application.time.monotonic',side_effect=lambda:clock[0]):
                run(source,engine=engine,runtime_provider=prepare,seconds=10)
        self.assertEqual(seen,[155.0])

    def test_application_prepares_once_and_passes_the_resolved_handle(self):
        handle=controlled_runtime()
        seen=[]
        def layout(document,deadline,*,runtime):
            seen.append(runtime)
            return {node.id:(node.x,node.y) for node in document.nodes}
        with tempfile.TemporaryDirectory() as folder,blocked_network():
            source=Path(folder)/'story.twee'
            source.write_bytes(fixture('crossing'))
            with patch('twine_edge_overlap.application.ensure_runtime',return_value=handle) as prepare,patch('twine_edge_overlap.application.graphviz.layout',side_effect=layout):
                run(source)
            prepare.assert_called_once()
            self.assertEqual(seen,[handle])

    def test_preparation_is_excluded_but_read_time_stays_consumed(self):
        clock=[100.0]
        seen=[]
        def snapshot(source):
            clock[0]+=2
            return source.read_bytes()
        def prepare():
            clock[0]+=50
            return object()
        def engine(document,deadline):
            seen.append((clock[0],deadline))
            return {node.id:(node.x,node.y) for node in document.nodes}
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee'
            source.write_bytes(fixture('crossing'))
            with patch('twine_edge_overlap.application.time.monotonic',side_effect=lambda:clock[0]),patch('twine_edge_overlap.application.snapshot',side_effect=snapshot):
                run(source,engine=engine,runtime_provider=prepare,seconds=10)
        self.assertEqual(seen,[(152.0,160.0)])

    def test_preparation_failure_is_not_baseline_fallback_even_when_clean(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee'
            original=fixture('clean')
            source.write_bytes(original)
            with self.assertRaises(DependencyError):
                run(source,runtime_provider=lambda:(_ for _ in ()).throw(DependencyError('offline')))
            self.assertEqual(source.read_bytes(),original)
            self.assertEqual(list(Path(folder).iterdir()),[source])
