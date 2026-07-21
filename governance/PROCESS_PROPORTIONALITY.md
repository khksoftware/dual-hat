<!-- SPDX-License-Identifier: Apache-2.0 -->

# Process Proportionality

Avoid over-bureaucratization. Dual Hat uses the lightest process that provides enough authority, safety, traceability, recovery, and confidence for the actual risk. A ceremony, artifact, gate, rerun, handoff, reconciliation, or check is justified only when it prevents or detects a material failure more effectively than a simpler control.

## Cardinal rules

1. Prefer one short authoritative record over multiple overlapping artifacts.
2. Reuse still-valid evidence. Do not rerun, rehash, regenerate, re-review, or repackage solely because unrelated or presentational state changed.
3. Combine adjacent checks and handoffs when their authority, inputs, timing, and audience are the same.
4. Escalate depth only for demonstrated risk, uncertainty, changed inputs, unexplained failure, or an explicit governing requirement.
5. Do not create a new protocol, schema, ledger, manifest, report, or approval surface when an existing record or a concise field is sufficient.
6. Keep explanations of omitted work proportionate; a one-line rationale is enough for an obvious focused choice.
7. Treat process wall time, repeated operator attention, and maintenance burden as engineering costs. When they become material, simplify the owning control instead of normalizing the overhead.
8. Preserve human decisions for material judgment, authority, consent, irreversibility, safety, rights, and meaningful loss risk. Do not require interaction merely to advance routine process state.
9. Schedule a lifecycle step at the latest safe point when performing it earlier would predictably require the same step to be repeated before its evidence can be used. Do not defer a step past the point where it protects a material decision or prevents costly rework.
10. When changed inputs genuinely require renewed validation, review, reconciliation, packaging, or repository checks, assess the delta and affected surface first. Rerun the whole process only when impact cannot be bounded reliably or a material risk or governing requirement demands it.
11. For every ad hoc fix, assess whether the failure class can recur across inputs, work items, environments, or consumers. When it can, prefer the smallest proportionate repair in the owning layer that prevents recurrence, while still correcting the current instance. Do not turn an isolated defect into a broad redesign without demonstrated recurrence risk.

## Common application areas

- **Planning and sealing:** scale work orders to the change; avoid duplicating roadmap, backlog, decision, and scope prose.
- **Handoffs in both directions:** update only information needed to resume or decide; do not restate repository history or evidence already referenced.
- **Preflight and repository state:** check boundaries affected by the work; reuse environment evidence until a defined invalidation trigger occurs.
- **Validation and independent review:** default to the smallest credible affected set; expand for risk or unexplained results, not ceremony.
- **Status and monitoring:** report meaningful milestones, changed state, blockers, and terminal outcomes; compact unchanged heartbeats.
- **Documentation and reconciliation:** repair the owning authority and only downstream projections that are actually affected.
- **Release, packaging, and publication:** generate and verify only authorized deliverables; do not rebuild unchanged products to refresh narrative evidence.
- **Closure and archival:** retain decision-bearing and non-reproducible evidence; reference rather than copy; avoid elaborate closeout for a small reversible change.
- **Dependencies, security, privacy, rights, and recovery:** keep protections proportional but never waive a material safeguard merely because it has process cost.

Mandatory does not mean maximally elaborate. A mandatory outcome may be satisfied by a lighter mechanism when it provides equivalent evidence and protection. New process must identify its consumer, prevented failure, invalidation trigger, expected cost, and retirement or simplification condition.
