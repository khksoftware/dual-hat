# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

DUAL_HAT_CAPABILITY_PROOFS = {"canonical_path_containment", "network_policy_validation", "rights_readiness_validation"}

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from framework_completeness import validate_framework  # noqa: E402
from path_containment import is_reparse  # noqa: E402
from staged_publication import (  # noqa: E402
    PublicationValidationError,
    stage_manifest_owned,
    verify_commit_tree,
)
from publication_ownership import standalone_owned  # noqa: E402


class FrameworkTests(unittest.TestCase):
    @staticmethod
    def _git(root: Path, *args: str) -> None:
        subprocess.run(("git", *args), cwd=root, check=True, capture_output=True, text=True)

    @staticmethod
    def _write_publication(root: Path, readme: str) -> None:
        readme_bytes = readme.encode("utf-8")
        manifest = {
            "schema": "dual-hat-export-manifest/3.0",
            "tree_sha256": "TEST-TREE",
            "content_files": [{
                "path": "README.md",
                "sha256": hashlib.sha256(readme_bytes).hexdigest().upper(),
            }],
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        marker = {
            "schema": "dual-hat-published-state/1.0",
            "tree_sha256": "TEST-TREE",
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest().upper(),
        }
        (root / ".dual-hat").mkdir(exist_ok=True)
        (root / "README.md").write_bytes(readme_bytes)
        (root / ".dual-hat/export-manifest.json").write_bytes(manifest_bytes)
        (root / ".dual-hat/published-state.json").write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _publication_repo(self, root: Path) -> None:
        self._git(root, "init", "-b", "main")
        self._git(root, "config", "user.name", "Dual Hat Test")
        self._git(root, "config", "user.email", "dual-hat-test@example.invalid")
        self._write_publication(root, "initial\n")
        self._git(root, "add", "--", "README.md", ".dual-hat/export-manifest.json", ".dual-hat/published-state.json")
        self._git(root, "commit", "-m", "Initial governed publication")

    def test_semantic_completeness(self):
        self.assertEqual((), validate_framework(ROOT))

    def test_json_and_schema_files_parse(self):
        for path in [*ROOT.rglob("*.json"), *ROOT.rglob("*.schema.json")]:
            json.loads(path.read_text(encoding="utf-8"))

    def test_examples_cover_operating_workflows(self):
        expected = {
            "bounded-task.example.json", "context-pack.example.json",
            "current-handover.example.json", "technical-debt.example.json",
            "validation-run.example.json", "roadmap-and-phase.example.md",
            "planning-backlog.example.json", "future-work.example.json",
            "planning-history.example.jsonl", "planning-lifecycle.example.md",
        }
        self.assertTrue(expected.issubset({path.name for path in (ROOT / "examples").iterdir()}))

    def test_templates_cover_bootstrap_domains(self):
        expected = {
            "WORK_ORDER.md", "CURRENT_HANDOVER.md", "CURRENT_HANDOVER.json",
            "ACTIVE_SESSION.md", "CONTEXT_PACK.md", "ROADMAP.md",
            "TECHNICAL_DEBT_BACKLOG.json", "CANONICAL_ENTRYPOINTS.md",
            "CANONICAL_DOMAIN_INDEX.md", "PRODUCT_REPOSITORY.md",
            "PLANNING_BACKLOG.json", "FUTURE_WORK_REGISTRY.json",
            "PLANNING_HISTORY.jsonl",
        }
        self.assertTrue(expected.issubset({path.name for path in (ROOT / "templates").iterdir()}))

    def test_role_and_retrieval_help_is_first_class(self):
        expected = {
            "governance/ARCHITECTURE_OFFICE_GUIDE.md",
            "governance/ENGINEERING_AGENT_GUIDE.md",
            "sessions/TASK_CONTEXT_RETRIEVAL.md",
            "guides/COMMAND_REFERENCE.md",
        }
        self.assertTrue(all((ROOT / path).is_file() for path in expected))
        self.assertFalse((ROOT / "docs").exists())

    def test_research_iterations_do_not_require_capability_churn(self):
        proportionality = (ROOT / "governance/PROCESS_PROPORTIONALITY.md").read_text(encoding="utf-8")
        lifecycle = (ROOT / "process/CAPABILITY_LIFECYCLE.md").read_text(encoding="utf-8")
        self.assertIn("prefer explicit iterations within the same capability", proportionality)
        self.assertIn("does not require a separate capability identity", lifecycle)

    def test_specialist_review_and_long_run_reporting_contracts(self):
        review = (ROOT / "governance/CODE_REVIEW_CONTRACT.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("Architecture/Design, UX, and QA", review)
        self.assertIn("bounded falsification-oriented posture", review)
        self.assertIn("one-to-five-minute user-update cadence", engineering)
        self.assertIn("Never invent percentage completion for an opaque worker", engineering)

    def test_117_routes_by_intended_end_without_mandatory_pipeline(self):
        operating = (ROOT / "architecture/OPERATING_MODEL.md").read_text(encoding="utf-8")
        framework = (ROOT / "framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        architecture = (ROOT / "prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (operating, framework, architecture, engineering):
            normalized = " ".join(guidance.lower().split())
            for route in ("discover", "decide", "deliver", "single-role"):
                self.assertIn(route, normalized)
            self.assertIn("not", normalized)
            self.assertTrue("mandatory pipeline" in normalized or "mandatory stages" in normalized)

    def test_117_composes_distinct_value_roster_and_diagnoses_assignment(self):
        review = (ROOT / "governance/CODE_REVIEW_CONTRACT.md").read_text(encoding="utf-8")
        routing = (ROOT / "governance/MODEL_TIER_AND_RUNTIME_BINDING.md").read_text(encoding="utf-8")
        architecture = (ROOT / "prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (review, architecture):
            normalized = " ".join(guidance.lower().split())
            self.assertIn("smallest", normalized)
            self.assertIn("distinct", normalized)
            self.assertIn("failure axes", normalized)
        for guidance in (routing, architecture, engineering):
            normalized = " ".join(guidance.lower().split())
            self.assertIn("re-tier", normalized)
            self.assertIn("re-role", normalized)
            self.assertIn("capability", normalized)
            self.assertTrue("ownership" in normalized or "authority" in normalized)

    def test_117_shared_artifact_lanes_are_single_writer(self):
        validation = (ROOT / "governance/VALIDATION_AND_PARALLELISM.md").read_text(encoding="utf-8")
        review = (ROOT / "governance/CODE_REVIEW_CONTRACT.md").read_text(encoding="utf-8")
        framework = (ROOT / "framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (validation, review, framework, engineering):
            normalized = " ".join(guidance.lower().split())
            self.assertIn("shared", normalized)
            self.assertIn("artifact lane", normalized)
            self.assertIn("writer", normalized)
            self.assertIn("read-only", normalized)
            self.assertIn("active writer at a time", normalized)
            self.assertIn("trivial serial", normalized)
            self.assertIn("checkpoint", normalized)
            self.assertIn("quiescent", normalized)

    def test_117_deliver_or_declare_is_only_for_governed_blockage(self):
        framework = (ROOT / "framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        architecture = (ROOT / "prompts/ARCHITECTURE_OFFICE_PROMPT.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (framework, architecture, engineering):
            normalized = " ".join(guidance.lower().split())
            self.assertIn("deliver", normalized)
            self.assertIn("declare", normalized)
            self.assertIn("blocked boundary", normalized)
            self.assertIn("exact obstacle", normalized)
            self.assertIn("preserved state", normalized)
            self.assertIn("recoverable", normalized)

    def test_117_durable_learning_avoids_per_run_ledger(self):
        proportionality = (ROOT / "governance/PROCESS_PROPORTIONALITY.md").read_text(encoding="utf-8")
        phase = (ROOT / "process/PHASE_RUN_PROTOCOL.md").read_text(encoding="utf-8")
        framework = (ROOT / "framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        for guidance in (proportionality, phase, framework):
            normalized = " ".join(guidance.lower().split())
            self.assertIn("accumulated framework release", normalized)
            self.assertIn("governed phase progression", normalized)
            self.assertIn("contradiction", normalized)
            self.assertIn("staleness", normalized)
            self.assertIn("per-run", normalized)

    def test_117_role_guides_apply_turn_exit_audit(self):
        for relative in (
            "governance/ARCHITECTURE_OFFICE_GUIDE.md",
            "governance/ENGINEERING_AGENT_GUIDE.md",
        ):
            guidance = (ROOT / relative).read_text(encoding="utf-8")
            normalized = " ".join(guidance.lower().split())
            self.assertIn("mandatory turn-exit audit", normalized)
            self.assertIn("before every response boundary", normalized)
            self.assertIn("do not emit a terminal response", normalized)
            self.assertIn("execute it in the same turn", normalized)
            self.assertIn("resumable next-action receipt", normalized)
            self.assertIn("accidental turn termination", normalized)

    def test_117_version_and_plugin_ownership_boundary(self):
        version = json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))
        publication = (ROOT / "release/PUBLICATION.md").read_text(encoding="utf-8")
        # This milestone test protects invariants introduced at 1.17.0 and
        # still binding for the remainder of the 1.17.x line; the exact
        # published patch version is expected to advance without requiring
        # a change here.
        self.assertTrue(version["version"].startswith("1.17."))
        current_release_notes = f"release/RELEASE_NOTES_v{version['version']}.md"
        self.assertTrue((ROOT / current_release_notes).is_file())
        source_map_path = ROOT / "export/EXPORT_SOURCES.json"
        if source_map_path.is_file():
            source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
            self.assertIn(current_release_notes, source_map["included"])
        # First-use readers land on this link before anything else; it must
        # always name the currently published release, not whichever one was
        # current when the paragraph was last edited.
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(current_release_notes, readme)
        self.assertIn("canonical source owns only the portable Dual Hat core", publication)
        self.assertIn("standalone", publication)
        self.assertIn("must not carry a", publication)
        self.assertNotIn("E" + "OS", publication)
        # Standalone-only plugin distribution legitimately exists under
        # plugins/ since 1.16.0; the portable-core boundary this test
        # protects is that none of it is ever classified as canonical
        # portable-core source, not that the directory itself is absent.
        plugins_root = ROOT / "plugins"
        if plugins_root.is_dir():
            for path in plugins_root.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(ROOT).as_posix()
                self.assertTrue(
                    standalone_owned(relative),
                    f"{relative} exists under plugins/ but is not "
                    "classified as standalone-owned",
                )

    def test_117_plugin_bundle_tracks_canonical_version(self):
        version = json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))["version"]
        payload_path = ROOT / "plugins/dual-hat/framework-payload.json"
        if not payload_path.is_file():
            self.skipTest("no plugin bundle present in this checkout")
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        # The plugin marketplace is a documented, officially supported
        # install path; a stale bundle silently ships whatever governance
        # or continuation defects the canonical framework has already fixed.
        # Note: the plugin manifests' own "version" field is independent
        # packaging metadata (bumped when the bundle is refreshed) and is
        # not expected to equal the framework version, so it isn't checked
        # here -- only the bundle's own framework identity is.
        self.assertEqual(version, payload["framework_version"])
        self.assertIn(version, payload["framework_root"])
        # framework_root is relative to the payload file's own directory
        # (plugins/dual-hat/), not the repository root.
        self.assertTrue((payload_path.parent / payload["framework_root"]).resolve().is_dir())

    def test_117_distinguishes_reassignment_from_authority_transition(self):
        transitions = (ROOT / "governance/ROLE_TRANSITIONS.md").read_text(encoding="utf-8")
        normalized = " ".join(transitions.lower().split())
        for required in (
            "re-tiering",
            "primary-hat transition",
            "specialist reassignment",
            "atomic safe boundary",
            "checkpointed",
            "architecture's acceptance authority",
        ):
            self.assertIn(required, normalized)
        self.assertIn("single-role pass", normalized)
        self.assertIn("sole authority to accept and archive", normalized)

    def test_117_single_role_pass_cannot_self_accept(self):
        operating = (ROOT / "architecture/OPERATING_MODEL.md").read_text(encoding="utf-8")
        framework = (ROOT / "framework/DUAL_HAT_FRAMEWORK.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (operating, framework, engineering):
            normalized = " ".join(guidance.lower().split())
            self.assertIn("single-role pass", normalized)
            self.assertIn("accept", normalized)
            self.assertTrue("architecture" in normalized or "self-acceptance" in normalized)

    def test_117_blocked_state_has_entry_and_reentry_semantics(self):
        lifecycle = (ROOT / "process/WORK_ITEM_LIFECYCLE.md").read_text(encoding="utf-8")
        normalized = " ".join(lifecycle.lower().split())
        for required in (
            "governed lifecycle state",
            "no safe in-scope action remains",
            "exact obstacle",
            "re-entry condition",
            "neither accepted nor archived",
            "recorded checkpoint",
        ):
            self.assertIn(required, normalized)

    def test_117_durable_learning_has_nonplanning_owner(self):
        inventory = json.loads(
            (ROOT / "repository/FRAMEWORK_CAPABILITY_INVENTORY.json").read_text(encoding="utf-8")
        )
        domains = {row["id"]: row for row in inventory["domains"]}
        self.assertIn("durable-learning governance", domains["architecture"]["responsibilities"])
        self.assertNotIn(
            "accumulated durable-learning review",
            domains["planning"]["responsibilities"],
        )

    def test_117_plan_optimization_is_proportionate_and_retests_assumptions(self):
        proportionality = (ROOT / "governance/PROCESS_PROPORTIONALITY.md").read_text(encoding="utf-8")
        planning = (ROOT / "planning/PLANNING_MODEL.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        for guidance in (proportionality, planning, engineering):
            normalized = " ".join(guidance.lower().split())
            for required in (
                "brute force",
                "value",
                "sequence",
                "parallelism",
                "checkpoint",
                "evidence reuse",
                "cheaper equivalent control",
                "sealed independent architecture optimization review",
                "straightforward",
                "bottleneck",
                "throughput",
                "value yield",
                "batching",
                "wall time",
                "confirm",
                "revise",
                "retire",
                "unchallenged",
                "supported",
                "consequence",
                "uncertainty",
            ):
                self.assertIn(required, normalized)
            self.assertIn("healthy work", normalized)
            self.assertIn("ceremony", normalized)

    def test_concurrency_controls_require_executable_adverse_timing_validation(self):
        guidance = " ".join(
            (
                ROOT / "governance/VALIDATION_AND_PARALLELISM.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "competing actors",
            "adverse timing",
            "simultaneous acquisition",
            "token replacement",
            "stale-owner finalization",
            "process-identity reuse",
            "delayed child appearance",
            "cannot substantiate race-safety",
            "ordinary serial logic",
        ):
            self.assertIn(required, guidance)
        for required in (
            "inactivity-based",
            "stdout/stderr churn does not",
            "near two minutes",
            "near five minutes",
            "extend to ten minutes",
            "actively productive work has no ordinary wall-clock kill",
            "emergency ceiling is a last-resort invariant",
        ):
            self.assertIn(required, guidance)

    def test_hash_gates_declare_byte_policy_and_guard_worktree_drift(self):
        validation = " ".join(
            (
                ROOT / "validation/VALIDATION_PROTOCOL.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "every hash binding declares its byte policy",
            "repository-byte identity",
            "utf-8 without bom",
            "canonical lf newlines",
            "rejects invalid encoding, bom, and bare cr",
            "normalizes crlf to lf",
            "binary outputs, archives, databases, and release products always use",
            "never validate a mutable worktree input by hashing",
        ):
            self.assertIn(required, validation)

    def test_defect_closure_repairs_and_independently_reviews_the_failed_defense(self):
        proportionality = " ".join(
            (
                ROOT / "governance/PROCESS_PROPORTIONALITY.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        review = " ".join(
            (
                ROOT / "governance/CODE_REVIEW_CONTRACT.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "concrete behavior",
            "owning root cause",
            "failed or missing prevention/detection defense",
            "reason it let the defect escape",
            "proportional executable regression evidence",
            "fail against the defective state",
            "directly analogous instances",
            "narrowest appropriate authority",
            "independent adversarial review",
            "attempts falsification",
            "new failure modes",
            "disproportionate runtime or maintenance cost",
            "independence is mandatory",
        ):
            self.assertIn(required, proportionality)
        self.assertIn("cannot approve its own prevention or detection repair", review)

    def test_systemic_mechanism_gap_recognition_is_pinned_and_cross_referenced_with_defect_closure(self):
        # Capability 234's closure surfaced two real defects that each looked
        # like an isolated slip but were not: a handover artifact went 11
        # commits stale because nothing mechanically checked its freshness,
        # and three consecutive phase closures in a row each failed to update
        # the same navigation pointers and archive the same superseded
        # document, because no documented closure step and no mechanical
        # check ever required it. Neither was fixed by correcting the one
        # instance in front of the agent; both required recognizing that the
        # apparent one-off was actually caused by one missing systemic
        # mechanism (an undocumented process step, or a synchronization check
        # that was never made mechanical) and repairing that mechanism. This
        # test pins the generalized rule (PROCESS_PROPORTIONALITY.md rule 19)
        # and its cross-reference back to rule 15's correction-to-control
        # loop, so the two related rules stay linked rather than existing as
        # disconnected prose.
        proportionality = " ".join(
            (ROOT / "governance/PROCESS_PROPORTIONALITY.md").read_text(encoding="utf-8").split()
        )
        for required in (
            "a missing systemic mechanism",
            "a process step that was never documented as mandatory",
            "a check that was never made mechanical, so correctness depended only on an agent remembering to do it",
            'a pointer, cross-reference, or "current state" marker that must track changing state but has no enforcement keeping it synchronized',
            "evidence of one shared systemic cause, not as independent bad luck",
            "do not close the investigation after explaining away each occurrence separately",
            "document the missing step, or add the missing mechanical enforcement",
            "the defect class becomes structurally hard to ship",
            "an instance-only fix leaves the same defect free to recur at the next occasion the pattern applies",
            "This complements rule 15's correction-to-control loop",
            "a precondition for generalizing that root cause correctly, not a substitute for it",
            "See rule 19 when the failure to prevent or detect this defect is itself evidence of a missing systemic mechanism",
        ):
            self.assertIn(required, proportionality)

    def test_chat_switchover_uses_fresh_state_without_stopping_healthy_work(self):
        protocol = " ".join(
            (
                ROOT / "sessions/SESSION_AND_HANDOVER_PROTOCOL.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "ready to switch chats.",
            "nearest safe, low-ambiguity boundary",
            "without pausing healthy background work",
            "classify and reconcile every in-flight task",
            "delegated agent",
            "owned process",
            "fresh authoritative snapshot",
            "never construct the handoff from stale or assumed state",
            "compact current-project handoff artifact",
            "copyable bootstrap instruction",
            "full active goal",
            "exact current counters or state",
            "authoritative repository paths",
            "worktree ownership",
            "pending gates",
            "standing interaction",
            "safe to switch",
            "clean boundary cannot be reached promptly",
            "safest available handoff",
        ):
            self.assertIn(required, protocol)

    def test_consequential_parallel_work_has_one_nonopaque_orchestrator(self):
        guidance = " ".join(
            (
                ROOT / "governance/VALIDATION_AND_PARALLELISM.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "consequential delegated execution must not be opaque",
            "authoritative repository/workspace identity",
            "prohibited stale locations",
            "exactly one orchestrator",
            "parallel workers are pure bounded executors",
            "immutable leases",
            "structured terminal result",
            "never allocate follow-on work",
            "relaunch/reset a failed operation",
            "maximal contiguous checkpoint prefix",
            "retains later valid ranges behind gaps",
            "deduplicates exact identities",
            "residual immutable lease after quiescence",
            "complete recoverable unit payload",
            "hash-only receipt cannot",
            "cursor advancement occur atomically",
        ):
            self.assertIn(required, guidance)

    def test_inventory_separates_required_domains(self):
        payload = json.loads((ROOT / "repository/FRAMEWORK_CAPABILITY_INVENTORY.json").read_text(encoding="utf-8"))
        ids = {domain["id"] for domain in payload["domains"]}
        self.assertEqual(
            {"architecture", "engineering_execution", "planning", "validation",
             "repository_governance", "sessions_and_continuity",
             "publication_and_closure", "repository_and_product_onboarding",
             "model_tiers_and_runtime_binding", "documentation_and_help"},
            ids,
        )

    def test_manifest_owned_staging_and_committed_tree_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            self._write_publication(root, "updated\n")
            staged = stage_manifest_owned(root)
            self.assertEqual(
                [".dual-hat/export-manifest.json", ".dual-hat/published-state.json", "README.md"],
                staged["staged_paths"],
            )
            self._git(root, "commit", "-m", "Forward publication")
            verified = verify_commit_tree(root)
            self.assertEqual("passed", verified["status"])
            self.assertEqual(3, verified["tree_file_count"])

    def test_staging_cleans_python_cache_but_rejects_unknown_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            cache = root / "tooling/__pycache__"
            cache.mkdir(parents=True)
            (cache / "unsafe.pyc").write_bytes(b"compiled")
            loose_cache = root / "generated.pyo"
            loose_cache.write_bytes(b"compiled")
            staged = stage_manifest_owned(root)
            self.assertEqual(
                [
                    "generated.pyo",
                    "tooling/__pycache__/",
                    "tooling/__pycache__/unsafe.pyc",
                ],
                staged["cleaned_python_cache_paths"],
            )
            self.assertEqual(3, staged["cleaned_python_cache_count"])
            self.assertFalse(cache.exists())
            self.assertFalse(loose_cache.exists())
            self._git(root, "reset")
            cache.mkdir(parents=True)
            retained = cache / "retain.txt"
            retained.write_text("not generated bytecode\n", encoding="utf-8")
            (cache / "generated.pyc").write_bytes(b"compiled")
            with self.assertRaisesRegex(PublicationValidationError, "unknown"):
                stage_manifest_owned(root)
            self.assertTrue(retained.exists())
            self.assertFalse((cache / "generated.pyc").exists())
            retained.unlink()
            cache.rmdir()
            (root / "manual.txt").write_text("unowned", encoding="utf-8")
            with self.assertRaisesRegex(PublicationValidationError, "unknown"):
                stage_manifest_owned(root)

    def test_staging_rejects_directory_symlink_without_touching_external_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "publication"
            external = base / "external"
            root.mkdir()
            external.mkdir()
            self._publication_repo(root)
            external_cache = external / "outside.pyc"
            external_cache.write_bytes(b"external-bytecode")
            local_cache = root / "tooling/__pycache__"
            local_cache.mkdir(parents=True)
            local_artifact = local_cache / "local.pyc"
            local_artifact.write_bytes(b"local-bytecode")
            link = root / "linked-cache"
            try:
                link.symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest("host does not permit a directory symlink fixture")
            try:
                with self.assertRaisesRegex(
                    PublicationValidationError,
                    "symlink or reparse entries.*linked-cache",
                ):
                    stage_manifest_owned(root)
                self.assertEqual(b"external-bytecode", external_cache.read_bytes())
                self.assertEqual(b"local-bytecode", local_artifact.read_bytes())
                self.assertTrue(is_reparse(link))
            finally:
                link.unlink(missing_ok=True)

    def test_staging_rejects_file_symlink_without_touching_external_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "publication"
            external = base / "external.pyc"
            root.mkdir()
            self._publication_repo(root)
            external.write_bytes(b"external-bytecode")
            link = root / "linked.pyc"
            try:
                link.symlink_to(external)
            except OSError:
                self.skipTest("host does not permit a file symlink fixture")
            try:
                with self.assertRaisesRegex(
                    PublicationValidationError,
                    "symlink or reparse entries.*linked.pyc",
                ):
                    stage_manifest_owned(root)
                self.assertEqual(b"external-bytecode", external.read_bytes())
                self.assertTrue(is_reparse(link))
            finally:
                link.unlink(missing_ok=True)

    @unittest.skipUnless(os.name == "nt", "junction fixture requires compatible host")
    def test_staging_rejects_junction_without_touching_external_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "publication"
            external = base / "external"
            root.mkdir()
            external.mkdir()
            self._publication_repo(root)
            external_cache = external / "outside.pyc"
            external_cache.write_bytes(b"external-bytecode")
            junction = root / "junction-cache"
            created = subprocess.run(
                ("cmd", "/c", "mklink", "/J", str(junction), str(external)),
                capture_output=True,
                text=True,
            )
            if created.returncode:
                self.skipTest("host does not permit a junction fixture")
            try:
                with self.assertRaisesRegex(
                    PublicationValidationError,
                    "symlink or reparse entries.*junction-cache",
                ):
                    stage_manifest_owned(root)
                self.assertEqual(b"external-bytecode", external_cache.read_bytes())
                self.assertTrue(is_reparse(junction))
            finally:
                if is_reparse(junction):
                    junction.rmdir()

    def test_actual_test_runner_discovers_nonpackage_tests_from_any_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp)
            tests = fixture / "copied-tests"
            caller = fixture / "caller"
            tests.mkdir()
            caller.mkdir()
            (tests / "test_probe.py").write_text(
                "import unittest\n\n"
                "class ProbeTests(unittest.TestCase):\n"
                "    def test_probe(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            environment = dict(os.environ)
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            documented = subprocess.run(
                (
                    sys.executable,
                    "tooling/run_tests.py",
                    "--start-directory",
                    str(tests),
                ),
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            eos_path = subprocess.run(
                (
                    sys.executable,
                    str(ROOT / "tooling/run_tests.py"),
                    "--start-directory",
                    str(tests),
                ),
                cwd=caller,
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertIn("OK", documented.stderr)
            self.assertIn("OK", eos_path.stderr)
            self.assertFalse(any(fixture.rglob("*.pyc")))
            self.assertFalse(
                any(path.name == "__pycache__" for path in fixture.rglob("*"))
            )

    def test_committed_release_products_coexist_with_source_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            release = root / "release/v0.1.0"
            release.mkdir(parents=True)
            for name in (
                "dual-hat-0.1.0.zip",
                "dual-hat-0.1.0.release.json",
                "dual-hat-0.1.0.zip.sha256",
            ):
                (release / name).write_bytes(b"release product")
            self._git(root, "add", "release/v0.1.0")
            self._git(root, "commit", "-m", "Publish release")
            verified = verify_commit_tree(root)
            self.assertEqual("passed", verified["status"])
            self.assertEqual(3, verified["tree_file_count"])

    def test_staging_scans_manifest_owned_content_for_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            credential_fixture = "api_" + "key = 'abcdefghijklmnopqrstuvwx'\n"
            self._write_publication(root, credential_fixture)
            with self.assertRaisesRegex(PublicationValidationError, "possible secrets"):
                stage_manifest_owned(root)


if __name__ == "__main__":
    unittest.main()
