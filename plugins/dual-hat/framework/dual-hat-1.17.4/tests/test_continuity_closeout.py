# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from continuity_closeout import FULL_TRIGGERS, deferred_publication_inventory, select_closeout, work_estimate


class ContinuityCloseoutTests(unittest.TestCase):
    EVIDENCE = {"architecture_directed":True,"next_stream":"governance","source":"sealed GOV-0007 closeout direction"}

    def test_lightweight_and_every_full_trigger(self):
        light = select_closeout(same_stream_next=True, triggers=[], continuity_count=1, continuity_evidence=self.EVIDENCE)
        self.assertEqual("lightweight_continuity", light["selection"]); self.assertFalse(light["publication_authorized"])
        for trigger in FULL_TRIGGERS:
            with self.subTest(trigger=trigger): self.assertEqual("full", select_closeout(same_stream_next=True, triggers=[trigger], continuity_count=0, continuity_evidence=self.EVIDENCE)["selection"])

    def test_counter_is_advisory_and_user_request_wins(self):
        advisory = select_closeout(same_stream_next=True, triggers=[], continuity_count=3, continuity_evidence=self.EVIDENCE)
        self.assertEqual("lightweight_continuity", advisory["selection"]); self.assertTrue(advisory["advisory_three_item_threshold_reached"]); self.assertFalse(advisory["counter_forced_full_closure"])
        requested = select_closeout(same_stream_next=True, triggers=[], continuity_count=0, continuity_evidence=self.EVIDENCE, user_requested_publication=True)
        self.assertEqual("full", requested["selection"]); self.assertTrue(requested["publication_authorized"])
        with self.assertRaises(ValueError): select_closeout(same_stream_next=True,triggers=[],continuity_count=0,continuity_evidence={"architecture_directed":False,"next_stream":"governance","source":"guess"})

    def test_estimate_and_material_revision(self):
        initial = work_estimate(low_hours=4,high_hours=7,segments=["implementation"],included=["validation"],uncertainties=["shared contracts"],expansion_conditions=["hard stop"])
        revised = work_estimate(low_hours=5,high_hours=8,segments=["implementation"],included=["validation"],uncertainties=[],expansion_conditions=[],revision=2,prior=initial,revision_reason="scope changed")
        self.assertEqual(1, revised["prior_revision"]); self.assertEqual("scope changed", revised["revision_reason"])
        with self.assertRaises(ValueError): work_estimate(low_hours=5,high_hours=8,segments=["x"],included=[],uncertainties=[],expansion_conditions=[],revision=2)

    def test_deferred_publication_inventory_is_not_a_release(self):
        value = deferred_publication_inventory(canonical_commit="abc",retained_changes=["GOV-0006"],current_changes=["GOV-0007"],expected_version="1.2.0",compatibility="additive",release_notes=["onboarding"],dependencies=[])
        self.assertFalse(value["published"]); self.assertEqual(["GOV-0006"], value["retained_prior_changes"])


if __name__ == "__main__": unittest.main()
