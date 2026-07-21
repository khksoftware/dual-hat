"""Validate Dual Hat operating modes and platform profiles.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import copy, hashlib, json, os, subprocess, sys, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from work_item_governance import *
from profile_conformance import (capability_evidence_digest, capability_preflight, evidence_content_sha256,
    governed_repository_digest, resolve_profile, runtime_gap_stop_report, runtime_profile_failures, validate_profile)

DUAL_HAT_CAPABILITY_PROOFS = {"sealed_work_order", "repository_state_preservation", "explicit_user_and_architecture_reporting", "resumable_handoff", "detached_validation", "post_run_residue_inspection"}

def receipts(profile, root):
    interpreter=Path(sys.executable).resolve(); interpreter_hash=hashlib.sha256(interpreter.read_bytes()).hexdigest().upper(); result={}
    repository_hash=governed_repository_digest(root,str(profile["preflight_artifact"])); output="Ran 1 test in <duration>s\n\nOK\n"
    for rows in profile["capability_evidence"].values():
        for locator in rows:
            if not locator.startswith("test:") or locator in result: continue
            relative=locator.split(":",1)[1]; evidence=(root/relative).resolve()
            relative_path=Path(relative)
            result[locator]={"schema":"dual-hat-capability-test-receipt/1.2","locator":locator,"command":[interpreter.as_posix(),"-B","-m","unittest","discover","-s",relative_path.parent.as_posix(),"-p",relative_path.name],"interpreter_path":interpreter.as_posix(),"interpreter_sha256":interpreter_hash,"evidence_sha256":evidence_content_sha256(evidence),"governed_repository_sha256":repository_hash,"returncode":0,"discovered":1,"executed":1,"passed":1,"failed":0,"errored":0,"skipped":0,"output_normalization":"unittest_duration_redacted_v1","output":output,"output_sha256":hashlib.sha256(output.encode()).hexdigest().upper()}
    return result

def order(kind="gov"):
    revision_hash="A"*64
    value = {"schema":"dual-hat-sealed-work-order/1.1", "work_item_id":"GOV-0001" if kind=="gov" else "Capability 1", "work_item_type":kind, "title":"Bounded item", "operating_mode":"integrated", "active_role":"architecture", "lifecycle_state":"author_approved_for_execution", "approved_scope":["bounded"], "explicit_exclusions":[], "stop_gates":["new architecture"], "authorized_repositories":["repository"], "authorized_paths":["tracked source"], "authorized_mutation":"bounded", "destructive_permissions":["owned temporary cleanup"], "required_validation":["tests"], "publication_authority":{"push":False,"force_push":False,"tag":False,"github_release":False}, "dependency_permissions":{"existing":True,"new_external":False}, "external_service_permissions":{"push":False,"hosted_release":False}, "approval_state":"author_approved_for_execution", "approval_timestamp":"2030-01-01T00:00:00Z", "source_revisions":[{"revision":1,"sha256":revision_hash}], "revision_hash_set_sha256":hashlib.sha256((revision_hash+"\n").encode()).hexdigest().upper(), "revision_hash_set_encoding":"uppercase SHA-256 values in revision order, LF-terminated", "current_revision":1, "sealed_state":"immutable_approved_contract", "material_revision_rule":"revise, reapprove, and reseal", "product_increment":kind=="capability", "governance_contract_change":kind=="gov"}
    return seal(value)

def contexts(value):
    handover={"active_work_item":{"work_item_id":value["work_item_id"],"work_item_type":value["work_item_type"],"title":value["title"],"operating_mode":value["operating_mode"],"active_role":"engineering","lifecycle_state":"engineering","work_order_revision":value["current_revision"],"work_order_hash":value["work_order_hash"]}}
    profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8"))
    preflight=capability_preflight(profile,profile["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,ROOT,receipts(profile,ROOT))
    preflight.update({"work_item_id":value["work_item_id"],"work_order_revision":value["current_revision"],"work_order_hash":value["work_order_hash"],"platform_profile_id":profile["profile_id"],"platform_profile_version":profile["profile_version"]})
    return handover, profile, preflight

class OperatingModeTests(unittest.TestCase):
    def test_public_work_item_schema_and_example_cover_the_executable_contract(self):
        schema=json.loads((ROOT/"schemas/work-item.schema.json").read_text(encoding="utf-8")); example=json.loads((ROOT/"examples/integrated-work-item.example.json").read_text(encoding="utf-8"))
        self.assertEqual((),validate_sealed(example)); self.assertFalse(set(example)-set(schema["properties"])); self.assertIn("extension_classification",schema["properties"])
    def test_sealing_approval_and_stale_detection(self):
        approved=order(); handover,profile,preflight=contexts(approved); self.assertEqual((),validate_sealed(approved)); self.assertTrue(execution_authorized(approved,"Execute the approved work order.",current_handover=handover,platform_profile=profile,platform_preflight=preflight,evidence_root=ROOT))
        stale=copy.deepcopy(approved); stale["title"]="changed"; self.assertIn("stale work-order hash",validate_sealed(stale)); self.assertFalse(execution_authorized(approved,"maybe start"))
        self.assertIn("current handover context is missing",execution_contract_failures(approved,current_handover=None,platform_profile=profile,platform_preflight=preflight))
        contradictory=copy.deepcopy(handover); contradictory["active_work_item"]["work_order_revision"]=99; self.assertIn("current handover contradicts sealed work order",execution_contract_failures(approved,current_handover=contradictory,platform_profile=profile,platform_preflight=preflight))
        terminal=copy.deepcopy(handover); terminal["active_work_item"].update({"lifecycle_state":"archived","active_role":"architecture_review"}); self.assertIn("current handover role or lifecycle does not authorize engineering execution",execution_contract_failures(approved,current_handover=terminal,platform_profile=profile,platform_preflight=preflight))
        legacy=copy.deepcopy(approved); legacy["schema"]="dual-hat-sealed-work-order/1.0"; legacy=seal(legacy)
        self.assertEqual((),validate_sealed(legacy)); self.assertTrue(any("legacy work-order schema cannot authorize execution" in row for row in execution_contract_failures(legacy,current_handover=handover,platform_profile=profile,platform_preflight=preflight)))
    def test_semantic_classification(self):
        self.assertEqual((),classification_failures(order("gov"))); self.assertEqual((),classification_failures(order("capability")))
        bad=order("gov"); bad["product_increment"]=True; self.assertTrue(classification_failures(bad))
    def test_integrated_and_split_lifecycle(self):
        path=["architecture","work_order_ready","author_approved_for_execution","engineering","engineering_complete","architecture_review","accepted","archived"]
        self.assertTrue(all(transition_allowed(a,b) for a,b in zip(path,path[1:]))); self.assertFalse(transition_allowed("engineering_complete","accepted"))
        self.assertTrue(transition_allowed("architecture_review","remediation_required")); self.assertTrue(transition_allowed("remediation_required","engineering"))
    def test_integrated_mode_requires_visible_single_hat_labels(self):
        modes=(ROOT/"guides/OPERATING_MODES.md").read_text(encoding="utf-8")
        transitions=(ROOT/"governance/ROLE_TRANSITIONS.md").read_text(encoding="utf-8")
        architecture=(ROOT/"prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        engineering=(ROOT/"prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for text in (modes,transitions):
            self.assertIn("[Architect Office]",text); self.assertIn("[Engineering Agent]",text)
            self.assertIn("one hat",text.casefold())
        self.assertIn("begin every assistant-authored chat message with `[Architect Office]`",architecture)
        self.assertIn("begin every assistant-authored chat message with `[Engineering Agent]`",engineering)
    def test_mode_switch_package_and_dirty_block(self):
        package=json.loads((ROOT/"templates/MODE_TRANSITION_PACKAGE.json").read_text(encoding="utf-8")); self.assertEqual((),mode_switch_failures(package))
        self.assertEqual("dual-hat-mode-transition/1.1",package["schema"]); self.assertTrue(package["model_tier_binding"]); self.assertTrue(package["rollback_point"]); self.assertTrue(package["current_handover"])
        package["lifecycle_state"]="engineering"; package["repository"]["dirty_worktree"]=True; self.assertEqual(2,len(mode_switch_failures(package)))
        schema=json.loads((ROOT/"schemas/mode-transition-package.schema.json").read_text(encoding="utf-8"))
        conditional=schema["allOf"][0]["if"]; self.assertEqual(["schema"],conditional["required"])
        example=json.loads((ROOT/"examples/split-mode-transition.example.json").read_text(encoding="utf-8")); self.assertIn("platform_profile",example)
    def test_architecture_boundary_and_acceptance_archival(self):
        safe={k:False for k in ("external_consumer","shared_schema","engineering_behavior","validator_or_generator","publication_or_repository","synchronized_propagation","uncertain_reach")}; safe["exclusive_architecture_owner"]=True
        self.assertTrue(architecture_direct_mutation_allowed(safe)); unsafe={**safe,"uncertain_reach":True}; self.assertFalse(architecture_direct_mutation_allowed(unsafe))
        self.assertTrue(archival_allowed("accepted")); self.assertTrue(archival_allowed("accepted_with_follow_up",follow_up_blocking=False)); self.assertFalse(archival_allowed("remediation_required")); self.assertFalse(archival_allowed("accepted",actor="engineering"))
    def test_profile_conformance_and_fallback(self):
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8")); self.assertEqual((),validate_profile(profile,DUAL_HAT_CORE_VERSION)); self.assertTrue(resolve_profile(profile,DUAL_HAT_CORE_VERSION)["core_applies"])
        with self.assertRaises(ValueError): resolve_profile(None,DUAL_HAT_CORE_VERSION)
        weak=copy.deepcopy(profile); weak["guarantees"]["security_not_weakened"]=False; self.assertTrue(validate_profile(weak,DUAL_HAT_CORE_VERSION))
        unexplained=copy.deepcopy(profile); unexplained["capability_evidence_rationale"].pop("independent_deep_review"); self.assertTrue(validate_profile(unexplained,DUAL_HAT_CORE_VERSION))
        mismatch=copy.deepcopy(profile); mismatch["supported_configuration"]["operating_system"]="definitely-not-this-host"; self.assertTrue(runtime_profile_failures(mismatch)); self.assertTrue(capability_preflight(mismatch,["sealed_work_order"],DUAL_HAT_CORE_VERSION,ROOT,receipts(mismatch,ROOT))["hard_stop"])
    def test_preflight_blocks_known_gap_and_partial_conformance(self):
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8"))
        self.assertTrue(capability_preflight(profile,["sealed_work_order"],DUAL_HAT_CORE_VERSION,ROOT,receipts(profile,ROOT))["execution_authorized"])
        result=capability_preflight(profile,["missing_mandatory_rule"],DUAL_HAT_CORE_VERSION,ROOT,receipts(profile,ROOT)); self.assertTrue(result["hard_stop"]); self.assertFalse(result["execution_authorized"])
        profile["mandatory_capabilities"]["sealed_work_order"]=False; self.assertTrue(validate_profile(profile,DUAL_HAT_CORE_VERSION))
        minimal=copy.deepcopy(profile); minimal["mandatory_capabilities"]={"sealed_work_order":True}; minimal["capability_evidence"]={"sealed_work_order":["test:fake.py"]}
        self.assertIn("platform profile omits mandatory Dual Hat core capabilities",validate_profile(minimal,DUAL_HAT_CORE_VERSION))
        approved=order(); handover,profile,preflight=contexts(approved); preflight["capability_evidence_sha256"]="F"*64
        self.assertIn("platform preflight evidence binding is stale or forged",execution_contract_failures(approved,current_handover=handover,platform_profile=profile,platform_preflight=preflight,evidence_root=ROOT))
        fake=copy.deepcopy(profile); fake["capability_evidence"]={name:["test:missing-evidence.py"] for name in fake["mandatory_capabilities"]}
        self.assertFalse(capability_preflight(fake,fake["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,ROOT)["execution_authorized"])
        misbound=copy.deepcopy(profile); misbound["capability_evidence"]["independent_deep_review"]=["test:tests/test_quality_review.py"]
        self.assertIn("semantically misbound", " ".join(capability_preflight(misbound,misbound["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,ROOT,receipts(misbound,ROOT))["failures"]))
        self.assertTrue(capability_preflight(profile,["independent_deep_review"],DUAL_HAT_CORE_VERSION,ROOT,receipts(profile,ROOT))["execution_authorized"])

    def test_preflight_receipts_bind_test_bytes_profile_and_content_not_live_head(self):
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as temporary:
            root=Path(temporary); proof=root/"proof.py"; proof.write_text("DUAL_HAT_CAPABILITY_PROOFS="+repr(set(profile["mandatory_capabilities"]))+"\nimport unittest\nclass Proof(unittest.TestCase):\n def test_one(self): self.assertTrue(True)\n",encoding="utf-8")
            subprocess.run(("git","init"),cwd=root,check=True,capture_output=True); subprocess.run(("git","add","proof.py"),cwd=root,check=True,capture_output=True)
            profile["preflight_artifact"]="platform-preflight.json"
            profile["capability_evidence"]={name:["test:proof.py"] for name in profile["mandatory_capabilities"]}
            bound=receipts(profile,root); first=capability_preflight(profile,profile["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,root,bound)
            self.assertTrue(first["execution_authorized"]); self.assertNotIn("evidence_repository_commit",first)
            self.assertEqual(bound,receipts(profile,root)); self.assertTrue(first["runtime_profile_verified"])
            proof.write_bytes(proof.read_bytes().replace(b"\r\n",b"\n").replace(b"\n",b"\r\n"))
            self.assertTrue(capability_preflight(profile,profile["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,root,bound)["execution_authorized"])
            proof.write_text("DUAL_HAT_CAPABILITY_PROOFS="+repr(set(profile["mandatory_capabilities"]))+"\nimport unittest\nclass Proof(unittest.TestCase):\n def test_two(self): self.assertTrue(True)\n",encoding="utf-8")
            self.assertTrue(capability_preflight(profile,profile["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,root,bound)["hard_stop"])
            refreshed=receipts(profile,root); second=capability_preflight(profile,profile["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,root,refreshed)
            self.assertNotEqual(first["verified_capability_evidence_sha256"],second["verified_capability_evidence_sha256"])
            contradictory=copy.deepcopy(refreshed); contradictory["test:proof.py"]["passed"]=2
            self.assertTrue(capability_preflight(profile,profile["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,root,contradictory)["hard_stop"])
            changed=copy.deepcopy(profile); changed["profile_version"]="1.1.1"
            self.assertNotEqual(second["platform_profile_sha256"],capability_preflight(changed,changed["mandatory_capabilities"],DUAL_HAT_CORE_VERSION,root,refreshed)["platform_profile_sha256"])
    def test_runtime_gap_generates_blocking_resumable_handoff(self):
        handoff={"active_role":"engineering","operating_mode":"integrated","work_item_id":"GOV-1","sealed_work_order_hash":"A"*64,"platform_profile":{"id":"p","version":"1"},"repository_and_remote_state":{},"dirty_worktree_state":{},"completed_steps":[],"pending_steps":[],"partial_outputs":[],"temporary_and_ignored_state":[],"containment_actions":[],"permitted_next_action":"await Architecture"}
        report=runtime_gap_stop_report(gap_kind="tool_defect",unmet_requirement="mandatory validation",limitation="validator unavailable",handoff=handoff)
        self.assertEqual("hard_stop",report["status"]); self.assertTrue(report["mutation_blocked"]); self.assertTrue(report["architecture_disposition_required"])
        with self.assertRaises(ValueError): runtime_gap_stop_report(gap_kind="tool_defect",unmet_requirement="x",limitation="y",handoff={})
    def test_extensible_registered_work_item_types_fail_closed(self):
        registered=load_work_item_types(ROOT/"governance/WORK_ITEM_TYPE_REGISTRY.json"); self.assertEqual(frozenset({"capability","gov"}),registered)
        defect=order("gov"); defect["work_item_type"]="defect"; defect["work_item_id"]="DEFECT-0001"; defect=seal(defect)
        self.assertTrue(any("unknown work-item type" in failure for failure in validate_sealed(defect,registered_types=registered)))
        extension={"defect":{"identity_pattern":"^DEFECT-[0-9]{4}$","semantic_owner":"bounded defect correction","classification_rule":"defect correction only","classification":{"required_true":["extension_classification.defect_correction"],"required_false":["product_increment","governance_contract_change"]},"compatible_execution_lifecycles":["author_approved_for_execution","engineering"]}}
        defect["extension_classification"]={"defect_correction":True}; defect["governance_contract_change"]=False; defect=seal(defect)
        self.assertEqual((),validate_sealed(defect,registered_types={"defect"},type_registry=extension))
        self.assertEqual((),classification_failures(defect,type_registry=extension))
        incomplete={"defect":{"identity_pattern":"^DEFECT-[0-9]+$","classification":{},"compatible_execution_lifecycles":["author_approved_for_execution"]}}
        self.assertTrue(validate_sealed(defect,registered_types={"defect"},type_registry=incomplete)); self.assertTrue(classification_failures(defect,type_registry=incomplete))
        bare=copy.deepcopy(extension); bare["defect"]["classification"]["required_true"]=["defect_correction"]
        self.assertTrue(registry_failures(bare)); self.assertTrue(validate_sealed(defect,registered_types={"defect"},type_registry=bare))
        handover,profile,preflight=contexts(defect)
        author_only=copy.deepcopy(extension); author_only["defect"]["compatible_execution_lifecycles"]=["author_approved_for_execution"]
        failures=execution_contract_failures(defect,current_handover=handover,platform_profile=profile,platform_preflight=preflight,registered_types={"defect"},type_registry=author_only,evidence_root=ROOT)
        self.assertIn("current handover lifecycle is incompatible with registered work-item semantics",failures)
        extension["defect"]["compatible_execution_lifecycles"].append("engineering")
        failures=execution_contract_failures(defect,current_handover=handover,platform_profile=profile,platform_preflight=preflight,registered_types={"defect"},type_registry=extension,evidence_root=ROOT)
        self.assertNotIn("current handover lifecycle is incompatible with registered work-item semantics",failures)
    def test_architecture_boundary_review_is_independent_and_blocks_acceptance(self):
        review={"reviewer_role":"architecture","sealed_work_order_hash_verified":True,"primary_evidence_inspected":["diff","remote"],"engineering_self_report_only":False,"tests_only":False,"deviation_found":False,"material_violation_unresolved":False,"specific_remediation_obligation":None,"systemic_control_obligation":None,"analogous_gap_review":"recorded","architecture_disposition":"accepted"}
        self.assertEqual((),boundary_review_failures(review))
        violated={**review,"deviation_found":True,"material_violation_unresolved":True,"specific_remediation_obligation":None,"systemic_control_obligation":None,"analogous_gap_review":"","architecture_disposition":"accepted"}
        failures=boundary_review_failures(violated); self.assertIn("acceptance is blocked by unresolved material boundary violation",failures); self.assertIn("boundary violation lacks specific remediation",failures); self.assertIn("boundary violation lacks systemic control strengthening",failures)
        self.assertTrue(boundary_review_failures({**review,"engineering_self_report_only":True})); self.assertTrue(boundary_review_failures({**review,"tests_only":True}))
    def test_architecture_proposes_next_work_after_acceptance_without_authorizing_it(self):
        guide=(ROOT/"governance/ARCHITECTURE_OFFICE_GUIDE.md").read_text(encoding="utf-8")
        prompt=(ROOT/"prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        for text in (guide,prompt):
            self.assertIn("propose the next work to plan",text)
            self.assertIn("does not authorize execution",text.replace("planning guidance distinct from execution authority","does not authorize execution"))
    def test_current_handover_is_generic_and_historical_schema_is_retained(self):
        schema=json.loads((ROOT/"schemas/current-handover.schema.json").read_text(encoding="utf-8")); template=json.loads((ROOT/"templates/CURRENT_HANDOVER.json").read_text(encoding="utf-8"))
        self.assertEqual("dual-hat-current-handover/1.1",template["schema"]); self.assertIn("active_work_item",template); self.assertNotIn("active_capability",template)
        self.assertIn("dual-hat-current-handover/1.0",schema["properties"]["schema"]["enum"])
        self.assertEqual("^[a-z][a-z0-9_]*$",schema["properties"]["active_work_item"]["properties"]["work_item_type"]["pattern"])

    def test_third_party_dependency_evaluation_is_mandatory_in_both_hats(self):
        contract=(ROOT/"governance/THIRD_PARTY_DEPENDENCY_EVALUATION.md").read_text(encoding="utf-8")
        engineering=(ROOT/"prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        architecture=(ROOT/"prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        for required in ("license", "cost", "reliability", "safety", "hardware", "support status", "pros/cons comparison"):
            self.assertIn(required,contract)
        for prompt in (engineering,architecture):
            self.assertIn("third-party",prompt)
            self.assertIn("license",prompt)
            self.assertIn("cost",prompt)
            self.assertIn("reliability",prompt)
            self.assertIn("hardware",prompt)
            self.assertIn("support status",prompt)
            self.assertIn("pros/cons",prompt)

    def test_long_running_work_prefers_subagent_offload_without_false_parallelism(self):
        contract=(ROOT/"governance/VALIDATION_AND_PARALLELISM.md").read_text(encoding="utf-8")
        engineering=(ROOT/"prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (contract,engineering):
            self.assertIn("long-running",guidance)
            self.assertIn("dedicated sub-agent",guidance)
            self.assertIn("current work item",guidance)
            self.assertIn("every remaining task",guidance)

    def test_delegation_retains_visible_heartbeat_and_terminal_reporting(self):
        contract=(ROOT/"governance/VALIDATION_AND_PARALLELISM.md").read_text(encoding="utf-8")
        watchdog=(ROOT/"validation/PROCESS_WATCHDOG.md").read_text(encoding="utf-8")
        engineering=(ROOT/"prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (contract,watchdog,engineering):
            self.assertIn("user-communication accountability",guidance)
            self.assertIn("heartbeat",guidance)
            self.assertIn("without waiting for the user",guidance)
        self.assertIn("every five minutes",contract)
        self.assertIn("before every status or final response",contract)
        self.assertIn("does not send a final response",contract)
        self.assertIn("persistent watcher",contract)

    def test_active_task_continuity_has_only_governed_early_stops(self):
        framework=(ROOT/"framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        engineering=(ROOT/"prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        architecture=(ROOT/"prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        transitions=(ROOT/"governance/ROLE_TRANSITIONS.md").read_text(encoding="utf-8")
        self.assertIn("Active-task continuity",framework)
        for guidance in (framework,engineering,transitions):
            self.assertIn("explicitly orders",guidance)
            self.assertIn("user decision",guidance)
            self.assertIn("Architecture Office decision",guidance)
            self.assertIn("explicitly specified stop gate",guidance)
            self.assertIn("end of a message",guidance)
            self.assertIn("side question",guidance)
        self.assertIn("transition directly to `[Architect Office]`",framework)
        self.assertIn("task is complete and reported",architecture)

if __name__ == "__main__": unittest.main()
