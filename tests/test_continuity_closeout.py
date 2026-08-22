# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from continuity_closeout import FULL_TRIGGERS, deferred_publication_inventory, reconciliation_audit, select_closeout, work_estimate
from dispatch_reconciliation import dispatch_inventory

DUAL_HAT_CAPABILITY_PROOFS = {"closure_reconciliation_audit"}


class ContinuityCloseoutTests(unittest.TestCase):
    EVIDENCE = {"architecture_directed":True,"next_stream":"governance","source":"sealed GOV-9007 closeout direction"}
    AUDIT = reconciliation_audit(
        reviewer_role="independent", engineering_self_report_only=False,
        items=[{"source": "sealed_scope", "description": "implement the sealed feature", "status": "done", "evidence": "commit abc1234"}],
    )
    DISPATCH = dispatch_inventory(workers=[{
        "handle": "worker-1", "assigned_outcome": "implement the sealed feature", "owner": "engineering",
        "durable_cursor": "commit abc1234", "heartbeat_interval_seconds": 300, "last_probe_age_seconds": 10,
        "state": "finished", "outcome_complete": True, "terminal_evidence": "final result received and consumed",
    }])

    def test_lightweight_and_every_full_trigger(self):
        light = select_closeout(same_stream_next=True, triggers=[], continuity_count=1, continuity_evidence=self.EVIDENCE, reconciliation_audit=self.AUDIT, dispatch_inventory=self.DISPATCH)
        self.assertEqual("lightweight_continuity", light["selection"]); self.assertFalse(light["publication_authorized"])
        self.assertIn("independent_closure_reconciliation_audit", light["required_lightweight_evidence"])
        self.assertEqual(self.AUDIT, light["reconciliation_audit"])
        for trigger in FULL_TRIGGERS:
            with self.subTest(trigger=trigger): self.assertEqual("full", select_closeout(same_stream_next=True, triggers=[trigger], continuity_count=0, continuity_evidence=self.EVIDENCE, reconciliation_audit=self.AUDIT, dispatch_inventory=self.DISPATCH)["selection"])

    def test_counter_is_advisory_and_user_request_wins(self):
        advisory = select_closeout(same_stream_next=True, triggers=[], continuity_count=3, continuity_evidence=self.EVIDENCE, reconciliation_audit=self.AUDIT, dispatch_inventory=self.DISPATCH)
        self.assertEqual("lightweight_continuity", advisory["selection"]); self.assertTrue(advisory["advisory_three_item_threshold_reached"]); self.assertFalse(advisory["counter_forced_full_closure"])
        requested = select_closeout(same_stream_next=True, triggers=[], continuity_count=0, continuity_evidence=self.EVIDENCE, reconciliation_audit=self.AUDIT, dispatch_inventory=self.DISPATCH, user_requested_publication=True)
        self.assertEqual("full", requested["selection"]); self.assertTrue(requested["publication_authorized"])
        with self.assertRaises(ValueError): select_closeout(same_stream_next=True,triggers=[],continuity_count=0,continuity_evidence={"architecture_directed":False,"next_stream":"governance","source":"guess"},reconciliation_audit=self.AUDIT, dispatch_inventory=self.DISPATCH)

    def test_estimate_and_material_revision(self):
        initial = work_estimate(low_hours=4,high_hours=7,segments=["implementation"],included=["validation"],uncertainties=["shared contracts"],expansion_conditions=["hard stop"])
        revised = work_estimate(low_hours=5,high_hours=8,segments=["implementation"],included=["validation"],uncertainties=[],expansion_conditions=[],revision=2,prior=initial,revision_reason="scope changed")
        self.assertEqual(1, revised["prior_revision"]); self.assertEqual("scope changed", revised["revision_reason"])
        with self.assertRaises(ValueError): work_estimate(low_hours=5,high_hours=8,segments=["x"],included=[],uncertainties=[],expansion_conditions=[],revision=2)

    def test_deferred_publication_inventory_is_not_a_release(self):
        value = deferred_publication_inventory(canonical_commit="abc",retained_changes=["GOV-9006"],current_changes=["GOV-9007"],expected_version="1.2.0",compatibility="additive",release_notes=["onboarding"],dependencies=[])
        self.assertFalse(value["published"]); self.assertEqual(["GOV-9006"], value["retained_prior_changes"])

    def test_reconciliation_audit_requires_independent_reviewer_not_self_report(self):
        with self.assertRaises(ValueError) as engineering_role:
            reconciliation_audit(reviewer_role="engineering", engineering_self_report_only=False, items=[{"source": "sealed_scope", "description": "x", "status": "done", "evidence": "commit abc"}])
        self.assertIn("context-isolated independent reviewer", str(engineering_role.exception))
        with self.assertRaises(ValueError) as self_report:
            reconciliation_audit(reviewer_role="independent", engineering_self_report_only=True, items=[{"source": "sealed_scope", "description": "x", "status": "done", "evidence": "commit abc"}])
        self.assertIn("engineering self-report", str(self_report.exception))
        with self.assertRaises(ValueError): reconciliation_audit(reviewer_role="independent", engineering_self_report_only=False, items=[])

    def test_reconciliation_audit_requires_cited_evidence_and_valid_taxonomy(self):
        with self.assertRaises(ValueError): reconciliation_audit(reviewer_role="independent", engineering_self_report_only=False, items=[{"source": "sealed_scope", "description": "x", "status": "done", "evidence": ""}])
        with self.assertRaises(ValueError): reconciliation_audit(reviewer_role="independent", engineering_self_report_only=False, items=[{"source": "invented_source", "description": "x", "status": "done", "evidence": "commit abc"}])
        with self.assertRaises(ValueError): reconciliation_audit(reviewer_role="independent", engineering_self_report_only=False, items=[{"source": "incremental_request", "description": "x", "status": "finished", "evidence": "commit abc"}])
        with self.assertRaises(ValueError): reconciliation_audit(reviewer_role="independent", engineering_self_report_only=False, items=[{"source": "sealed_scope", "status": "done", "evidence": "commit abc"}])

    def test_reconciliation_audit_blocks_partial_and_not_done_unless_deferred(self):
        blocked = reconciliation_audit(
            reviewer_role="independent", engineering_self_report_only=False,
            items=[
                {"source": "sealed_scope", "description": "core feature", "status": "done", "evidence": "commit abc1234"},
                {"source": "incremental_request", "description": "user asked for extra export mode", "status": "not_done", "evidence": "no commit touches export.py"},
                {"source": "interim_finding", "description": "bug found in validation", "status": "partial", "evidence": "test_x::test_y still failing"},
            ],
        )
        self.assertFalse(blocked["closure_authorized"])
        self.assertEqual(["user asked for extra export mode", "bug found in validation"], blocked["blocking_items"])
        with self.assertRaises(ValueError): select_closeout(same_stream_next=True, triggers=[], continuity_count=0, continuity_evidence=self.EVIDENCE, reconciliation_audit=blocked, dispatch_inventory=self.DISPATCH)

        deferred = reconciliation_audit(
            reviewer_role="independent", engineering_self_report_only=False,
            items=[{"source": "interim_finding", "description": "cosmetic bug", "status": "not_done", "evidence": "issue tracker note", "author_deferred": True}],
        )
        self.assertTrue(deferred["closure_authorized"])
        self.assertEqual((), tuple(deferred["blocking_items"]))
        authorized = select_closeout(same_stream_next=True, triggers=[], continuity_count=0, continuity_evidence=self.EVIDENCE, reconciliation_audit=deferred, dispatch_inventory=self.DISPATCH)
        self.assertEqual("lightweight_continuity", authorized["selection"])

    def test_reconciliation_audit_re_derives_rather_than_trusting_the_caller(self):
        """`reconciliation_audit` carried the identical trust-the-caller property that
        was already closed for `dispatch_inventory` --
        select_closeout() believed the caller's own `closure_authorized`/`blocking_items`
        fields instead of re-deriving them from `items`, the way it re-derives the dispatch
        disposition from `workers`. A hand-forged audit that claims authorization despite a
        real blocking item must be refused, naming the contradiction."""
        forged = {
            "schema": "dual-hat-reconciliation-audit/1.0", "reviewer_role": "independent",
            "engineering_self_report_only": False,
            "items": [{"source": "interim_finding", "description": "bug found in validation", "status": "not_done", "evidence": "test_x::test_y still failing"}],
            "blocking_items": [], "closure_authorized": True,
        }
        with self.assertRaises(ValueError) as forged_authorization:
            select_closeout(same_stream_next=True, triggers=[], continuity_count=0, continuity_evidence=self.EVIDENCE, reconciliation_audit=forged, dispatch_inventory=self.DISPATCH)
        self.assertIn("blocked by unresolved reconciliation findings", str(forged_authorization.exception))
        self.assertIn("bug found in validation", str(forged_authorization.exception))

        # A second forgery that would slip past the blocking-items check above but still
        # disagrees with the re-derivation: the caller's own summary fields must match
        # what re-deriving from `items` actually produces, not merely agree on the
        # authorized/blocked verdict.
        contradicted = {
            "schema": "dual-hat-reconciliation-audit/1.0", "reviewer_role": "independent",
            "engineering_self_report_only": False,
            "items": [{"source": "sealed_scope", "description": "core feature", "status": "done", "evidence": "commit abc1234"}],
            "blocking_items": ["a finding the caller invented"], "closure_authorized": True,
        }
        with self.assertRaises(ValueError) as contradicted_summary:
            select_closeout(same_stream_next=True, triggers=[], continuity_count=0, continuity_evidence=self.EVIDENCE, reconciliation_audit=contradicted, dispatch_inventory=self.DISPATCH)
        self.assertIn("contradicts its own reconciled items", str(contradicted_summary.exception))

    def test_closeout_decision_carries_the_dispatch_inventory_it_reconciled(self):
        """select_closeout() validated the dispatch inventory it was handed but
        echoed nothing of it in the returned decision -- the inventory's only
        trace was a literal string in a hardcoded evidence list, identical
        whether the inventory held twenty discharged workers or none. Hand-rolled
        against the schema document in this framework's established idiom
        (see test_dispatch_reconciliation.py), because the framework takes no
        external validation dependency."""
        decision = select_closeout(same_stream_next=True, triggers=[], continuity_count=0, continuity_evidence=self.EVIDENCE, reconciliation_audit=self.AUDIT, dispatch_inventory=self.DISPATCH)
        self.assertEqual(self.DISPATCH, decision["dispatch_inventory"])
        schema = json.loads((ROOT / "schemas/closeout-decision.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(), set(decision) - set(schema["properties"]))
        self.assertEqual(set(), set(schema["required"]) - set(decision))
        nested = schema["properties"]["dispatch_inventory"]
        self.assertEqual(set(), set(decision["dispatch_inventory"]) - set(nested["properties"]))
        self.assertEqual(set(), set(nested["required"]) - set(decision["dispatch_inventory"]))
        self.assertEqual("dual-hat-dispatch-inventory/1.0", nested["properties"]["schema"]["const"])
        self.assertEqual(decision["dispatch_inventory"]["schema"], nested["properties"]["schema"]["const"])
        self.assertIs(False, nested["properties"]["unregistered_dispatch_detectable"]["const"])

    def test_publication_and_closure_and_lifecycle_governance_text(self):
        publication = (ROOT / "process/PUBLICATION_AND_CLOSURE.md").read_text(encoding="utf-8")
        lifecycle = (ROOT / "process/WORK_ITEM_LIFECYCLE.md").read_text(encoding="utf-8")
        exit_report = (ROOT / "templates/EXIT_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("Every capability's closing gate includes a mandatory independent reconciliation audit", publication)
        self.assertIn("context-isolated from the work under review", publication)
        self.assertIn("cold-context reviewer pattern already used elsewhere in this framework", publication)
        self.assertIn("never the same agent or context that executed the work", publication)
        self.assertIn("facts, not words", publication)
        self.assertIn("the sealed work order's approved scope", publication)
        self.assertIn("every incremental request or instruction the stakeholder gave during execution", publication)
        self.assertIn("every interim finding, bug, or gap identified during execution that was committed to being addressed", publication)
        self.assertIn("disposition of done, partially done, or not done", publication)
        self.assertIn("cited evidence", publication)
        self.assertIn("never a narrative completion claim", publication)
        self.assertIn("A disposition of partially done or not done blocks closure until resolved or explicitly deferred by the author", publication)
        self.assertIn("This rule is product-neutral and applies to every capability regardless of product or profile", publication)
        self.assertIn("Acceptance and archival also require the closing gate's independent reconciliation audit", lifecycle)
        self.assertIn("Independent closure reconciliation audit", exit_report)


if __name__ == "__main__": unittest.main()
