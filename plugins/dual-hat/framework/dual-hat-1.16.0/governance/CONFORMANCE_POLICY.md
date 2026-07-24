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
- unresolved findings, debt, exceptions, and stakeholder decisions.

Closure fails on an unvalidated required behavior, contradictory authority, unexplained drift, omitted changed file, stale current-state projection, unknown artifact, hidden retry, unowned transient, or unreported exception. Evidence is bound to a deterministic candidate identity and states commands, environment, counts, skips, failures, reuse, and cleanup.

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
