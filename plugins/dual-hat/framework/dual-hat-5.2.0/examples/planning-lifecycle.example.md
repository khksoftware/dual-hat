<!-- SPDX-License-Identifier: Apache-2.0 -->

# Planning Lifecycle Example

The adjacent backlog, future-work, and history fixtures form one reconciled example. `WORK-0001` advances from `candidate` to `ready`; `FUTURE-0001` remains `monitored` until its measurable trigger fires. Neither state authorizes implementation.

Run from the framework root:

```text
python tooling/planning_reconciliation.py --backlog examples/planning-backlog.example.json --future-work examples/future-work.example.json --history examples/planning-history.example.jsonl
```

When a future item triggers, append a `triggered` event before changing its current status. A separately authorized backlog item receives its own stable ID and initial history event; record the relationship in dependencies or requirements rather than silently changing the future item into executable work. Completion or supersession follows the same append-event-then-current-projection reconciliation and must be reflected in roadmap, session, and handover state where applicable.
