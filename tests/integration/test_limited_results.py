from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import fixture
from runtime_support import blocked_network,controlled_runtime
from twine_edge_overlap.application import run
from twine_edge_overlap.domain.model import Metrics
from twine_edge_overlap.domain.result import classify
from twine_edge_overlap.errors import BudgetError
from twine_edge_overlap.formats.profile import parse,verify


class LimitedResultsTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(blocked_network())
        self.enterContext(patch('twine_edge_overlap.application.ensure_runtime',side_effect=AssertionError('unexpected acquisition')))

    def execute(self,engine,case='coincident',**kwargs):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'input.twee'
            original=fixture(case)
            source.write_bytes(original)
            result=run(source,engine=engine,runtime_provider=controlled_runtime,**kwargs)
            self.assertEqual(source.read_bytes(),original)
            verify(parse(original),parse(result.path.read_bytes()))
            self.assertTrue(all(a<=b for a,b in zip(result.after.values,result.before.values)))
            return result

    def test_result_states_include_nodes_and_traversals(self):
        self.assertEqual(classify(Metrics(0,0,0)),'sucesso')
        for values in ((1,0,0),(0,1,0),(0,0,1)):
            self.assertEqual(classify(Metrics(*values)),'limitações')
        self.assertEqual(classify(None,valid=False),'falha')
        self.assertEqual(classify(Metrics(0,0,0),opaque=True),'limitações')

    def test_partial_improvement(self):
        def partial(doc,deadline):
            positions={n.id:(n.x,n.y) for n in doc.nodes}
            positions['P2']=(500,1000)
            return positions
        result=self.execute(partial)
        self.assertEqual(result.status,'limitações')
        self.assertNotEqual(result.before,result.after)
        self.assertIn('parcial',result.reason.lower())

    def test_no_improvement_retains_baseline_and_says_so(self):
        result=self.execute(lambda doc,deadline:{n.id:(n.x,n.y) for n in doc.nodes})
        self.assertEqual(result.before,result.after)
        self.assertIn('nenhuma melhoria',result.reason.lower())

    def test_regressive_candidate_is_rejected(self):
        result=self.execute(lambda doc,deadline:{n.id:(500,500) for n in doc.nodes},case='crossing')
        self.assertEqual(result.before,result.after)
        self.assertIn('regressão',result.reason.lower())

    def test_motor_timeout_has_valid_fallback(self):
        def timeout(doc,deadline): raise BudgetError('Timeout controlado')
        result=self.execute(timeout)
        self.assertEqual(result.status,'limitações')
        self.assertEqual(result.before,result.after)
        self.assertIn('Timeout controlado',result.reason)

    def test_only_nodes_or_traversals_remaining_prevent_success(self):
        for case in ('isolated_overlap','through_isolated'):
            with self.subTest(case=case):
                result=self.execute(lambda doc,deadline:{n.id:(n.x,n.y) for n in doc.nodes},case=case)
                self.assertEqual(result.status,'limitações')
                self.assertEqual(result.after.edges,0)
                self.assertGreater(result.after.nodes+result.after.traversals,0)

    def test_global_budget_after_baseline_has_fallback(self):
        clock=[0.]
        def late(doc,deadline):
            clock[0]=10.
            return {n.id:(n.x+10,n.y) for n in doc.nodes}
        with patch('twine_edge_overlap.application.time.monotonic',side_effect=lambda:clock[0]):
            result=self.execute(late,seconds=1)
        self.assertEqual(result.before,result.after)
        self.assertIn('prazo global',result.reason.lower())

    def test_budget_before_valid_baseline_is_failure_without_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'input.twee'
            source.write_bytes(fixture('crossing'))
            with self.assertRaises(BudgetError): run(source,seconds=0,runtime_provider=controlled_runtime)
            self.assertEqual(list(Path(folder).glob('*.layout*.twee')),[])
