"""A local static inventory never invents a libc baseline or approves an audit."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from unit import test_candidate_archive
from unit.test_runtime_build_tools import tool
from twine_edge_overlap.runtime_platform import HostEnvironment


class StaticInventoryTests(unittest.TestCase):
    def fixture(self,folder):
        candidate,inventory,provenance,_=test_candidate_archive.CandidateArchiveTests().fixture(folder)
        verifier=tool('verify-artifact')
        record=json.loads(provenance.read_text())
        record['artifact_id']='linux-musl-x86_64'
        record['recipe'].update(id=record['artifact_id'],abi='musl',cmake=dict(CMAKE_EXE_LINKER_FLAGS='-static'))
        record['sdk']['facts']=dict(target_os='linux',target_arch='x86_64',target_libc_family='musl',static_linking=True)
        report=Path(folder)/'static-elf-inspection.txt'
        report.write_text('There is no dynamic section in this file.\n')
        record['static_elf_inspection']=dict(report_sha256=verifier.digest(report),no_interpreter=True,
            no_dynamic_section=True,no_needed_libraries=True,no_glibc_symbols=True)
        provenance.write_text(json.dumps(record))
        data=json.loads(inventory.read_text())
        data.update(artifact_id=record['artifact_id'],abi='musl',minimum_libc=None,
                    native_linkage='static-elf',provenance_sha256=verifier.digest(provenance))
        inventory.write_text(json.dumps(data))
        return candidate,inventory,provenance,record,data

    def test_measured_static_inventory_packages_without_libc_version_or_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate,inventory,provenance,record,data=self.fixture(folder)
            verifier=tool('verify-artifact')
            self.assertIsNone(verifier.load_inventory(inventory,provenance)['minimum_libc'])
            packed=tool('pack-candidate').pack(candidate,inventory,provenance,Path(folder)/'packed')
            self.assertFalse(packed['qualified'])
            audit=Path(folder)/'review.json';audit.write_text(json.dumps(dict(approved=False)))
            verify_tree=verifier.verify_tree
            with patch.object(verifier,'detect_host',return_value=HostEnvironment(os='linux',arch='x86_64')), \
                 patch.object(verifier,'verify_tree',side_effect=lambda root,data:verify_tree(root,data,enforce_modes=os.name!='nt')), \
                 patch.object(verifier,'run_bounded') as runner:
                with self.assertRaisesRegex(ValueError,'Reviewed audit'):
                    verifier.inspect(candidate,None,provenance,audit,inventory=inventory)
                runner.assert_not_called()

    def test_static_inventory_requires_exact_static_recipe_sdk_and_measurement(self):
        verifier=tool('verify-artifact')
        mutations=(lambda r:r['recipe'].update(abi='glibc'),
                   lambda r:r['recipe']['cmake'].update(CMAKE_EXE_LINKER_FLAGS='-static-libgcc'),
                   lambda r:r['sdk']['facts'].update(static_linking=False),
                   lambda r:r['static_elf_inspection'].update(no_interpreter=False))
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as folder:
                _,inventory,provenance,record,data=self.fixture(folder)
                mutation(record);provenance.write_text(json.dumps(record))
                data['provenance_sha256']=verifier.digest(provenance)
                with self.assertRaises(ValueError):verifier.inventory_data(data,provenance)
        with tempfile.TemporaryDirectory() as folder:
            _,inventory,provenance,record,data=self.fixture(folder)
            report=Path(folder)/'static-elf-inspection.txt'
            report.write_text('There is no dynamic section in this file.\nINTERP\n')
            with self.assertRaises(ValueError):verifier.inventory_data(data,provenance)
            record['static_elf_inspection']['report_sha256']=verifier.digest(report)
            provenance.write_text(json.dumps(record));data['provenance_sha256']=verifier.digest(provenance)
            with self.assertRaises(ValueError):verifier.inventory_data(data,provenance)

    @unittest.skipIf(os.name=='nt','Creation measures native POSIX modes')
    def test_static_creation_is_explicit_and_conflicting_baseline_is_refused(self):
        verifier=tool('verify-artifact')
        with tempfile.TemporaryDirectory() as folder:
            candidate,inventory,provenance,_,_=self.fixture(folder)
            with patch.object(verifier,'detect_host',return_value=HostEnvironment(os='linux',arch='x86_64')):
                with self.assertRaises(ValueError):verifier.create_inventory(candidate,provenance)
                with self.assertRaises(ValueError):
                    verifier.create_inventory(candidate,provenance,minimum_libc='1.2.5',static_elf=True)
                data=verifier.create_inventory(candidate,provenance,static_elf=True)
                self.assertIsNone(data['minimum_libc'])
                self.assertEqual(data['native_linkage'],'static-elf')
                data.pop('native_linkage')
                with self.assertRaises(ValueError):verifier.inventory_data(data,provenance)


if __name__=='__main__':unittest.main()
