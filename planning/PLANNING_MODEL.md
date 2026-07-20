<!-- SPDX-License-Identifier: Apache-2.0 -->

# Planning Model

Planning separates authorization from intent. A roadmap states direction and current sequencing; a backlog stores bounded candidate work; a future-work registry stores trigger-governed planning; phases group related outcomes; milestones state observable graduation; capabilities are atomic authorized changes. None authorizes execution without an active work order or equivalent decision.

## Required lifecycle

Planning items have stable IDs, title, objective, owner, dependencies, status, entry and exit criteria, requirements, validation, risks, triggers, history, and supersession. Status transitions are append-only events or otherwise auditable. Current and historical projections cannot contradict one another.

Phase entry verifies dependencies and protected boundaries. Capability closure reconciles roadmap, backlog, debt, triggers, session, and handover. Phase closure additionally reviews unresolved work, test-suite health, debt budget, graduation evidence, release/tag decision, rollback/reopen conditions, and final handover. Avoid duplicate roadmaps, milestone ledgers, or status dashboards that independently claim current truth.

Requirement-to-roadmap traceability is bidirectional: every scheduled requirement reaches a capability or explicit defer decision; every capability identifies its requirement, maintenance, debt, or remediation basis.
