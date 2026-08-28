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
    WORKER_PERMITTED_FIELDS,
    WORKER_REQUIRED_FIELDS,
    WORKER_STATES,
    dispatch_inventory,
)

EVIDENCE = {"architecture_directed": True, "next_stream": "governance", "source": "sealed GOV-9014 closeout direction"}
AUDIT = reconciliation_audit(
    reviewer_role="independent", engineering_self_report_only=False,
    items=[{"source": "sealed_scope", "description": "make delegated-dispatch accounting executable", "status": "done", "evidence": "commit abc1234"}],
)


def worker(**overrides: object) -> dict[str, object]:
    """A fully and correctly registered, discharged worker; overrides introduce one defect at a time."""
    base: dict[str, object] = {
        "handle": "worker-7f2a", "assigned_outcome": "draft the reconciler", "owner": "architecture",
        "durable_cursor": "process/work-items/GOV-9014/EVIDENCE.md", "heartbeat_interval_seconds": 300,
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

    def test_worker_registration_shape_is_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown registration fields"):
            dispatch_inventory(workers=[worker(unsealed_claim="accepted")])

    def test_outcome_complete_requires_an_exact_boolean(self):
        with self.assertRaisesRegex(ValueError, "outcome_complete must be boolean"):
            dispatch_inventory(workers=[worker(outcome_complete="false")])

    def test_worker_scalar_fields_reject_coercible_non_strings(self):
        cases = (
            ("handle", "real platform handle"),
            ("assigned_outcome", "assigned_outcome must be string"),
            ("owner", "owner must be string"),
            ("durable_cursor", "durable_cursor must be string"),
            ("terminal_evidence", "terminal_evidence must be string"),
            ("successor_handle", "successor_handle must be string or null"),
        )
        for field, message in cases:
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, message):
                dispatch_inventory(workers=[worker(**{field: 7})])

    def test_heartbeat_and_probe_values_must_be_finite(self):
        with self.assertRaisesRegex(ValueError, "non-finite last_probe_age_seconds"):
            dispatch_inventory(workers=[worker(last_probe_age_seconds=float("nan"))])

    def test_finished_worker_with_incomplete_outcome_is_refused(self):
        inventory = dispatch_inventory(workers=[worker(handle="worker-finished-incomplete", outcome_complete=False)])
        self.assertFalse(inventory["closure_authorized"])
        self.assertTrue(any("worker-finished-incomplete" in row and "finished" in row and "incomplete" in row for row in inventory["blocking_workers"]))

    def test_successor_must_be_registered(self):
        nonexistent = dispatch_inventory(workers=[worker(handle="worker-dead-missing", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-not-registered")])
        self.assertFalse(nonexistent["closure_authorized"])
        self.assertTrue(any("worker-dead-missing" in row and "worker-not-registered" in row and "not registered" in row for row in nonexistent["blocking_workers"]))

    def test_successor_must_be_distinct_from_the_failed_worker(self):
        self_successor = dispatch_inventory(workers=[worker(handle="worker-dead-self", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-dead-self")])
        self.assertFalse(self_successor["closure_authorized"])
        self.assertTrue(any("worker-dead-self" in row and "itself" in row for row in self_successor["blocking_workers"]))

    def test_successor_must_own_the_same_assigned_outcome(self):
        inventory = dispatch_inventory(workers=[
            worker(handle="worker-dead-mismatch", assigned_outcome="finish the primary assigned outcome", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-other-outcome"),
            worker(handle="worker-other-outcome", assigned_outcome="unrelated cleanup"),
        ])
        self.assertFalse(inventory["closure_authorized"])
        self.assertTrue(any("worker-dead-mismatch" in row and "worker-other-outcome" in row and "different assigned outcome" in row for row in inventory["blocking_workers"]))

    def test_successor_chain_may_reach_completion_through_multiple_registered_hops(self):
        inventory = dispatch_inventory(workers=[
            worker(handle="worker-chain-a", assigned_outcome="complete the assigned review", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-chain-b"),
            worker(handle="worker-chain-b", assigned_outcome="complete the assigned review", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-chain-c"),
            worker(handle="worker-chain-c", assigned_outcome="complete the assigned review"),
        ])
        self.assertTrue(inventory["closure_authorized"])
        self.assertEqual([],inventory["blocking_workers"])

    def test_two_worker_successor_cycle_is_refused_and_named(self):
        inventory = dispatch_inventory(workers=[
            worker(handle="worker-cycle-a", assigned_outcome="complete the assigned review", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-cycle-b"),
            worker(handle="worker-cycle-b", assigned_outcome="complete the assigned review", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-cycle-a"),
        ])
        blocking=" | ".join(inventory["blocking_workers"])
        self.assertFalse(inventory["closure_authorized"])
        self.assertIn("cycle",blocking)
        self.assertIn("worker-cycle-a",blocking)
        self.assertIn("worker-cycle-b",blocking)

    def test_successor_tail_entering_a_cycle_is_refused_and_named(self):
        inventory = dispatch_inventory(workers=[
            worker(handle="worker-tail", assigned_outcome="complete the assigned review", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-loop-a"),
            worker(handle="worker-loop-a", assigned_outcome="complete the assigned review", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-loop-b"),
            worker(handle="worker-loop-b", assigned_outcome="complete the assigned review", state="dead", outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-loop-a"),
        ])
        blocking=" | ".join(inventory["blocking_workers"])
        self.assertFalse(inventory["closure_authorized"])
        self.assertIn("worker-tail",blocking)
        self.assertIn("worker-loop-a",blocking)
        self.assertIn("worker-loop-b",blocking)
        self.assertIn("cycle",blocking)

    def test_json_valid_huge_integer_never_leaks_overflow(self):
        inventory = dispatch_inventory(workers=[worker(handle="worker-huge-probe", state="running", outcome_complete=False, terminal_evidence="", last_probe_age_seconds=10**10000)])
        self.assertFalse(inventory["closure_authorized"])
        self.assertTrue(any("worker-huge-probe" in row and "heartbeat interval" in row for row in inventory["blocking_workers"]))

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
            for field in ("handle", "assigned_outcome", "owner", "durable_cursor", "state", "terminal_evidence"):
                self.assertIsInstance(registered[field],str,field)
            self.assertTrue(registered["successor_handle"] is None or isinstance(registered["successor_handle"],str))
            self.assertIs(type(registered["outcome_complete"]),bool)
            for field in ("heartbeat_interval_seconds", "last_probe_age_seconds"):
                self.assertIsInstance(registered[field],(int,float),field); self.assertIsNot(type(registered[field]),bool)
        # The state vocabulary must not drift between the code and the schema.
        self.assertEqual(sorted(WORKER_STATES), sorted(item["properties"]["state"]["enum"]))
        # The residual is declared as a constant in the schema, not merely emitted.
        self.assertIs(False, schema["properties"]["unregistered_dispatch_detectable"]["const"])

    def test_the_governing_sentence_this_enforces_is_still_present_and_unchanged(self):
        policy = (ROOT / "governance/CONFORMANCE_POLICY.md").read_text(encoding="utf-8")
        self.assertIn("An unregistered, nonterminal,\nunprobed, or silently forgotten handle blocks closure, as does an incomplete\noutcome whose stalled or dead worker has no registered successor.", policy)

    def test_the_amended_terminus_rule_in_principle_8_is_what_this_module_implements(self):
        """A CONFORMANCE check over principle 8, not a presence check over its file.

        **The test immediately above is a presence check, and this one exists because
        that is not enough.** Asserting a governing sentence is IN a file passes for any
        mechanism whatsoever, including one that contradicts the sentence word for word
        -- which is exactly what happened here: principle 8 named a completed terminus
        while this module admitted an abandoned one, for a whole correction round, with
        nothing in the suite able to see it.

        This test reads principle 8's own terminus clause, DERIVES from the words in it
        which termini are admissible, and exercises `dispatch_inventory` against every
        terminus a successor chain can end in. It goes red if the mechanism admits a
        terminus the principle does not name, if it refuses one the principle does name,
        and -- because the expectation is derived rather than written down here -- if the
        principle is reworded away from the mechanism. A consistent change to both is not
        a failure, because agreement is the property under test.
        """
        principles = (ROOT / "governance/GOVERNING_PRINCIPLES.md").read_text(encoding="utf-8")
        section = principles[principles.index("## 8. The dispatch inventory"):principles.index("## 9. Worker states")]
        opening = section.index("requires successor graphs to")
        clause = " ".join(section[opening:section.index(", and reports whether", opening)].split())
        self.assertIn("same-outcome worker", clause)

        # Derived from the clause, never written down here. Rewording the principle
        # changes what this test expects of the mechanism, which is the entire point.
        admits_completed = "completed" in clause
        admits_abandoned = "explicitly recorded as deliberately abandoned" in clause
        self.assertTrue(admits_completed, f"principle 8 names no completed terminus: {clause!r}")

        # `dead` is inadmissible on a DIFFERENT authority, and conflating the two is how
        # a wide draft of this field read as correct: CONFORMANCE_POLICY.md's successor
        # clause names a stalled or dead worker, so relieving `dead` would falsify THAT
        # sentence rather than this one. Derived from it rather than assumed.
        policy = " ".join((ROOT / "governance/CONFORMANCE_POLICY.md").read_text(encoding="utf-8").split())
        self.assertIn("incomplete outcome whose stalled or dead worker has no registered successor", policy)

        outcome = "complete the assigned review"
        termini = {
            "completed": (admits_completed, dict(
                state="finished", outcome_complete=True, terminal_evidence="final result received and consumed")),
            "abandoned": (admits_abandoned, dict(
                state="finished", outcome_complete=False, outcome_abandoned=True,
                terminal_evidence="cancel issued and acknowledged")),
            "merely incomplete": (False, dict(
                state="finished", outcome_complete=False, terminal_evidence="terminal notification received")),
            "dead and abandoned": (False, dict(
                state="dead", outcome_complete=False, outcome_abandoned=True,
                terminal_evidence="platform reports process absence")),
            "dead and incomplete": (False, dict(
                state="dead", outcome_complete=False, terminal_evidence="platform reports process absence")),
            "stalled": (False, dict(state="stalled", outcome_complete=False, terminal_evidence="")),
            "running": (False, dict(state="running", outcome_complete=False, terminal_evidence="")),
        }
        for label, (admissible, overrides) in termini.items():
            with self.subTest(terminus=label):
                inventory = dispatch_inventory(workers=[
                    worker(handle="chain-head", assigned_outcome=outcome, state="dead", outcome_complete=False,
                           terminal_evidence="platform reports process absence", successor_handle="chain-terminus"),
                    worker(handle="chain-terminus", assigned_outcome=outcome, **overrides),
                ])
                self.assertEqual(admissible, inventory["closure_authorized"], (
                    f"principle 8 admits terminus {label!r}: {admissible}; the mechanism says "
                    f"{inventory['closure_authorized']}. Clause read: {clause!r}. "
                    f"Blocking: {inventory['blocking_workers']}"))

        # The clause says SAME-outcome, so a completed terminus owning a different
        # assigned outcome discharges nothing. Also derived from the clause.
        self.assertIn("same-outcome", clause)
        mismatched = dispatch_inventory(workers=[
            worker(handle="chain-head", assigned_outcome=outcome, state="dead", outcome_complete=False,
                   terminal_evidence="platform reports process absence", successor_handle="other-outcome"),
            worker(handle="other-outcome", assigned_outcome="an unrelated cleanup", state="finished",
                   outcome_complete=True, terminal_evidence="final result received and consumed"),
        ])
        self.assertFalse(mismatched["closure_authorized"])


class AbandonedOutcomeTests(unittest.TestCase):
    """A successfully cancelled worker had no discharge at all, and the two moves
    that did clear it both wrote a false claim into the gate.

    Cancelling produces a worker that stopped BEFORE completing its assigned
    outcome -- that is what cancelling is -- so it registers as `finished` with
    `outcome_complete: False`. `finished` is terminal and therefore not in
    `SUCCESSOR_REQUIRING_STATES`, so no successor could discharge it either, and
    the row deadlocked permanently. Measured before this field existed:
    reclassifying the worker to `dead`, and flipping `outcome_complete` to `True`,
    each returned `closure_authorized=True`.

    Both directions are proven here. An abandoned outcome must not block; an
    incomplete outcome that nobody flagged must still block, or the field has
    relieved the gate of the case it exists for rather than of one case.
    """

    def test_a_deliberately_abandoned_outcome_discharges_a_cancelled_worker(self):
        inventory = dispatch_inventory(workers=[worker(
            handle="worker-cancelled-1", state="finished", outcome_complete=False, outcome_abandoned=True,
            terminal_evidence="terminal notification received; cancel issued at commit abc1234",
        )])
        self.assertEqual([], inventory["blocking_workers"])
        self.assertTrue(inventory["closure_authorized"])
        self.assertEqual("lightweight_continuity", close(inventory)["selection"])

    def test_an_unflagged_incomplete_outcome_still_blocks(self):
        """The other direction, and the one that decides whether this is a gate.

        Omitting the field and registering it `False` must behave identically: an
        outcome nobody recorded a decision about is not an abandoned one."""
        for registration in ({}, {"outcome_abandoned": False}):
            with self.subTest(registration=registration):
                inventory = dispatch_inventory(workers=[worker(
                    handle="worker-silent-2", state="finished", outcome_complete=False, **registration,
                )])
                self.assertFalse(inventory["closure_authorized"])
                self.assertTrue(any("worker-silent-2" in row and "incomplete" in row for row in inventory["blocking_workers"]))
                with self.assertRaises(ValueError):
                    close(inventory)

    def test_abandonment_never_substitutes_for_terminal_evidence(self):
        """Abandoning an outcome says nothing about whether the worker stopped.

        This is what keeps the flag from becoming a bare declaration: an
        abandonment can only be recorded against a worker whose stopping is itself
        evidenced, and the terminal-evidence check is untouched by the change."""
        inventory = dispatch_inventory(workers=[worker(
            handle="worker-unevidenced-3", state="finished", outcome_complete=False,
            outcome_abandoned=True, terminal_evidence="",
        )])
        self.assertFalse(inventory["closure_authorized"])
        self.assertTrue(any("worker-unevidenced-3" in row and "no recorded terminal evidence" in row for row in inventory["blocking_workers"]))

    def test_abandonment_never_discharges_a_nonterminal_worker(self):
        """Abandoning an outcome does not stop a process. Every nonterminal state
        still blocks with the flag set, including `stalled`, which is in
        `SUCCESSOR_REQUIRING_STATES` and must not lose its successor requirement
        this way -- it has not been shown to have stopped."""
        for state in sorted(NONTERMINAL_WORKER_STATES):
            with self.subTest(state=state):
                inventory = dispatch_inventory(workers=[worker(
                    handle="worker-running-4", state=state, outcome_complete=False,
                    outcome_abandoned=True, terminal_evidence="",
                )])
                self.assertFalse(inventory["closure_authorized"])
                self.assertTrue(any("nonterminal" in row for row in inventory["blocking_workers"]))
                with self.assertRaises(ValueError):
                    close(inventory)

    def test_a_dead_worker_with_an_abandoned_outcome_STILL_REQUIRES_A_SUCCESSOR(self):
        """The scope guard, and it is the whole reason this field is `finished`-only.

        An earlier draft relieved every TERMINAL state, which swept in `dead` -- and
        that half, and only that half, falsified CONFORMANCE_POLICY.md's sentence
        that an incomplete outcome whose *stalled or dead* worker has no registered
        successor blocks closure. It was withdrawn. **Death is not a decision:** the
        outcome is still owed and a successor is what says who will deliver it,
        whereas a cancel is a supervisor choosing that nobody will.

        This test is the guard against the widening coming back. If it ever passes
        with an empty blocking list, the framework has quietly re-adopted a change
        nobody authorized and a governing sentence has become false with nothing
        else able to see it."""
        abandoned = dispatch_inventory(workers=[worker(
            handle="worker-dead-abandoned-5", state="dead", outcome_complete=False, outcome_abandoned=True,
            terminal_evidence="platform reports process absence", successor_handle=None,
        )])
        self.assertFalse(abandoned["closure_authorized"])
        self.assertTrue(any(
            "worker-dead-abandoned-5" in row and "no registered successor" in row
            for row in abandoned["blocking_workers"]
        ))
        unflagged = dispatch_inventory(workers=[worker(
            handle="worker-dead-abandoned-5", state="dead", outcome_complete=False,
            terminal_evidence="platform reports process absence", successor_handle=None,
        )])
        self.assertFalse(unflagged["closure_authorized"])
        self.assertEqual(abandoned["blocking_workers"], unflagged["blocking_workers"])

    def test_a_successor_chain_may_now_terminate_in_an_abandoned_worker(self):
        """The one residual no scoping removes, pinned so it cannot be discovered
        from behaviour instead of read.

        GOVERNING_PRINCIPLES.md section 8 was AMENDED on 2026-08-26 to name this as
        a second legitimate terminus: a successor graph terminates in a same-outcome
        worker whose assigned outcome is 'either completed or explicitly recorded as
        deliberately abandoned'. Before the amendment the principle named only a
        completed terminus, and this behaviour falsified it.

        The amendment is not a widening, and the test below this one is what holds
        that line: an outcome merely incomplete, unrecorded or inferred is still no
        terminus, and `dead` is still relieved of nothing."""
        inventory = dispatch_inventory(workers=[
            worker(handle="worker-chain-head", assigned_outcome="complete the assigned review", state="dead",
                   outcome_complete=False, terminal_evidence="process absence", successor_handle="worker-chain-tail"),
            worker(handle="worker-chain-tail", assigned_outcome="complete the assigned review", state="finished",
                   outcome_complete=False, outcome_abandoned=True, terminal_evidence="cancel issued and acknowledged"),
        ])
        self.assertEqual([], inventory["blocking_workers"])
        self.assertTrue(inventory["closure_authorized"])

    def test_outcome_abandoned_requires_an_exact_boolean(self):
        """Load-bearing rather than tidy: the string `"false"` is truthy, so a
        coerced read of it would silently relieve a block."""
        for value in ("false", "true", 1, 0, None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "outcome_abandoned must be boolean"):
                dispatch_inventory(workers=[worker(outcome_complete=False, outcome_abandoned=value)])

    def test_an_outcome_cannot_be_both_complete_and_deliberately_abandoned(self):
        """A record claiming both is structurally invalid, not doubly discharged."""
        with self.assertRaisesRegex(ValueError, "both complete and deliberately abandoned"):
            dispatch_inventory(workers=[worker(outcome_complete=True, outcome_abandoned=True)])

    def test_a_registration_without_the_field_produces_a_record_of_unchanged_shape(self):
        """The change is additive for every existing caller, proven rather than
        asserted: a worker registered without the field emits no such key, so an
        adopter validating produced records against the published schema sees
        nothing new until it records an abandonment itself."""
        inventory = dispatch_inventory(workers=[worker(handle="worker-unchanged-6")])
        registered = inventory["workers"][0]
        self.assertNotIn("outcome_abandoned", registered)
        self.assertEqual(
            {"handle", "assigned_outcome", "owner", "durable_cursor", "heartbeat_interval_seconds",
             "last_probe_age_seconds", "state", "outcome_complete", "terminal_evidence", "successor_handle"},
            set(registered),
        )

    def test_the_permitted_field_vocabulary_does_not_drift_between_the_code_and_the_schemas(self):
        """The state vocabulary was pinned against the schema enum and the FIELD
        vocabulary was not, so a field could be permitted by the module and unknown
        to the schema -- or the reverse -- with nothing failing. Both schemas
        declaring these workers are pinned, including the nested copy inside the
        closeout decision, which no test reached at worker level at all."""
        dispatch = json.loads((ROOT / "schemas/dispatch-inventory.schema.json").read_text(encoding="utf-8"))
        closeout = json.loads((ROOT / "schemas/closeout-decision.schema.json").read_text(encoding="utf-8"))
        for label, item in (
            ("dispatch-inventory", dispatch["properties"]["workers"]["items"]),
            ("closeout-decision", closeout["properties"]["dispatch_inventory"]["properties"]["workers"]["items"]),
        ):
            with self.subTest(schema=label):
                self.assertFalse(item["additionalProperties"])
                self.assertEqual(sorted(WORKER_PERMITTED_FIELDS), sorted(item["properties"]))
                self.assertEqual(sorted(WORKER_REQUIRED_FIELDS), sorted(item["required"]))
                self.assertIn("outcome_abandoned", item["properties"])
                self.assertEqual("boolean", item["properties"]["outcome_abandoned"]["type"])

    def test_a_recorded_abandonment_survives_a_json_round_trip_through_the_gate(self):
        """`select_closeout` re-derives the disposition from the registered workers,
        so the new field has to survive normalization and be permitted on the way
        back in. Without that the gate would refuse an inventory it had produced."""
        inventory = json.loads(json.dumps(dispatch_inventory(workers=[worker(
            handle="worker-roundtrip-7", state="finished", outcome_complete=False, outcome_abandoned=True,
            terminal_evidence="terminal notification received; cancel issued",
        )])))
        self.assertIs(True, inventory["workers"][0]["outcome_abandoned"])
        self.assertEqual("lightweight_continuity", close(inventory)["selection"])


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
