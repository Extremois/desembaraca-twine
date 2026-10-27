"""Local packaging contracts; synthetic bytes never qualify native support."""
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from common import ROOT
from runtime_support import blocked_network
from unit.test_runtime_build_tools import tool


class CandidateArchiveTests(unittest.TestCase):
    def fixture(self, folder):
        root=Path(folder)
        candidate=root/'candidate'
        (candidate/'bin').mkdir(parents=True)
        (candidate/'notices').mkdir()
        files={'bin/dot':b'synthetic executable bytes','notices/COPYING':b'synthetic license fixture'}
        entries=[]
        for name,content in files.items():
            path=candidate/name
            path.write_bytes(content)
            mode=0o755 if name=='bin/dot' else 0o644
            path.chmod(mode)
            entries.append(dict(path=name,size=len(content),sha256=hashlib.sha256(content).hexdigest(),mode=mode))
        provenance=root/'provenance.json'
        record=dict(completed=True,artifact_id='linux-glibc-x86_64',
                    recipe=dict(id='linux-glibc-x86_64',os='linux',arch='x86_64',abi='glibc'),
                    recipe_sha256='a'*64,sdk=dict(environment_digest='b'*64),
                    executable_sha256=entries[0]['sha256'])
        provenance.write_text(json.dumps(record))
        inventory=root/'inventory.json'
        inventory.write_text(json.dumps(dict(kind='local-candidate-inventory',schema_version=1,
            qualification='inventory-only-not-qualified',artifact_id=record['artifact_id'],platform='linux',
            artifact_arch='x86_64',abi='glibc',minimum_libc='2.27',
            provenance_sha256=hashlib.sha256(provenance.read_bytes()).hexdigest(),
            executable_relative_path='bin/dot',files=entries,notices=[])))
        return candidate,inventory,provenance,files

    def test_archive_is_repeatable_exact_and_exclusive_without_network(self):
        packer=tool('pack-candidate')
        with tempfile.TemporaryDirectory() as folder,blocked_network():
            root=Path(folder)
            candidate,inventory,provenance,files=self.fixture(folder)
            before,cwd=dict(os.environ),Path.cwd()
            first=packer.pack(candidate,inventory,provenance,root/'first')
            second=packer.pack(candidate,inventory,provenance,root/'second')
            archive=root/'first/candidate.zip'
            self.assertEqual(archive.read_bytes(),(root/'second/candidate.zip').read_bytes())
            self.assertEqual(first['archive_sha256'],second['archive_sha256'])
            self.assertEqual(first['archive_sha256'],hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertFalse(first['qualified'])
            self.assertEqual(first['executable_sha256'], hashlib.sha256(files['bin/dot']).hexdigest())
            self.assertNotIn('url',first)
            self.assertEqual((root/'first/inventory.json').read_bytes(),inventory.read_bytes())
            with zipfile.ZipFile(archive) as incoming:
                self.assertEqual(incoming.namelist(),sorted(files))
                for name,content in files.items():
                    self.assertEqual(incoming.read(name),content)
                    entry=incoming.getinfo(name)
                    self.assertEqual(entry.date_time,(1980,1,1,0,0,0))
                    self.assertEqual(stat.S_IMODE(entry.external_attr>>16),0o755 if name=='bin/dot' else 0o644)
            with self.assertRaises(FileExistsError):packer.pack(candidate,inventory,provenance,root/'first')
            self.assertEqual(archive.read_bytes(),(root/'second/candidate.zip').read_bytes())
            self.assertEqual(os.environ,before)
            self.assertEqual(Path.cwd(),cwd)

    def test_changed_or_uninventoried_files_fail_before_output_creation(self):
        packer=tool('pack-candidate')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            candidate,inventory,provenance,files=self.fixture(folder)
            binary=candidate/'bin/dot'
            binary.write_bytes(b'changed')
            with self.assertRaises(ValueError):packer.pack(candidate,inventory,provenance,root/'bad')
            self.assertFalse((root/'bad').exists())
            binary.write_bytes(files['bin/dot'])
            extra=candidate/'unexpected'
            extra.write_bytes(b'uninventoried')
            with self.assertRaises(ValueError):packer.pack(candidate,inventory,provenance,root/'bad')
            self.assertFalse((root/'bad').exists())
            extra.unlink()
            if os.name!='nt':
                extra.symlink_to(provenance)
                with self.assertRaises(ValueError):packer.pack(candidate,inventory,provenance,root/'bad')
                self.assertFalse((root/'bad').exists())

    def test_archive_limit_includes_zip_headers_and_no_final_file_is_published(self):
        packer=tool('pack-candidate')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            candidate,inventory,provenance,_=self.fixture(folder)
            with patch.object(packer,'MAX_ARCHIVE_BYTES',128),self.assertRaises(ValueError):
                packer.pack(candidate,inventory,provenance,root/'limited')
            self.assertFalse((root/'limited/candidate.zip').exists())
            self.assertFalse((root/'limited/candidate.json').exists())

    def test_mutation_during_copy_is_detected_before_archive_publication(self):
        packer=tool('pack-candidate')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            candidate,inventory,provenance,_=self.fixture(folder)
            original=zipfile.ZipFile.open
            def change(archive,name,mode='r',*args,**kwargs):
                if mode=='w' and getattr(name,'filename',name)=='bin/dot':
                    (candidate/'bin/dot').write_bytes(b'changed during copy')
                return original(archive,name,mode,*args,**kwargs)
            with patch.object(zipfile.ZipFile,'open',change),self.assertRaises(ValueError):
                packer.pack(candidate,inventory,provenance,root/'raced')
            self.assertFalse((root/'raced/candidate.zip').exists())
            self.assertFalse((root/'raced/candidate.json').exists())
