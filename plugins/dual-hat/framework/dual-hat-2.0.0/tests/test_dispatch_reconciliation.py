# SPDX-License-Identifier: Apache-2.0
"""Executable proof of CONFORMANCE_POLICY.md's delegated-dispatch closure gate.

The governing sentence -- an unregistered, nonterminal, unprobed, or silently
forgotten handle blocks closure, as does an incomplete outcome whose stalled or
dead worker has no registered successor -- was adopted and in force with nothing
able to detect a violation of it. These tests are that detection.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from continuity_closeout import reconciliation_audit, select_closeout
from dispatch_reconciliation import (
    DISPATCH_INVENTORY_SCHEMA,
    NONTERMINAL_WORKER_STATES,
    TERMINAL_WORKER_STATES,
    WORKER_STATES,
    dispatch_inventory,
)

EVIDENCE = {"architecture_directed": True, "next_stream": "governance", "source": "sealed GOV-0014 closeout direction"}
AUDIT = reconciliation_audit(
    reviewer_role="independent", engineering_self_report_only=False,
    items=[{"source": "sealed_scope", "description": "make delegated-dispatch accounting executable", "status": "done", "evidence": "commit abc1234"}],
)


def worker(**overrides: object) -> dict[str, object]:
    """A fully and correctly registered, discharged worker; overrides introduce one defect at a time."""
    base: dict[str, object] = {
        "handle": "worker-7f2a", "assigned_outcome": "draft the reconciler", "owner": "architecture",
        "durable_cursor": "engineering/process/work-items/GOV-0014/EVIDENCE.md", "heartbeat_interval_seconds": 300,
        "last_probe_age_seconds": 12, "state": "finished", "outcome_complete": True,
        "terminal_evidence": "final report received and consumed at commit abc1234",
    }
    base.update(overrides)
    return base


def close(inventory: dict[str, object]) -> dict[str, object]:
    return select_closeout(
        same_stream_next=True, triggers=[], continuity_count=0,
        continuity_evidence=EVIDENCE, reconciliation_audit=AUDIT, dispatch_inventory=inventory,
    )


class DispatchClosureGateTests(unittest.TestCase):
    def test_closure_is_refused_while_a_registered_worker_is_nonterminal(self):
        """The first Red. Before the gate existed this closure was AUTHORIZED --
        that authorization was the defect, executed rather than argued."""
        inventory = dispatch_inventory(workers=[worker(state="running", outcome_complete=False, terminal_evidence="")])
        self.assertFalse(inventory["closure_authorized"])
        with self.assertRaises(ValueError) as refusal:
            close(inventory)
        self.assertIn("worker-7f2a", str(refusal.exception))
        self.assertIn("nonterminal", str(refusal.exception))

    def test_refusal_names_the_handle_for_a_stale_heartbeat(self):
        inventory = dispatch_inventory(workers=[worker(
            handle="worker-stale-1", state="running", outcome_complete=False, terminal_evidence="",
            heartbeat_interval_seconds=300, last_probe_age_seconds=4000,
        )])
        blocking = " | ".join(inventory["blocking_workers"])
        self.assertIn("worker-stale-1", blocking)
        self.assertIn("beyond its declared 300s heartbeat interval", blocking)
        with self.assertRaises(ValueError) as refusal:
            close(inventory)
        self.assertIn("worker-stale-1", str(refusal.exception))

    def test_refusal_names_the_handle_for_a_terminal_claim_without_terminal_evidence(self):
        inventory = dispatch_inventory(workers=[worker(handle="worker-claimed-2", state="finished", terminal_evidence="")])
        blocking = " | ".join(inventory["blocking_workers"])
        self.assertIn("worker-claimed-2", blocking)
        self.assertIn("no recorded terminal evidence", blocking)
        with self.assertRaises(ValueError) as refusal:
            close(inventory)
        self.assertIn("worker-claimed-2", str(refusal.exception))

    def test_refusal_names_the_handle_for_a_dead_worker_with_no_registered_successor(self):
        inventory = dispatch_inventory(workers=[worker(
            handle="worker-dead-3", state="dead", outcome_complete=False,
            terminal_evidence="platform reports process absence", successor_handle=None,
        )])
        blocking = " | ".join(inventory["blocking_workers"])
        self.assertIn("worker-dead-3", blocking)
        self.assertIn("no registered successor", blocking)
        with self.assertRaises(ValueError) as refusal:
            close(inventory)
        self.assertIn("worker-dead-3", str(refusal.exception))

    def test_a_registered_successor_discharges_the_dead_worker(self):
        inventory = dispatch_inventory(workers=[
            worker(handle="worker-dead-4", state="dead", outcome_complete=False,
                   terminal_evidence="platform reports process absence", successor_handle="worker-successor-4"),
            worker(handle="worker-successor-4", state="finished", outcome_complete=True,
                   terminal_evidence="successor final result received and consumed"),
        ])
        self.assertEqual([], inventory["blocking_workers"])
        self.assertTrue(inventory["closure_authorized"])
        self.assertEqual("lightweight_continuity", close(inventory)["selection"])

    def test_every_nonterminal_state_blocks_and_every_terminal_state_can_discharge(self):
        for state in sorted(NONTERMINAL_WORKER_STATES):
            with self.subTest(state=state):
                inventory = dispatch_inventory(workers=[worker(state=state, outcome_complete=False, terminal_evidence="", successor_handle="worker-successor")])
                self.assertFalse(inventory["closure_authorized"])
                with self.assertRaises(ValueError):
                    close(inventory)
        for state in sorted(TERMINAL_WORKER_STATES):
            with self.subTest(state=state):
                inventory = dispatch_inventory(workers=[worker(state=state, outcome_complete=True, terminal_evidence="result consumed")])
                self.assertTrue(inventory["closure_authorized"])
                self.assertEqual("lightweight_continuity", close(inventory)["selection"])

    def test_counts_are_reconciled_and_every_blocking_entry_names_a_registered_handle(self):
        inventory = dispatch_inventory(workers=[
            worker(handle="a", state="finished", outcome_complete=True, terminal_evidence="consumed"),
            worker(handle="b", state="running", outcome_complete=False, terminal_evidence="", last_probe_age_seconds=9000),
            worker(handle="c", state="stalled", outcome_complete=False, terminal_evidence=""),
        ])
        self.assertEqual(3, inventory["registered_count"])
        self.assertEqual(1, inventory["terminal_count"])
        self.assertEqual(2, inventory["nonterminal_count"])
        self.assertEqual(inventory["registered_count"], inventory["terminal_count"] + inventory["nonterminal_count"])
        handles = {str(item["handle"]) for item in inventory["workers"]}
        for entry in inventory["blocking_workers"]:
            self.assertTrue(any(handle in entry for handle in handles), entry)

    def test_structurally_invalid_registration_raises_rather_than_authorizing(self):
        with self.assertRaises(ValueError):
            dispatch_inventory(workers=[{"handle": "x", "state": "finished"}])
        with self.assertRaises(ValueError):
            dispatch_inventory(workers=[worker(handle="   ")])
        with self.assertRaises(ValueError):
            dispatch_inventory(workers=[worker(state="probably_fine")])
        with self.assertRaises(ValueError):
            dispatch_inventory(workers=[worker(durable_cursor="")])
        with self.assertRaises(ValueError) as unbound:
            dispatch_inventory(workers=[worker(heartbeat_interval_seconds=0)])
        self.assertIn("no heartbeat contract bound before launch", str(unbound.exception))
        with self.assertRaises(ValueError) as duplicated:
            dispatch_inventory(workers=[worker(handle="dup"), worker(handle="dup")])
        self.assertIn("same handle twice", str(duplicated.exception))

    def test_the_gate_refuses_a_malformed_inventory_rather_than_passing_it_through(self):
        with self.assertRaises(ValueError) as refusal:
            close({"schema": "dual-hat-dispatch-inventory/1.0", "workers": []})
        self.assertIn("delegated-dispatch reconciliation", str(refusal.exception))

    def test_the_named_residual_is_recorded_in_the_artifact_not_only_in_prose(self):
        """An empty inventory and a session that never registered its delegation are
        byte-identical. The record says so rather than implying proof it cannot give."""
        empty = dispatch_inventory(workers=[])
        self.assertTrue(empty["closure_authorized"])
        self.assertEqual(0, empty["registered_count"])
        self.assertIs(False, empty["unregistered_dispatch_detectable"])
        self.assertEqual("lightweight_continuity", close(empty)["selection"])

    def test_the_produced_record_conforms_to_its_own_published_schema(self):
        """Keeps the schema from becoming a declared mechanism nothing executes.
        Hand-rolled against the schema document in this framework's established
        idiom, because the framework takes no external validation dependency."""
        schema = json.loads((ROOT / "schemas/dispatch-inventory.schema.json").read_text(encoding="utf-8"))
        inventory = dispatch_inventory(workers=[
            worker(handle="a", state="finished", outcome_complete=True, terminal_evidence="consumed"),
            worker(handle="b", state="stalled", outcome_complete=False, terminal_evidence="", successor_handle="a"),
        ])
        self.assertEqual(set(), set(inventory) - set(schema["properties"]))
        self.assertEqual(set(), set(schema["required"]) - set(inventory))
        self.assertEqual("dual-hat-dispatch-inventory/1.0", schema["properties"]["schema"]["const"])
        self.assertEqual(inventory["schema"], schema["properties"]["schema"]["const"])
        item = schema["properties"]["workers"]["items"]
        for registered in inventory["workers"]:
            self.assertEqual(set(), set(registered) - set(item["properties"]))
            self.assertEqual(set(), set(item["required"]) - set(registered))
        # The state vocabulary must not drift between the code and the schema.
        self.assertEqual(sorted(WORKER_STATES), sorted(item["properties"]["state"]["enum"]))
        # The residual is declared as a constant in the schema, not merely emitted.
        self.assertIs(False, schema["properties"]["unregistered_dispatch_detectable"]["const"])

    def test_the_governing_sentence_this_enforces_is_still_present_and_unchanged(self):
        policy = (ROOT / "governance/CONFORMANCE_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("An unregistered, nonterminal,\nunprobed, or silently forgotten handle blocks closure, as does an incomplete\noutcome whose stalled or dead worker has no registered successor.", policy)


def forged(*, workers: list[dict[str, object]], **summary: object) -> dict[str, object]:
    """An inventory assembled by hand rather than produced by the reconciler.

    Defaults describe a clean, closure-authorizing summary; `summary` overrides
    introduce one contradiction at a time. Nothing here calls
    `dispatch_inventory()`, which is the entire point: the gate must reach its own
    disposition from the registered workers rather than believing the summary.
    """
    inventory: dict[str, object] = {
        "schema": DISPATCH_INVENTORY_SCHEMA, "workers": workers,
        "registered_count": len(workers), "terminal_count": len(workers), "nonterminal_count": 0,
        "blocking_workers": [], "closure_authorized": True,
        "unregistered_dispatch_detectable": False,
    }
    inventory.update(summary)
    return inventory


class ForgedInventoryTests(unittest.TestCase):
    """The gate must be a control over what a caller hands it, not only over what
    the reconciler produces. Every case below authorized closure before these
    tests existed; each one was executed and observed authorizing."""

    def test_a_hand_forged_inventory_cannot_authorize_what_the_reconciler_refuses(self):
        """The gate re-derives the disposition; a forged summary cannot override it.

        Without this, `continuity_closeout` need never import the reconciler and
        the seal's falsifiable outcome is false as literally worded: a registered
        delegated worker sits nonterminal, unprobed past its heartbeat interval,
        and closure is authorized anyway."""
        with self.assertRaises(ValueError) as refusal:
            close(forged(workers=[worker(
                handle="ghost-1", state="running", outcome_complete=False, terminal_evidence="",
                heartbeat_interval_seconds=300, last_probe_age_seconds=99999,
            )]))
        self.assertIn("ghost-1", str(refusal.exception))
        self.assertIn("nonterminal", str(refusal.exception))

    def test_an_inventory_that_contradicts_its_own_blocking_workers_is_refused(self):
        """The gate held the refusal text in its hand and passed anyway."""
        with self.assertRaises(ValueError) as refusal:
            close(forged(
                workers=[worker(handle="ghost-2", state="stalled", outcome_complete=False, terminal_evidence="")],
                blocking_workers=["ghost-2 is registered nonterminal and was never discharged"],
                closure_authorized=True,
            ))
        self.assertIn("ghost-2", str(refusal.exception))

    def test_an_inventory_whose_schema_is_not_the_published_constant_is_refused(self):
        """`required_dispatch_fields` was key-presence only; the schema key's value
        was never compared to the constant the schema document pins as a `const`."""
        with self.assertRaises(ValueError) as refusal:
            close(forged(workers=[], schema="totally-made-up/9.9"))
        self.assertIn("dual-hat-dispatch-inventory/1.0", str(refusal.exception))

    def test_a_workers_value_that_is_not_a_list_is_refused_rather_than_authorized(self):
        inventory = forged(workers=[])
        inventory["workers"] = "not-a-list"
        with self.assertRaises(ValueError) as refusal:
            close(inventory)
        self.assertIn("registered worker list", str(refusal.exception))

    def test_counts_that_disagree_with_the_registered_workers_are_refused(self):
        """A summary field no longer has to be merely present; it has to be true."""
        discharged = worker(handle="ghost-3", state="finished", outcome_complete=True, terminal_evidence="consumed")
        for field, value in (("registered_count", 7), ("terminal_count", 0), ("nonterminal_count", 4)):
            with self.subTest(field=field):
                with self.assertRaises(ValueError) as refusal:
                    close(forged(workers=[discharged], **{field: value}))
                self.assertIn(field, str(refusal.exception))

    def test_a_declared_residual_flipped_to_true_is_refused(self):
        """`unregistered_dispatch_detectable` is a schema `const`. An inventory
        claiming this control detects unregistered dispatch is claiming something
        the mechanism cannot do, and must not be honoured."""
        with self.assertRaises(ValueError) as refusal:
            close(forged(workers=[], unregistered_dispatch_detectable=True))
        self.assertIn("unregistered_dispatch_detectable", str(refusal.exception))

    def test_a_null_or_falsey_handle_is_refused_rather_than_stringified(self):
        """`str(None)` is `'None'`, a non-empty string that passed the guard whose
        stated purpose is to require a real platform handle. Every other identity
        field already used `str(x or '')`; the handle did not, and the schema
        declares `minLength: 1`."""
        for bad in (None, 0, False, ""):
            with self.subTest(handle=bad):
                with self.assertRaises(ValueError) as refusal:
                    dispatch_inventory(workers=[worker(handle=bad)])
                self.assertIn("real platform handle", str(refusal.exception))

    def test_a_genuinely_reconciled_inventory_still_closes(self):
        """The control on the control. A gate that refuses everything is not a
        gate, and the seal's fourth stop gate fires if a legitimate closure is
        refused. Both live callers' shapes are exercised here."""
        discharged = dispatch_inventory(workers=[worker(
            handle="worker-real-1", state="finished", outcome_complete=True,
            terminal_evidence="final result received and consumed",
        )])
        self.assertEqual("lightweight_continuity", close(discharged)["selection"])
        self.assertEqual("lightweight_continuity", close(dispatch_inventory(workers=[]))["selection"])

    def test_the_reconciler_output_survives_a_json_round_trip_through_the_gate(self):
        """A real inventory read back from its own published schema's serialization
        must still close, so the re-derivation cannot be satisfied only by object
        identity with a live reconciler call."""
        inventory = json.loads(json.dumps(dispatch_inventory(workers=[worker(
            handle="worker-real-2", state="dead", outcome_complete=False,
            terminal_evidence="platform reports process absence", successor_handle="worker-real-3",
        ), worker(
            handle="worker-real-3", state="finished", outcome_complete=True,
            terminal_evidence="successor final result received and consumed",
        )])))
        self.assertEqual("lightweight_continuity", close(inventory)["selection"])


if __name__ == "__main__":
    unittest.main()
