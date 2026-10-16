import copy
import hashlib
import io
import stat
import ssl
import unittest
import urllib.error
import urllib.request
import zipfile
from unittest.mock import patch
from common import ROOT
from twine_edge_overlap import runtime
from twine_edge_overlap.errors import DependencyError
from runtime_support import synthetic_artifact,synthetic_runner,ControlledTransport,isolated_cache,archive_bytes,ControlledResponse,blocked_network


class ArchiveSafetyTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(blocked_network())

    def rejected(self,artifact,data):
        artifact=runtime.Artifact(copy.deepcopy(artifact.data))
        artifact.data['archive_sha256']=hashlib.sha256(data).hexdigest()
        with isolated_cache() as root:
            with self.assertRaises(DependencyError):
                runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(data),runner=lambda *a,**k:self.fail('unsafe payload executed')).ensure()
            self.assertFalse(any(root.rglob('active.json')))

    def test_unsafe_member_names(self):
        artifact,_=synthetic_artifact()
        for name in ('../escape','/absolute','C:/drive','//server/share','dir\\file','name:ads','CON.txt','part./name','part /name','a/../../escape','a\x00b'):
            # ZipInfo truncates at NUL; that result still fails the pinned inventory.
            with self.subTest(name=name): self.rejected(artifact,archive_bytes({name:b'bad'}))

    def test_symlink_and_reparse_member_and_duplicate_case(self):
        artifact,_=synthetic_artifact()
        for attributes in ((stat.S_IFLNK|0o777)<<16,stat.FILE_ATTRIBUTE_REPARSE_POINT):
            data=io.BytesIO()
            with zipfile.ZipFile(data,'w') as archive:
                entry=zipfile.ZipInfo('bin/dot.exe')
                entry.external_attr=attributes
                archive.writestr(entry,b'controlled executable')
            self.rejected(artifact,data.getvalue())
        self.rejected(artifact,archive_bytes({'bin/dot.exe':b'controlled executable','BIN/DOT.EXE':b'controlled executable'}))

    def test_truncated_zip_and_real_transfer_and_expansion_limits(self):
        artifact,data=synthetic_artifact()
        self.rejected(artifact,b'not a zip')
        self.rejected(artifact,data[:-12])
        for key,value in (('archive_bytes_limit',10),('expanded_bytes_limit',1),('entry_limit',1)):
            changed=runtime.Artifact(copy.deepcopy(artifact.data))
            changed.data[key]=value
            with self.subTest(limit=key): self.rejected(changed,data)

    def test_redirect_rejects_downgrade_untrusted_host_and_credentials(self):
        from urllib.request import Request
        for url in ('http://gitlab.com/file','https://evil.invalid/file','https://user:secret@gitlab.com/file','https://gitlab.com:8443/file'):
            with self.subTest(url=url),self.assertRaises(ValueError):
                runtime._Redirects(['gitlab.com']).redirect_request(Request('https://gitlab.com/start'),None,302,'found',{},url)

    def test_final_origin_is_checked_even_with_custom_transport(self):
        artifact,data=synthetic_artifact()
        class Transport:
            def open(self,*args,**kwargs): return ControlledResponse(data,url='https://evil.invalid/file')
        with isolated_cache() as root,self.assertRaises(DependencyError):
            runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=Transport(),runner=synthetic_runner).ensure()

    def test_five_https_redirects_are_allowed_but_sixth_is_rejected(self):
        redirects=runtime._Redirects(['runtime.invalid'])
        request=urllib.request.Request('https://runtime.invalid/start')
        for index in range(5):
            request=redirects.redirect_request(request,None,302,'found',{},f'https://runtime.invalid/{index}')
            self.assertEqual(request.host,'runtime.invalid')
        with self.assertRaisesRegex(ValueError,'redirecionamento'):
            redirects.redirect_request(request,None,302,'found',{},'https://runtime.invalid/sixth')

    def test_tls_and_http_failures_preserve_the_previous_generation(self):
        errors=(urllib.error.URLError(ssl.SSLCertVerificationError('certificate rejected')),
                urllib.error.HTTPError('https://runtime.invalid/package',503,'unavailable',{},None))
        artifact,data=synthetic_artifact()
        for error in errors:
            with self.subTest(error=type(error).__name__),isolated_cache() as root:
                manager=runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(data),runner=synthetic_runner)
                previous=manager.ensure()
                selector=(manager.root/'active.json').read_bytes()
                manager.opener=ControlledTransport(error=error)
                with self.assertRaises(DependencyError) as result:
                    manager.ensure(force_repair=True)
                message=str(result.exception)
                self.assertIn('internet',message)
                self.assertIn('nenhuma cópia gerada',message)
                self.assertIn('Restabeleça',message)
                self.assertEqual((manager.root/'active.json').read_bytes(),selector)
                self.assertEqual(manager.ensure().generation_id,previous.generation_id)

    def test_received_bytes_are_limited_despite_false_content_length(self):
        artifact,data=synthetic_artifact()
        artifact.data['archive_bytes_limit']=len(data)-1
        class Transport:
            def open(self,*args,**kwargs):
                return ControlledResponse(data,headers={'Content-Length':'1'})
        with isolated_cache() as root:
            manager=runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=Transport(),runner=lambda *a,**k:self.fail('payload executed'))
            with self.assertRaisesRegex(DependencyError,'limite de transferência'):
                manager.ensure()
            self.assertFalse((manager.root/'active.json').exists())

    def test_expanded_stream_bytes_cannot_exceed_the_pinned_file_size(self):
        artifact,data=synthetic_artifact()
        real_open=zipfile.ZipFile.open
        def oversized(archive,member,*args,**kwargs):
            if isinstance(member,zipfile.ZipInfo) and member.filename=='bin/dot.exe':
                # Simulate a decompressor yielding more bytes than its metadata.
                return io.BytesIO(b'x'*(member.file_size+1))
            return real_open(archive,member,*args,**kwargs)
        with isolated_cache() as root,patch.object(zipfile.ZipFile,'open',oversized):
            manager=runtime.RuntimeManager(artifact=artifact,cache_root=root,opener=ControlledTransport(data),runner=lambda *a,**k:self.fail('payload executed'))
            with self.assertRaisesRegex(DependencyError,'limite real'):
                manager.ensure()
            self.assertFalse((manager.root/'active.json').exists())
