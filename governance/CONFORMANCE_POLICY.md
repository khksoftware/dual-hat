<!-- SPDX-License-Identifier: Apache-2.0 -->

# Conformance Policy

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
