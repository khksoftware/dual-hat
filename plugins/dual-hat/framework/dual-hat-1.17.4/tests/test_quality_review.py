"""Systemic quality-rule, tier, finding, and baseline tests.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

DUAL_HAT_CAPABILITY_PROOFS = {"quality_rule_discovery"}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from quality_review import (  # noqa: E402
    baseline_hash, compare_baselines, derive_governed_baseline_state, discover_rule_files, effective_review_plan, load_rules,
    governed_state_binding_hash, review_acceptance_blockers, select_review_tier, validate_baseline,
    validate_baseline_against_state, validate_baseline_from_repository, validate_rule, write_generated_json,
)


def rule(rule_id: str, *, precedence: str, action: dict, tiers=None, validity=None, scope=None) -> dict:
    value = {
        "rule_id": rule_id, "title": rule_id, "source": "test", "owner": "test",
        "rationale": "Systemic test-owned rule rationale.", "status": "enabled",
        "scope": scope if scope is not None else {"repositories": ["repo"], "triggers": ["review"]},
        "review_tiers": tiers or ["light", "standard", "deep"], "action": action,
        "precedence": precedence, "created_date": "2026-01-01", "modified_date": "2026-01-01",
        "revision": 1, "provenance": "test", "conflict_behavior": "surface", "lifecycle_state": "active",
    }
    if validity: value["validity"] = validity
    return value


def bind_baseline(baseline: dict, *, disposition: str | None = None) -> dict:
    state = {
        "schema":"dual-hat-governed-state-binding/1.0", "repository_identity":"test",
        "repository_commit":baseline["repository_commit"], "dual_hat_commit":baseline["dual_hat_commit"],
        "dual_hat_version":baseline["dual_hat_version"], "active_platform_profile":baseline["active_platform_profile"],
        "rule_set_hash":baseline["rule_set_hash"], "effective_plan_hash":baseline["effective_plan_hash"],
        "work_item_id":"GOV-0001", "work_order_revision":1, "sealed_work_order_hash":"D"*64,
        "lifecycle_state":"engineering", "architecture_disposition_state":disposition or baseline["architecture_disposition_state"],
        "source_paths":{"resolver_config":"quality/state.json"},
    }
    state["binding_hash"] = governed_state_binding_hash(state)
    baseline["governed_state_binding"] = state
    return state


class QualityReviewTests(unittest.TestCase):
    def test_canonical_architecture_rules_satisfy_runtime_contract(self) -> None:
        rules=load_rules(ROOT/"review/ARCHITECTURE_DEFAULT_RULES.json")
        self.assertEqual(7,len(rules)); self.assertTrue(any(rule["precedence"]=="non_waivable" for rule in rules))

    def test_discovery_detects_manual_change_and_hashes_normalized_rules(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary); rules = root / "rules"; rules.mkdir()
            config = root / "sources.json"
            config.write_text(json.dumps({"sources": [{"source_id": "user", "path": "rules", "required": True}]}), encoding="utf-8")
            path = rules / "user.json"
            path.write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0", "rules": [rule("USER-1", precedence="user", action={"type": "require"})]}), encoding="utf-8")
            first = discover_rule_files(root, config)
            payload = json.loads(path.read_text(encoding="utf-8")); payload["rules"][0]["revision"] = 2
            path.write_text(json.dumps(payload), encoding="utf-8")
            second = discover_rule_files(root, config, first)
            self.assertEqual(["rules/user.json"], second["changes"]["modified"])
            self.assertNotEqual(first["rule_set_hash"], second["rule_set_hash"])

    def test_top_level_comment_is_schema_valid_metadata_not_rule_identity(self) -> None:
        schema = json.loads((ROOT / "schemas/quality-rule.schema.json").read_text(encoding="utf-8"))
        self.assertEqual({"type": "string"}, schema["properties"]["$comment"])
        with TemporaryDirectory() as temporary:
            root = Path(temporary); rules = root / "rules"; rules.mkdir()
            config = root / "sources.json"
            config.write_text(json.dumps({"sources": [{"source_id": "user", "path": "rules", "required": True}]}), encoding="utf-8")
            path = rules / "user.json"
            payload = {"$comment": "first", "schema": "dual-hat-quality-rules/1.0", "rules": [rule("USER-1", precedence="user", action={"type": "require"})]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            first = discover_rule_files(root, config)
            payload["$comment"] = "second"; path.write_text(json.dumps(payload), encoding="utf-8")
            second = discover_rule_files(root, config, first)
            self.assertEqual(["rules/user.json"], second["changes"]["modified"])
            self.assertNotEqual(first["source_inventory_hash"], second["source_inventory_hash"])
            self.assertEqual(first["rule_set_hash"], second["rule_set_hash"])

    def test_tier_suppression_applies_but_non_waivable_conflict_blocks(self) -> None:
        architecture = [
            rule("ARCH-DISCRETIONARY", precedence="architecture_default", action={"type": "require"}),
            rule("CORE-RIGHTS", precedence="non_waivable", action={"type": "require"}),
        ]
        suppress = rule("USER-SUPPRESS", precedence="user", tiers=["light"],
                        action={"type": "suppress", "target_rule_id": "ARCH-DISCRETIONARY"})
        context = {"repository": "repo", "trigger": "review", "date": "2026-07-20"}
        light = effective_review_plan(architecture, [suppress], "light", context, "A" * 64)
        deep = effective_review_plan(architecture, [suppress], "deep", context, "A" * 64)
        self.assertEqual(["ARCH-DISCRETIONARY"], [row["underlying_rule_id"] for row in light["suppressed_rules"]])
        self.assertEqual([], deep["suppressed_rules"])
        waive = rule("USER-WAIVE-RIGHTS", precedence="user",
                     action={"type": "exempt", "target_rule_id": "CORE-RIGHTS"})
        blocked = effective_review_plan(architecture, [waive], "deep", context, "B" * 64)
        self.assertFalse(blocked["review_authorized"])
        self.assertEqual("non_waivable_conflict", blocked["conflicts"][0]["type"])

    def test_repository_wide_context_includes_every_scoped_review_category(self) -> None:
        architecture = [
            rule("ARCH-CORRECT", precedence="architecture_default", action={"type": "require"},
                 scope={"review_categories": ["correctness"]}),
            rule("ARCH-SECURITY", precedence="architecture_default", action={"type": "require"},
                 scope={"review_categories": ["security"]}),
        ]
        plan = effective_review_plan(
            architecture, [], "deep",
            {"repository": "repo", "review_category": "*", "path": "*"}, "A" * 64,
        )
        self.assertEqual(
            {"ARCH-CORRECT", "ARCH-SECURITY"},
            {row["rule_id"] for row in plan["active_architecture_rules"]},
        )

    def test_narrower_scope_and_explicit_tier_win_user_rule_precedence(self) -> None:
        architecture = [rule("ARCH-TARGET", precedence="architecture_default", action={"type":"require"},
                             scope={"paths":["*"]})]
        broad = rule("USER-BROAD", precedence="user", action={"type":"suppress", "target_rule_id":"ARCH-TARGET"},
                     scope={"paths":["core/*"]})
        narrow = rule("USER-NARROW", precedence="user", action={"type":"adjust_severity", "target_rule_id":"ARCH-TARGET", "severity":"high"},
                      scope={"paths":["core/src/framework/*"]})
        context = {"path":"core/src/framework/example.py", "date":"2026-07-20"}
        plan = effective_review_plan(architecture, [broad, narrow], "deep", context, "A"*64)
        self.assertEqual(["USER-NARROW"], [row["rule_id"] for row in plan["active_user_rules"]])
        general = rule("USER-GENERAL-TIER", precedence="user", action={"type":"suppress", "target_rule_id":"ARCH-TARGET"}, scope={"paths":["core/*"]})
        explicit = rule("USER-EXPLICIT-TIER", precedence="user", tiers=["deep"], action={"type":"adjust_severity", "target_rule_id":"ARCH-TARGET", "severity":"medium"}, scope={"paths":["core/*"]})
        plan = effective_review_plan(architecture, [general, explicit], "deep", context, "B"*64)
        self.assertEqual(["USER-EXPLICIT-TIER"], [row["rule_id"] for row in plan["active_user_rules"]])
        broadened = rule("USER-BROADENED", precedence="user", action={"type":"suppress", "target_rule_id":"ARCH-TARGET"}, scope={"paths":["core/a.py", "core/b.py"]})
        single = rule("USER-SINGLE", precedence="user", action={"type":"adjust_severity", "target_rule_id":"ARCH-TARGET", "severity":"low"}, scope={"paths":["core/a.py"]})
        plan = effective_review_plan(architecture, [broadened, single], "deep", {"path":"core/a.py", "date":"2026-07-20"}, "C"*64)
        self.assertEqual(["USER-SINGLE"], [row["rule_id"] for row in plan["active_user_rules"]])
        wildcard_dimensions=rule("USER-WILDCARD-DIMS",precedence="user",action={"type":"suppress","target_rule_id":"ARCH-TARGET"},scope={"repositories":["*"],"paths":["*"]})
        exact=rule("USER-EXACT",precedence="user",action={"type":"adjust_severity","target_rule_id":"ARCH-TARGET","severity":"low"},scope={"paths":["core/a.py"]})
        plan=effective_review_plan(architecture,[wildcard_dimensions,exact],"deep",{"repository":"repo","path":"core/a.py","date":"2026-07-20"},"D"*64)
        self.assertEqual(["USER-EXACT"],[row["rule_id"] for row in plan["active_user_rules"]])
        mixed=rule("USER-MIXED",precedence="user",action={"type":"suppress","target_rule_id":"ARCH-TARGET"},scope={"paths":["*","core/a.py"]})
        plan=effective_review_plan(architecture,[mixed,exact],"deep",{"path":"core/a.py","date":"2026-07-20"},"E"*64)
        self.assertEqual(["USER-EXACT"],[row["rule_id"] for row in plan["active_user_rules"]])

    def test_runtime_rule_validation_matches_public_required_semantics_and_revisions(self) -> None:
        invalid = rule("USER-INVALID", precedence="user", action={"type":"require"}); invalid["owner"]=""; invalid["created_date"]="today"
        with TemporaryDirectory() as temporary:
            root=Path(temporary); rules=root/"rules"; rules.mkdir(); config=root/"sources.json"
            config.write_text(json.dumps({"sources":[{"path":"rules","required":True}]}),encoding="utf-8")
            (rules/"invalid.json").write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0","rules":[invalid]}),encoding="utf-8")
            self.assertTrue(discover_rule_files(root,config)["errors"])
            older=rule("USER-REV",precedence="user",action={"type":"require"}); newer=json.loads(json.dumps(older)); newer["revision"]=2; newer["modified_date"]="2026-02-01"
            (rules/"invalid.json").write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0","rules":[older]}),encoding="utf-8"); (rules/"newer.json").write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0","rules":[newer]}),encoding="utf-8")
            inventory=discover_rule_files(root,config); self.assertEqual([],inventory["errors"]); self.assertEqual(2,inventory["rules"][0]["revision"])
            invalid_later=json.loads(json.dumps(newer)); invalid_later["revision"]=3; invalid_later["created_date"]="2026-99-99"
            (rules/"later.json").write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0","rules":[invalid_later]}),encoding="utf-8")
            failed=discover_rule_files(root,config); self.assertTrue(failed["errors"])
            plan=effective_review_plan([],failed["rules"],"deep",{"date":"2026-07-20"},failed["rule_set_hash"],failed["errors"])
            self.assertFalse(plan["review_authorized"]); self.assertEqual(failed["errors"],plan["validation_failures"])

    def test_runtime_rule_contract_rejects_schema_divergence(self) -> None:
        invalid=rule("USER-BAD",precedence="user",action={"type":"require"})
        invalid.update({"created_date":"2026-99-99","review_tiers":["deep","deep"],"unknown":"rejected"})
        failures=validate_rule(invalid)
        self.assertTrue(any("real ISO date" in row for row in failures)); self.assertTrue(any("unknown fields" in row for row in failures)); self.assertTrue(any("review_tiers" in row for row in failures))
        for mutation in ({"rule_id":123},{"action":{"type":"suppress","target_rule_id":""}},{"action":{"type":"replace","target_rule_id":"ARCH","replacement":""}},{"action":{"type":"require","severity":"high"}}):
            value=rule("USER-TYPED",precedence="user",action={"type":"require"}); value.update(mutation)
            self.assertTrue(validate_rule(value),mutation)

    def test_generated_review_output_is_contained_atomic_and_has_no_residue(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = write_generated_json(root, "quality/plan.json", {"valid": True})
            self.assertEqual({"valid": True}, json.loads(output.read_text(encoding="utf-8")))
            self.assertEqual([], list(output.parent.glob("*.tmp")))
            with self.assertRaises(Exception):
                write_generated_json(root, "../escape.json", {})

    def test_tier_selection_and_finding_closure_fail_closed(self) -> None:
        self.assertEqual("deep", select_review_tier(["authorization"]))
        self.assertEqual("standard", select_review_tier(["publishing_or_release"], internal_release_only=True))
        self.assertEqual(("H-1", "M-1"), review_acceptance_blockers([
            {"finding_id": "H-1", "severity": "high", "disposition": "open"},
            {"finding_id": "M-1", "severity": "medium", "disposition": "open"},
        ]))

    def test_pending_baseline_is_hash_bound_and_non_regression_is_direction_aware(self) -> None:
        baseline = {
            "baseline_id": "BASE-1", "repository_commit": "A"*40, "dual_hat_commit": "B"*40, "dual_hat_version": "1.1.0",
            "date": "2026-07-20", "review_scope": [], "exclusions": [], "selected_review_tier": "deep",
            "active_platform_profile": {"profile_id":"test","profile_version":"1.1.0","profile_sha256":"C"*64}, "user_rule_sources": [], "rule_set_hash": "A" * 64,
            "effective_plan_hash": "B" * 64, "suppressed_architecture_rules": [], "replaced_rules": [],
            "severity_adjustments": [], "rule_conflicts": [], "non_waivable_controls": ["REVIEW-NW-001"], "review_methods": ["independent review"],
            "tool_versions": {}, "principal_metrics": {"coverage": {"value": 90, "desired_direction": "increase"}},
            "risk_areas": [], "accepted_exceptions": [], "user_approved_tradeoffs": [], "unresolved_findings": [],
            "debt_references": [], "validation_evidence": ["detached committed-tree tests"], "preliminary_findings_mapping": [], "final_findings": [],
            "remediated_findings": [], "residual_risk": [], "architecture_disposition_state": "pending_architecture_acceptance",
        }
        expected = bind_baseline(baseline)
        baseline["baseline_hash"] = baseline_hash(baseline)
        self.assertEqual((), validate_baseline(baseline))
        self.assertEqual((), validate_baseline_against_state(baseline, expected))
        wrong={**expected,"repository_commit":"F"*40}; wrong["binding_hash"]=governed_state_binding_hash(wrong)
        self.assertTrue(any("internally derived" in row for row in validate_baseline_against_state(baseline, expected, caller_assertion=wrong)))
        accepted=json.loads(json.dumps(baseline)); accepted["architecture_disposition_state"]="accepted"; bind_baseline(accepted,disposition="accepted"); accepted["baseline_hash"]=baseline_hash(accepted)
        self.assertEqual((), validate_baseline(accepted))

    def test_actual_state_is_derived_and_historical_comparison_is_distinct(self) -> None:
        with TemporaryDirectory() as temporary:
            root=Path(temporary); (root/"profile").mkdir(); (root/"quality/rules").mkdir(parents=True); (root/"dual-hat/release").mkdir(parents=True); (root/"work").mkdir()
            profile=json.loads((ROOT/"examples/platform-profile.example.json").read_text(encoding="utf-8")); (root/"profile/active.json").write_text(json.dumps(profile),encoding="utf-8")
            (root/"dual-hat/release/VERSION.json").write_text(json.dumps({"version":profile["dual_hat_core_version"]}),encoding="utf-8")
            sources={"sources":[{"source_id":"user","path":"quality/rules","required":True}]}; (root/"quality/sources.json").write_text(json.dumps(sources),encoding="utf-8")
            user_rule=rule("USER-1",precedence="user",action={"type":"require"}); (root/"quality/rules/user.json").write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0","rules":[user_rule]}),encoding="utf-8")
            architecture_rule=rule("ARCH-1",precedence="non_waivable",action={"type":"require"}); (root/"quality/architecture.json").write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0","rules":[architecture_rule]}),encoding="utf-8")
            inventory=discover_rule_files(root,"quality/sources.json"); (root/"quality/inventory.json").write_text(json.dumps(inventory),encoding="utf-8")
            context={"date":"2026-07-20","repository":"test"}; plan=effective_review_plan([architecture_rule],inventory["rules"],"deep",context,inventory["rule_set_hash"],inventory["errors"]); (root/"quality/plan.json").write_text(json.dumps(plan),encoding="utf-8")
            seal=json.loads((ROOT/"examples/integrated-work-item.example.json").read_text(encoding="utf-8")); (root/"work/seal.json").write_text(json.dumps(seal),encoding="utf-8")
            handover={"active_work_item":{"work_item_id":seal["work_item_id"],"work_order_revision":seal["current_revision"],"work_order_hash":seal["work_order_hash"],"lifecycle_state":"engineering"}}; (root/"work/handover.json").write_text(json.dumps(handover),encoding="utf-8")
            config={"schema":"dual-hat-baseline-state-sources/1.0","repository_identity":"test","profile":"profile/active.json","dual_hat_version":"dual-hat/release/VERSION.json","rule_sources":"quality/sources.json","rule_inventory":"quality/inventory.json","architecture_rules":"quality/architecture.json","effective_plan":"quality/plan.json","sealed_work_order":"work/seal.json","current_handover":"work/handover.json"}; (root/"quality/state.json").write_text(json.dumps(config),encoding="utf-8")
            subprocess.run(("git","init"),cwd=root,check=True,capture_output=True); subprocess.run(("git","config","user.email","test@example.invalid"),cwd=root,check=True); subprocess.run(("git","config","user.name","Test"),cwd=root,check=True); subprocess.run(("git","config","core.autocrlf","true"),cwd=root,check=True); subprocess.run(("git","add","."),cwd=root,check=True); subprocess.run(("git","commit","-m","fixture"),cwd=root,check=True,capture_output=True)
            original_inventory=json.loads((root/"quality/inventory.json").read_text(encoding="utf-8")); inventory_mtime=(root/"quality/rules/user.json").stat().st_mtime_ns
            (root/"quality/rules/user.json").touch(); self.assertNotEqual(inventory_mtime,(root/"quality/rules/user.json").stat().st_mtime_ns)
            rule_bytes=(root/"quality/rules/user.json").read_bytes(); (root/"quality/rules/user.json").write_bytes(rule_bytes.replace(b"\n",b"\r\n"))
            self.assertEqual("",subprocess.run(("git","status","--porcelain=v1"),cwd=root,check=True,capture_output=True,text=True).stdout)
            actual=derive_governed_baseline_state(root,"quality/state.json")
            self.assertNotEqual(original_inventory["source_inventory_hash"],discover_rule_files(root,"quality/sources.json")["source_inventory_hash"])
            candidate={"baseline_id":"BASE-2","repository_commit":actual["repository_commit"],"dual_hat_commit":actual["dual_hat_commit"],"dual_hat_version":actual["dual_hat_version"],"date":"2026-07-20","review_scope":[],"exclusions":[],"selected_review_tier":"deep","active_platform_profile":actual["active_platform_profile"],"user_rule_sources":[],"rule_set_hash":actual["rule_set_hash"],"effective_plan_hash":actual["effective_plan_hash"],"suppressed_architecture_rules":[],"replaced_rules":[],"severity_adjustments":[],"rule_conflicts":[],"non_waivable_controls":["ARCH-1"],"review_methods":["independent review"],"tool_versions":{},"principal_metrics":{"coverage":{"value":80,"desired_direction":"increase"}},"risk_areas":[],"accepted_exceptions":[],"user_approved_tradeoffs":[],"unresolved_findings":[],"debt_references":[],"validation_evidence":["detached"],"preliminary_findings_mapping":[],"final_findings":[],"remediated_findings":[],"residual_risk":[],"governed_state_binding":actual,"architecture_disposition_state":"pending_architecture_acceptance"}; candidate["baseline_hash"]=baseline_hash(candidate)
            self.assertEqual((),validate_baseline_from_repository(candidate,root,"quality/state.json"))
            forged={**actual,"repository_commit":"F"*40}; forged["binding_hash"]=governed_state_binding_hash(forged)
            self.assertTrue(any("caller assertion" in row for row in validate_baseline_from_repository(candidate,root,"quality/state.json",caller_assertion=forged)))
            historical=json.loads(json.dumps(candidate)); historical["baseline_id"]="BASE-1"; historical["architecture_disposition_state"]="accepted"; bind_baseline(historical,disposition="accepted"); historical["principal_metrics"]["coverage"]["value"]=90; historical["baseline_hash"]=baseline_hash(historical)
            comparison=compare_baselines(historical,candidate,repository=root,resolver_config="quality/state.json")
            self.assertFalse(comparison["non_regression_passed"]); self.assertEqual("coverage",comparison["metric_regressions"][0]["metric"]); self.assertEqual([],comparison["invalid_historical_baseline_evidence"])
            (root/"dirty.txt").write_text("dirty",encoding="utf-8"); self.assertTrue(any("dirty repository" in row for row in validate_baseline_from_repository(candidate,root,"quality/state.json")))

    def test_baseline_rejects_open_medium_conflicts_and_missing_nonwaivable_evidence(self) -> None:
        baseline = json.loads((ROOT / "templates/REPOSITORY_QUALITY_BASELINE.json").read_text(encoding="utf-8"))
        baseline.update({"repository_commit":"A"*40, "dual_hat_commit":"B"*40, "dual_hat_version":"1.1.0", "date":"2026-07-20", "active_platform_profile":{"profile_id":"test","profile_version":"1.1.0","profile_sha256":"C"*64},
                         "rule_set_hash":"A"*64, "effective_plan_hash":"B"*64,
                         "unresolved_findings":[{"finding_id":"M-OPEN","severity":"medium","disposition":"open"}],
                         "rule_conflicts":[{"type":"conflict"}]})
        baseline["baseline_hash"] = baseline_hash(baseline)
        failures = validate_baseline(baseline)
        self.assertTrue(any("M-OPEN" in row for row in failures))
        self.assertTrue(any("conflicts" in row for row in failures))
        self.assertTrue(any("non-waivable" in row for row in failures))
        concealed=json.loads(json.dumps(baseline)); concealed.update({"architecture_disposition_state":"accepted", "unresolved_findings":{}, "final_findings":[{"finding_id":"H-HIDDEN","severity":"high","disposition":"open"}], "non_waivable_controls":"placeholder", "review_methods":"placeholder", "validation_evidence":"placeholder"}); concealed["baseline_hash"]=baseline_hash(concealed)
        hidden_failures=validate_baseline(concealed); self.assertTrue(any("H-HIDDEN" in row for row in hidden_failures)); self.assertTrue(any("must be an array" in row for row in hidden_failures))
        malformed=json.loads(json.dumps(baseline)); malformed.update({"architecture_disposition_state":"accepted","repository_commit":"","dual_hat_commit":"","date":"2026-99-99","rule_set_hash":"x","effective_plan_hash":"y","active_platform_profile":{}}); malformed["unresolved_findings"]=[]; malformed["rule_conflicts"]=[]; malformed["non_waivable_controls"]=["control"]; malformed["review_methods"]=["review"]; malformed["validation_evidence"]=["evidence"]; malformed["baseline_hash"]=baseline_hash(malformed)
        malformed_failures=validate_baseline(malformed); self.assertTrue(any("commit identity" in row for row in malformed_failures)); self.assertTrue(any("real ISO date" in row for row in malformed_failures)); self.assertTrue(any("platform profile" in row for row in malformed_failures))

    def test_discovery_rejects_nested_rule_source_link(self) -> None:
        with TemporaryDirectory() as temporary, TemporaryDirectory() as outside:
            root = Path(temporary); rules = root / "rules"; rules.mkdir()
            external = Path(outside) / "private"; external.mkdir()
            (external / "rule.json").write_text(json.dumps({"schema":"dual-hat-quality-rules/1.0","rules": []}), encoding="utf-8")
            try: (rules / "linked").symlink_to(external, target_is_directory=True)
            except OSError: self.skipTest("host does not permit a symlink fixture")
            config = root / "sources.json"; config.write_text(json.dumps({"sources":[{"path":"rules","required":True}]}), encoding="utf-8")
            inventory = discover_rule_files(root, config)
            self.assertTrue(inventory["errors"])
            self.assertEqual([], inventory["files"])


if __name__ == "__main__":
    unittest.main()
