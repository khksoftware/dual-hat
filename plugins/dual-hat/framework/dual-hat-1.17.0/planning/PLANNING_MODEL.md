<!-- SPDX-License-Identifier: Apache-2.0 -->

# Planning Model

New planning items declare `work_item_type` as `capability` or `gov`. Capability planning denotes product increments; independently bounded authority, protocol, lifecycle, shared-governance-schema, cross-repository, or role-model work uses GOV identity and a governance history surface. Historical records remain valid without mass rewrite.

Planning separates authorization from intent. A roadmap states direction and current sequencing; a backlog stores bounded candidate work; a future-work registry stores trigger-governed planning; phases group related outcomes; milestones state observable graduation; capabilities are atomic authorized changes. None authorizes execution without an active work order or equivalent decision.

Authorization may name one exact action or a bounded reusable class. A
categorical authorization declares objective eligibility conditions,
per-candidate evidence, excluded cost/privacy/risk classes, invalidation and
reapproval triggers, and cleanup of rejected installed candidates. It avoids
repeated approval prompts without weakening evaluation or expanding authority.

Execution authorization also does not settle consequential design details that the existing decision record leaves open. Before an implementation-ready specification fixes a material product, user-experience, workflow, commercial, privacy, or architectural choice, Architecture uses the lightest useful discussion artifact to expose and resolve the meaningful options. This is a decision-quality control, not a mandatory separate capability or ceremony.

Once the design or plan is ready and before execution, run a proportionate
optimization pass. Consider avoiding brute force, ordering for earlier value,
improving dependency sequence, allocating parallelism and resources,
checkpointing incremental execution, improving evidence reuse, and substituting a
cheaper equivalent control. Preserve scope, authority, acceptance, safety, and
recovery. A sealed independent Architecture optimization review is required
only when scale, complexity, risk, or irreversibility justifies its distinct
judgment; straightforward plans proceed without a separate ritual.
Long-running or materially resource-consuming execution also receives
proportionate reevaluation at meaningful checkpoints for changed bottlenecks,
throughput, failures, value yield, allocation, batching, cost, and wall time.
Retest material embedded assumptions or hypotheses against current evidence,
explicitly confirm, revise, or retire them, and distinguish supported
assumptions from merely unchallenged ones. Experiment only in proportion to
consequence and uncertainty. The reevaluation must not pause healthy work or
become a routine ceremony.

## Required lifecycle

Planning items have stable IDs, title, objective, owner, dependencies, status, entry and exit criteria, requirements, validation, risks, triggers, history, and supersession. Work-item planning assigns the abstract model tier required for each materially distinct activity, including implementation, architecture, independent review, security/privacy/rights review, and release review where applicable. It references the current project-local concrete mapping rather than embedding provider choices in portable policy. Status transitions are append-only events or otherwise auditable. Current and historical projections cannot contradict one another.

Authorization and preflight verify that every mandatory assigned tier has a current, evidence-backed concrete selection. A changed environment fingerprint or changed model capability/availability invalidates the mapping and triggers remapping at a safe boundary. Session and handover state record the mapping identity and fingerprint used by active work. Missing or stale mandatory mapping is a resumable hard stop; optional fallback requires the governed confirmation defined by the model-tier policy.

Phase entry verifies dependencies and protected boundaries. Capability closure reconciles roadmap, backlog, debt, triggers, session, and handover. Phase or governed subphase closure additionally reviews unresolved work, test-suite health, debt budget, graduation evidence, release/tag decision, rollback/reopen conditions, and final handover. Its transition cannot be represented only by status fields: Architecture also gives the user a concise narrative of completed activities, outcomes, limitations or carry-forward work, and the rationale for the next phase or subphase.

When phase closure and successor opening occur together, update current
planning, completed history, the successor capability ledger, session, and
handover as one atomic transition. The closed phase leaves current planning,
the successor receives its current execution lane, and validation rejects
simultaneous current/unopened or active/history contradictions.

Each project profile inventories its forward-looking authorities—such as roadmap, backlog, debt, future-work triggers, deferred decisions, risk/mitigation registers, and migration, upgrade, release, or productization plans—and assigns progression-point and change-driven review events. Default progression points are phase or governed subphase opening/closure, material roadmap replanning, and release/productization gates; an owning scope, assumption, dependency, or environment change may trigger a narrower review. Groom the affected delta for activation, completion, obsolescence, duplication, stale assumptions/conditions/owners/mappings/review dates/status, and next placement. Use a full portfolio review only when the progression point or breadth of change warrants it. Avoid duplicate roadmaps, milestone ledgers, or status dashboards that independently claim current truth.

The canonical future-work registry has the stronger item-level rule: at phase or governed subphase closure and material replanning, evaluate every registered trigger; advance satisfied triggers or explicitly disposition them; retire obsolete/duplicate triggers with successor/reason; refresh stale trigger state; and map every live trigger to planned work or a named trigger-only review event. Other forward-looking artifacts use their own concrete contracts when present and the portfolio rule above only as fallback.

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
