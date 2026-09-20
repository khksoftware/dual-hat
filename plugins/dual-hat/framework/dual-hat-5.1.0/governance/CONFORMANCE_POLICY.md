<!-- SPDX-License-Identifier: Apache-2.0 -->

# Conformance Policy

Conformance is all-or-nothing for mandatory core requirements. A platform profile implements the core; it does not approximate it. Preflight failure or a runtime-discovered gap blocks execution and conformance claims. Mode or platform switching requires a governed, resumable handoff. Platform-specific limitations cannot redefine core authority or establish precedent.

Conformance is a reasoned determination that implementation, repository state, validation evidence, documentation, publication, and cleanup satisfy the authorized objective. Passing tests alone is insufficient.

## Required dimensions

- scope and exclusions;
- architecture, requirements, invariants, and dependency direction;
- implementation completeness and owning-layer repair;
- semantic completeness of claimed capabilities;
- focused, broad, and risk-selected detached validation;
- migrations, compatibility, rollback, and external-state reconciliation;
- documentation/help convergence;
- artifact ownership, lifecycle, and final disposition;
- planning, session, handover, and publication truth;
- protected assets, secrets, licensing, and rights;
- broader-design and analogous-gap review;
- reachability of what the work introduced: whether any capability, control, rule or obligation it added is invoked, read or performed by anything;
- unresolved findings, debt, exceptions, and stakeholder decisions.

Closure fails on an unvalidated required behavior, contradictory authority, unexplained drift, omitted changed file, stale current-state projection, unknown artifact, hidden retry, unowned transient, or unreported exception. Evidence is bound to a deterministic candidate identity and states commands, environment, counts, skips, failures, reuse, and cleanup.

A closure states, for the surface its own changes touched, whether each capability, control, rule or obligation it introduced is reached by something that actually runs. The scope is the work's own diff, never the whole estate: a closure-time check whose cost scales with the project rather than with the change is one adopters route around, and a check that is routed around is itself the defect this dimension names. An unreached item is not a defect and not a deletion warrant -- it is an unanswered question, and this dimension requires only that the answer be recorded where the next reader of that item meets it. Four answers are admissible: the act that would reach it exists and runs, so a caller is added; the act is stopped by a standing boundary, so dormancy is recorded naming the boundary; the act does not exist, so dormancy is recorded naming the missing precondition; or nothing should ever reach it, so it is reported as dead without being removed in the same act. Fabricating a caller to clear an entry is forbidden: a call site nobody wanted converts a visible gap into an invisible one, which is worse than the gap. The residual is that reachability is decidable only for what the project's own tooling can resolve -- a name reached by reflection, a string table or a configured entry point may read as unreached, so this dimension binds what an adopter can compute and never asserts that its computation is complete.

Stale current-state projection is evaluated against the derived-artifact registry defined in [Repository Governance](REPOSITORY_GOVERNANCE.md), so the failure is computable rather than a judgement with nothing to evaluate it against: every registry entry the closure's changes reach is re-derived and diffed, and the set of entries the runner did not independently re-derive is reported by name. A closure that names no registry cannot claim this dimension; it reports the projection as unchecked. The residual is the registry's own completeness — a canonical record absent from the registry is invisible here, exactly as it is there — so this binds what an adopter has declared and never establishes that the declaration is complete.

A terminal response, execution-lease release, capability closure, or cessation of
background-worker monitoring is nonconforming unless its termination-preflight
receipt proves complete reconciliation of the authoritative planned-scope inventory
or identifies an active named hard-stop gate. An unregistered, nonterminal,
unprobed, or silently forgotten handle blocks closure, as does an incomplete
outcome whose stalled or dead worker has no registered successor. The dispatch
registration duty, the reconciliation cadence, and the evidence definitions of
worker state that this gate is evaluated against are stated in
[Governing Principles](GOVERNING_PRINCIPLES.md).

## Detached validation decision

Detached committed-tree validation is required when clean-checkout behavior may differ: packaging, export, release, snapshots, paths, ownership, ignored workspace, generated artifacts, schemas or persisted state, dependencies, discovery/loading, archives, migrations, handovers, publication binding, platform-sensitive files, broad multi-surface behavior, phase closure, release/tag, or external publication. A low-risk omission must be explicit with risk class, rationale, and compensating validation.

## Reporting

Every completed bounded run produces an automatic self-contained exit report. The report identifies commits, branch, publication/alignment, worktrees, phase or release state, changes, validation, detached decision, resource observations, protected assets, artifact dispositions, unresolved boundaries, required stakeholder action, and next authorized work. A canonical conformance artifact is retained when policy requires it; chat delivery does not replace repository authority.

A claim such as `complete`, `all`, `none remaining`, or an equivalent universal
statement is valid only against an explicitly named scope or authoritative
inventory. Reconcile that scope by count and disposition before making the
claim, and state the material remainder. Completion of a sample, batch, wave,
medium, or other bounded subset must be reported as subset completion, never as
completion of its parent objective. If the parent inventory is unknown or not
yet reconciled, report the status as partial or unknown rather than inferring
completion. Reuse an existing manifest or ledger for this check; do not create a
new ceremony solely to support the wording.

A representative sample supports conclusions about the sampled items and,
only when a preregistered sampling design justifies inference, the declared
population. It does not support source-, channel-, site-, feed-, corpus-, or
catalog-wide exclusion merely because sampled items were redundant, weak, or
out of scope. When a finite or enumerable corpus is intended for broad intake,
inventory its items first, then track catalog completeness, triage
completeness, and mining or processing completeness separately. Apply
relevance and exclusion item by item; use a population-wide disposition only
for a demonstrated population-wide condition or a valid sampling inference.
