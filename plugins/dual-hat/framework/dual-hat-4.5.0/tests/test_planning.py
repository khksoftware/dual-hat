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

from planning_reconciliation import reconcile_planning  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
