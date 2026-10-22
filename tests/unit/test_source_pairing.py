import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

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

            result = self.pairing_tool.verify_pairing(cand_file, src_file, application_revision="c" * 40)
            self.assertTrue(result["pairing_valid"])

            with out_file.open("x", encoding="utf-8") as stream:
                json.dump(result, stream)

            # Attempting to overwrite existing receipt must fail
            with self.assertRaises(FileExistsError):
                with out_file.open("x", encoding="utf-8") as stream:
                    json.dump(result, stream)


if __name__ == "__main__":
    unittest.main()
