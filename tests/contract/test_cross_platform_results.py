import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from common import fixture
from runtime_support import controlled_runtime
from twine_edge_overlap import cli
from twine_edge_overlap.domain.model import Result,Metrics
from twine_edge_overlap.errors import DependencyError


class CrossPlatformResultTests(unittest.TestCase):
    def invoke(self,args):
        out,err=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):code=cli.main(args)
        return code,out.getvalue(),err.getvalue()

    def test_warning_is_independent_of_processing_result_codes(self):
        for status,code in (('sucesso',0),('limitações',2)):
            result=Result(status,Path.cwd()/'synthetic.layout.twee',Metrics(1,1,1),Metrics(0,0,0),'test')
            def process(path,progress):
                progress('Aviso: ambiente não validado; melhor esforço')
                return result
            with patch.object(cli,'run',side_effect=process):
                actual,out,err=self.invoke(['synthetic.twee'])
            self.assertEqual(actual,code)
            self.assertEqual(out.count(' -> '),3)
            self.assertIn(str(result.path),out)
            self.assertIn('melhor esforço',err)

    def test_dependency_failure_and_interrupt_have_no_partial_success(self):
        for error,code in ((DependencyError('Componente incompatível'),1),(KeyboardInterrupt(),130)):
            with patch.object(cli,'run',side_effect=error):
                actual,out,err=self.invoke(['synthetic.twee'])
            self.assertEqual(actual,code)
            self.assertNotIn('Arquivo gerado:',out)
            self.assertIn('Falha',err)

    def test_byte_node_edge_and_header_limits_precede_acquisition(self):
        base=fixture()
        too_many_nodes=base+b''.join(('\n:: Extra%d {"position":"0,0","size":"1,1"}\ntext\n'%i).encode() for i in range(101))
        too_many_edges=base.replace(b'[[P1]]',b'[[P1]]\n'*301)
        long_header=base.replace(b'"retain": true',b'"retain": "'+b'x'*9000+b'"')
        for data in (b'x'*(10*1024**2+1),too_many_nodes,too_many_edges,long_header):
            with tempfile.TemporaryDirectory() as folder:
                source=Path(folder)/'invalid.twee'
                source.write_bytes(data)
                with patch('twine_edge_overlap.application.ensure_runtime',side_effect=AssertionError('acquired invalid input')) as acquire:
                    code,out,err=self.invoke([str(source)])
                self.assertEqual(code,1,err)
                acquire.assert_not_called()
                self.assertEqual(list(Path(folder).iterdir()),[source])
