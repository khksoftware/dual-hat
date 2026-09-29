# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from planning_reconciliation import (  # noqa: E402
    check_claimed_identity,
    load_current_registry,
    reconcile_planning,
)


class PlanningReconciliationTests(unittest.TestCase):
    def test_lifecycle_example_reconciles(self):
        self.assertEqual(
            (),
            reconcile_planning(
                ROOT / "examples/planning-backlog.example.json",
                ROOT / "examples/future-work.example.json",
                ROOT / "examples/planning-history.example.jsonl",
            ),
        )

    def test_status_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            backlog = json.loads((ROOT / "examples/planning-backlog.example.json").read_text(encoding="utf-8"))
            backlog["items"][0]["status"] = "completed"
            (root / "backlog.json").write_text(json.dumps(backlog), encoding="utf-8")
            failures = reconcile_planning(
                root / "backlog.json",
                ROOT / "examples/future-work.example.json",
                ROOT / "examples/planning-history.example.jsonl",
            )
            self.assertTrue(any("current status does not match" in failure for failure in failures))

    def test_duplicate_current_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            future = json.loads((ROOT / "examples/future-work.example.json").read_text(encoding="utf-8"))
            future["items"][0]["id"] = "WORK-0001"
            (root / "future.json").write_text(json.dumps(future), encoding="utf-8")
            failures = reconcile_planning(
                ROOT / "examples/planning-backlog.example.json",
                root / "future.json",
                ROOT / "examples/planning-history.example.jsonl",
            )
            self.assertTrue(any("duplicate planning id" in failure for failure in failures))

    def test_invalid_transition_and_initial_state_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lines = [json.loads(line) for line in (ROOT / "examples/planning-history.example.jsonl").read_text(encoding="utf-8").splitlines()]
            lines[0]["to_status"] = "authorized"
            lines[1]["from_status"] = "authorized"
            (root / "history.jsonl").write_text("\n".join(json.dumps(row) for row in lines) + "\n", encoding="utf-8")
            failures = reconcile_planning(
                ROOT / "examples/planning-backlog.example.json",
                ROOT / "examples/future-work.example.json",
                root / "history.jsonl",
            )
            self.assertTrue(any("first backlog event must enter" in failure for failure in failures))
            self.assertTrue(any("invalid backlog transition" in failure for failure in failures))

    def test_bootstrap_planning_records_start_reconciled(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "product"
            subprocess.run(
                (
                    sys.executable,
                    str(ROOT / "scripts/bootstrap_product.py"),
                    "--profile",
                    str(ROOT / "examples/product-profile.example.json"),
                    "--target",
                    str(target),
                ),
                check=True,
                capture_output=True,
                text=True,
            )
            planning = target / "engineering/planning"
            self.assertEqual(
                (),
                reconcile_planning(
                    planning / "PLANNING_BACKLOG.json",
                    planning / "FUTURE_WORK_REGISTRY.json",
                    planning / "PLANNING_HISTORY.jsonl",
                ),
            )


class ClaimedIdentityTests(unittest.TestCase):
    """The enforceable half of the handover-as-claims paragraph in
    SESSION_AND_HANDOVER_PROTOCOL.md -- an identifier hit alone never counts as
    reconciled."""

    def _registry_with_mutated_backlog_title(self, temp_root, new_title):
        backlog = json.loads((ROOT / "examples/planning-backlog.example.json").read_text(encoding="utf-8"))
        backlog["items"][0]["title"] = new_title
        backlog_path = temp_root / "backlog.json"
        backlog_path.write_text(json.dumps(backlog), encoding="utf-8")
        return load_current_registry(backlog_path, ROOT / "examples/future-work.example.json")

    def test_identifier_collision_when_a_later_item_reuses_a_reserved_number(self):
        # Generic form of the originating incident: a stale handover's claim names
        # WORK-0001 as "Add bounded status reporting" (the example's own live title at
        # the time the claim was written); the live registry now carries a completely
        # different item under that same reserved identifier.
        with tempfile.TemporaryDirectory() as temp:
            registry = self._registry_with_mutated_backlog_title(Path(temp), "Retire the legacy ingest adapter")
            claimed = {
                "namespace": "backlog",
                "identifier": "WORK-0001",
                "title": "Add bounded status reporting",
            }
            self.assertEqual("identifier-collision", check_claimed_identity(claimed, registry))

    def test_identity_match_survives_a_status_change_since_the_handover(self):
        # A claim whose live entry changed state since the handover: the identifier,
        # namespace and title are exactly what the claim asserts; only the status moved
        # on. Identity is intact -- check_claimed_identity says nothing about status
        # drift, which is reconcile_planning's own concern, not this function's.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            backlog = json.loads((ROOT / "examples/planning-backlog.example.json").read_text(encoding="utf-8"))
            self.assertEqual("ready", backlog["items"][0]["status"])
            backlog["items"][0]["status"] = "authorized"
            backlog_path = root / "backlog.json"
            backlog_path.write_text(json.dumps(backlog), encoding="utf-8")
            registry = load_current_registry(backlog_path, ROOT / "examples/future-work.example.json")
            claimed = {
                "namespace": "backlog",
                "identifier": "WORK-0001",
                "title": "Add bounded status reporting",
            }
            self.assertEqual("identity-match", check_claimed_identity(claimed, registry))

    def test_absent_identifier_is_reported_as_absent_not_matched(self):
        registry = load_current_registry(
            ROOT / "examples/planning-backlog.example.json",
            ROOT / "examples/future-work.example.json",
        )
        claimed = {"namespace": "backlog", "identifier": "WORK-9999", "title": "Never queued"}
        self.assertEqual("absent", check_claimed_identity(claimed, registry))

    def test_identifier_presence_check_alone_reports_the_collision_as_reconciled(self):
        # Pins the originating defect this function exists to close: a shallow
        # identifier-presence check -- "does this id exist in the live registry" --
        # reports the identifier-collision fixture above as reconciled, because it
        # never compares title, purpose, namespace or provenance. check_claimed_identity
        # is the fix; this test proves the shallow check's blind spot on the same
        # fixture the fix is proven against.
        with tempfile.TemporaryDirectory() as temp:
            registry = self._registry_with_mutated_backlog_title(Path(temp), "Retire the legacy ingest adapter")
            claimed_identifier = "WORK-0001"

            # The old behaviour this repairs: presence alone, nothing else compared.
            identifier_presence_check_reports_reconciled = claimed_identifier in registry
            self.assertTrue(
                identifier_presence_check_reports_reconciled,
                "the shallow check is expected to be fooled -- that is the defect",
            )

            claimed = {
                "namespace": "backlog",
                "identifier": claimed_identifier,
                "title": "Add bounded status reporting",
            }
            self.assertNotEqual("identity-match", check_claimed_identity(claimed, registry))
            self.assertEqual("identifier-collision", check_claimed_identity(claimed, registry))


if __name__ == "__main__":
    unittest.main()
