"""Validate Dual Hat operating modes and platform profiles.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import copy, json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from work_item_governance import *
from profile_conformance import capability_preflight, resolve_profile, runtime_gap_stop_report, validate_profile

def order(kind="gov"):
    value = {"work_item_id":"GOV-0001" if kind=="gov" else "CAP-EXAMPLE", "work_item_type":kind, "title":"Bounded item", "operating_mode":"integrated", "active_role":"architecture", "lifecycle_state":"author_approved_for_execution", "approved_scope":["bounded"], "explicit_exclusions":[], "stop_gates":["new architecture"], "authorized_repositories":["repository"], "authorized_mutation":"bounded", "required_validation":["tests"], "publication_authority":{"push":False}, "approval_state":"author_approved_for_execution", "approval_timestamp":"2030-01-01T00:00:00Z", "product_increment":kind=="capability", "governance_contract_change":kind=="gov"}
    return seal(value)

class OperatingModeTests(unittest.TestCase):
    def test_sealing_approval_and_stale_detection(self):
        approved=order(); self.assertEqual((),validate_sealed(approved)); self.assertTrue(execution_authorized(approved,"Execute the approved work order."))
        stale=copy.deepcopy(approved); stale["title"]="changed"; self.assertIn("stale work-order hash",validate_sealed(stale)); self.assertFalse(execution_authorized(approved,"maybe start"))
    def test_semantic_classification(self):
        self.assertEqual((),classification_failures(order("gov"))); self.assertEqual((),classification_failures(order("capability")))
        bad=order("gov"); bad["product_increment"]=True; self.assertTrue(classification_failures(bad))
    def test_integrated_and_split_lifecycle(self):
        path=["architecture","work_order_ready","author_approved_for_execution","engineering","engineering_complete","architecture_review","accepted","archived"]
        self.assertTrue(all(transition_allowed(a,b) for a,b in zip(path,path[1:]))); self.assertFalse(transition_allowed("engineering_complete","accepted"))
        self.assertTrue(transition_allowed("architecture_review","remediation_required")); self.assertTrue(transition_allowed("remediation_required","engineering"))
    def test_mode_switch_package_and_dirty_block(self):
        package=json.loads((ROOT/"templates/MODE_TRANSITION_PACKAGE.json").read_text(encoding="utf-8")); self.assertEqual((),mode_switch_failures(package))
        package["lifecycle_state"]="engineering"; package["repository"]["dirty_worktree"]=True; self.assertEqual(2,len(mode_switch_failures(package)))
    def test_architecture_boundary_and_acceptance_archival(self):
        safe={k:False for k in ("external_consumer","shared_schema","engineering_behavior","validator_or_generator","publication_or_repository","synchronized_propagation","uncertain_reach")}; safe["exclusive_architecture_owner"]=True
        self.assertTrue(architecture_direct_mutation_allowed(safe)); unsafe={**safe,"uncertain_reach":True}; self.assertFalse(architecture_direct_mutation_allowed(unsafe))
        self.assertTrue(archival_allowed("accepted")); self.assertTrue(archival_allowed("accepted_with_follow_up",follow_up_blocking=False)); self.assertFalse(archival_allowed("remediation_required")); self.assertFalse(archival_allowed("accepted",actor="engineering"))
    def test_profile_conformance_and_fallback(self):
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8")); self.assertEqual((),validate_profile(profile,"1.0.1")); self.assertTrue(resolve_profile(profile,"1.0.1")["core_applies"])
        with self.assertRaises(ValueError): resolve_profile(None,"1.0.1")
        weak=copy.deepcopy(profile); weak["guarantees"]["security_not_weakened"]=False; self.assertTrue(validate_profile(weak,"1.0.1"))
    def test_preflight_blocks_known_gap_and_partial_conformance(self):
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8"))
        self.assertTrue(capability_preflight(profile,["sealed_work_order"],"1.0.1")["execution_authorized"])
        result=capability_preflight(profile,["missing_mandatory_rule"],"1.0.1"); self.assertTrue(result["hard_stop"]); self.assertFalse(result["execution_authorized"])
        profile["mandatory_capabilities"]["sealed_work_order"]=False; self.assertTrue(validate_profile(profile,"1.0.1"))
    def test_runtime_gap_generates_blocking_resumable_handoff(self):
        handoff={"active_role":"engineering","operating_mode":"integrated","work_item_id":"GOV-1","sealed_work_order_hash":"A"*64,"platform_profile":{"id":"p","version":"1"},"repository_and_remote_state":{},"dirty_worktree_state":{},"completed_steps":[],"pending_steps":[],"partial_outputs":[],"temporary_and_ignored_state":[],"containment_actions":[],"permitted_next_action":"await Architecture"}
        report=runtime_gap_stop_report(gap_kind="tool_defect",unmet_requirement="mandatory validation",limitation="validator unavailable",handoff=handoff)
        self.assertEqual("hard_stop",report["status"]); self.assertTrue(report["mutation_blocked"]); self.assertTrue(report["architecture_disposition_required"])
        with self.assertRaises(ValueError): runtime_gap_stop_report(gap_kind="tool_defect",unmet_requirement="x",limitation="y",handoff={})
    def test_extensible_registered_work_item_types_fail_closed(self):
        registered=load_work_item_types(ROOT/"governance/WORK_ITEM_TYPE_REGISTRY.json"); self.assertEqual(frozenset({"capability","gov"}),registered)
        defect=order("gov"); defect["work_item_type"]="defect"; defect=seal(defect)
        self.assertIn("unknown work-item type",validate_sealed(defect,registered_types=registered))
        self.assertNotIn("unknown work-item type",validate_sealed(defect,registered_types=registered|{"defect"}))
    def test_architecture_boundary_review_is_independent_and_blocks_acceptance(self):
        review={"sealed_work_order_hash_verified":True,"primary_evidence_inspected":["diff","remote"],"engineering_self_report_only":False,"tests_only":False,"deviation_found":False,"material_violation_unresolved":False,"specific_remediation_obligation":None,"systemic_control_obligation":None,"analogous_gap_review":"recorded","architecture_disposition":"accepted"}
        self.assertEqual((),boundary_review_failures(review))
        violated={**review,"deviation_found":True,"material_violation_unresolved":True,"specific_remediation_obligation":None,"systemic_control_obligation":None,"analogous_gap_review":"","architecture_disposition":"accepted"}
        failures=boundary_review_failures(violated); self.assertIn("acceptance is blocked by unresolved material boundary violation",failures); self.assertIn("boundary violation lacks specific remediation",failures); self.assertIn("boundary violation lacks systemic control strengthening",failures)
        self.assertTrue(boundary_review_failures({**review,"engineering_self_report_only":True})); self.assertTrue(boundary_review_failures({**review,"tests_only":True}))
    def test_current_handover_is_generic_and_historical_schema_is_retained(self):
        schema=json.loads((ROOT/"schemas/current-handover.schema.json").read_text(encoding="utf-8")); template=json.loads((ROOT/"templates/CURRENT_HANDOVER.json").read_text(encoding="utf-8"))
        self.assertEqual("dual-hat-current-handover/1.1",template["schema"]); self.assertIn("active_work_item",template); self.assertNotIn("active_capability",template)
        self.assertIn("dual-hat-current-handover/1.0",schema["properties"]["schema"]["enum"])
        self.assertEqual("^[a-z][a-z0-9_]*$",schema["properties"]["active_work_item"]["properties"]["work_item_type"]["pattern"])

if __name__ == "__main__": unittest.main()
