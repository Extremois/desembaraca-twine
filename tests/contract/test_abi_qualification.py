"""ABI qualification is distinct from per-distribution compatibility declarations."""
import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from common import ROOT
from twine_edge_overlap.runtime_catalog import GATES, abi_target_matches, classify_support
from twine_edge_overlap.runtime_platform import HostEnvironment
from unit.test_runtime_build_tools import tool
from unit import test_qualification_tools as qualification_fixtures


class ABIQualificationTests(unittest.TestCase):
    def registry(self):
        return json.loads((ROOT/'tools/runtime/abi-targets.json').read_bytes())

    def target(self):
        return next(row for row in self.registry()['targets'] if row['os']=='linux' and row['abi']=='glibc' and row['arch']=='x86_64')

    def test_scope_has_seven_targets_fourteen_slots_and_no_apple_requirement(self):
        data=self.registry()
        self.assertEqual(len(data['targets']),7)
        self.assertEqual(sum(len(row['python_qualifications']) for row in data['targets']),14)
        self.assertTrue(all(row['qualification_scope']=='abi' for row in data['targets']))
        self.assertFalse(data['macos_signing_required'])
        audit=json.loads((ROOT/'tools/runtime/licenses/macos.json').read_bytes())
        self.assertFalse(audit['signing_and_notarization_requirements']['required'])
        self.assertFalse(audit['approved'])
        self.assertEqual(len(json.loads((ROOT/'tools/runtime/support-targets.json').read_bytes())['targets']),69)

    def test_matching_uses_abi_and_baseline_without_requiring_distro_or_kernel(self):
        target=self.target()
        host=HostEnvironment(os='linux',arch='x86_64',distribution_id='fedora',distribution_version='44',libc_family='glibc',libc_version='2.43')
        self.assertTrue(abi_target_matches(target,host))
        self.assertTrue(tool('qualify-target').host_matches(target,host))
        for altered in (replace(host,libc_family='musl'),replace(host,libc_version='2.26'),replace(host,arch='aarch64'),replace(host,bits=32)):
            self.assertFalse(abi_target_matches(target,altered))
        mac=next(row for row in self.registry()['targets'] if row['os']=='darwin' and row['arch']=='aarch64')
        self.assertTrue(abi_target_matches(mac,HostEnvironment(os='darwin',arch='aarch64',os_version='15.7')))
        self.assertFalse(abi_target_matches(mac,HostEnvironment(os='darwin',arch='aarch64',os_version='14.7')))

    def test_abi_status_needs_both_python_slots_and_does_not_promote_distributions(self):
        target=copy.deepcopy(self.target());target.update(application_revision='a'*40,artifact_id='synthetic-abi')
        evidence={}
        for slot in target['python_qualifications']:
            minor=slot['python_minor'];slot.update(status='validada',application_revision='a'*40,artifact_id='synthetic-abi',evidence_ids=[minor])
            evidence[minor]=dict(target_id=target['id'],python_minor=minor,application_revision='a'*40,artifact_id='synthetic-abi',snapshot_id=None,environment_kind='github-actions',passed=True,checks=dict.fromkeys(GATES,True))
        matrix=dict(abi_targets=[target],targets=[],evidence=evidence)
        host=HostEnvironment(os='linux',arch='x86_64',libc_family='glibc',libc_version='2.43',distribution_id='unlisted')
        decision=classify_support(host,dict(id='synthetic-abi',abi='glibc'),matrix,application_revision='a'*40)
        self.assertEqual(decision.level,'official')
        self.assertIn('ABI',decision.reason)
        del evidence['3.14']
        self.assertEqual(classify_support(host,dict(id='synthetic-abi',abi='glibc'),matrix,application_revision='a'*40).level,'best_effort')

    def test_promotion_accepts_actions_on_different_kernels_for_one_abi(self):
        registry=self.registry();target=self.target()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);records=qualification_fixtures.QualificationToolTests().records(target,root)
            for record in records:
                record.update(environment_kind='github-actions',distribution_id='fedora',os_version='44',abi='glibc',libc_version='2.43')
                record['network']['observation']='github-actions-log'
            records[1].update(kernel='another-runner-kernel',image_digest='f'*64)
            proposal=tool('promote-support').propose(registry,target['id'],records,root)
            self.assertEqual(next(row for row in proposal['targets'] if row['id']==target['id'])['status'],'validada')
            bad=copy.deepcopy(records);bad[1]['abi']='musl'
            with self.assertRaises(ValueError):tool('promote-support').propose(registry,target['id'],bad,root)
            bad=copy.deepcopy(records);bad[1]['environment_kind']='native'
            with self.assertRaises(ValueError):tool('promote-support').propose(registry,target['id'],bad,root)
