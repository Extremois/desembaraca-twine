from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch
from common import ROOT

from twine_edge_overlap.runtime_platform import (
    HostEnvironment, cache_directory, normalize_arch, parse_os_release,
    runtime_environment, assert_managed_path,
)


class PlatformTests(unittest.TestCase):
    def test_windows_server_keeps_product_identity_and_measured_build(self):
        from types import SimpleNamespace
        from twine_edge_overlap import runtime_platform as platform_module
        version=SimpleNamespace(build=26100,product_type=3)
        with patch.object(platform_module.sys,'platform','win32'), \
             patch.object(platform_module.sys,'getwindowsversion',return_value=version,create=True), \
             patch.object(platform_module,'_windows_architecture',return_value=('x86_64',False)):
            host=platform_module.detect_host()
        self.assertEqual((host.os,host.os_version,host.build_id),('windows','server','26100'))

    def test_alma_image_variant_comes_from_bounded_release_package_query(self):
        from twine_edge_overlap.runtime_platform import _alma_cpu_variant
        from twine_edge_overlap.engines.process import ProcessResult
        identity=dict(ID='almalinux',VERSION_ID='10.2')
        for payload,expected in ((b'x86_64\t10.2\n','distribution-default'),(b'x86_64_v2\t10.2\n','x86-64-v2'),(b'x86_64_v2\t10.1\n',''),(b'x86_64\t10.2\nx86_64_v2\t10.2\n','')):
            calls=[]
            def query(argv,**kwargs):
                calls.append((argv,kwargs))
                return ProcessResult(0,payload,b'')
            self.assertEqual(_alma_cpu_variant(identity,'x86_64',runner=query),expected)
            self.assertEqual(calls[0][0][0],'/usr/bin/rpm')
            self.assertEqual(calls[0][0][-1],'almalinux-release')
            self.assertLessEqual(calls[0][1]['timeout'],1)
            self.assertLessEqual(calls[0][1]['max_output'],65536)
            self.assertEqual(calls[0][1]['env']['PATH'],'')
        def missing(*a,**k):raise FileNotFoundError()
        self.assertEqual(_alma_cpu_variant(identity,'x86_64',runner=missing),'')

    def test_arch_and_data_parser_do_not_execute_shell(self):
        self.assertEqual(normalize_arch('AMD64'), 'x86_64')
        self.assertEqual(normalize_arch('arm64'), 'aarch64')
        self.assertEqual(parse_os_release('ID=ubuntu\nVERSION_ID="24.04"\nX="$(touch /never)"')['X'], '$(touch /never)')
        with self.assertRaises(ValueError):
            parse_os_release('ID=ubuntu\nID=arch')

    def test_cache_ignores_relative_xdg_and_preserves_windows(self):
        home = Path(tempfile.gettempdir()) / 'profile'
        linux = HostEnvironment(os='linux', arch='x86_64')
        self.assertEqual(cache_directory(linux, environ={'XDG_CACHE_HOME': 'relative'}, home=home), home.resolve() / '.cache/DesembaracaTwine/runtimes/graphviz')
        self.assertEqual(cache_directory(linux, environ={'XDG_CACHE_HOME': str(home / 'cache')}, home=home), home.resolve() / 'cache/DesembaracaTwine/runtimes/graphviz')
        self.assertEqual(cache_directory(HostEnvironment(os='darwin', arch='aarch64'), environ={}, home=home), home.resolve() / 'Library/Caches/DesembaracaTwine/runtimes/graphviz')
        self.assertEqual(cache_directory(HostEnvironment(os='windows', arch='x86_64'), environ={'LOCALAPPDATA': str(home)}, home=home), home / 'DesembaracaTwine/runtimes/graphviz')
        with patch('twine_edge_overlap.runtime_platform.detect_host',side_effect=AssertionError('cache repeated classification')):
            self.assertEqual(cache_directory(environ={},home=home).name,'graphviz')

    def test_child_environment_does_not_inherit_loader_overrides(self):
        parent = {'HOME': '/home/example', 'LANG': 'C.UTF-8', 'LD_PRELOAD': '/bad', 'DYLD_LIBRARY_PATH': '/bad', 'GVBINDIR': '/bad', 'PATH': '/bad'}
        before = parent.copy()
        env = runtime_environment(Path('/private/bin/dot'), host_os='linux', environ=parent)
        self.assertEqual(env['PATH'], str(Path('/private/bin')))
        self.assertEqual(env['GVBINDIR'], str(Path('/private/bin')))
        self.assertNotIn('LD_PRELOAD', env)
        self.assertNotIn('DYLD_LIBRARY_PATH', env)
        self.assertEqual(parent, before)

    @unittest.skipIf(os.name == 'nt', 'POSIX symlink semantics; covered natively on POSIX')
    def test_managed_links_rejected_but_trusted_base_can_be_alias(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            real = base / 'real'
            real.mkdir()
            alias = base / 'alias'
            alias.symlink_to(real, target_is_directory=True)
            root = alias.resolve() / 'managed'
            root.mkdir()
            assert_managed_path(root / 'new', root)
            (root / 'escape').symlink_to(base, target_is_directory=True)
            with self.assertRaises(ValueError):
                assert_managed_path(root / 'escape/file', root)

