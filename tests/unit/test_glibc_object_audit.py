import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from common import ROOT


def tool():
    spec=importlib.util.spec_from_file_location('glibc_object_audit',ROOT/'tools/runtime/audit-glibc-objects.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


class GlibcObjectAuditTests(unittest.TestCase):
    def test_member_observation_requires_exact_bytes_and_cache_containment(self):
        module=tool()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cache=root/'cache';(cache/'o/hash').mkdir(parents=True)
            obj=cache/'o/hash/source.o';obj.write_bytes(b'object')
            members={str(obj):dict(sha256=hashlib.sha256(b'object').hexdigest())}
            self.assertEqual(module.observed_member(str(obj),members,cache),obj.resolve())
            obj.write_bytes(b'changed')
            with self.assertRaises(ValueError):module.observed_member(str(obj),members,cache)
            outside=root/'outside.o';outside.write_bytes(b'object')
            members[str(outside)]=members[str(obj)]
            with self.assertRaises(ValueError):module.observed_member(str(outside),members,cache)
            with self.assertRaises(ValueError):module.observed_member('relative.o',members,cache)

    def test_sdk_selection_refuses_other_variants_missing_startup_and_ambiguous_inputs(self):
        module=tool()
        record=dict(completed=True,artifact_id='linux-glibc-x86_64',linkage=dict(inputs=[
            dict(path='/cache/o/hash/crt1.o',scope='sdk'),dict(path='/cache/o/hash/libc_nonshared.a',scope='sdk')]))
        self.assertEqual(set(module.sdk_inputs(record)),{'crt1.o','libc_nonshared.a'})
        for changed in (dict(record,artifact_id='linux-musl-x86_64'),dict(record,completed=False),
                        dict(record,linkage=dict(inputs=record['linkage']['inputs'][1:])),
                        dict(record,linkage=dict(inputs=record['linkage']['inputs']+[dict(path='/other/crt1.o',scope='sdk')]))):
            with self.subTest(record=changed),self.assertRaises(ValueError):module.sdk_inputs(changed)
