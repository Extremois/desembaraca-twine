import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from common import fixture
from runtime_support import blocked_network,controlled_runtime
from twine_edge_overlap.application import run
from twine_edge_overlap.engines import graphviz
from twine_edge_overlap.engines.process import run_bounded,ProcessLimitError,ProcessResult
from twine_edge_overlap.errors import EngineError,BudgetError
from twine_edge_overlap.formats.profile import parse


class EngineFailureTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(blocked_network())
        self.enterContext(patch('twine_edge_overlap.application.ensure_runtime',side_effect=AssertionError('unexpected acquisition')))
        self.enterContext(patch.object(graphviz,'ensure_runtime',side_effect=AssertionError('unexpected acquisition')))

    def test_malformed_json_ids_and_nonfinite_coordinates(self):
        doc=parse(fixture())
        valid={'bb':'0,0,400,500','objects':[{'name':'n0','pos':'50,450'},{'name':'n1','pos':'350,50'}]}
        invalid=[b'not-json',b'[]',b'{}',b'{"bb":"NaN,0,400,500","objects":[]}']
        for names in (['n0'],['n0','n0'],['n0','extra']):
            invalid.append(json.dumps(dict(valid,objects=[{'name':n,'pos':'0,0'} for n in names])).encode())
        for pos in ('NaN,0','Infinity,0','1e50,0','0','0,0,0'):
            invalid.append(json.dumps(dict(valid,objects=[{'name':'n0','pos':pos},{'name':'n1','pos':'0,0'}])).encode())
        for data in invalid:
            with self.subTest(data=data),self.assertRaises(EngineError): graphviz.decode_layout(data,doc)

    def test_error_exit_and_output_limit_are_typed(self):
        doc=parse(fixture())
        with patch.object(graphviz,'run_bounded',return_value=ProcessResult(7,b'',b'failure')),self.assertRaises(EngineError):
            graphviz.layout(doc,time.monotonic()+30,runtime=controlled_runtime())
        with patch.object(graphviz,'run_bounded',side_effect=ProcessLimitError('limit')),self.assertRaises(BudgetError):
            graphviz.layout(doc,time.monotonic()+30,runtime=controlled_runtime())

    def test_timeout_and_combined_output_are_bounded(self):
        start=time.monotonic()
        with self.assertRaises(ProcessLimitError):
            run_bounded([sys.executable,'-c','import time;time.sleep(10)'],timeout=.2)
        self.assertLess(time.monotonic()-start,3)
        with self.assertRaises(ProcessLimitError):
            run_bounded([sys.executable,'-c','import sys;sys.stdout.write("x"*6000);sys.stderr.write("y"*6000)'],max_output=8192)

    def test_interrupt_reaps_child_without_shell(self):
        real_popen=subprocess.Popen
        children=[]
        def start(*args,**kwargs):
            self.assertIs(kwargs['shell'],False)
            child=real_popen(*args,**kwargs);children.append(child);return child
        with patch('twine_edge_overlap.engines.process.subprocess.Popen',side_effect=start),patch('twine_edge_overlap.engines.process.queue.Queue.get',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                run_bounded([sys.executable,'-c','import time;time.sleep(10)'])
        self.assertIsNotNone(children[0].poll())

    def test_invalid_motor_output_falls_back_to_valid_baseline(self):
        def malformed(doc,deadline): raise EngineError('JSON inválido controlado')
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'story.twee';source.write_bytes(fixture('crossing'))
            result=run(source,engine=malformed,runtime_provider=controlled_runtime)
            self.assertEqual(result.status,'limitações')
            self.assertEqual(result.path.read_bytes(),source.read_bytes())
            self.assertIn('JSON inválido',result.reason)
