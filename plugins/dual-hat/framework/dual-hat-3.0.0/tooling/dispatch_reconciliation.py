"""Delegated-dispatch inventory reconciliation for the closure gate.

Makes an already-adopted governance sentence executable. CONFORMANCE_POLICY.md
states that an unregistered, nonterminal, unprobed, or silently forgotten handle
blocks closure, as does an incomplete outcome whose stalled or dead worker has no
registered successor. Until now nothing could detect a violation of it.

The registration fields and the worker-state vocabulary are not invented here:
GOVERNING_PRINCIPLES.md requires every verified dispatch to register its real
handle, assigned outcome, owner, durable cursor or process identity, heartbeat
contract, and current state, and defines the states by evidence -- `finished`
means the assigned final result was received and consumed, `dead` means process
authority reports terminal exit or absence, `stalled` means the declared
heartbeat threshold was exceeded and explicit probes show no progress, and
`unreachable` remains nonterminal until it meets the `stalled` or `dead` test.

This is a sibling of `continuity_closeout.reconciliation_audit`, deliberately
matching its shape -- per-item required fields, cited rather than narrated
evidence, `blocking_*`, `closure_authorized`, and a refusal that names its
subject -- rather than a second mechanism for the same job.

Two divergences from that sibling are deliberate and grounded in source, not
oversights. It requires no independent reviewer, because GOVERNING_PRINCIPLES.md
assigns this reconciliation to the main role rather than to a context-isolated
one; requiring independence would contradict the rule being enforced. And it
accepts an empty inventory, because a session that delegated nothing is
legitimate -- see `unregistered_dispatch_detectable` for what that costs.

`continuity_closeout.select_closeout()` re-derives its dispatch disposition by
calling `dispatch_inventory()` on the registered workers it was handed, rather
than reading the summary flags off the inventory. This module is therefore the
single implementation of the state vocabulary and of what blocks closure; the
gate cannot drift away from it, and a hand-assembled inventory cannot authorize
a closure this module would refuse.

Blocking is reported per detected condition rather than per independent cause.
Three conditions block independently -- a registered nonterminal worker, a
terminal claim with no recorded terminal evidence, and a stalled or dead worker
with an incomplete outcome and no registered successor. The stale-heartbeat
message is deliberately additive rather than independent: it is emitted only for
a worker already blocked as nonterminal, because a terminal state carrying
recorded terminal evidence is discharged and its probe age no longer governs.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from typing import Mapping, Sequence


DISPATCH_INVENTORY_SCHEMA = "dual-hat-dispatch-inventory/1.0"
TERMINAL_WORKER_STATES = frozenset({"finished", "dead"})
NONTERMINAL_WORKER_STATES = frozenset({"running", "unreachable", "stalled"})
WORKER_STATES = TERMINAL_WORKER_STATES | NONTERMINAL_WORKER_STATES
SUCCESSOR_REQUIRING_STATES = frozenset({"stalled", "dead"})
WORKER_REQUIRED_FIELDS = frozenset({
    "handle", "assigned_outcome", "owner", "durable_cursor",
    "heartbeat_interval_seconds", "last_probe_age_seconds", "state", "outcome_complete",
})


def dispatch_inventory(*, workers: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Reconcile the authoritative dispatch inventory into a closure disposition.

    Structurally invalid registration raises, because an inventory that cannot be
    trusted must not be silently treated as an inventory that authorizes closure.
    Substantive conditions become `blocking_workers` entries, each naming the
    handle, so the refusal identifies its subject rather than asserting a count.
    """
    normalized: list[dict[str, object]] = []
    blocking: list[str] = []
    seen: set[str] = set()
    terminal = nonterminal = 0
    for worker in workers:
        missing = WORKER_REQUIRED_FIELDS - set(worker)
        if missing:
            raise ValueError(f"dispatch inventory worker is missing required registration fields: {sorted(missing)}")
        handle = str(worker["handle"] or "").strip()
        if not handle:
            raise ValueError("dispatch inventory requires each worker's real platform handle, not a narrative name")
        if handle in seen:
            raise ValueError(f"dispatch inventory registers the same handle twice: {handle}")
        seen.add(handle)
        state = worker["state"]
        if state not in WORKER_STATES:
            raise ValueError(f"unknown worker state for {handle}: {state!r}")
        for field in ("assigned_outcome", "owner", "durable_cursor"):
            if not str(worker[field] or "").strip():
                raise ValueError(f"worker {handle} is registered without {field}")
        interval = worker["heartbeat_interval_seconds"]
        probe_age = worker["last_probe_age_seconds"]
        for label, value in (("heartbeat_interval_seconds", interval), ("last_probe_age_seconds", probe_age)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"worker {handle} declares a non-numeric {label}")
        if interval <= 0:
            raise ValueError(f"worker {handle} has no heartbeat contract bound before launch")
        if probe_age < 0:
            raise ValueError(f"worker {handle} declares a negative last_probe_age_seconds")

        terminal_evidence = str(worker.get("terminal_evidence") or "").strip()
        successor = str(worker.get("successor_handle") or "").strip()
        outcome_complete = bool(worker["outcome_complete"])

        if state in TERMINAL_WORKER_STATES:
            terminal += 1
            if not terminal_evidence:
                blocking.append(f"{handle} claims terminal state '{state}' with no recorded terminal evidence")
        else:
            nonterminal += 1
            blocking.append(f"{handle} is registered nonterminal ('{state}') and was never discharged")
            if probe_age > interval:
                blocking.append(
                    f"{handle} was last probed {probe_age}s ago, beyond its declared {interval}s heartbeat interval"
                )
        if state in SUCCESSOR_REQUIRING_STATES and not outcome_complete and not successor:
            blocking.append(
                f"{handle} is '{state}' with an incomplete assigned outcome and no registered successor"
            )
        normalized.append({"terminal_evidence": "", "successor_handle": None, **dict(worker), "handle": handle})

    return {
        "schema": DISPATCH_INVENTORY_SCHEMA,
        "workers": normalized,
        "registered_count": len(normalized),
        "terminal_count": terminal,
        "nonterminal_count": nonterminal,
        "blocking_workers": blocking,
        "closure_authorized": not blocking,
        "unregistered_dispatch_detectable": False,
    }
