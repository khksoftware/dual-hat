# SPDX-License-Identifier: Apache-2.0
"""Small in-memory proofs for generic review assurance; no product fixture."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from review_assurance import (BASIS_SCHEMA, DEEP_REVIEW_HAZARDS, EVIDENCE_SCHEMA,
                              REVIEW_PLAN_SCHEMA, canonical_digest,
                              deep_review_plan_failures, falsify_checker, python_carrier_inventory,
                              required_interactions, validate_assurance)


def fixture():
    basis = {
        "schema": BASIS_SCHEMA, "source_bindings": {"prior-contract": "a" * 64},
        "contract": {"Record": [["key", "str"], ["value", "int"]], "ordering": "key ascending"},
        "changes": [], "source_obligations": ["old-exact-value"],
        "obligations": [["decode", "value", "exact-type"]],
        "transitions": [{"id": "revoke", "writes": ["authority"]}, {"id": "rename", "writes": ["label"]}],
        "invariants": [{"id": "retained-state", "reads": ["authority", "state"], "observations": ["state", "history", "replay"]}],
    }
    evidence = {
        "schema": EVIDENCE_SCHEMA, "basis_sha256": canonical_digest(basis),
        "source_bindings": dict(basis["source_bindings"]), "contract": copy.deepcopy(basis["contract"]),
        "cases": [{"id": "case", "obligation": ["decode", "value", "exact-type"], "witness": "boolean where integer is required", "covers": ["old-exact-value"]}],
        "witnesses": [{"id": "joined", "observations": {"state": "unchanged", "history": "retirement recorded", "replay": "same result"}}],
        "interactions": [{"transition": "revoke", "invariant": "retained-state", "witness_id": "joined"}],
    }
    return basis, evidence


def deep_review_plan_fixture():
    chain = {
        "authority": "Current author decision and its superseded predecessor",
        "producer": "The controller that creates the exact object",
        "representation": "Canonical fields, bytes, and digest",
        "transition": "The only state edge the object can open",
        "consumer": "The author-visible consumer and interface",
        "failure_recovery": "Every partial boundary stops or recovers without invention",
        "evidence": "A source-backed positive and negative integration witness",
    }
    return {
        "schema": REVIEW_PLAN_SCHEMA,
        "tier": "deep_complete_object",
        "subject_sha256": "a" * 64,
        "separation": {
            "candidate_frozen": True,
            "candidate_author_separate": True,
            "sibling_findings_hidden": True,
            "ambient_context_disclosed": True,
            "durable_report_target_predeclared": True,
            "package_no_write": True,
            "tooling_execution_copy_separate": True,
            "post_tool_inventory_verified": True,
            "transitive_imports_manifested": True,
        },
        "claims": [{
            "id": "delivery",
            "assertion": "The author receives the complete result",
            "risk": "A local hash can be mistaken for delivery",
            "chain": chain,
            "source_anchors": [{"id": "delivery-adapter", "sha256": "b" * 64}],
            "falsification_cases": [
                {"id": "visible", "polarity": "positive", "witness": "consumer receives bytes"},
                {"id": "hash-only", "polarity": "negative", "witness": "hash without bytes refuses"},
            ],
        }],
        "hazard_dispositions": [{"hazard": hazard, "status": "applicable",
                                 "basis": "Checked against primary source"}
                                for hazard in DEEP_REVIEW_HAZARDS],
    }


class ReviewAssuranceTests(unittest.TestCase):
    def test_deep_review_plan_requires_complete_claim_chains_and_future_hazard_population(self):
        plan = deep_review_plan_fixture()
        self.assertEqual((), deep_review_plan_failures(plan))
        mutants = []
        damaged = copy.deepcopy(plan); damaged["claims"][0]["chain"].pop("consumer"); mutants.append(damaged)
        damaged = copy.deepcopy(plan); damaged["claims"][0]["source_anchors"] = []; mutants.append(damaged)
        damaged = copy.deepcopy(plan); damaged["claims"][0]["falsification_cases"] = damaged["claims"][0]["falsification_cases"][:1]; mutants.append(damaged)
        damaged = copy.deepcopy(plan); damaged["hazard_dispositions"].pop(); mutants.append(damaged)
        damaged = copy.deepcopy(plan); damaged["separation"]["sibling_findings_hidden"] = False; mutants.append(damaged)
        damaged = copy.deepcopy(plan); damaged["separation"]["package_no_write"] = False; mutants.append(damaged)
        damaged = copy.deepcopy(plan); damaged["claims"].append(copy.deepcopy(damaged["claims"][0])); mutants.append(damaged)
        for damaged in mutants:
            self.assertTrue(deep_review_plan_failures(damaged), damaged)

    def test_source_falsification_detects_an_extractor_blind_spot(self):
        from review_assurance import falsify_source_adapter, markdown_contract_units
        basis, evidence = fixture()
        source = b'Intro\n\n## Layout\n\nFields in order.\n\n## Behavior\n\nRevocation preserves history.\n'
        basis['contract'] = markdown_contract_units(source.decode())
        evidence['basis_sha256'] = canonical_digest(basis)
        evidence['contract'] = copy.deepcopy(basis['contract'])
        sources = {'contract.md': source}
        def extract(actual):
            result = copy.deepcopy(evidence)
            result['contract'] = markdown_contract_units(actual['contract.md'].decode())
            return result
        mutations = [('remove-behavior', {'contract.md': source[:source.index(b'## Behavior')]}),
                     ('change-clause', {'contract.md': source.replace(b'preserves', b'discards')})]
        report = falsify_source_adapter(basis, sources, extract, mutations)
        self.assertTrue(report['green'], report)
        blind = falsify_source_adapter(basis, sources, lambda _: copy.deepcopy(evidence), mutations)
        self.assertFalse(blind['green'])
        self.assertTrue(all(not row['rejected'] for row in blind['mutants']))
        self.assertEqual(source, sources['contract.md'])

    def test_source_falsification_requires_applied_unique_mutations_and_valid_control(self):
        from review_assurance import falsify_source_adapter
        basis, evidence = fixture()
        sources = {'spec': b'original'}
        for mutations in ([], [('noop', sources)], [('bad', {'spec': 'not bytes'})],
                          [('same', {'spec': b'a'}), ('same', {'spec': b'b'})]):
            report = falsify_source_adapter(basis, sources, lambda _: evidence, mutations)
            self.assertFalse(report['green'], report)
        evidence['contract'] = {}
        report = falsify_source_adapter(basis, sources, lambda _: evidence, [('change', {'spec': b'changed'})])
        self.assertFalse(report['green'])
        self.assertTrue(report['baseline_errors'])

    def test_markdown_contract_inventory_preserves_all_bytes_and_ignores_fenced_headings(self):
        from review_assurance import markdown_contract_units
        text = 'Preamble\n\n## A\n\n```text\n## Not a heading\n```\n\n## B\n\nRule.\n'
        units = markdown_contract_units(text)
        self.assertEqual(['preamble', 'section:A', 'section:B'], list(units))
        self.assertEqual(text, ''.join(units.values()))
        self.assertIn('## Not a heading', units['section:A'])
        with self.assertRaises(ValueError): markdown_contract_units('## A\n\n## A\n')
        with self.assertRaises(ValueError): markdown_contract_units('## A\n```python\n')

    def test_source_proof_cannot_only_exercise_parser_failure(self):
        from review_assurance import falsify_source_adapter
        basis, evidence = fixture()
        def extract(sources):
            sources['spec'].decode('utf-8')
            return evidence
        report = falsify_source_adapter(basis, {'spec': b'valid'}, extract,
                                        [('invalid-encoding', {'spec': b'\xff'})])
        self.assertFalse(report['green'], report)
        self.assertTrue(report['errors'])

    def test_source_section_order_survives_canonical_json(self):
        from review_assurance import markdown_contract_inventory
        first, second = '## A\nFirst.\n', '## B\nSecond.\n'
        expected = markdown_contract_inventory(first + second)
        reordered = markdown_contract_inventory(second + first)
        self.assertNotEqual(canonical_digest(expected), canonical_digest(reordered))
        self.assertEqual(canonical_digest(expected), canonical_digest(json.loads(json.dumps(expected, sort_keys=True))))

    def test_falsification_is_identical_after_canonical_json_round_trip(self):
        basis, evidence = fixture()
        original = falsify_checker(basis, evidence)
        decoded = json.loads(json.dumps(evidence, sort_keys=True))
        self.assertEqual(original, falsify_checker(basis, decoded))

    def test_acceptance_consumer_requires_both_inputs_and_preserves_existing_blockers(self):
        from quality_review import review_acceptance_blockers
        basis, evidence = fixture()
        self.assertTrue(review_acceptance_blockers([], require_assurance=True))
        self.assertTrue(review_acceptance_blockers([], assurance_basis=basis))
        self.assertEqual((), review_acceptance_blockers([], assurance_basis=basis, assurance_evidence=evidence, require_assurance=True))
        evidence["contract"].pop("Record")
        self.assertTrue(review_acceptance_blockers([], assurance_basis=basis, assurance_evidence=evidence, require_assurance=True))
        self.assertEqual(("blocking",), review_acceptance_blockers([{"finding_id": "blocking", "severity": "high", "disposition": "open"}]))

    def test_real_accepted_deep_baseline_path_requires_plan_basis_and_evidence(self):
        from quality_review import ASSURANCE_REQUIRED_FROM_VERSION, baseline_hash, governed_state_binding_hash, validate_baseline
        basis, evidence = fixture()
        payload = {
            "baseline_id": "BASE-ASSURED", "repository_commit": "A" * 40,
            "dual_hat_commit": "B" * 40, "dual_hat_version": ".".join(map(str, ASSURANCE_REQUIRED_FROM_VERSION)), "date": "2026-09-08",
            "review_scope": [], "exclusions": [], "selected_review_tier": "deep",
            "active_platform_profile": {"profile_id": "test", "profile_version": "1.0.0",
                                        "profile_sha256": "C" * 64},
            "user_rule_sources": [], "rule_set_hash": "D" * 64, "effective_plan_hash": "E" * 64,
            "review_methods": ["independent review"], "tool_versions": {},
            "principal_metrics": {"coverage": {"value": 1, "desired_direction": "increase"}},
            "risk_areas": [], "accepted_exceptions": [], "user_approved_tradeoffs": [],
            "unresolved_findings": [], "debt_references": [], "validation_evidence": ["assurance"],
            "architecture_disposition_state": "accepted", "suppressed_architecture_rules": [],
            "replaced_rules": [], "severity_adjustments": [], "rule_conflicts": [],
            "non_waivable_controls": ["deep assurance"], "preliminary_findings_mapping": [],
            "final_findings": [], "remediated_findings": [], "residual_risk": [],
            "deep_review_plan": deep_review_plan_fixture(),
            "review_assurance_basis": basis, "review_assurance_evidence": evidence,
        }
        binding = {
            "schema": "dual-hat-governed-state-binding/1.0", "repository_identity": "test",
            "repository_commit": payload["repository_commit"], "dual_hat_commit": payload["dual_hat_commit"],
            "dual_hat_version": payload["dual_hat_version"],
            "active_platform_profile": payload["active_platform_profile"],
            "rule_set_hash": payload["rule_set_hash"], "effective_plan_hash": payload["effective_plan_hash"],
            "work_item_id": "GOV-TEST", "work_order_revision": 1,
            "sealed_work_order_hash": "F" * 64, "lifecycle_state": "accepted",
            "architecture_disposition_state": "accepted", "source_paths": {"fixture": "test"},
        }
        binding["binding_hash"] = governed_state_binding_hash(binding)
        payload["governed_state_binding"] = binding
        # The accepted plan must name the governed state it reviewed.
        payload["deep_review_plan"]["subject_sha256"] = binding["binding_hash"].lower()
        payload["baseline_hash"] = baseline_hash(payload)
        self.assertEqual((), validate_baseline(payload))
        for field in ("deep_review_plan", "review_assurance_basis", "review_assurance_evidence"):
            damaged = copy.deepcopy(payload); damaged.pop(field); damaged["baseline_hash"] = baseline_hash(damaged)
            self.assertTrue(validate_baseline(damaged), field)
        damaged = copy.deepcopy(payload); damaged["review_assurance_evidence"]["cases"] = []
        damaged["baseline_hash"] = baseline_hash(damaged)
        self.assertTrue(validate_baseline(damaged))

    def test_valid_control_and_only_dependency_relevant_pairs(self):
        basis, evidence = fixture()
        self.assertEqual((), validate_assurance(basis, evidence))
        self.assertEqual({("revoke", "retained-state"): ["state", "history", "replay"]}, required_interactions(basis))

    def test_whole_contract_loss_change_addition_and_field_order_refuse(self):
        for mode in ("loss", "change", "addition", "order"):
            with self.subTest(mode=mode):
                basis, evidence = fixture()
                if mode == "loss": del evidence["contract"]["Record"]
                if mode == "change": evidence["contract"]["ordering"] = "descending"
                if mode == "addition": evidence["contract"]["surprise"] = []
                if mode == "order": evidence["contract"]["Record"].reverse()
                self.assertTrue(validate_assurance(basis, evidence))

    def test_explicit_replacement_is_before_bound_and_requires_reason_authority(self):
        basis, evidence = fixture()
        row = {"id": "ordering", "before_sha256": canonical_digest("key ascending"), "after": "key descending", "disposition": "replace", "authority": "approved decision", "reason": "reverse view"}
        basis["changes"] = [row]
        evidence["basis_sha256"] = canonical_digest(basis)
        evidence["contract"]["ordering"] = row["after"]
        self.assertEqual((), validate_assurance(basis, evidence))
        for key, value in (("before_sha256", "0" * 64), ("reason", ""), ("authority", "")):
            broken = copy.deepcopy(basis); broken["changes"][0][key] = value
            damaged = copy.deepcopy(evidence); damaged["basis_sha256"] = canonical_digest(broken)
            self.assertTrue(validate_assurance(broken, damaged))

    def test_explicit_addition_and_removal_are_accounted(self):
        for disposition in ("add", "remove"):
            basis, evidence = fixture()
            key = "new" if disposition == "add" else "ordering"
            basis["changes"] = [{"id": key, "before_sha256": None if disposition == "add" else canonical_digest(basis["contract"][key]), "after": 5 if disposition == "add" else None, "disposition": disposition, "reason": "bounded change", "authority": "decision"}]
            if disposition == "add": evidence["contract"][key] = 5
            else: del evidence["contract"][key]
            evidence["basis_sha256"] = canonical_digest(basis)
            self.assertEqual((), validate_assurance(basis, evidence))

    def test_relabeling_and_rewording_do_not_defeat_semantic_deduplication(self):
        basis, evidence = fixture()
        row = copy.deepcopy(evidence["cases"][0]); row.update(id="another", witness="completely different prose", covers=[])
        evidence["cases"].append(row)
        self.assertTrue(any("duplicate semantic" in error for error in validate_assurance(basis, evidence)))

    def test_missing_and_extra_obligations_and_lost_source_accounting_refuse(self):
        for mode in ("missing", "extra", "lost-source", "duplicate-source"):
            basis, evidence = fixture()
            if mode == "missing": evidence["cases"] = []
            if mode == "extra": evidence["cases"][0]["obligation"] = ["different"]
            if mode == "lost-source": evidence["cases"][0]["covers"] = []
            if mode == "duplicate-source": evidence["cases"][0]["covers"] *= 2
            self.assertTrue(validate_assurance(basis, evidence))

    def test_new_dependency_effect_cannot_hide_behind_old_interaction_count(self):
        basis, evidence = fixture()
        basis["transitions"][1]["writes"].append("authority")
        evidence["basis_sha256"] = canonical_digest(basis)
        self.assertEqual(2, len(required_interactions(basis)))
        self.assertTrue(validate_assurance(basis, evidence))

    def test_every_required_observation_and_witness_is_checked(self):
        for mode in ("state", "history", "replay", "witness", "empty", "orphan"):
            basis, evidence = fixture()
            if mode in {"state", "history", "replay"}: del evidence["witnesses"][0]["observations"][mode]
            if mode == "witness": evidence["interactions"][0]["witness_id"] = "absent"
            if mode == "empty": evidence["witnesses"][0]["observations"]["state"] = ""
            if mode == "orphan": evidence["interactions"] = []
            self.assertTrue(validate_assurance(basis, evidence))

    def test_basis_and_primary_source_drift_refuse(self):
        basis, evidence = fixture()
        evidence["basis_sha256"] = "0" * 64
        self.assertTrue(validate_assurance(basis, evidence))
        evidence["basis_sha256"] = canonical_digest(basis)
        evidence["source_bindings"]["prior-contract"] = "b" * 64
        self.assertTrue(validate_assurance(basis, evidence))

    def test_malformed_inputs_fail_closed(self):
        for value in (None, [], {}, {"schema": BASIS_SCHEMA}, "looks valid"):
            self.assertTrue(validate_assurance(value, value))
        basis, evidence = fixture()
        for key in basis:
            broken = copy.deepcopy(basis); broken[key] = None
            self.assertTrue(validate_assurance(broken, evidence))
        for key in evidence:
            broken = copy.deepcopy(evidence); broken[key] = None
            self.assertTrue(validate_assurance(basis, broken))

    def test_checker_falsification_rejects_every_mutant_and_a_disabled_checker(self):
        basis, evidence = fixture()
        report = falsify_checker(basis, evidence)
        self.assertTrue(report["green"], report)
        self.assertEqual(11, len(report["mutants"]))
        disabled = falsify_checker(basis, evidence, checker=lambda *_: ())
        self.assertFalse(disabled["green"])
        self.assertFalse(any(row["rejected"] for row in disabled["mutants"]))

    def test_red_control_cannot_be_reported_as_successful_falsification(self):
        basis, evidence = fixture(); evidence["cases"] = []
        report = falsify_checker(basis, evidence)
        self.assertFalse(report["green"]); self.assertEqual([], report["mutants"])

    def test_literal_carrier_adapter_preserves_type_and_order_and_refuses_duplicates(self):
        text = "```python\nclass Record:\n    key: str\n    value: int | None\n```"
        self.assertEqual({"Record": [("key", "str"), ("value", "int | None")]}, python_carrier_inventory(text))
        with self.assertRaises(ValueError): python_carrier_inventory(text + "\n" + text)
        with self.assertRaises(SyntaxError): python_carrier_inventory("```python\nclass !\n```")

    def test_carrier_metadata_detects_mutability_defaults_bases_and_methods(self):
        original = "```python\n@dataclass(frozen=True)\nclass Record:\n    key: str\n```"
        expected = python_carrier_inventory(original, metadata=True)
        for changed in (original.replace("frozen=True", "frozen=False"), original.replace("key: str", "key: str = 'default'"), original.replace("class Record:", "class Record(Base):"), original.replace("    key: str", "    key: str\n    def extra(self): pass")):
            self.assertNotEqual(expected, python_carrier_inventory(changed, metadata=True))


if __name__ == "__main__":
    unittest.main()
