"""Synthetic policy evidence never qualifies a real support target."""
import copy
import json
import unittest
from dataclasses import replace
from common import ROOT
from twine_edge_overlap.runtime_catalog import GATES, classify_support, support_status
from twine_edge_overlap.runtime_platform import HostEnvironment
from twine_edge_overlap.runtime_snapshot import collect_snapshot
from twine_edge_overlap.engines.process import ProcessResult
from runtime_support import blocked_network


class SupportPolicyTests(unittest.TestCase):
    def test_shared_evidence_cannot_replace_python_dependent_trials(self):
        target,evidence,host,snapshot=self.fixture()
        common=copy.deepcopy(evidence['3.12'])
        common.update(python_minor=None,checks=dict.fromkeys(GATES,True))
        evidence['common']=common
        target['evidence_ids']=['common']
        for item in (evidence['3.12'],evidence['3.14']):item['checks']={'first_run':True}
        self.assertNotEqual(support_status(target,evidence),'validada')

    def test_ambiguous_cpu_image_family_never_inherits_default_validation(self):
        target,evidence,host,snapshot=self.fixture()
        target.update(distribution_id='almalinux',version='10.2',channel='stable',snapshot_id=None)
        for item in evidence.values():item['snapshot_id']=None
        variant=copy.deepcopy(target)
        variant.update(id='synthetic-v2',cpu_variant='x86-64-v2',application_revision=None,artifact_id=None)
        for slot in variant['python_qualifications']:slot.update(target_id=variant['id'],status='pendente',evidence_ids=[])
        host=replace(host,distribution_id='almalinux',distribution_version='10.2')
        matrix=dict(targets=[target,variant],evidence=evidence)
        decision=classify_support(host,dict(id='synthetic-policy'),matrix,application_revision='a'*40)
        self.assertEqual(decision.level,'best_effort')
        self.assertEqual(classify_support(replace(host,cpu_variant='x86-64-v2'),dict(id='synthetic-policy'),matrix,application_revision='a'*40).level,'best_effort')
        self.assertEqual(classify_support(replace(host,cpu_variant='distribution-default'),dict(id='synthetic-policy'),matrix,application_revision='a'*40).level,'official')
        variant.update(application_revision='a'*40,artifact_id='synthetic-policy')
        for slot in variant['python_qualifications']:
            key='v2-'+slot['python_minor']
            slot.update(status='validada',application_revision='a'*40,artifact_id='synthetic-policy',evidence_ids=[key])
            evidence[key]=dict(evidence[slot['python_minor']],target_id=variant['id'])
        self.assertEqual(classify_support(replace(host,cpu_variant='x86-64-v2'),dict(id='synthetic-policy'),matrix,application_revision='a'*40).target_id,variant['id'])

    def fixture(self):
        target=copy.deepcopy(json.loads((ROOT/'tools/runtime/support-targets.json').read_text(encoding='utf-8'))['targets'][0])
        metadata=dict(distribution_id='arch',version_id=None,build_id=None,channel='rolling',native_arch='x86_64',kernel_release='test-kernel')
        snapshot=collect_snapshot('pacman',lambda:metadata.copy(),runner=lambda *a,**k:ProcessResult(0,b'a 1\n',b''))
        target.update(os='linux',arch='x86_64',distribution_id='arch',version='rolling',channel='rolling',cpu_variant='distribution-default',snapshot_id=snapshot.snapshot_id,application_revision='a'*40,artifact_id='synthetic-policy')
        evidence={}
        for slot in target['python_qualifications']:
            key=slot['python_minor']
            slot.update(status='validada',application_revision='a'*40,artifact_id='synthetic-policy',evidence_ids=[key])
            evidence[key]=dict(target_id=target['id'],python_minor=key,application_revision='a'*40,artifact_id='synthetic-policy',snapshot_id=snapshot.snapshot_id,environment_kind='native',passed=True,checks=dict.fromkeys(GATES,True))
        host=HostEnvironment(os='linux',arch='x86_64',distribution_id='arch')
        return target,evidence,host,snapshot

    def test_exact_rolling_identity_and_both_python_slots_without_network(self):
        target,evidence,host,snapshot=self.fixture()
        matrix=dict(targets=[target],evidence=evidence)
        with blocked_network():
            self.assertEqual(classify_support(host,dict(id='synthetic-policy'),matrix,snapshot=snapshot,application_revision='a'*40).level,'official')
            for other in (None,replace(snapshot,known=False),replace(snapshot,snapshot_id='f'*64)):
                self.assertEqual(classify_support(host,dict(id='synthetic-policy'),matrix,snapshot=other,application_revision='a'*40).level,'best_effort')
            self.assertEqual(classify_support(replace(host,distribution_id='derivative'),dict(id='synthetic-policy'),matrix,snapshot=snapshot,application_revision='a'*40).level,'best_effort')
            for altered in (replace(host,python_version=(3,13)),replace(host,translated=True)):
                self.assertEqual(classify_support(altered,dict(id='synthetic-policy'),matrix,snapshot=snapshot,application_revision='a'*40).level,'best_effort')

    def test_known_failed_gate_is_not_erased_by_another_successful_record(self):
        target,evidence,host,snapshot=self.fixture()
        failed=copy.deepcopy(evidence['3.12'])
        failed['checks']={'twine':False}
        evidence['failed-common']=failed
        target['python_qualifications'][0]['evidence_ids'].append('failed-common')
        self.assertNotEqual(support_status(target,evidence),'validada')

    def test_unavailable_cell_and_hand_edited_status_do_not_grant_support(self):
        target,evidence,host,snapshot=self.fixture()
        pending=copy.deepcopy(target)
        pending['id']='other-pending'
        pending['status']='validada'
        pending['application_revision']=None
        for slot in pending['python_qualifications']:
            slot.update(target_id=pending['id'],status='pendente',evidence_ids=[])
        self.assertEqual(support_status(pending,{}),'pendente')
        decision=classify_support(host,dict(id='synthetic-policy'),dict(targets=[target,pending],evidence=evidence),snapshot=snapshot,application_revision='a'*40)
        self.assertEqual(decision.level,'official')
