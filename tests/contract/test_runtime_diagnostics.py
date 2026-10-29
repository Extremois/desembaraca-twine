import errno
import contextlib
import io
import unittest
from unittest.mock import patch
from common import ROOT
from twine_edge_overlap.errors import execution_diagnostic
from twine_edge_overlap import cli, runtime
from twine_edge_overlap.runtime_platform import HostEnvironment


class RuntimeDiagnosticTests(unittest.TestCase):
    def test_catalog_failure_reaches_cli_as_readable_portuguese_without_acquisition(self):
        out,err=io.StringIO(),io.StringIO()
        host=HostEnvironment(os='linux',arch='riscv64',libc_family='glibc',libc_version='2.39')
        with patch.object(runtime.runtime_platform,'detect_host',return_value=host), \
                patch.object(runtime,'RuntimeManager') as manager, \
                contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            code=cli.main(['--prepare-runtime'])
        self.assertEqual(code,1)
        self.assertEqual(out.getvalue(),'')
        self.assertIn('Não há componente qualificado compatível com o ambiente identificado',err.getvalue())
        self.assertIn('nenhuma cópia gerada',err.getvalue())
        self.assertIn('Consulte a matriz e os pré-requisitos',err.getvalue())
        manager.assert_not_called()

    def test_execution_errors_explain_impact_recovery_without_guessing_security_cause(self):
        for system in ('windows','linux','darwin'):
            for error in (PermissionError(errno.EACCES,'SECRET-PATH'),OSError(errno.ENOEXEC,'SECRET-PATH'),OSError(errno.ENOENT,'SECRET-PATH')):
                message=str(execution_diagnostic(error,system))
                self.assertIn('nenhuma cópia gerada',message)
                self.assertIn('--repair-runtime',message)
                for forbidden in ('SECRET-PATH','sudo','xattr','spctl','Instale Graphviz','Gatekeeper bloqueou'):
                    self.assertNotIn(forbidden,message)

    def test_uncertain_failure_does_not_claim_noexec_or_signature_failure(self):
        message=str(execution_diagnostic(OSError(errno.EIO,'PRIVATE'), 'darwin'))
        for forbidden in ('noexec','assinatura inválida','PRIVATE'):
            self.assertNotIn(forbidden,message)
