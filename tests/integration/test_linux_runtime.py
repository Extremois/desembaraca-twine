"""Run only with a real Linux candidate; skipped drivers never approve the matrix."""
import os
import sys
import unittest
from native_acceptance import InstalledCandidateAcceptance


@unittest.skipUnless(sys.platform.startswith('linux') and os.environ.get('TWINE_NATIVE_ACCEPTANCE')=='1',
                     'Requires explicit real Linux candidate and existing native SDK; no approval from skip')
class LinuxCandidateAcceptanceTests(InstalledCandidateAcceptance,unittest.TestCase):
    pass
