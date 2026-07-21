<!-- SPDX-License-Identifier: Apache-2.0 -->

# Planning Model

New planning items declare `work_item_type` as `capability` or `gov`. Capability planning denotes product increments; independently bounded authority, protocol, lifecycle, shared-governance-schema, cross-repository, or role-model work uses GOV identity and a governance history surface. Historical records remain valid without mass rewrite.

Planning separates authorization from intent. A roadmap states direction and current sequencing; a backlog stores bounded candidate work; a future-work registry stores trigger-governed planning; phases group related outcomes; milestones state observable graduation; capabilities are atomic authorized changes. None authorizes execution without an active work order or equivalent decision.

## Required lifecycle

Planning items have stable IDs, title, objective, owner, dependencies, status, entry and exit criteria, requirements, validation, risks, triggers, history, and supersession. Status transitions are append-only events or otherwise auditable. Current and historical projections cannot contradict one another.

Phase entry verifies dependencies and protected boundaries. Capability closure reconciles roadmap, backlog, debt, triggers, session, and handover. Phase closure additionally reviews unresolved work, test-suite health, debt budget, graduation evidence, release/tag decision, rollback/reopen conditions, and final handover. Avoid duplicate roadmaps, milestone ledgers, or status dashboards that independently claim current truth.

Requirement-to-roadmap traceability is bidirectional: every scheduled requirement reaches a capability or explicit defer decision; every capability identifies its requirement, maintenance, debt, or remediation basis. The broader intent-to-delivery chain follows the [traceability protocol](TRACEABILITY_PROTOCOL.md).

## Canonical planning records

An adopting profile binds exactly one current backlog, one future-work registry, and one append-only planning history. Start them from `templates/PLANNING_BACKLOG.json`, `templates/FUTURE_WORK_REGISTRY.json`, and `templates/PLANNING_HISTORY.jsonl`; remove the illustrative history row before use. Their contracts are `schemas/planning-backlog.schema.json`, `schemas/future-work.schema.json`, and `schemas/planning-history-event.schema.json`.

The current registries are projections, not history. Each item ID is unique across both registries, and every current item has at least one history event. The first event has a null `from_status`; each later event continues the previous status; the last event agrees with the current projection. A `superseded` item names its replacement. Future work additionally owns a measurable event, selector, invoker, review interval, and last evaluation time. A triggered future item still does not authorize execution: promotion creates a separately authorized backlog item and preserves the relationship.

After any planning mutation, append the event and update the current projection as one bounded change, then run `tooling/planning_reconciliation.py`. Reconcile affected roadmap, requirement, debt, session, and handover authorities before closure. See the runnable [planning lifecycle example](../examples/planning-lifecycle.example.md).

Backlog transitions are `candidate → ready → authorized → in_progress → completed`,
with explicit branches to `blocked`, `deferred`, `cancelled`, or `superseded` as
validated by the reconciler. Future work begins `monitored`, may become `triggered`,
and then returns to monitoring or becomes `promoted`, `retired`, or `superseded`.
Terminal states do not reopen in place; new authority receives a new item and records
the supersession relationship. Completed capability or phase work is reconciled
against its roadmap, requirement, debt, session, and handover references before the
current item is removed; append-only history then remains the historical authority.
