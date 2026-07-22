<!-- SPDX-License-Identifier: Apache-2.0 -->

# Phase-Run Protocol

A phase groups capabilities that deliver one graduation outcome. The phase proposal states purpose, boundaries, dependencies, entry criteria, exit criteria, milestones, validation strategy, debt budget, release intent, rollback, and authorization owner. Opening updates all current planning/session authorities atomically and does not begin later phases.

## Execution

- Sequence bounded capabilities with explicit internal gates.
- Close, validate, commit, and report each capability before the next opens.
- Reconcile roadmap, backlog, debt, deferred triggers, documentation, and health after each capability.
- Use safe parallel validation only from a complete inventory with one owner per shard and one reconciliation owner.
- Preserve unresolved risk and accepted debt; do not convert deferral into completion language.

## Phase health and closure

At phase or governed subphase end, review outcomes, requirements, test relevance and semantic adequacy, coverage gaps, obsolete/redundant/flaky tests, runtime trends, shardability, fixture quality, escaped defects, debt, deferred work, documentation, repository hygiene, and protected assets. Strengthen, consolidate, or retire tests based on defect-detection value rather than count or raw coverage.

The repository-hygiene review also dispositions phase- and capability-scoped outputs. Current operational artifacts remain active; historical evidence moves to the governed archive with traceability; reproducible or valueless duplicates are removed. Capability chronology must not remain mixed into current product output merely because it once supported validation.

Before announcing or opening the next phase or governed subphase, Architecture delivers a brief human-readable transition report without waiting to be asked. It summarizes the activities performed, material outcomes, limitations and carried-forward items, and why the next destination is appropriate. Machine evidence, archive records, and a bare closed/opened announcement do not replace this narrative report.

Groom the affected forward-looking portfolio against the outcomes and environment that now exist. This includes roadmap and backlog entries, debt, future-work triggers, deferred decisions, risk/mitigation registers, migration or upgrade plans, and comparable project-profile authorities. Advance satisfied items; record completed outcomes; retire obsolete and duplicate items with an explicit replacement or reason; and refresh stale assumptions, conditions, owners, mappings, review events, and status. Map every still-live item to planned work or label it trigger-only/deferred with its next evaluation event. Planning advancement informs authorization and never grants it by itself.

For the concrete future-work registry, evaluate every trigger individually. A satisfied trigger advances to its decision- or implementation-ready state or receives an explicit terminal disposition; obsolete and duplicate triggers retire with successor/reason; stale conditions, owners, mappings, review events, and status are updated; and every live trigger maps to a planned phase/work item or an explicit trigger-only next review point. This concrete contract takes precedence over the general portfolio fallback above.

Closure requires every exit criterion, zero unaccepted blockers, current planning/session/handover state, conformance, detached committed-tree validation, clean worktree, authorized release/tag decision, and rollback/reopening instructions. Publish a final handover. A closed phase is immutable; correction proceeds forward through a new bounded capability.
