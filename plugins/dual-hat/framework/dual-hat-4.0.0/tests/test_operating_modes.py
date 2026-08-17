"""Validate Dual Hat operating modes and platform profiles.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import copy, hashlib, inspect, json, os, subprocess, sys, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
sys.path.insert(0, str(ROOT / "tests"))
# The single-canonical-home predicate is defined once, in test_framework.py, and
# shared rather than restated -- a test suite for a work item about removing
# duplication should not open by duplicating its own helper. Only the plain
# mixin is imported; importing a TestCase would make the loader collect
# test_framework's own tests a second time under this module.
from test_framework import CanonicalHomeAssertions  # noqa: E402
from work_item_governance import *
from profile_conformance import (capability_evidence_digest, capability_preflight, evidence_content_sha256,
    governed_repository_digest, resolve_profile, runtime_gap_stop_report, runtime_profile_failures, validate_profile)
# The modules themselves, not only their names: the version-authority proofs
# below observe what the governance module hands its collaborators and feed it
# malformed release evidence, neither of which a star-imported name can reach.
# Importing a module binds no version -- resolution stays at call time.
import profile_conformance, release_package, work_item_governance  # noqa: E402

DUAL_HAT_CAPABILITY_PROOFS = {"sealed_work_order", "repository_state_preservation", "explicit_user_and_architecture_reporting", "resumable_handoff", "detached_validation", "post_run_residue_inspection"}

def core_version():
    """Resolve the active core version the way every consumer must: at call time.

    A module-level binding here would be the same import-scope resolution the
    governance module refuses, one file further out, and would take every test in
    this module down on release evidence most of them never consult.
    """
    version, failures = active_core_version()
    if failures: raise AssertionError(f"active core version is unresolvable from governed release evidence: {failures}")
    return version

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
    value = {"schema":"dual-hat-sealed-work-order/1.1", "work_item_id":"GOV-9001" if kind=="gov" else "Capability 9001", "work_item_type":kind, "title":"Bounded item", "operating_mode":"integrated", "active_role":"architecture", "lifecycle_state":"author_approved_for_execution", "approved_scope":["bounded"], "explicit_exclusions":[], "stop_gates":["new architecture"], "authorized_repositories":["repository"], "authorized_paths":["tracked source"], "authorized_mutation":"bounded", "destructive_permissions":["owned temporary cleanup"], "required_validation":["tests"], "publication_authority":{"push":False,"force_push":False,"tag":False,"github_release":False}, "dependency_permissions":{"existing":True,"new_external":False}, "external_service_permissions":{"push":False,"hosted_release":False}, "approval_state":"author_approved_for_execution", "approval_timestamp":"2030-01-01T00:00:00Z", "source_revisions":[{"revision":1,"sha256":revision_hash}], "revision_hash_set_sha256":hashlib.sha256((revision_hash+"\n").encode()).hexdigest().upper(), "revision_hash_set_encoding":"uppercase SHA-256 values in revision order, LF-terminated", "current_revision":1, "sealed_state":"immutable_approved_contract", "material_revision_rule":"revise, reapprove, and reseal", "product_increment":kind=="capability", "governance_contract_change":kind=="gov"}
    return seal(value)

def contexts(value):
    handover={"active_work_item":{"work_item_id":value["work_item_id"],"work_item_type":value["work_item_type"],"title":value["title"],"operating_mode":value["operating_mode"],"active_role":"engineering","lifecycle_state":"engineering","work_order_revision":value["current_revision"],"work_order_hash":value["work_order_hash"]}}
    profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8"))
    expected=f"engineering/process/work-items/{value['work_item_id']}/PLATFORM_PREFLIGHT.json"
    execution_profile=copy.deepcopy(profile); execution_profile["preflight_artifact"]=expected
    preflight=capability_preflight(execution_profile,profile["mandatory_capabilities"],core_version(),ROOT,receipts(execution_profile,ROOT))
    preflight.update({"preflight_artifact":expected,"work_item_id":value["work_item_id"],"work_order_revision":value["current_revision"],"work_order_hash":value["work_order_hash"],"platform_profile_id":profile["profile_id"],"platform_profile_version":profile["profile_version"]})
    return handover, profile, preflight

def termination_context(value):
    process={"process_id":"owned-build-1","state":"terminal","terminal_evidence":"process authority reports exit 0"}
    worker={"handle":"worker-1","assigned_outcome":"review the bounded result","owner":"engineering","durable_cursor":"review cursor 1","heartbeat_interval_seconds":300,"last_probe_age_seconds":0,"state":"finished","outcome_complete":True,"terminal_evidence":"final result received and consumed"}
    receipt={"schema":"dual-hat-termination-preflight-receipt/1.0","governing_identity":{"work_item_id":value["work_item_id"],"work_order_hash":value["work_order_hash"]},"terminal_condition":"planned_scope_completion","planned_item_dispositions":[{"scope_item":"bounded","disposition":"complete","evidence":"bounded work completed"}],"required_results":[{"scope_item":"bounded","evidence":"result received and consumed"}],"processes":[process],"workers":[worker]}
    authority={"schema":"dual-hat-platform-authority-snapshot/1.0","work_item_id":value["work_item_id"],"work_order_hash":value["work_order_hash"],"processes":[process],"workers":[worker]}
    return receipt, authority

def hard_stop_receipt(receipt, *, abort=False):
    result=copy.deepcopy(receipt); result["terminal_condition"]="hard_stop"; result["planned_item_dispositions"][0]["disposition"]="blocked"; result["hard_stop"]={"gate":"new architecture","evidence":"gate is active","preserved_state":"cursor 1","affected_work":"bounded","resumption_condition":"author resolves new architecture"}
    if abort: result["hard_stop"].update({"abort_authority":"new architecture","terminal_disposition":"author-authorized abort recorded"})
    return result

def termination_transition_allowed(current, target, value, receipt, authority):
    parameters=inspect.signature(transition_allowed).parameters
    if "sealed_order" not in parameters:
        return transition_allowed(current,target)
    return transition_allowed(current,target,sealed_order=value,termination_receipt=receipt,platform_authority_snapshot=authority)

class OperatingModeTests(CanonicalHomeAssertions, unittest.TestCase):
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
        coupled=order("capability"); coupled["extension_classification"]={"coupled_governance_change":True}; coupled=seal(coupled); self.assertEqual((),classification_failures(coupled))
        invalid=order("gov"); invalid["extension_classification"]={"coupled_governance_change":True}; invalid=seal(invalid); self.assertTrue(classification_failures(invalid))
    def test_integrated_and_split_lifecycle(self):
        path=["architecture","work_order_ready","author_approved_for_execution","engineering","engineering_complete","architecture_review","accepted","archived"]
        approved=order(); receipt,authority=termination_context(approved)
        self.assertTrue(all(termination_transition_allowed(a,b,approved,receipt,authority) for a,b in zip(path,path[1:]))); self.assertFalse(transition_allowed("engineering_complete","accepted"))
        self.assertTrue(transition_allowed("architecture_review","remediation_required")); self.assertTrue(transition_allowed("remediation_required","engineering"))

    def test_termination_preflight_requires_exact_approved_scope_dispositions(self):
        approved=order(); receipt,authority=termination_context(approved)
        cases={"absent_receipt":None,"missing_scope":copy.deepcopy(receipt),"extra_scope":copy.deepcopy(receipt)}
        cases["missing_scope"]["planned_item_dispositions"]=[]
        cases["extra_scope"]["planned_item_dispositions"].append({"scope_item":"invented","disposition":"complete","evidence":"not sealed"})
        for label,candidate in cases.items():
            with self.subTest(case=label): self.assertFalse(termination_transition_allowed("engineering","engineering_complete",approved,candidate,authority))

    def test_termination_preflight_requires_nonempty_evidence_for_every_required_result(self):
        approved=order(); receipt,authority=termination_context(approved)
        absent=copy.deepcopy(receipt); del absent["required_results"]
        empty=copy.deepcopy(receipt); empty["required_results"][0]["evidence"]=""
        missing_scope=copy.deepcopy(receipt); missing_scope["required_results"]=[]
        for label,candidate in (("absent",absent),("empty_evidence",empty),("missing_scope",missing_scope)):
            with self.subTest(case=label): self.assertFalse(termination_transition_allowed("engineering","engineering_complete",approved,candidate,authority))

    def test_termination_preflight_requires_a_named_sealed_hard_stop(self):
        approved=order(); receipt,authority=termination_context(approved); hard_stop=hard_stop_receipt(receipt)
        self.assertTrue(termination_transition_allowed("engineering","engineering_blocked",approved,hard_stop,authority))
        unknown_gate=copy.deepcopy(hard_stop); unknown_gate["hard_stop"]["gate"]="arbitrary pause"
        self.assertFalse(termination_transition_allowed("engineering","engineering_blocked",approved,unknown_gate,authority))

    def test_termination_preflight_abort_requires_sealed_authority_and_terminal_disposition(self):
        approved=order(); receipt,authority=termination_context(approved); abort=hard_stop_receipt(receipt,abort=True)
        for current in ("engineering","engineering_paused","engineering_blocked"):
            with self.subTest(valid_edge=current): self.assertTrue(termination_transition_allowed(current,"engineering_aborted",approved,abort,authority))
        no_authority=copy.deepcopy(abort); no_authority["hard_stop"]["abort_authority"]=""
        no_disposition=copy.deepcopy(abort); no_disposition["hard_stop"]["terminal_disposition"]=""
        for label,candidate in (("authority",no_authority),("terminal_disposition",no_disposition)):
            with self.subTest(missing=label): self.assertFalse(termination_transition_allowed("engineering","engineering_aborted",approved,candidate,authority))

    def test_termination_preflight_requires_owned_process_terminality(self):
        approved=order(); receipt,authority=termination_context(approved)
        running_process=copy.deepcopy(receipt); running_process["processes"][0]["state"]="running"; running_authority=copy.deepcopy(authority); running_authority["processes"]=copy.deepcopy(running_process["processes"])
        self.assertFalse(termination_transition_allowed("engineering","engineering_complete",approved,running_process,running_authority))

    def test_termination_preflight_binds_receipt_to_sealed_work_order_hash(self):
        approved=order(); receipt,authority=termination_context(approved)
        wrong_receipt=copy.deepcopy(receipt); wrong_receipt["governing_identity"]["work_order_hash"]="F"*64
        wrong_authority=copy.deepcopy(authority); wrong_authority["work_order_hash"]="F"*64
        for label,candidate,snapshot in (("receipt",wrong_receipt,authority),("authority",receipt,wrong_authority)):
            with self.subTest(binding=label): self.assertFalse(termination_transition_allowed("engineering","engineering_complete",approved,candidate,snapshot))
    def test_termination_preflight_reuses_dispatch_reconciliation(self):
        approved=order(); receipt,authority=termination_context(approved)
        running=copy.deepcopy(receipt); running["workers"][0].update({"handle":"worker-stale-1","state":"running","outcome_complete":False,"terminal_evidence":"","last_probe_age_seconds":301}); running_authority=copy.deepcopy(authority); running_authority["workers"]=copy.deepcopy(running["workers"])
        calls=[]; canonical=work_item_governance.dispatch_inventory
        def spy(*,workers):
            calls.append(workers)
            return canonical(workers=workers)
        work_item_governance.dispatch_inventory=spy
        try:
            failures=termination_preflight_failures("engineering","engineering_complete",sealed_order=approved,termination_receipt=running,platform_authority_snapshot=running_authority)
        finally:
            work_item_governance.dispatch_inventory=canonical
        self.assertEqual([running["workers"]],calls)
        self.assertTrue(any("worker-stale-1 is registered nonterminal" in row for row in failures))
        self.assertTrue(any("worker-stale-1 was last probed 301s ago" in row for row in failures))
        incomplete=copy.deepcopy(receipt); del incomplete["workers"][0]["owner"]; incomplete_authority=copy.deepcopy(authority); incomplete_authority["workers"]=copy.deepcopy(incomplete["workers"])
        failures=termination_preflight_failures("engineering","engineering_complete",sealed_order=approved,termination_receipt=incomplete,platform_authority_snapshot=incomplete_authority)
        self.assertTrue(any("missing required registration fields: ['owner']" in row for row in failures))
        base=copy.deepcopy(receipt["workers"][0])
        cases=[]
        finished_false=copy.deepcopy(base); finished_false.update({"handle":"worker-finished-false","outcome_complete":False}); cases.append(("finished_false",[finished_false],"incomplete assigned outcome"))
        string_false=copy.deepcopy(base); string_false.update({"handle":"worker-string-false","outcome_complete":"false"}); cases.append(("string_false",[string_false],"outcome_complete must be boolean"))
        unknown=copy.deepcopy(base); unknown.update({"handle":"worker-unknown-field","unsealed_claim":"accepted"}); cases.append(("unknown_field",[unknown],"unknown registration fields"))
        nonfinite=copy.deepcopy(base); nonfinite.update({"handle":"worker-nan","last_probe_age_seconds":float("nan")}); cases.append(("nan_probe",[nonfinite],"non-finite last_probe_age_seconds"))
        nonexistent=copy.deepcopy(base); nonexistent.update({"handle":"worker-missing-successor","state":"dead","outcome_complete":False,"terminal_evidence":"process absence","successor_handle":"worker-not-registered"}); cases.append(("nonexistent_successor",[nonexistent],"is not registered"))
        self_successor=copy.deepcopy(base); self_successor.update({"handle":"worker-self-successor","state":"dead","outcome_complete":False,"terminal_evidence":"process absence","successor_handle":"worker-self-successor"}); cases.append(("self_successor",[self_successor],"itself as successor"))
        mismatch=copy.deepcopy(base); mismatch.update({"handle":"worker-mismatch","assigned_outcome":"finish the primary assigned outcome","state":"dead","outcome_complete":False,"terminal_evidence":"process absence","successor_handle":"worker-other"}); other=copy.deepcopy(base); other.update({"handle":"worker-other","assigned_outcome":"unrelated cleanup"}); cases.append(("successor_outcome_mismatch",[mismatch,other],"different assigned outcome"))
        for label,workers,expected in cases:
            candidate=copy.deepcopy(receipt); candidate["workers"]=workers; snapshot=copy.deepcopy(authority); snapshot["workers"]=copy.deepcopy(workers)
            with self.subTest(adversarial_worker=label):
                failures=termination_preflight_failures("engineering","engineering_complete",sealed_order=approved,termination_receipt=candidate,platform_authority_snapshot=snapshot)
                self.assertTrue(any(expected in row for row in failures),failures)
    def test_termination_preflight_refuses_non_schema_scalar_worker_fields(self):
        approved=order(); receipt,authority=termination_context(approved); base=copy.deepcopy(receipt["workers"][0])
        cases=(("handle","real platform handle"),("assigned_outcome","assigned_outcome must be string"),("owner","owner must be string"),("durable_cursor","durable_cursor must be string"),("terminal_evidence","terminal_evidence must be string"),("successor_handle","successor_handle must be string or null"))
        for field,expected in cases:
            invalid=copy.deepcopy(base); invalid[field]=7; candidate=copy.deepcopy(receipt); candidate["workers"]=[invalid]; snapshot=copy.deepcopy(authority); snapshot["workers"]=copy.deepcopy(candidate["workers"])
            with self.subTest(field=field):
                failures=termination_preflight_failures("engineering","engineering_complete",sealed_order=approved,termination_receipt=candidate,platform_authority_snapshot=snapshot)
                self.assertTrue(any(expected in row for row in failures),failures)
                self.assertFalse(termination_transition_allowed("engineering","engineering_complete",approved,candidate,snapshot))
    def test_termination_preflight_accepts_a_multihop_successor_chain_ending_complete(self):
        approved=order(); receipt,authority=termination_context(approved); base=copy.deepcopy(receipt["workers"][0]); outcome="complete the assigned review"
        completed=copy.deepcopy(base); completed.update({"handle":"worker-chain-c","assigned_outcome":outcome})
        middle=copy.deepcopy(base); middle.update({"handle":"worker-chain-b","assigned_outcome":outcome,"state":"dead","outcome_complete":False,"terminal_evidence":"process absence","successor_handle":"worker-chain-c"})
        first=copy.deepcopy(base); first.update({"handle":"worker-chain-a","assigned_outcome":outcome,"state":"dead","outcome_complete":False,"terminal_evidence":"process absence","successor_handle":"worker-chain-b"})
        valid=copy.deepcopy(receipt); valid["workers"]=[first,middle,completed]; valid_snapshot=copy.deepcopy(authority); valid_snapshot["workers"]=copy.deepcopy(valid["workers"])
        self.assertTrue(termination_transition_allowed("engineering","engineering_complete",approved,valid,valid_snapshot))
    def test_termination_preflight_refuses_a_two_worker_successor_cycle(self):
        approved=order(); receipt,authority=termination_context(approved); base=copy.deepcopy(receipt["workers"][0]); outcome="complete the assigned review"
        first=copy.deepcopy(base); first.update({"assigned_outcome":outcome,"state":"dead","outcome_complete":False,"terminal_evidence":"process absence"})
        cycle_a=copy.deepcopy(first); cycle_a.update({"handle":"worker-cycle-a","successor_handle":"worker-cycle-b"}); cycle_b=copy.deepcopy(first); cycle_b.update({"handle":"worker-cycle-b","successor_handle":"worker-cycle-a"})
        cycle=copy.deepcopy(receipt); cycle["workers"]=[cycle_a,cycle_b]; cycle_snapshot=copy.deepcopy(authority); cycle_snapshot["workers"]=copy.deepcopy(cycle["workers"])
        cycle_failures=termination_preflight_failures("engineering","engineering_complete",sealed_order=approved,termination_receipt=cycle,platform_authority_snapshot=cycle_snapshot)
        self.assertTrue(any("worker-cycle-a" in row and "worker-cycle-b" in row and "cycle" in row for row in cycle_failures),cycle_failures)
    def test_termination_preflight_refuses_a_successor_tail_entering_a_cycle(self):
        approved=order(); receipt,authority=termination_context(approved); base=copy.deepcopy(receipt["workers"][0]); outcome="complete the assigned review"
        first=copy.deepcopy(base); first.update({"assigned_outcome":outcome,"state":"dead","outcome_complete":False,"terminal_evidence":"process absence"})
        cycle_a=copy.deepcopy(first); cycle_a.update({"handle":"worker-cycle-a","successor_handle":"worker-cycle-b"}); cycle_b=copy.deepcopy(first); cycle_b.update({"handle":"worker-cycle-b","successor_handle":"worker-cycle-a"})
        tail=copy.deepcopy(first); tail.update({"handle":"worker-tail","successor_handle":"worker-cycle-a"}); tailed=copy.deepcopy(receipt); tailed["workers"]=[tail,cycle_a,cycle_b]; tailed_snapshot=copy.deepcopy(authority); tailed_snapshot["workers"]=copy.deepcopy(tailed["workers"])
        tail_failures=termination_preflight_failures("engineering","engineering_complete",sealed_order=approved,termination_receipt=tailed,platform_authority_snapshot=tailed_snapshot)
        self.assertTrue(any("worker-tail" in row and "worker-cycle-a" in row and "worker-cycle-b" in row and "cycle" in row for row in tail_failures),tail_failures)
    def test_termination_preflight_never_leaks_overflow_for_a_huge_integer(self):
        approved=order(); receipt,authority=termination_context(approved); base=copy.deepcopy(receipt["workers"][0])
        huge=copy.deepcopy(base); huge.update({"handle":"worker-huge-probe","state":"running","outcome_complete":False,"terminal_evidence":"","last_probe_age_seconds":10**10000}); huge_receipt=copy.deepcopy(receipt); huge_receipt["workers"]=[huge]; huge_snapshot=copy.deepcopy(authority); huge_snapshot["workers"]=copy.deepcopy(huge_receipt["workers"])
        huge_failures=termination_preflight_failures("engineering","engineering_complete",sealed_order=approved,termination_receipt=huge_receipt,platform_authority_snapshot=huge_snapshot)
        self.assertIsInstance(huge_failures,tuple); self.assertTrue(huge_failures); self.assertFalse(termination_transition_allowed("engineering","engineering_complete",approved,huge_receipt,huge_snapshot))
    def test_integrated_mode_requires_visible_single_hat_labels(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # governance/ROLE_TRANSITIONS.md, which governs role and mode
        # transitions; guides/OPERATING_MODES.md restates the label rule for a
        # reader. The two prompt assertions are file-specific -- each names its
        # own label -- so they stay unconditional.
        architecture=(ROOT/"prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        engineering=(ROOT/"prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        substance=("[architect office]","[engineering agent]","one hat")
        self.assert_single_canonical_home(
            lower=True,
            canonical="governance/ROLE_TRANSITIONS.md",
            canonical_substance=substance,
            secondaries={"guides/OPERATING_MODES.md": substance},
        )
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
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8")); self.assertEqual((),validate_profile(profile,core_version())); self.assertTrue(resolve_profile(profile,core_version())["core_applies"])
        with self.assertRaises(ValueError): resolve_profile(None,core_version())
        weak=copy.deepcopy(profile); weak["guarantees"]["security_not_weakened"]=False; self.assertTrue(validate_profile(weak,core_version()))
        unexplained=copy.deepcopy(profile); unexplained["capability_evidence_rationale"].pop("independent_deep_review"); self.assertTrue(validate_profile(unexplained,core_version()))
        mismatch=copy.deepcopy(profile); mismatch["supported_configuration"]["operating_system"]="definitely-not-this-host"; self.assertTrue(runtime_profile_failures(mismatch)); self.assertTrue(capability_preflight(mismatch,["sealed_work_order"],core_version(),ROOT,receipts(mismatch,ROOT))["hard_stop"])
    def test_admission_gate_applies_the_version_from_governed_release_evidence(self):
        """The core version the gate applies is the one release evidence declares.

        Asserted over the value actually handed to both consumers rather than
        over whichever symbol supplies it, so the invariant survives any later
        change in how the version is obtained; and anchored on a direct read of
        release/VERSION.json rather than on the resolver, so the shipped example
        and the resolver cannot satisfy it by being wrong in the same direction.
        """
        shipped=json.loads((ROOT/"release/VERSION.json").read_text(encoding="utf-8"))["version"]
        applied=[]; original_validate=work_item_governance.validate_profile; original_preflight=profile_conformance.capability_preflight
        def spy_validate(profile,core_version): applied.append(core_version); return original_validate(profile,core_version)
        def spy_preflight(profile,requirements,core_version,*rest,**named): applied.append(core_version); return {}
        work_item_governance.validate_profile=spy_validate; profile_conformance.capability_preflight=spy_preflight
        try: work_item_governance.execution_contract_failures(order(),current_handover=None,platform_profile={"mandatory_capabilities":{"sealed_work_order":True}},platform_preflight={})
        finally: work_item_governance.validate_profile=original_validate; profile_conformance.capability_preflight=original_preflight
        self.assertEqual([shipped,shipped],applied,"the profile admission gate and the preflight derivation must both apply the version release/VERSION.json declares")

    def test_malformed_release_evidence_fails_conformance_rather_than_import(self):
        """Malformed version evidence is a conformance failure, never an ImportError.

        work_item_governance is imported by the sealing, classification,
        transition and archival controls and by call sites that never touch a
        platform profile. Resolution bound at import would turn unreadable or
        ambiguous release evidence into an ImportError for every one of them,
        through a channel carrying none of the conformance vocabulary a caller
        is equipped to handle. Failure belongs in the returned failures tuple.
        """
        shipped=json.loads((ROOT/"release/VERSION.json").read_text(encoding="utf-8"))
        cases={"wrong schema string":{**shipped,"schema":"dual-hat-version/2.0"},
            "unknown field":{**shipped,"unexpected_field":"present"},
            "empty version":{**shipped,"version":""},
            "non-semver version":{**shipped,"version":"1.18"},
            "maturity contradicting the version":{**shipped,"version":"0.9.0","maturity":"stable_1_x"}}
        approved=order(); profile={"mandatory_capabilities":{"sealed_work_order":True}}
        for name,record in cases.items():
            with self.subTest(case=name), TemporaryDirectory() as temporary:
                root=Path(temporary); (root/"release").mkdir(); (root/"release/VERSION.json").write_text(json.dumps(record),encoding="utf-8")
                original_root=release_package.ROOT; release_package.ROOT=root
                try: failures=work_item_governance.execution_contract_failures(approved,current_handover=None,platform_profile=profile)
                except ImportError as exc: self.fail(f"{name}: malformed release evidence raised ImportError instead of reporting a conformance failure: {exc}")
                finally: release_package.ROOT=original_root
                self.assertTrue(any("governed release evidence" in row for row in failures),f"{name}: no governed-release-evidence conformance failure entry in {failures}")

    def test_preflight_blocks_known_gap_and_partial_conformance(self):
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8"))
        self.assertTrue(capability_preflight(profile,["sealed_work_order"],core_version(),ROOT,receipts(profile,ROOT))["execution_authorized"])
        result=capability_preflight(profile,["missing_mandatory_rule"],core_version(),ROOT,receipts(profile,ROOT)); self.assertTrue(result["hard_stop"]); self.assertFalse(result["execution_authorized"])
        profile["mandatory_capabilities"]["sealed_work_order"]=False; self.assertTrue(validate_profile(profile,core_version()))
        minimal=copy.deepcopy(profile); minimal["mandatory_capabilities"]={"sealed_work_order":True}; minimal["capability_evidence"]={"sealed_work_order":["test:fake.py"]}
        self.assertIn("platform profile omits mandatory Dual Hat core capabilities",validate_profile(minimal,core_version()))
        approved=order(); handover,profile,preflight=contexts(approved); preflight["capability_evidence_sha256"]="F"*64
        self.assertIn("platform preflight evidence binding is stale or forged",execution_contract_failures(approved,current_handover=handover,platform_profile=profile,platform_preflight=preflight,evidence_root=ROOT))
        handover,profile,preflight=contexts(approved); preflight["preflight_artifact"]="engineering/process/work-items/other/PLATFORM_PREFLIGHT.json"
        self.assertIn("platform preflight contradicts work order or profile",execution_contract_failures(approved,current_handover=handover,platform_profile=profile,platform_preflight=preflight,evidence_root=ROOT))
        fake=copy.deepcopy(profile); fake["capability_evidence"]={name:["test:missing-evidence.py"] for name in fake["mandatory_capabilities"]}
        self.assertFalse(capability_preflight(fake,fake["mandatory_capabilities"],core_version(),ROOT)["execution_authorized"])
        misbound=copy.deepcopy(profile); misbound["capability_evidence"]["independent_deep_review"]=["test:tests/test_quality_review.py"]
        self.assertIn("semantically misbound", " ".join(capability_preflight(misbound,misbound["mandatory_capabilities"],core_version(),ROOT,receipts(misbound,ROOT))["failures"]))
        self.assertTrue(capability_preflight(profile,["independent_deep_review"],core_version(),ROOT,receipts(profile,ROOT))["execution_authorized"])

    def test_preflight_receipts_bind_test_bytes_profile_and_content_not_live_head(self):
        profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as temporary:
            root=Path(temporary); proof=root/"proof.py"; proof.write_text("DUAL_HAT_CAPABILITY_PROOFS="+repr(set(profile["mandatory_capabilities"]))+"\nimport unittest\nclass Proof(unittest.TestCase):\n def test_one(self): self.assertTrue(True)\n",encoding="utf-8")
            subprocess.run(("git","init"),cwd=root,check=True,capture_output=True); subprocess.run(("git","add","proof.py"),cwd=root,check=True,capture_output=True)
            profile["preflight_artifact"]="platform-preflight.json"
            profile["capability_evidence"]={name:["test:proof.py"] for name in profile["mandatory_capabilities"]}
            bound=receipts(profile,root); first=capability_preflight(profile,profile["mandatory_capabilities"],core_version(),root,bound)
            self.assertTrue(first["execution_authorized"]); self.assertNotIn("evidence_repository_commit",first)
            self.assertEqual(bound,receipts(profile,root)); self.assertTrue(first["runtime_profile_verified"])
            proof.write_bytes(proof.read_bytes().replace(b"\r\n",b"\n").replace(b"\n",b"\r\n"))
            self.assertTrue(capability_preflight(profile,profile["mandatory_capabilities"],core_version(),root,bound)["execution_authorized"])
            proof.write_text("DUAL_HAT_CAPABILITY_PROOFS="+repr(set(profile["mandatory_capabilities"]))+"\nimport unittest\nclass Proof(unittest.TestCase):\n def test_two(self): self.assertTrue(True)\n",encoding="utf-8")
            self.assertTrue(capability_preflight(profile,profile["mandatory_capabilities"],core_version(),root,bound)["hard_stop"])
            refreshed=receipts(profile,root); second=capability_preflight(profile,profile["mandatory_capabilities"],core_version(),root,refreshed)
            self.assertNotEqual(first["verified_capability_evidence_sha256"],second["verified_capability_evidence_sha256"])
            contradictory=copy.deepcopy(refreshed); contradictory["test:proof.py"]["passed"]=2
            self.assertTrue(capability_preflight(profile,profile["mandatory_capabilities"],core_version(),root,contradictory)["hard_stop"])
            changed=copy.deepcopy(profile); changed["profile_version"]="1.1.1"
            self.assertNotEqual(second["platform_profile_sha256"],capability_preflight(changed,changed["mandatory_capabilities"],core_version(),root,refreshed)["platform_profile_sha256"])
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
        # Re-pointed (the re-pointing pass). Canonical home
        # governance/ARCHITECTURE_OFFICE_GUIDE.md. The original expressed the
        # prompt's alternate wording with an inline .replace(); that is carried
        # over exactly as an interchangeable-alternatives tuple, which the
        # predicate already supports, so nothing is loosened or tightened.
        substance=("propose the next work to plan",
                   ("does not authorize execution",
                    "planning guidance distinct from execution authority"))
        self.assert_single_canonical_home(
            canonical="governance/ARCHITECTURE_OFFICE_GUIDE.md",
            canonical_substance=substance,
            secondaries={"prompts/ARCHITECTURE_OFFICE_PROMPT.md": substance},
        )
    def test_current_handover_is_generic_and_historical_schema_is_retained(self):
        schema=json.loads((ROOT/"schemas/current-handover.schema.json").read_text(encoding="utf-8")); template=json.loads((ROOT/"templates/CURRENT_HANDOVER.json").read_text(encoding="utf-8"))
        self.assertEqual("dual-hat-current-handover/1.1",template["schema"]); self.assertIn("active_work_item",template); self.assertNotIn("active_capability",template)
        self.assertIn("dual-hat-current-handover/1.0",schema["properties"]["schema"]["enum"])
        self.assertEqual("^[a-z][a-z0-9_]*$",schema["properties"]["active_work_item"]["properties"]["work_item_type"]["pattern"])

    def test_third_party_dependency_evaluation_is_mandatory_in_both_hats(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # governance/THIRD_PARTY_DEPENDENCY_EVALUATION.md -- the contract that
        # defines the evaluation. Its two contract-only requirements ("safety"
        # and the fuller "pros/cons comparison") stay unconditional; only the
        # seven criteria the prompts restate are re-pointed.
        contract=(ROOT/"governance/THIRD_PARTY_DEPENDENCY_EVALUATION.md").read_text(encoding="utf-8")
        self.assertIn("safety",contract)
        self.assertIn("pros/cons comparison",contract)
        substance=("third-party","license","cost","reliability","hardware",
                   "support status","pros/cons")
        self.assert_single_canonical_home(
            canonical="governance/THIRD_PARTY_DEPENDENCY_EVALUATION.md",
            canonical_substance=substance,
            secondaries={
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": substance,
            },
        )

    def test_long_running_work_prefers_subagent_offload_without_false_parallelism(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # governance/VALIDATION_AND_PARALLELISM.md, which owns delegation.
        substance=("on standby to orchestrate and remain immediately available for user interaction",
                   "capability or governance work item, regardless of how many streams it is divided into, delegate execution to sub-agents by default",
                   "every remaining task")
        self.assert_single_canonical_home(
            canonical="governance/VALIDATION_AND_PARALLELISM.md",
            canonical_substance=substance,
            secondaries={"prompts/ENGINEERING_AGENT_PROMPT.md": substance},
        )

    def test_reconciliation_survives_a_competing_new_thread_and_prefers_resuming_workers(self):
        # Caught live: a delegated worker returned a checkpoint and stopped as
        # instructed, but the primary agent got pulled into a newly surfaced
        # finding without resuming it first, leaving it silently idle while
        # believed to still be running; separately, continuations of the same
        # assignment were relaunched fresh instead of resumed, discarding
        # accumulated context. The reconciliation obligation already existed
        # ("before every final response, reconcile... delegated workers") but
        # didn't survive contact with a competing, more salient thread - a
        # lengthy response addressing the new thread satisfied the letter of
        # the rule without the reconciliation happening. This test guards the
        # explicit failure-mode wording added to close that gap.
        # Re-pointed (the re-pointing pass) on the three failure-mode phrases
        # only. Canonical home governance/VALIDATION_AND_PARALLELISM.md, which
        # owns delegation and reconciliation. Every file-specific assertion
        # below stays unconditional.
        engineering_guide = (ROOT/"governance/ENGINEERING_AGENT_GUIDE.md").read_text(encoding="utf-8")
        contract = (ROOT/"governance/VALIDATION_AND_PARALLELISM.md").read_text(encoding="utf-8")
        failure_modes = ("newly surfaced finding","side investigation","user tangent")
        self.assert_single_canonical_home(
            lower=True,
            canonical="governance/VALIDATION_AND_PARALLELISM.md",
            canonical_substance=failure_modes,
            secondaries={"governance/ENGINEERING_AGENT_GUIDE.md": failure_modes},
        )
        self.assertIn("most likely to be silently left idle while attention follows the new thread",engineering_guide)
        self.assertIn("is not reconciled merely because the new thread was addressed thoroughly",engineering_guide)
        self.assertIn("sits silently idle while it is believed to still be running",contract)
        self.assertIn("the gap surfaces only when someone asks for a status update much later",contract)
        normalized_engineering_guide = " ".join(engineering_guide.split())
        self.assertIn("prefer resuming the existing worker for continuation of the same bounded assignment",normalized_engineering_guide)
        self.assertIn("discards its accumulated context",normalized_engineering_guide)

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

    def test_numeric_progress_binds_exact_population_identity(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # governance/VALIDATION_AND_PARALLELISM.md. The two original loops are
        # merged into one substance list -- they ran over the same two files, so
        # splitting them was incidental, not semantic. The inline
        # .replace("yesterday's checkpoint", "earlier checkpoint") becomes an
        # alternatives tuple, preserving exactly which strings satisfy it.
        # The contract-only "proxy row count" stays unconditional.
        contract=(ROOT/"governance/VALIDATION_AND_PARALLELISM.md").read_text(encoding="utf-8")
        substance=("counted unit","denominator population","completion predicate",
                   "secondary evidence","routed/split extras",
                   "uniqueness, coverage, and cursor arithmetic",
                   "living","authoritative evidence","hard-code",
                   ("earlier checkpoint","yesterday's checkpoint"))
        self.assert_single_canonical_home(
            canonical="governance/VALIDATION_AND_PARALLELISM.md",
            canonical_substance=substance,
            secondaries={"prompts/ENGINEERING_AGENT_PROMPT.md": substance},
        )
        self.assertIn("proxy row count",contract)

    def test_active_task_continuity_has_only_governed_early_stops(self):
        # Re-pointed (the re-pointing pass). This test was RED at HEAD -- the
        # known B-1 -- because it required "no safe in-scope action remains" in
        # ENGINEERING_AGENT_PROMPT.md, where that string no longer lives. It is
        # resolved by re-pointing onto the canonical-home contract, NOT by
        # restoring the string, which would reinstate the duplicate this work
        # item exists to remove.
        #
        # Canonical home: framework/DUAL_HAT_FRAMEWORK.md. Measured, not
        # assumed -- it carries all nine loop phrases in full (ROLE_TRANSITIONS
        # also carries nine of nine; ENGINEERING_AGENT_PROMPT carries eight).
        # The framework contract is chosen over the role-transitions document
        # because an obligation binding whenever ANY role may stop is a
        # framework-wide invariant, which is what that file declares itself to
        # hold; ROLE_TRANSITIONS applies it and GOVERNING_PRINCIPLES states the
        # principle. Choosing by which file other files already happen to link
        # to would have inverted that shape to save one pointer.
        #
        # The three file-specific assertions below stay UNCONDITIONAL and
        # outside the canonical-home disjunction. They are not duplication --
        # each exists in exactly one file -- so folding them in would convert an
        # unconditional obligation into a waivable one for no gain.
        framework=(ROOT/"framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        architecture=(ROOT/"prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("Active-task continuity",framework)
        self.assertIn("transition directly to `[Architect Office]`",framework)
        self.assertIn("task is complete and reported",architecture)
        substance=("explicitly orders","user decision","Architecture Office decision",
                   "explicitly specified stop gate","end of a message","side question",
                   "termination preflight","no safe in-scope action remains","persistent")
        self.assert_single_canonical_home(
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={
                "governance/ROLE_TRANSITIONS.md": substance,
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
            },
        )

    def test_active_goal_interlocks_response_with_continuation_action(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # framework/DUAL_HAT_FRAMEWORK.md, which carries all eleven phrases in
        # full; so do all three secondaries today, so the pre-consolidation
        # branch holds unchanged and nothing is unguarded in the interim.
        # The three framework-only assertions stay unconditional: they are not
        # duplication and must not become waivable.
        framework=(ROOT/"framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        self.assertIn("promise",framework)
        self.assertIn("automatic continuation",framework)
        self.assertIn("Repeated premature termination",framework)
        substance=("same turn","observable continuation action","reactivate",
                   "persisted cursor","execution lease","classify","progress response",
                   "terminal","response","boundary","cannot release it")
        self.assert_single_canonical_home(
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={
                "governance/ROLE_TRANSITIONS.md": substance,
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": substance,
            },
        )

    def test_active_goal_has_response_end_watchdog(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # framework/DUAL_HAT_FRAMEWORK.md: the response-end watchdog is stated
        # there as a framework-wide invariant and restated by both prompts.
        substance=("response-end watchdog","poll","reactivate","worker",
                   "continuation receipt","durable cursor or process identity",
                   "same turn","prose-only status")
        self.assert_single_canonical_home(
            lower=True,
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": substance,
            },
        )

    def test_persistent_goal_is_checked_and_restored_at_response_boundaries(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # framework/DUAL_HAT_FRAMEWORK.md. "checked execution invariant" is
        # framework-only and stays unconditional.
        framework=(ROOT/"framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        self.assertIn("checked execution invariant",framework)
        substance=("goal","continuation instruction","context","restore",
                   "before answering","reactivate")
        self.assert_single_canonical_home(
            lower=True,
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={
                "governance/ROLE_TRANSITIONS.md": substance,
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": substance,
            },
        )

    def test_itemized_review_cannot_skip_from_partial_triage_to_persistence(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # framework/DUAL_HAT_FRAMEWORK.md.
        substance=("evidence acquired","partially triaged","fully adjudicated",
                   "persist-ready","completion predicate","no omissions or duplicates",
                   "context-exhausted worker","durable evidence and cursor")
        self.assert_single_canonical_home(
            lower=True,
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={"prompts/ENGINEERING_AGENT_PROMPT.md": substance},
        )

    def test_closure_requires_proactive_delivery_of_promised_results(self):
        closure=(ROOT/"process/PUBLICATION_AND_CLOSURE.md").read_text(encoding="utf-8")
        for required in ("explicitly promised stakeholder-facing", "proactively presented", "archiving an artifact is not delivery", "do not wait for the stakeholder"):
            self.assertIn(required,closure)

    def test_validation_gate_cannot_share_compound_command_with_mutation(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # governance/ENGINEERING_AGENT_GUIDE.md -- measured, not preferred:
        # validation/VALIDATION_PROTOCOL.md would be the topical owner but does
        # not carry either phrase today, and a canonical home must be asserted
        # in full or the assertion is a lie about where the obligation lives.
        substance=("validation gate","compound shell")
        self.assert_single_canonical_home(
            canonical="governance/ENGINEERING_AGENT_GUIDE.md",
            canonical_substance=substance,
            secondaries={"prompts/ENGINEERING_AGENT_PROMPT.md": substance},
        )

    def test_gates_distinguish_committed_inputs_from_runtime_state(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # validation/VALIDATION_PROTOCOL.md, which owns gate semantics; the
        # guide and the prompt restate it. The protocol-only assertion stays
        # unconditional.
        protocol=(ROOT/"validation/VALIDATION_PROTOCOL.md").read_text(encoding="utf-8")
        substance=("lifecycle and packaging class","committed-tree identity",
                   "runtime data","production")
        self.assert_single_canonical_home(
            canonical="validation/VALIDATION_PROTOCOL.md",
            canonical_substance=substance,
            secondaries={
                "governance/ENGINEERING_AGENT_GUIDE.md": substance,
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
            },
        )
        self.assertIn("must not require such state to be Git tracked"," ".join(protocol.split()))

    def test_transition_gates_distinguish_prestate_from_replay(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # validation/VALIDATION_PROTOCOL.md; protocol-only assertion stays
        # unconditional.
        protocol=(ROOT/"validation/VALIDATION_PROTOCOL.md").read_text(encoding="utf-8")
        substance=("pre-state","post-state","immutable execution evidence",
                   "public command surface")
        self.assert_single_canonical_home(
            canonical="validation/VALIDATION_PROTOCOL.md",
            canonical_substance=substance,
            secondaries={
                "governance/ENGINEERING_AGENT_GUIDE.md": substance,
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
            },
        )
        self.assertIn("later maintenance commits must not invalidate historical evidence"," ".join(protocol.split()))

    def test_zero_test_execution_is_not_passing_evidence(self):
        # Re-pointed (the re-pointing pass). Canonical home
        # validation/VALIDATION_PROTOCOL.md.
        substance=("nonzero","zero","validation failure")
        self.assert_single_canonical_home(
            canonical="validation/VALIDATION_PROTOCOL.md",
            canonical_substance=substance,
            secondaries={"prompts/ENGINEERING_AGENT_PROMPT.md": substance},
        )

    def test_closure_dispositions_scoped_outputs_off_current_surfaces(self):
        closure=(ROOT/"process/PUBLICATION_AND_CLOSURE.md").read_text(encoding="utf-8")
        phase=(ROOT/"process/PHASE_RUN_PROTOCOL.md").read_text(encoding="utf-8")
        prompt=(ROOT/"prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for required in ("only current operationally consumed artifacts", "historical evidence", "disposable duplication"):
            self.assertIn(required,closure)
        self.assertIn("Capability chronology must not remain mixed into current product output",phase)
        self.assertIn("active/output locations limited to current operational artifacts",prompt)

if __name__ == "__main__": unittest.main()
