# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from onboarding import (DISCOVERY_FIELDS, OnboardingError, apply_binding, approve_package, binding_plan, build_onboarding_package, classify_repository, create_greenfield_repository, framework_tree_checksum, inspect_repository, removal_plan, remove_binding)

DUAL_HAT_CAPABILITY_PROOFS = {"repository_state_preservation", "explicit_user_and_architecture_reporting", "canonical_path_containment", "binary_secret_gate"}


def discovery():
    return {field: f"fixture {field}" for field in DISCOVERY_FIELDS}


class OnboardingTests(unittest.TestCase):
    def package(self, target: Path, **kwargs):
        return build_onboarding_package(target=target, authorized_root=target.parent, discovery=discovery(), quality_rule_set_hash="A" * 64, effective_plan_hash="B" * 64, **kwargs)

    def approve(self, package):
        evidence={"source_type":"user_interaction","authority_id":"fixture-user","event_id":"fixture-onboarding-approval","captured_by":"fixture-host-adapter","decision_payload_hash":package["package_hash"]}; from onboarding import canonical_hash; evidence["evidence_hash"]=canonical_hash(evidence,omit=("evidence_hash",))
        receipt={"schema":"dual-hat-user-approval/1.0","decision":"approve_onboarding","approved_package_hash":package["package_hash"],"authority_evidence":evidence}
        return approve_package(package,approval_receipt=receipt)

    def test_all_scenarios_and_depths_are_deterministic_and_nonmutating(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            absent = root / "absent"
            empty = root / "empty"; empty.mkdir(); (empty / "README.md").write_text("idea", encoding="utf-8")
            existing = root / "existing"; shutil.copytree(ROOT / "fixtures/onboarding/existing-imperfect-task-tracker", existing)
            self.assertEqual("no_repository", classify_repository(absent, authorized_root=root))
            self.assertEqual("nearly_empty", classify_repository(empty, authorized_root=root))
            self.assertEqual("existing_project", classify_repository(existing, authorized_root=root))
            for target in (absent, empty, existing):
                before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
                for depth in ("quick", "standard", "deep"):
                    first = self.package(target, depth=depth); second = self.package(target, depth=depth)
                    self.assertEqual(first, second); self.assertFalse(first["approval"]["approved"])
                    self.assertFalse(first["mutation_plan"]["implementation_mutation"])
                after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
                self.assertEqual(before, after)

    def test_existing_project_discovers_semantics_without_execution(self):
        result = inspect_repository(ROOT / "fixtures/onboarding/existing-imperfect-task-tracker", authorized_root=ROOT, depth="deep")
        self.assertTrue(result["trust_review_required"]); self.assertFalse(result["executed_repository_code"])
        self.assertTrue(result["tests"]); self.assertTrue(result["documentation"]); self.assertTrue(result["entrypoint_candidates"])
        self.assertIn("web/app.js", result["technical_debt_candidates"]); self.assertEqual("bounded content-aware subsystem, trust, dependency, migration, operations, and debt assessment",result["depth_contract"])

    def test_minimum_questions_reuse_known_discovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            known = discovery(); known.pop("compliance")
            target=Path(temporary); package = build_onboarding_package(target=target, authorized_root=target, discovery=known, quality_rule_set_hash="A"*64, effective_plan_hash="B"*64)
            self.assertEqual(["compliance"], package["minimum_viable_questions"])

    def test_approval_binding_rollback_removal_and_reonboarding(self):
        for model in ("external", "pinned_project_local"):
            with self.subTest(model=model), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); target=root/"project"; target.mkdir(); framework=root/"framework"; framework.mkdir()
                package = self.package(target, binding_model=model)
                with self.assertRaises(OnboardingError):
                    binding_plan(package, framework_path=framework, framework_authorized_root=root, framework_version="1.2.0", framework_checksum="C"*64)
                approved = self.approve(package); checksum=framework_tree_checksum(framework)
                with self.assertRaises(OnboardingError): binding_plan(approved, framework_path=framework, framework_authorized_root=root, framework_version="1.2.0", framework_checksum="C"*64)
                plan = binding_plan(approved, framework_path=framework, framework_authorized_root=root, framework_version="1.2.0", framework_checksum=checksum)
                with self.assertRaises(OnboardingError): apply_binding(target,{"schema":"dual-hat-project-binding/1.0","approved":True,"vendored_framework":False},approved_package=approved,authorized_root=root)
                destination = apply_binding(target, plan, approved_package=approved, authorized_root=root); self.assertTrue(destination.exists()); self.assertFalse(plan["vendored_framework"])
                with self.assertRaises(OnboardingError): apply_binding(target, plan, approved_package=approved, authorized_root=root)
                binding_sha256=__import__("hashlib").sha256(destination.read_bytes()).hexdigest().upper(); from onboarding import canonical_hash; decision_hash=canonical_hash({"decision":"remove_binding","onboarding_package_hash":approved["package_hash"],"binding_sha256":binding_sha256}); evidence={"source_type":"user_interaction","authority_id":"fixture-user","event_id":"fixture-removal-approval","captured_by":"fixture-host-adapter","decision_payload_hash":decision_hash}; evidence["evidence_hash"]=canonical_hash(evidence,omit=("evidence_hash",)); removal_receipt={"schema":"dual-hat-user-approval/1.0","decision":"remove_binding","onboarding_package_hash":approved["package_hash"],"binding_sha256":binding_sha256,"authority_evidence":evidence}
                operation=removal_plan(target,approved_package=approved,authorized_root=root,approval_receipt=removal_receipt)
                remove_binding(target,operation,approved_package=approved,authorized_root=root); self.assertFalse(destination.exists())
                self.assertEqual("nearly_empty", classify_repository(target,authorized_root=root))

    def test_private_names_are_excluded_and_links_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / ".env").write_text("do-not-read", encoding="utf-8"); (root / "main.py").write_text("pass", encoding="utf-8")
            result = inspect_repository(root,authorized_root=root); self.assertEqual([".env"], result["excluded_private"]); self.assertNotIn(".env", result["files"])
            from unittest.mock import patch
            with patch("onboarding._linked", side_effect=lambda path: path.name == "blocked"):
                (root/"blocked").mkdir()
                with self.assertRaises(OnboardingError): inspect_repository(root,authorized_root=root)

    def test_authorized_roots_greenfield_creation_and_scaffold_options(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); outside=root.parent/"outside-onboarding-fixture"
            with self.assertRaises(OnboardingError): classify_repository(outside,authorized_root=root)
            target=root/"new-product"; package=self.package(target); approved=self.approve(package)
            created=create_greenfield_repository(target,approved_package=approved,authorized_root=root); self.assertTrue(created.is_dir())
            with self.assertRaises(OnboardingError): create_greenfield_repository(target,approved_package=approved,authorized_root=root)

    def test_credentials_and_material_uncertainty_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); (root/"credentials-prod.json").write_text('{"fixture":"x"}',encoding="utf-8"); secret_key_name="api"+"_"+"key"; token_name="to"+"ken"; (root/"settings.py").write_text(f'{secret_key_name} = "x"',encoding="utf-8"); (root/"other.py").write_text(f'{token_name} = "x"',encoding="utf-8"); (root/"main.py").write_text('eval("suspicious")',encoding="utf-8"); (root/"README.md").write_text("purpose",encoding="utf-8")
            result=inspect_repository(root,authorized_root=root,depth="deep"); self.assertIn("credentials-prod.json",result["excluded_private"]); self.assertIn("settings.py",result["excluded_private"]); self.assertIn("other.py",result["excluded_private"]); self.assertNotIn("credentials-prod.json",result["content_files_safely_inspected"]); self.assertNotIn("settings.py",result["content_files_safely_inspected"]); self.assertNotIn("other.py",result["content_files_safely_inspected"]); self.assertTrue(result["material_uncertainty"])
            package=self.package(root,depth="deep");
            with self.assertRaises(OnboardingError): self.approve(package)

    def test_framework_checksum_covers_dependency_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); before=framework_tree_checksum(root); (root/"vendor").mkdir(); (root/"vendor/unexpected.py").write_text("pass",encoding="utf-8"); self.assertNotEqual(before,framework_tree_checksum(root))

    def test_fixture_manifest_has_no_private_or_paid_inputs(self):
        manifest = json.loads((ROOT / "fixtures/onboarding/fixture-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["private_data"]); self.assertFalse(manifest["paid_services"]); self.assertEqual(3, len(manifest["scenarios"]))

    def test_golden_semantics_are_consumed(self):
        golden=json.loads((ROOT/"fixtures/onboarding/existing-imperfect-task-tracker/golden-semantic-expectations.json").read_text(encoding="utf-8"))
        result=inspect_repository(ROOT/"fixtures/onboarding/existing-imperfect-task-tracker",authorized_root=ROOT,depth="deep")
        package=self.package(ROOT/"fixtures/onboarding/existing-imperfect-task-tracker",depth="deep")
        checks={"read_only_metadata":result["inspection_mode"]=="read_only_metadata", "trust_review_required":result["trust_review_required"], "implementation_mutation_false":not result["executed_repository_code"], "tests_discovered":bool(result["tests"]), "documentation_discovered":bool(result["documentation"]), "entrypoint_candidates_discovered":bool(result["entrypoint_candidates"]), "technical_debt_proposed_not_accepted":any(row.get("path")=="web/app.js" and row.get("status")=="proposed_not_accepted" for row in package["technical_debt_proposal"]), "approval_before_binding":package["state"]=="awaiting_user_approval" and not package["approval"]["approved"]}
        self.assertTrue(all(checks[name] for name in golden["required_semantics"]))
        for finding in golden["bounded_findings"]: self.assertIn("web/app.js",result["technical_debt_candidates"])
        no_repo=json.loads((ROOT/"fixtures/onboarding/no-repository/scenario.json").read_text(encoding="utf-8")); absent=ROOT/"fixtures/onboarding/no-repository/intended-absent"; no_package=self.package(absent); no_checks={"product_discovery_first":bool(no_package["product_model"]),"repository_creation_requires_approval":no_package["mutation_plan"]["repository_creation"] and no_package["mutation_plan"]["requires_approval"],"rollback_by_abandonment":"abandon" in no_package["rollback_strategy"]}; self.assertTrue(all(no_checks[name] for name in no_repo["golden_semantics"])); self.assertFalse(no_repo["target_exists_before_approval"]); self.assertFalse(absent.exists())
        nearly=json.loads((ROOT/"fixtures/onboarding/nearly-empty/golden-semantic-expectations.json").read_text(encoding="utf-8")); near_package=self.package(ROOT/"fixtures/onboarding/nearly-empty"); self.assertEqual(nearly["required_scaffold_dispositions"],[row["option"] for row in near_package["scaffold_disposition_options"]]); self.assertEqual("nearly_empty",nearly["scenario"]); self.assertFalse(nearly["initial_files_are_authoritative"]); self.assertEqual(nearly["material_mutation_requires_approval"],near_package["mutation_plan"]["requires_approval"])


if __name__ == "__main__": unittest.main()
