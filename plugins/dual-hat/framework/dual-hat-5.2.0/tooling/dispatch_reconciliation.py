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
A registered nonterminal worker, a terminal claim without terminal evidence, a
finished worker with incomplete work, and a stalled or dead worker whose chain
of distinct registered same-outcome successors never reaches completion each
block. The stale-heartbeat message is deliberately additive rather than
independent: it is emitted only for a worker already blocked as nonterminal.
Structurally invalid registration -- including unknown fields, a non-boolean
outcome flag, or a non-finite heartbeat value -- raises instead of becoming
authorizing evidence.

An assigned outcome has two honest ends, not one. It can be COMPLETED, and it can
be DELIBERATELY ABANDONED -- a supervisor cancels the work, or answers a worker's
argument by calling the task off. `outcome_complete` is a boolean over *did the
assigned work finish*, so on its own it cannot express the second: a successfully
cancelled worker is `finished` with `outcome_complete: False`, `finished` is
terminal and therefore takes no successor, and the row can then never be
discharged at all. The two moves that do clear it -- reclassifying the worker
`dead`, or setting `outcome_complete: True` -- each authorize the closure and each
write a false claim into the gate that exists to check it.

`outcome_abandoned` is that third value, recorded rather than laundered. It is
permitted and never required, so an inventory that does not use it is unchanged in
every respect. It relieves exactly one blocking line -- the finished-worker-with-an-
incomplete-outcome line -- and it relieves it for `finished` and for NO OTHER STATE:

* a `dead` worker keeps its successor requirement in full. Death is not a decision:
  the outcome is still owed, someone must still deliver it, and a successor is what
  says who. **This bound is why CONFORMANCE_POLICY.md's sentence quoted above stays
  true of this module word for word**, and it is deliberately not expressed as a
  shared `state in TERMINAL_WORKER_STATES` term reused at both sites, because that
  is the form in which it would quietly widen again.
* it never discharges terminality. A nonterminal worker still blocks, because
  abandoning an outcome does not stop a process, and whether the worker stopped is
  a separate question carrying its own evidence.
* it never substitutes for `terminal_evidence`, which a terminal claim still
  requires -- so an abandonment can only be recorded against a worker whose
  stopping is itself evidenced.
* it is refused outright beside `outcome_complete: True`. An outcome cannot be both
  delivered and deliberately abandoned; a record claiming both is structurally
  invalid rather than doubly discharged.

The exact-boolean check on it is load-bearing rather than tidy: the string
`"false"` is truthy, and a coerced read of it would silently relieve a block.

BOTH GOVERNING SENTENCES ARE TRUE OF THIS MODULE, and one of them was AMENDED to
make that so rather than this module being widened to match a text nobody revisited.
CONFORMANCE_POLICY.md's sentence quoted above holds unchanged: its successor clause
names a stalled or dead worker, and both keep their successor requirement exactly as
before. GOVERNING_PRINCIPLES.md section 8 was amended on 2026-08-26 to name a second
terminus for a successor graph -- a same-outcome worker whose assigned outcome is
"either completed or explicitly recorded as deliberately abandoned" -- because the
unamended rule left a correctly executed, fully evidenced cancellation with no
discharge at all. **The amendment is a recorded end state, not a permission:** an
outcome that is merely incomplete, unrecorded or inferred is still no terminus, and
`dead` is still relieved of nothing.

AND THE AGREEMENT IS CHECKED RATHER THAN ASSERTED. The test named
`test_the_amended_terminus_rule_in_principle_8_is_what_this_module_implements` reads
principle 8's own sentence, derives from its wording which termini are admissible,
and exercises this function against every candidate terminus -- so the principle and
the mechanism cannot drift apart in either direction without a red. It exists in that
shape deliberately: the older pattern beside it, which asserts only that a governing
sentence is PRESENT in a file, passes for any mechanism whatsoever, including one
that contradicts the sentence word for word.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import math
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
WORKER_PERMITTED_FIELDS = WORKER_REQUIRED_FIELDS | {"terminal_evidence", "successor_handle", "outcome_abandoned"}


def _numeric_evidence(value: int | float) -> str:
    """Render numeric evidence without converting an unbounded integer to decimal."""
    if isinstance(value, int) and value.bit_length() > 256:
        return f"<{value.bit_length()}-bit integer>"
    return str(value)


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
        raw_handle = worker["handle"]
        if not isinstance(raw_handle, str):
            raise ValueError("dispatch inventory requires each worker's real platform handle to be a string")
        handle = raw_handle.strip()
        if not handle:
            raise ValueError("dispatch inventory requires each worker's real platform handle, not a narrative name")
        unknown = set(worker) - WORKER_PERMITTED_FIELDS
        if unknown:
            raise ValueError(f"worker {handle} carries unknown registration fields: {sorted(str(field) for field in unknown)}")
        if handle in seen:
            raise ValueError(f"dispatch inventory registers the same handle twice: {handle}")
        seen.add(handle)
        state = worker["state"]
        if state not in WORKER_STATES:
            raise ValueError(f"unknown worker state for {handle}: {state!r}")
        for field in ("assigned_outcome", "owner", "durable_cursor"):
            if not isinstance(worker[field], str):
                raise ValueError(f"worker {handle} {field} must be string")
            if not worker[field].strip():
                raise ValueError(f"worker {handle} is registered without {field}")
        interval = worker["heartbeat_interval_seconds"]
        probe_age = worker["last_probe_age_seconds"]
        for label, value in (("heartbeat_interval_seconds", interval), ("last_probe_age_seconds", probe_age)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"worker {handle} declares a non-numeric {label}")
            if isinstance(value, float) and not math.isfinite(value):
                raise ValueError(f"worker {handle} declares a non-finite {label}")
        if interval <= 0:
            raise ValueError(f"worker {handle} has no heartbeat contract bound before launch")
        if probe_age < 0:
            raise ValueError(f"worker {handle} declares a negative last_probe_age_seconds")
        if type(worker["outcome_complete"]) is not bool:
            raise ValueError(f"worker {handle} outcome_complete must be boolean")
        abandoned = worker.get("outcome_abandoned", False)
        if type(abandoned) is not bool:
            raise ValueError(f"worker {handle} outcome_abandoned must be boolean when present")
        if abandoned and worker["outcome_complete"] is True:
            raise ValueError(
                f"worker {handle} records its assigned outcome as both complete and deliberately abandoned"
            )

        raw_terminal_evidence = worker.get("terminal_evidence", "")
        if "terminal_evidence" in worker and not isinstance(raw_terminal_evidence, str):
            raise ValueError(f"worker {handle} terminal_evidence must be string when present")
        raw_successor = worker.get("successor_handle")
        if raw_successor is not None and not isinstance(raw_successor, str):
            raise ValueError(f"worker {handle} successor_handle must be string or null")
        terminal_evidence = raw_terminal_evidence.strip()
        successor = (raw_successor or "").strip()
        outcome_complete = worker["outcome_complete"]

        if state in TERMINAL_WORKER_STATES:
            terminal += 1
            if not terminal_evidence:
                blocking.append(f"{handle} claims terminal state '{state}' with no recorded terminal evidence")
        else:
            nonterminal += 1
            blocking.append(f"{handle} is registered nonterminal ('{state}') and was never discharged")
            if probe_age > interval:
                blocking.append(
                    f"{handle} was last probed {_numeric_evidence(probe_age)}s ago, "
                    f"beyond its declared {_numeric_evidence(interval)}s heartbeat interval"
                )
        if state in SUCCESSOR_REQUIRING_STATES and not outcome_complete and not successor:
            blocking.append(
                f"{handle} is '{state}' with an incomplete assigned outcome and no registered successor"
            )
        # `outcome_abandoned` relieves THIS line and no other, for `finished` and for no other
        # state. It is deliberately written here rather than as a derived `outcome_discharged`
        # term reused above: a `dead` worker keeps its successor requirement in full, and a
        # shared term is how that would quietly widen again. See the module docstring.
        if state == "finished" and not outcome_complete and not abandoned:
            blocking.append(f"{handle} claims finished state with an incomplete assigned outcome")
        normalized.append({"terminal_evidence": "", "successor_handle": None, **dict(worker), "handle": handle})

    registered = {str(worker["handle"]): worker for worker in normalized}
    for worker in normalized:
        handle = str(worker["handle"])
        if worker["state"] not in SUCCESSOR_REQUIRING_STATES or worker["outcome_complete"] is True:
            continue
        successor = str(worker.get("successor_handle") or "").strip()
        if not successor:
            continue
        if successor == handle:
            blocking.append(f"{handle} names itself as successor for an incomplete assigned outcome")
        elif successor not in registered:
            blocking.append(f"{handle}'s successor {successor} is not registered")
        elif registered[successor]["assigned_outcome"] != worker["assigned_outcome"]:
            blocking.append(f"{handle}'s registered successor {successor} owns a different assigned outcome")

    for worker in normalized:
        if worker["state"] not in SUCCESSOR_REQUIRING_STATES or worker["outcome_complete"] is True:
            continue
        start = str(worker["handle"])
        current = worker
        chain: list[str] = []
        positions: dict[str, int] = {}
        while current["outcome_complete"] is not True:
            handle = str(current["handle"])
            if handle in positions:
                cycle = [*chain[positions[handle]:], handle]
                blocking.append(f"{start}'s successor chain enters cycle: {' -> '.join(cycle)}")
                break
            positions[handle] = len(chain)
            chain.append(handle)
            if current["state"] not in SUCCESSOR_REQUIRING_STATES:
                break
            successor = str(current.get("successor_handle") or "").strip()
            if (not successor or successor == handle or successor not in registered
                    or registered[successor]["assigned_outcome"] != current["assigned_outcome"]):
                break
            current = registered[successor]

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
