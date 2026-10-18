"""Native macOS signature/execution acceptance; not simulated by another host."""
import os
import sys
import unittest
from native_acceptance import InstalledCandidateAcceptance


@unittest.skipUnless(sys.platform=='darwin' and os.environ.get('TWINE_NATIVE_ACCEPTANCE')=='1',
                     'Requires explicit signed macOS candidate and existing native SDK; no approval from skip')
class MacCandidateAcceptanceTests(InstalledCandidateAcceptance,unittest.TestCase):
    pass
