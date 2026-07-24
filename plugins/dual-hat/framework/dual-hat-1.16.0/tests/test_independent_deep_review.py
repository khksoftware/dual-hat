"""Focused semantic proof for the independent Deep-review capability.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

DUAL_HAT_CAPABILITY_PROOFS = {"independent_deep_review"}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
from work_item_governance import boundary_review_failures  # noqa: E402


class IndependentDeepReviewCapabilityTests(unittest.TestCase):
    def test_independent_architecture_boundary_contract(self) -> None:
        conformant = {
            "reviewer_role": "architecture", "sealed_work_order_hash_verified": True,
            "primary_evidence_inspected": ["committed diff", "repository state"],
            "engineering_self_report_only": False, "tests_only": False,
            "deviation_found": False, "material_violation_unresolved": False,
            "specific_remediation_obligation": None, "systemic_control_obligation": None,
            "analogous_gap_review": "completed; no evidence-confirmed adjacent gap",
            "architecture_disposition": "accepted",
        }
        self.assertEqual((), boundary_review_failures(conformant))
        self.assertIn("only Architecture", " ".join(boundary_review_failures({**conformant, "reviewer_role": "engineering"})))
        self.assertIn("self-report", " ".join(boundary_review_failures({**conformant, "engineering_self_report_only": True})))
        self.assertIn("passing tests", " ".join(boundary_review_failures({**conformant, "tests_only": True})))
        violated = {**conformant, "deviation_found": True, "material_violation_unresolved": True,
                    "specific_remediation_obligation": None, "systemic_control_obligation": None,
                    "analogous_gap_review": "", "architecture_disposition": "accepted"}
        failures = boundary_review_failures(violated)
        self.assertIn("acceptance is blocked by unresolved material boundary violation", failures)
        self.assertIn("boundary violation lacks specific remediation", failures)
        self.assertIn("boundary violation lacks systemic control strengthening", failures)
        self.assertIn("boundary violation lacks analogous-gap review", failures)


if __name__ == "__main__": unittest.main()
