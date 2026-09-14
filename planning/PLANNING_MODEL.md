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

Once the design or plan is ready and before execution, run the proportionate
optimization pass, and the reevaluation that long-running execution receives.
[Governing Principles](../governance/GOVERNING_PRINCIPLES.md) principle 1 binds
the pass itself -- consider whether the same authorized outcome can be reached
more cheaply, apply only improvements that preserve authority, acceptance,
safety and recovery, and do not turn the pass into a reviewed artifact of its
own. **This document is the owning authority for what the pass covers**, which
principle 1 deliberately does not enumerate: better sequencing, earlier value,
better dependency ordering, better allocation of parallelism and resources,
incremental execution with useful checkpoints, better evidence reuse, and a
cheaper equivalent control. For ongoing long-running or materially
resource-consuming execution, reevaluate proportionately at meaningful
checkpoints when duration, scale, or observed change warrants it -- changed
bottlenecks, throughput, failures, value yield, allocation, batching, cost and
wall time -- and apply only bounded improvements whose expected benefit exceeds
disruption and revalidation cost. Retest material assumptions embedded in the
current design or plan against current evidence and explicitly confirm, revise,
or retire them; an unchallenged assumption is not a supported one. Scale
experimentation to the assumption's consequence and uncertainty. Do not pause
healthy work merely to inspect it. Planning binds one thing principle 1 does not
state: an optimization must preserve the authorized scope, not only authority,
acceptance, safety, and recovery.

Every plan receives at least two adversarial reduction passes before it is ready
for approval, and *plan* is read at its widest: any design, brief, dispatch,
batch, sequence, estimate, test population or execution approach, whether or not
it is called a test plan or a cost projection, whether or not it goes to an
approver, and whether or not anyone suspects it of being large. If you are about
to do a thing more than once, or to hand a way of doing it to someone else, that
is a plan and this rule governs it. A narrow reading is not available in this
text: the rule's own first pass removes broad coverage carrying no distinct risk,
which is a property of execution designs and not only of estimates. The first removes work already proved by
unchanged evidence, duplicated coverage, repeated setup or adjudication, and
manual steps an existing governed operation performs deterministically. The
second challenges every survivor against measured command or runtime evidence
and requires the distinct risk or outcome that item alone establishes. Repeat
the challenge while generic contingency, duplicated handoff or publication
work, an hour-scale allowance for seconds-scale commands, or another unsupported
component remains. Record the unreduced plan, what each pass removed, the
measured basis of the remainder, its de-duplicated test population, the distinct
risk owned by every retained test or end-to-end anchor, and a hard ceiling that
unused allowance cannot expand. A challenged plan returns to Architecture for
reduction; execution does not consume the disputed allowance.

For design and test planning, make principle 1's Pareto (80/20) heuristic concrete
before selecting a matrix: enumerate the materially distinct semantics, failure
modes, branches, subsystem owners or protected boundaries, and risk classes first.
Plan the smallest defect-sensitive representative set that covers those classes;
put repeated combinatorial and scale breadth in a cheaper analytical, simulated, or
in-memory layer where its relevant semantic equivalence is sound; and retain a small
set of real integration, end-to-end, or durable anchors for what the cheaper layer
cannot establish. The plan states omitted cross-products and nonclaims. It requires
exhaustive execution only when each cell owns distinct semantics, impact cannot be
bounded, material safety or integrity risk requires it, or explicit semantic-release
authority requires it. The [Validation Protocol](../validation/VALIDATION_PROTOCOL.md)
owns the evidence composition; the 80/20 name is never a numeric coverage quota.

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

**Reading an item is itself a disposition point, and this binds outside review events.** The grooming and trigger rules above are attached to progression points and change-driven reviews, so an item read at any other time -- during adjacent work, a triage, an inspection, or by noticing it in passing -- has no obligation attached to that reading. It acquires one here. An item that has been opened and understood leaves that act with one of four outcomes, and returning it unchanged is not among them: **worked**; **re-owned**, meaning placed in a named queue with a named owner able to act on it, which for an item whose subject lies in a scope the reader does not own means that scope's queue rather than a note in a report; **corrected**, where the record was inaccurate or has been overtaken by other work; or **closed**, where it is demonstrably no longer relevant.

**The reason to state this as an obligation is that putting the item back is the cheapest available outcome**, and an item put back is indistinguishable from an item nobody read. A register whose entries are repeatedly read and repeatedly survive unchanged is not a register being managed; the reading is producing no disposition, and nothing in the register records that it happened.

**Deferral with a stated reason is not a disposition.** Recording why an item was not worked is better than silence and does not discharge this: the item still leaves the reading with an owner and a queue position, or it does not survive the reading. **An item may only be closed as irrelevant on demonstrated grounds** -- a subject that no longer exists, a duplicate whose survivor is named, a claim shown false -- never on the reader's impression that it no longer matters.

**Classification: judgement-only. Advice.** Nothing in this framework's shipped source enforces it and nothing can: the registers, the queues and the reading occasions are all the adopting project's, and a detector would have to know that a human or agent read an item, which no artifact records. It holds because a reasonable agent reads it and complies, and because a register that only grows is visible to whoever owns the work it represents.

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
