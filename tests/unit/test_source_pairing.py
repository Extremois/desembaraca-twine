import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
from unittest.mock import patch

from common import ROOT
from unit.test_runtime_build_tools import tool


class SourcePairingTests(unittest.TestCase):
    def setUp(self):
        self.pairing_tool = tool("verify-source-pairing")
        self.candidate_sample = {
            "kind": "local-candidate-archive",
            "qualified": False,
            "artifact_id": "linux-glibc-x86_64",
            "platform": "linux",
            "artifact_arch": "x86_64",
            "abi": "glibc",
            "executable_sha256": "43ce8d686720467c21be91cab4b8f3b246baae49c2cfe293714ebdf8a82f5716",
            "provenance_sha256": "312e0d57ee7ef8df03c44d31140b9cd8eb07241938dac487f227567075f7c621",
            "archive": "candidate.zip",
            "archive_sha256": "f446b7718e94eafa9adc29953aa4f1f65e588d5ee10a80d973771c32e91d1e7f",
            "archive_bytes": 1234567,
            "inventory": "inventory.json",
            "inventory_sha256": "a" * 64,
            "file_count": 480
        }
        self.sources_sample = {
            "kind": "candidate-source-review-material",
            "approved": False,
            "artifact_id": "linux-glibc-x86_64",
            "executable_sha256": "43ce8d686720467c21be91cab4b8f3b246baae49c2cfe293714ebdf8a82f5716",
            "provenance_sha256": "312e0d57ee7ef8df03c44d31140b9cd8eb07241938dac487f227567075f7c621",
            "archive": "sources.tar.gz",
            "archive_sha256": "25e58c76a94135c80924500b170c0ad7ce0852e3d4911cdcd5b827cd86c0c93b",
            "archive_bytes": 68388251,
            "sdk_files": 18102,
            "file_count": 18175
        }

    def test_valid_pairing_generates_canonical_receipt(self):
        pairing = self.pairing_tool.pair_records(
            self.candidate_sample,
            self.sources_sample,
            application_revision="b" * 40
        )
        self.assertEqual(pairing["kind"], "corresponding-source-delivery-pairing")
        self.assertTrue(pairing["pairing_valid"])
        self.assertEqual(pairing["artifact_id"], "linux-glibc-x86_64")
        self.assertEqual(pairing["executable_sha256"], self.candidate_sample["executable_sha256"])
        self.assertEqual(pairing["provenance_sha256"], self.candidate_sample["provenance_sha256"])
        self.assertFalse(pairing["delivery_binding"]["active_catalog_promoted"])
        self.assertEqual(pairing["delivery_binding"]["status"], "unpromoted_pending_authorized_distribution")
        self.assertIn("lgpl_2_1_section_6_d", pairing["obligations"])

    def test_real_packers_produce_pairable_receipts(self):
        # Synthetic payloads exercise the producer contract, never native acceptance.
        from unit.test_candidate_archive import CandidateArchiveTests
        from unit.test_source_package import SourcePackageTests

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate, inventory, provenance, _ = CandidateArchiveTests().fixture(root)
            candidate_record = json.loads(provenance.read_bytes())
            source_fixture = SourcePackageTests()
            source_fixture.setUp()
            graphviz, sdk, provenance, source_lock, sdk_lock = source_fixture.fixture(root)
            source_record = json.loads(provenance.read_bytes())
            candidate_record.update(source=source_record['source'],
                                    native_os='linux', native_arch='x86_64',
                                    recipe_sha256=source_record['recipe_sha256'])
            candidate_record['sdk'].update(source_record['sdk'])
            provenance.write_text(json.dumps(candidate_record), encoding='utf-8')
            data = json.loads(inventory.read_bytes())
            data['provenance_sha256'] = hashlib.sha256(provenance.read_bytes()).hexdigest()
            inventory.write_text(json.dumps(data), encoding='utf-8')
            tool('pack-candidate').pack(candidate, inventory, provenance, root / 'binary')
            with patch.object(source_fixture.module, 'SOURCE_LOCK', source_lock), \
                    patch.object(source_fixture.module, 'SDK_LOCK', sdk_lock):
                source_fixture.module.pack(graphviz, sdk, provenance, root / 'sources')
            result = self.pairing_tool.verify_pairing(
                root / 'binary/candidate.json', root / 'sources/sources.json',
                root / 'binary/candidate.zip', root / 'sources/sources.tar.gz')
            self.assertTrue(result['pairing_valid'])
            self.assertEqual(result['archive_verification'], {'candidate': True, 'sources': True})
            self.assertFalse(result['delivery_binding']['active_catalog_promoted'])

    def test_mismatched_artifact_id_is_rejected(self):
        altered_sources = copy.deepcopy(self.sources_sample)
        altered_sources["artifact_id"] = "linux-glibc-aarch64"
        with self.assertRaises(ValueError) as ctx:
            self.pairing_tool.pair_records(self.candidate_sample, altered_sources)
        self.assertIn("Artifact ID mismatch", str(ctx.exception))

    def test_mismatched_executable_sha_is_rejected(self):
        altered_sources = copy.deepcopy(self.sources_sample)
        altered_sources["executable_sha256"] = "0" * 64
        with self.assertRaises(ValueError) as ctx:
            self.pairing_tool.pair_records(self.candidate_sample, altered_sources)
        self.assertIn("Executable SHA-256 mismatch", str(ctx.exception))

    def test_mismatched_provenance_sha_is_rejected(self):
        altered_sources = copy.deepcopy(self.sources_sample)
        altered_sources["provenance_sha256"] = "f" * 64
        with self.assertRaises(ValueError) as ctx:
            self.pairing_tool.pair_records(self.candidate_sample, altered_sources)
        self.assertIn("Provenance SHA-256 mismatch", str(ctx.exception))

    def test_invalid_receipt_kind_is_rejected(self):
        bad_cand = copy.deepcopy(self.candidate_sample)
        bad_cand["kind"] = "arbitrary-kind"
        with self.assertRaises(ValueError):
            self.pairing_tool.pair_records(bad_cand, self.sources_sample)

        bad_src = copy.deepcopy(self.sources_sample)
        bad_src["kind"] = "arbitrary-kind"
        with self.assertRaises(ValueError):
            self.pairing_tool.pair_records(self.candidate_sample, bad_src)

    def test_invalid_types_are_rejected_as_validation_errors(self):
        for key, values in {
            'artifact_id': [42, [], {}],
            'executable_sha256': [None, 42, []],
            'provenance_sha256': [None, 42, []],
            'archive_sha256': [None, 42, []],
            'archive_bytes': [True, 1.5, '12', 0, -1],
        }.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    candidate = dict(self.candidate_sample, **{key: value})
                    sources = dict(self.sources_sample, **{key: value})
                    with self.assertRaises(ValueError):
                        self.pairing_tool.pair_records(candidate, sources)

    def test_planned_urls_never_certify_distribution(self):
        pairing = self.pairing_tool.pair_records(
            self.candidate_sample, self.sources_sample,
            candidate_url='https://example.org/releases/v1/candidate.zip',
            sources_url='https://example.org/releases/v1/sources.tar.gz')
        self.assertEqual(pairing['delivery_binding']['status'],
                         'unpromoted_pending_authorized_distribution')
        self.assertEqual(pairing['archive_verification'], {'candidate': False, 'sources': False})

    def test_incomplete_or_unsafe_delivery_urls_and_revision_are_rejected(self):
        candidate_url = 'https://example.org/releases/v1/candidate.zip'
        for sources_url in (None, 'http://example.org/releases/v1/sources.tar.gz',
                            'https://other.org/releases/v1/sources.tar.gz',
                            'https://example.org/releases/v2/sources.tar.gz',
                            candidate_url, 'https://user:secret@example.org/releases/v1/sources.tar.gz',
                            'https://example.org/releases/v1/sources.tar.gz?token=secret',
                            'https://example.org/releases/v1/sources.tar.gz#fragment'):
            with self.subTest(sources_url=sources_url), self.assertRaises(ValueError):
                self.pairing_tool.pair_records(self.candidate_sample, self.sources_sample,
                                              candidate_url=candidate_url, sources_url=sources_url)
        with self.assertRaises(ValueError):
            self.pairing_tool.pair_records(self.candidate_sample, self.sources_sample,
                                          application_revision='main')

    def test_archive_disk_verification(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cand_zip = root / "candidate.zip"
            src_tar = root / "sources.tar.gz"

            cand_content = b"fake candidate zip data"
            cand_zip.write_bytes(cand_content)
            cand_receipt = copy.deepcopy(self.candidate_sample)
            cand_receipt["archive_sha256"] = hashlib.sha256(cand_content).hexdigest()
            cand_receipt["archive_bytes"] = len(cand_content)

            src_content = b"fake sources tar data"
            src_tar.write_bytes(src_content)
            src_receipt = copy.deepcopy(self.sources_sample)
            src_receipt["archive_sha256"] = hashlib.sha256(src_content).hexdigest()
            src_receipt["archive_bytes"] = len(src_content)

            # Valid match
            pairing = self.pairing_tool.pair_records(
                cand_receipt,
                src_receipt,
                candidate_archive=cand_zip,
                sources_archive=src_tar
            )
            self.assertTrue(pairing["pairing_valid"])
            self.assertEqual(pairing['archive_verification'], {'candidate': True, 'sources': True})

            src_tar.write_bytes(b'tampered sources')
            with self.assertRaisesRegex(ValueError, 'Sources archive on disk'):
                self.pairing_tool.pair_records(cand_receipt, src_receipt,
                                              candidate_archive=cand_zip, sources_archive=src_tar)
            src_tar.write_bytes(src_content)

            # Tampered candidate
            cand_zip.write_bytes(b"tampered data")
            with self.assertRaises(ValueError) as ctx:
                self.pairing_tool.pair_records(
                    cand_receipt,
                    src_receipt,
                    candidate_archive=cand_zip,
                    sources_archive=src_tar
                )
            self.assertIn("does not match receipt", str(ctx.exception))

    def test_cli_invocation_creates_receipt_and_prevents_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cand_file = root / "candidate.json"
            src_file = root / "sources.json"
            out_file = root / "pairing.json"

            cand_file.write_text(json.dumps(self.candidate_sample), encoding="utf-8")
            src_file.write_text(json.dumps(self.sources_sample), encoding="utf-8")

            command = [sys.executable, str(ROOT / 'tools/runtime/verify-source-pairing.py'),
                       '--candidate-receipt', str(cand_file), '--sources-receipt', str(src_file),
                       '--application-revision', 'c' * 40, '--output', str(out_file)]
            result = subprocess.run(command, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(out_file.read_bytes())['pairing_valid'])
            original = out_file.read_bytes()
            result = subprocess.run(command, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'already exists', result.stderr)
            self.assertEqual(out_file.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
