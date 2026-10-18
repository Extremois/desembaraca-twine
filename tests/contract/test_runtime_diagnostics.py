import errno
import unittest
from common import ROOT
from twine_edge_overlap.errors import execution_diagnostic


class RuntimeDiagnosticTests(unittest.TestCase):
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
