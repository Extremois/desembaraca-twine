import importlib.util
from pathlib import Path
import tempfile
import struct
import io
import tarfile
import unittest
import copy
from unittest.mock import patch
from common import ROOT


class NativeBaselineTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('native_baseline',ROOT/'.github/scripts/check-native-baseline.py')
        self.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.tool)

    def test_recovery_receipt_requires_every_failure_crash_and_concurrent_result(self):
        scenarios={name:dict(passed=True,offline_references=6,old_handle_usable=True)
            for name in ('download','disk_full','execution_denied','corrupt_archive','during_download','before_select','after_select','concurrent_first_use')}
        scenarios['concurrent_first_use'].update(acquisition_calls=1,same_generation=True)
        for name in ('during_download','before_select','after_select'):scenarios[name].update(exitcode=77,lock_reacquired=True)
        report=dict(passed=True,real_engine=True,scenarios=scenarios)
        self.tool.validate_recovery_report(report)
        for name in scenarios:
            bad=copy.deepcopy(report);del bad['scenarios'][name]
            with self.assertRaises(ValueError):self.tool.validate_recovery_report(bad)
        for name,field,value in (('download','offline_references',0),('before_select','lock_reacquired',False),
                                 ('after_select','exitcode',0),('concurrent_first_use','acquisition_calls',2)):
            bad=copy.deepcopy(report);bad['scenarios'][name][field]=value
            with self.assertRaises(ValueError):self.tool.validate_recovery_report(bad)

    def test_network_observation_requires_child_control_and_zero_corpus_socket_calls(self):
        spec=importlib.util.spec_from_file_location('observer',ROOT/'tools/runtime/observe-linux-network.py')
        observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
        control=observer.parse_trace('100 execve("/private/python", [], []) = 0\n'
            '101 execve("/private/python", [], []) = 0\n101 socket(AF_INET, SOCK_STREAM, 0) = 3\n'
            '101 connect(3, {sa_family=AF_INET}, 16) = -1 ECONNREFUSED (Connection refused)\n')
        corpus=observer.parse_trace('100 execve("/private/python", [], []) = 0\n'
            '102 execve("/cache/bin/dot", [], []) = 0\n')
        self.tool.validate_network_observation(control,corpus)
        for bad in (dict(control,network_syscalls={}),dict(control,successful_executables=['/private/python'])):
            with self.assertRaises(ValueError):self.tool.validate_network_observation(bad,corpus)
        for bad in (dict(corpus,network_syscalls=dict(socket=1)),
                    dict(corpus,successful_executables=['/private/python'])):
            with self.assertRaises(ValueError):self.tool.validate_network_observation(control,bad)

    def test_application_evidence_rejects_wrong_wheel_missing_cases_or_failed_cache(self):
        cases=[dict(case='case_'+str(i),known_resolvable=i<6) for i in range(13)]
        rows=[dict(case=r['case'],before=[1,1,1],after=[0,0,0]) for r in cases]
        flags=dict(acquisition_calls=1,offline_acquisition_calls=0,healthy_generation_reused=True,
                   final_destination_probe=True,probe_before_ready=True,external_unicode_paths=True,
                   real_engine=True,fixture_transport=True,executable_mode=0o755,generation_mode=0o700)
        report=dict(passed=True,qualified=False,python='3.12.15',arch='x86_64',engine_sha256='a'*64,
            wheel_sha256='b'*64,installed_package_verified=True,entrypoints_verified=True,
            observations=dict(explicit=dict(flags,cases=rows),automatic=dict(flags,cases=rows[:1])),cases=rows)
        self.tool.validate_application_report(report,'3.12.15','b'*64,'a'*64,cases)
        mutations=[dict(wheel_sha256='c'*64),dict(python='3.14.8'),dict(cases=rows[:12]),
                   dict(installed_package_verified=False),dict(entrypoints_verified=False)]
        for change in mutations:
            with self.assertRaises(ValueError):self.tool.validate_application_report(dict(report,**change),'3.12.15','b'*64,'a'*64,cases)
        for field,value in [('offline_acquisition_calls',1),('healthy_generation_reused',False)]:
            bad=copy.deepcopy(report);bad['observations']['explicit'][field]=value
            with self.assertRaises(ValueError):self.tool.validate_application_report(bad,'3.12.15','b'*64,'a'*64,cases)
        bad=copy.deepcopy(report);bad['cases'][0]['after']=[1,0,0]
        with self.assertRaises(ValueError):self.tool.validate_application_report(bad,'3.12.15','b'*64,'a'*64,cases)

    def test_private_python_archive_rejects_escape_links_special_files_and_expansion(self):
        spec=importlib.util.spec_from_file_location('python_probe',ROOT/'.github/scripts/probe-private-python.py')
        tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
        def member(name,kind=tarfile.REGTYPE,target='',size=0):
            row=tarfile.TarInfo(name);row.type=kind;row.linkname=target;row.size=size;return row
        good=[member('python',tarfile.DIRTYPE),member('python/bin/python3.12'),
              member('python/bin/python3',tarfile.SYMTYPE,'python3.12')]
        tool.validate_members(good)
        for rows in ([member('../escape')],[member('/python/file')],
                     [member('python/link',tarfile.SYMTYPE,'../../escape')],
                     [member('python/link',tarfile.SYMTYPE,'bin'),member('python/link/file')],
                     [member('python/fifo',tarfile.FIFOTYPE)],
                     [member('python/a'),member('python/a')],
                     [member('python/big',size=65*1024**2)]):
            with self.assertRaises(ValueError):tool.validate_members(rows)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);archive=root/'input.tar.gz'
            with tarfile.open(archive,'w:gz') as stream:
                row=member('python/bin/python3.12',size=4);row.mode=0o755
                stream.addfile(row,io.BytesIO(b'test'))
            tool.extract_private(archive,root/'private')
            self.assertEqual((root/'private/python/bin/python3.12').read_bytes(),b'test')

    def test_private_python_report_requires_both_exact_patches_and_unchanged_system(self):
        pins=[dict(minor='3.12',patch='3.12.15',sha256='a'*64),dict(minor='3.14',patch='3.14.8',sha256='b'*64)]
        rows=[dict(minor=p['minor'],archive_sha256=p['sha256'],facts=dict(python=p['patch'],implementation='CPython',
              arch='x86_64',bits=64,venv_active=True,gil_disabled=False,ssl_context=True,pip='test',ensurepip='test')) for p in pins]
        report=dict(passed=True,system_python_before='c'*64,system_python_after='c'*64,interpreters=rows)
        self.tool.validate_python_report(report,pins)
        for replacement in (dict(interpreters=rows[:1]),dict(system_python_after='d'*64),dict(passed=False)):
            with self.assertRaises(ValueError):self.tool.validate_python_report(dict(report,**replacement),pins)
        rows[1]['facts']['python']='3.14.0'
        with self.assertRaises(ValueError):self.tool.validate_python_report(report,pins)

    def test_host_kernel_wrong_distribution_or_unaccelerated_guest_cannot_approve_baseline(self):
        guest=dict(identity=dict(ID='ubuntu',VERSION_ID='18.04'),arch='x86_64',kernel='4.15.0-213-generic',glibc='glibc 2.27')
        self.tool.validate_baseline(guest,dict(enabled=True,present=True))
        for key,value in [('arch','aarch64'),('kernel','6.17.0-1022-azure'),('glibc','glibc 2.39'),
                          ('identity',dict(ID='ubuntu',VERSION_ID='24.04'))]:
            with self.assertRaises(ValueError):
                self.tool.validate_baseline(dict(guest,**{key:value}),dict(enabled=True,present=True))
        for kvm in ({'present':True,'enabled':False},{'present':False,'enabled':False}):
            with self.assertRaises(ValueError):self.tool.validate_baseline(guest,kvm)

    def test_focal_baseline_requires_its_own_identity_kernel_libc_and_kvm(self):
        guest=dict(identity=dict(ID='ubuntu',VERSION_ID='20.04'),arch='x86_64',
                   kernel='5.4.0-216-generic',glibc='glibc 2.31')
        kvm=dict(enabled=True,present=True)
        self.tool.validate_baseline(guest,kvm,'20.04')
        with self.assertRaises(ValueError):self.tool.validate_baseline(guest,kvm)
        for key,value in [('kernel','4.15.0-213-generic'),('kernel','6.17.0-1022-azure'),
                          ('glibc','glibc 2.27'),('arch','aarch64'),
                          ('identity',dict(ID='ubuntu',VERSION_ID='18.04'))]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                self.tool.validate_baseline(dict(guest,**{key:value}),kvm,'20.04')
        with self.assertRaises(ValueError):
            self.tool.validate_baseline(guest,dict(enabled=False,present=True),'20.04')
        with self.assertRaises(ValueError):self.tool.validate_baseline(guest,kvm,'22.04')

    def test_focal_image_pin_is_explicit_and_does_not_relax_bionic_budget(self):
        import json
        pin=json.loads((ROOT/'.github/native-images/ubuntu-20.04-amd64.json').read_bytes())
        self.tool.validate_pin(pin,'20.04')
        with self.assertRaises(ValueError):self.tool.validate_pin(pin)
        for key,value in [('url',pin['url'].replace('release-20250516','release')),
                          ('arch','aarch64'),('release','18.04'),('size',1024**3+1)]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.tool.validate_pin(dict(pin,**{key:value}),'20.04')
        with self.assertRaises(ValueError):self.tool.validate_pin(pin,'22.04')

    def test_candidate_source_binding_requires_full_revision_and_positive_run(self):
        self.tool.validate_candidate_source('a'*40,40565098269)
        for revision,run_id in [('main',40565098269),('a'*40,0),('a'*40,True),
                                ('a'*40,'40565098269'),(None,40565098269)]:
            with self.subTest(revision=revision,run_id=run_id),self.assertRaises(ValueError):
                self.tool.validate_candidate_source(revision,run_id)

    def test_jammy_profile_does_not_inherit_focal_or_host_identity(self):
        import json
        guest=dict(identity=dict(ID='ubuntu',VERSION_ID='22.04'),arch='x86_64',
                   kernel='5.15.0-198-generic',glibc='glibc 2.35')
        kvm=dict(enabled=True,present=True)
        self.tool.validate_baseline(guest,kvm,'22.04')
        pin=json.loads((ROOT/'.github/native-images/ubuntu-22.04-amd64.json').read_bytes())
        self.tool.validate_pin(pin,'22.04')
        for release in ('18.04','20.04','24.04'):
            with self.subTest(release=release),self.assertRaises(ValueError):
                self.tool.validate_baseline(guest,kvm,release)
        for key,value in [('kernel','5.4.0-216-generic'),('kernel','6.17.0-1022-azure'),
                          ('glibc','glibc 2.31'),('arch','aarch64'),
                          ('identity',dict(ID='ubuntu',VERSION_ID='20.04'))]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.tool.validate_baseline(dict(guest,**{key:value}),kvm,'22.04')
        for key,value in [('url',pin['url'].replace('release-20261020','release')),
                          ('arch','aarch64'),('release','20.04'),('size',1024**3+1)]:
            with self.subTest(pin_key=key),self.assertRaises(ValueError):
                self.tool.validate_pin(dict(pin,**{key:value}),'22.04')
        with self.assertRaises(ValueError):
            self.tool.validate_baseline(guest,dict(present=True,enabled=False),'22.04')

    def test_prepared_release_mismatch_fails_before_image_download_or_boot(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'input').mkdir()
            (root/'input/inputs.json').write_text(json.dumps(dict(abi='glibc',guest_release='20.04',
                engine_sha256=self.tool.ENGINE_SHA,candidate_revision='a'*40,candidate_run_id=40565098269)))
            with patch.dict(self.tool.os.environ,{'GITHUB_ACTIONS':'true'}), \
                    patch.object(self.tool.sys,'platform','linux'), \
                    patch.object(self.tool.platform,'machine',return_value='x86_64'), \
                    patch.object(self.tool.os,'geteuid',return_value=0,create=True), \
                    patch.object(self.tool.urllib.request,'urlopen') as download, \
                    patch.object(self.tool.subprocess,'Popen') as boot:
                with self.assertRaisesRegex(ValueError,'Prepared guest release'):
                    self.tool.execute(root,'18.04')
                download.assert_not_called();boot.assert_not_called()

    def test_resolute_requires_its_own_kernel_libc_image_and_cpu_variant(self):
        import json
        guest=dict(identity=dict(ID='ubuntu',VERSION_ID='26.04'),arch='x86_64',
                   kernel='7.0.0-38-generic',glibc='glibc 2.43')
        kvm=dict(enabled=True,present=True)
        self.tool.validate_baseline(guest,kvm,'26.04')
        pin=json.loads((ROOT/'.github/native-images/ubuntu-26.04-amd64.json').read_bytes())
        self.tool.validate_pin(pin,'26.04')
        for key,value in [('kernel','6.17.0-1022-azure'),('kernel','5.15.0-198-generic'),
                          ('glibc','glibc 2.35'),('arch','aarch64'),
                          ('identity',dict(ID='ubuntu',VERSION_ID='22.04'))]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.tool.validate_baseline(dict(guest,**{key:value}),kvm,'26.04')
        for key,value in [('url',pin['url'].replace('release-20261016','release')),
                          ('url',pin['url'].replace('amd64.img','amd64v3.img')),
                          ('arch','aarch64'),('release','22.04'),('size',1024**3+1)]:
            with self.subTest(pin_key=key),self.assertRaises(ValueError):
                self.tool.validate_pin(dict(pin,**{key:value}),'26.04')
        with self.assertRaises(ValueError):self.tool.validate_pin(pin,'22.04')
        with self.assertRaises(ValueError):
            self.tool.validate_baseline(guest,dict(present=True,enabled=False),'26.04')

    def test_image_pin_refuses_mutable_or_foreign_origins_and_excessive_downloads(self):
        pin=dict(url='https://cloud-images.ubuntu.com/releases/bionic/release-20230607/ubuntu-18.04-server-cloudimg-amd64.img',
                 size=405667840,sha256='8dd2e6b5e5aad20c3f836123b300cba9861249408cbb07c359145a65d6bab6b6')
        self.tool.validate_pin(pin)
        for key,value in [('url',pin['url'].replace('release-20230607','release')),
                          ('url',pin['url'].replace('cloud-images.ubuntu.com','example.com')),
                          ('size',1024**3),('sha256','not-a-hash')]:
            with self.assertRaises(ValueError):self.tool.validate_pin(dict(pin,**{key:value}))

    def test_stonking_cannot_inherit_resolute_or_another_cpu_image(self):
        import json
        guest=dict(identity=dict(ID='ubuntu',VERSION_ID='26.10'),arch='x86_64',
                   kernel='7.3.0-9-generic',glibc='glibc 2.44')
        kvm=dict(enabled=True,present=True)
        self.tool.validate_baseline(guest,kvm,'26.10')
        pin=json.loads((ROOT/'.github/native-images/ubuntu-26.10-amd64.json').read_bytes())
        self.tool.validate_pin(pin,'26.10')
        for key,value in [('kernel','7.0.0-38-generic'),('kernel','6.17.0-1022-azure'),
                          ('glibc','glibc 2.43'),('arch','aarch64'),
                          ('identity',dict(ID='ubuntu',VERSION_ID='26.04'))]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.tool.validate_baseline(dict(guest,**{key:value}),kvm,'26.10')
        for key,value in [('url',pin['url'].replace('release-20261025','release')),
                          ('url',pin['url'].replace('amd64.img','amd64v3.img')),
                          ('release','26.04'),('size',1024**3+1)]:
            with self.subTest(pin_key=key),self.assertRaises(ValueError):
                self.tool.validate_pin(dict(pin,**{key:value}),'26.10')
        with self.assertRaises(ValueError):self.tool.validate_pin(pin,'26.04')
        with self.assertRaises(ValueError):
            self.tool.validate_baseline(guest,dict(present=True,enabled=False),'26.10')

    def test_noble_requires_its_guest_kernel_instead_of_hosted_runner_identity(self):
        import json
        guest=dict(identity=dict(ID='ubuntu',VERSION_ID='24.04'),arch='x86_64',
                   kernel='6.8.0-147-generic',glibc='glibc 2.39')
        kvm=dict(enabled=True,present=True)
        self.tool.validate_baseline(guest,kvm,'24.04')
        pin=json.loads((ROOT/'.github/native-images/ubuntu-24.04-amd64.json').read_bytes())
        self.tool.validate_pin(pin,'24.04')
        for key,value in [('kernel','6.11.0-1018-azure'),('kernel','5.15.0-198-generic'),
                          ('glibc','glibc 2.35'),('arch','aarch64'),
                          ('identity',dict(ID='ubuntu',VERSION_ID='22.04'))]:
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.tool.validate_baseline(dict(guest,**{key:value}),kvm,'24.04')
        for key,value in [('url',pin['url'].replace('release-20261017','release')),
                          ('url',pin['url'].replace('amd64.img','arm64.img')),
                          ('release','22.04'),('size',1024**3+1)]:
            with self.subTest(pin_key=key),self.assertRaises(ValueError):
                self.tool.validate_pin(dict(pin,**{key:value}),'24.04')
        with self.assertRaises(ValueError):self.tool.validate_pin(pin,'22.04')
        with self.assertRaises(ValueError):
            self.tool.validate_baseline(guest,dict(present=True,enabled=False),'24.04')

    def test_guest_report_cannot_choose_a_path_on_the_runner(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.assertEqual(root/'clean.json',self.tool.guest_output_path(root,'clean','clean.json'))
            for reported in ('../secret.json','/etc/shadow','clean/../../secret.json','other.json'):
                with self.assertRaises(ValueError):self.tool.guest_output_path(root,'clean',reported)

    def test_musl_baseline_requires_its_own_bytes_and_static_elf_observation(self):
        guest=dict(abi='musl',engine_sha256='f4dfee4e052704b1a7efdb7b6a4c43583ccaa062aec800b76224dae24eb2b69b',
                   elf=dict(no_interpreter=True,no_dynamic_section=True),loader=None)
        self.tool.validate_engine_kind(guest,'musl')
        for replacement in (dict(abi='glibc'),dict(engine_sha256=self.tool.ENGINE_SHA),
                            dict(elf=dict(no_interpreter=False,no_dynamic_section=True)),dict(loader='/lib/ld-musl-x86_64.so.1')):
            with self.assertRaises(ValueError):self.tool.validate_engine_kind(dict(guest,**replacement),'musl')
        with self.assertRaises(ValueError):self.tool.validate_engine_kind(guest,'other')

    def test_guest_checks_real_elf_headers_before_executing_the_requested_abi(self):
        spec=importlib.util.spec_from_file_location('guest_probe',ROOT/'.github/scripts/probe-guest-baseline.py')
        tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
        data=bytearray(120);data[:6]=b'\x7fELF\x02\x01'
        struct.pack_into('<HH',data,16,2,62);struct.pack_into('<Q',data,32,64)
        struct.pack_into('<HH',data,54,56,1);struct.pack_into('<I',data,64,1)
        self.assertTrue(tool.inspect_binary(data,'musl')['no_interpreter'])
        with self.assertRaises(ValueError):tool.inspect_binary(data,'glibc')
        for kind in (2,3):
            modified=bytearray(data);struct.pack_into('<I',modified,64,kind)
            with self.assertRaises(ValueError):tool.inspect_binary(modified,'musl')
        modified=bytearray(data);struct.pack_into('<H',modified,18,183)
        with self.assertRaises(ValueError):tool.inspect_binary(modified,'musl')
        with self.assertRaises(ValueError):tool.inspect_binary(data[:64],'musl')
