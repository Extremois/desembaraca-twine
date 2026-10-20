import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from common import ROOT


def tool():
    spec=importlib.util.spec_from_file_location('public_sources',ROOT/'tools/runtime/verify-public-sources.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


class PublicSourcesTests(unittest.TestCase):
    def test_export_sources_are_recovered_without_actions_and_metadata_is_separate(self):
        module=tool()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def tar(path,files):
                with tarfile.open(path,'w:gz') as stream:
                    for name,data in files.items():
                        entry=tarfile.TarInfo(name);entry.size=len(data)
                        stream.addfile(entry,io.BytesIO(data))
            graphviz=root/'graphviz.tar.gz';graphviz.write_bytes(b'fixture upstream archive')
            sdk=root/'sdk.tar.gz';tar(sdk,{'sdk-version/LICENSE':b'SDK notice',
                'sdk-version/lib/source.c':b'library source'})
            project=root/'project.zip'
            recipe=b'{"artifact":"fixture"}\n'
            with zipfile.ZipFile(project,'w') as stream:
                stream.writestr('project-revision/tools/runtime/linux-glibc-x86_64.json',recipe)
                stream.writestr('project-revision/tools/runtime/build-common.py',b'fixture recipe source')
            graphviz_lock=dict(size=graphviz.stat().st_size,sha256=module.digest(graphviz),url='https://source.invalid/graphviz')
            sdk_lock=dict(size=sdk.stat().st_size,sha256=module.digest(sdk),url='https://source.invalid/sdk')
            project_lock=dict(size=project.stat().st_size,sha256=module.digest(project),root='project-revision',
                              url='https://source.invalid/project',revision='a'*40)
            provenance=dict(completed=True,artifact_id='linux-glibc-x86_64',executable_sha256='b'*64,
                recipe_sha256=module.hash_bytes(recipe),source=graphviz_lock,sdk=dict(facts=dict(archive=sdk_lock)))
            provenance_raw=json.dumps(provenance).encode()
            files={'graphviz.tar.gz':graphviz.read_bytes(),'sdk/LICENSE':b'SDK notice',
                'sdk/lib/source.c':b'library source','candidate-provenance.json':provenance_raw,
                'tools/runtime/linux-glibc-x86_64.json':recipe,'tools/runtime/build-common.py':b'fixture recipe source'}
            manifest=dict(artifact_id=provenance['artifact_id'],executable_sha256='b'*64,
                provenance_sha256=module.hash_bytes(provenance_raw),graphviz_archive_sha256=graphviz_lock['sha256'],
                sdk_archive_sha256=sdk_lock['sha256'],files=[dict(path=name,size=len(raw),sha256=module.hash_bytes(raw)) for name,raw in files.items()])
            files['manifest.json']=json.dumps(manifest).encode()
            source=root/'sources.tar.gz';tar(source,files)
            receipt=dict(artifact_id=provenance['artifact_id'],executable_sha256='b'*64,
                provenance_sha256=manifest['provenance_sha256'],archive_sha256=module.digest(source),
                archive_bytes=source.stat().st_size,file_count=len(files),sdk_files=2)
            receipt_path=root/'sources.json';receipt_path.write_text(json.dumps(receipt))
            with patch.object(module,'PROJECT_LOCK',project_lock),patch.object(module,'GRAPHVIZ_LOCK',graphviz_lock),\
                 patch.object(module,'SDK_LOCKS',{'x86_64':sdk_lock}):
                result=module.verify(source,receipt_path,project,graphviz,sdk)
                self.assertEqual(result['source_files_recovered'],5)
                self.assertEqual(result['generated_metadata_files'],['candidate-provenance.json','manifest.json'])
                self.assertFalse(result['approved']);self.assertFalse(result['qualified'])
                # A re-export with a consistent internal manifest still cannot replace public recipe bytes.
                replacement=b'altered recipe source'
                files['tools/runtime/build-common.py']=replacement
                manifest['files'][-1].update(size=len(replacement),sha256=module.hash_bytes(replacement))
                files['manifest.json']=json.dumps(manifest).encode();tar(source,files)
                receipt.update(archive_sha256=module.digest(source),archive_bytes=source.stat().st_size)
                receipt_path.write_text(json.dumps(receipt))
                with self.assertRaisesRegex(ValueError,'Public project source'):
                    module.verify(source,receipt_path,project,graphviz,sdk)

    def test_project_inventory_rejects_unsafe_duplicate_and_symlink_entries(self):
        module=tool()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'project.zip'
            for names in (['project/../escape'],['other/file'],['project/file','project/file']):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore',UserWarning)
                    with zipfile.ZipFile(path,'w') as stream:
                        for name in names:stream.writestr(name,b'fixture')
                with zipfile.ZipFile(path) as stream,self.assertRaises(ValueError):module.project_inventory(stream,'project')
            with zipfile.ZipFile(path,'w') as stream:
                entry=zipfile.ZipInfo('project/link');entry.create_system=3
                entry.external_attr=0o120777<<16;stream.writestr(entry,b'/outside')
            with zipfile.ZipFile(path) as stream,self.assertRaises(ValueError):module.project_inventory(stream,'project')
