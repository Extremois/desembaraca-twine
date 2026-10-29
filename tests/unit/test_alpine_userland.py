import importlib.util
import json
import unittest
from common import ROOT


class AlpineUserlandTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('alpine_userland',ROOT/'tools/runtime/check-alpine-userland.py')
        self.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.tool)
        self.lock=json.loads((ROOT/'tools/runtime/alpine-compatibility-images.json').read_bytes())

    def test_all_sixteen_slots_require_matching_pinned_image_os_python_and_cpu(self):
        self.assertEqual({(a,p) for a in ('3.21','3.22','3.23','3.24') for p in ('3.12','3.14')},
                         {(row['alpine'],row['python']) for row in self.lock['images']})
        self.assertEqual(8,len(self.lock['images']))
        for row in self.lock['images']:
            self.assertEqual({'x86_64','aarch64'},set(row['platforms']))
            for arch,pin in row['platforms'].items():
                with self.subTest(alpine=row['alpine'],python=row['python'],arch=arch):
                    facts=dict(identity=dict(ID='alpine',VERSION_ID=row['alpine']+'.0'),
                        implementation='CPython',python_minor=row['python'],machine=arch)
                    self.assertEqual(pin,self.tool.validate_slot(self.lock,row['alpine'],arch,row['python'],pin['reference'],facts))
                    for field,value in [('identity',dict(ID='ubuntu',VERSION_ID='24.04')),
                                        ('identity',dict(ID='alpine',VERSION_ID=row['alpine']+'0.0')),
                                        ('implementation','PyPy'),('python_minor','3.13'),
                                        ('machine','aarch64' if arch=='x86_64' else 'x86_64')]:
                        with self.assertRaises(ValueError):
                            self.tool.validate_slot(self.lock,row['alpine'],arch,row['python'],pin['reference'],dict(facts,**{field:value}))
                    with self.assertRaises(ValueError):
                        self.tool.validate_slot(self.lock,row['alpine'],arch,row['python'],'python:latest',facts)

    def test_unknown_release_and_duplicate_slot_cannot_select_a_fallback_image(self):
        row=self.lock['images'][0];pin=row['platforms']['x86_64']
        facts=dict(identity=dict(ID='alpine',VERSION_ID='3.21.0'),implementation='CPython',python_minor='3.12',machine='x86_64')
        with self.assertRaises(ValueError):
            self.tool.validate_slot(self.lock,'3.25','x86_64','3.12',pin['reference'],facts)
        self.lock['images'].append(row)
        with self.assertRaises(ValueError):
            self.tool.validate_slot(self.lock,row['alpine'],'x86_64',row['python'],pin['reference'],facts)
