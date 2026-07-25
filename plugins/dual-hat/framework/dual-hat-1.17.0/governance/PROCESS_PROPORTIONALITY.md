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
12. When research, experimentation, tuning, or similar repeated work pursues one bounded objective under the same authority and acceptance contract, prefer explicit iterations within the same capability. Do not create a sequence of capabilities merely to number successive attempts. Open a new capability only when the objective, authority, product boundary, rollback unit, or acceptance contract materially changes.
13. Capability preflight evidence is content-addressed and invalidation-driven. Reuse a passing receipt when its evidence bytes, interpreter/tool identity, applicable profile rule, environment fingerprint, and governed consumer boundary remain valid. Rerun only receipts invalidated by a changed input or expired condition, and record reused versus refreshed evidence. Do not recompute an unchanged catalog merely to bind a new work-item identifier.
14. A stakeholder may grant standing authorization for a precisely bounded class of dependencies, models, tools, or equivalent candidates. Reuse that authority while every candidate satisfies its declared license, cost, reliability, safety, hardware, support, privacy, integrity, and scope conditions; re-escalate only when a condition is absent or exceeded. Preserve rejected-candidate evidence and remove rejected installed candidates promptly instead of retaining them until a replacement exists.
15. When a stakeholder or another agent identifies a real mistake, omission,
inaccuracy, or process failure, the responsible role must not stop at
acknowledgment or instance repair. Generalize the error mode, identify the
owning root cause, select the smallest reasonable countermeasure, apply it to
the current work, and codify it at the lowest reusable authority that can
prevent or reliably detect similar recurrence. Check directly analogous
current-session state and report the disposition. Keep the response
proportionate: trivial slips need only a lightweight behavioral correction
unless they reveal a recurring or materially harmful failure class; do not use
the rule to create speculative controls or unrelated scope.
16. Before asserting that a current product, platform, tool, subscription, or
runtime can or cannot support a proposed operation, verify the claim against
current authoritative documentation and, when locally testable, the installed
surface and its actual authentication or capability state. Distinguish an
unsupported capability from a supported capability that is merely unconfigured,
logged out, unavailable under the current entitlement, or blocked by the present
environment.
17. Persist a lesson only when it is reusable beyond the immediate correction or
materially improves a governing control. Prefer the existing owning authority,
finding, decision, debt, or planning record; do not require a per-run lesson
ledger. At an accumulated framework release or governed phase progression,
consolidate duplicates, resolve contradictions, review staleness and scope, and
promote a lesson across contexts only when evidence supports the broader claim.
Retire or narrow stale guidance instead of preserving it as folklore.
18. Once a design or plan is execution-ready and before mutation, perform a
proportionate optimization pass. Consider whether the same authorized outcome
can avoid brute force, deliver value earlier, improve dependency sequencing,
allocate parallelism or resources better, execute incrementally with useful
checkpoints, improve evidence reuse, or use a cheaper equivalent control. Apply
only improvements that preserve authority, acceptance, safety, and recovery.
Require a sealed independent Architecture optimization review only when scale,
complexity, risk, or irreversibility makes its distinct judgment worthwhile;
straightforward work needs no separate review ritual.
For ongoing long-running or materially resource-consuming execution,
reevaluate proportionately at meaningful checkpoints when duration, scale, or
observed change warrants it. Check changed bottlenecks, throughput, failures,
value yield, allocation, batching, cost, and wall time, and apply only bounded
improvements whose expected benefit exceeds disruption and revalidation cost.
Retest material assumptions or hypotheses embedded in the current design or
plan against current evidence and explicitly confirm, revise, or retire them;
an unchallenged assumption is not a supported one. Scale experimentation to the
assumption's consequence and uncertainty.
Do not pause healthy work merely to inspect it or turn periodic reevaluation
into ceremony.

## Common application areas

- **Planning and sealing:** scale work orders to the change; avoid duplicating roadmap, backlog, decision, and scope prose.
- **Pre-execution optimization:** improve value order, sequencing, resource use,
  checkpointing, evidence reuse, and control cost only where the expected
  benefit justifies the review.
- **Handoffs in both directions:** update only information needed to resume or decide; do not restate repository history or evidence already referenced.
- **Preflight and repository state:** check boundaries affected by the work; reuse environment evidence until a defined invalidation trigger occurs.
- **Validation and independent review:** default to the smallest credible affected set; expand for risk or unexplained results, not ceremony.
- **Status and monitoring:** report meaningful milestones, changed state, blockers, and terminal outcomes; compact unchanged heartbeats.
- **Documentation and reconciliation:** repair the owning authority and only downstream projections that are actually affected.
- **Release, packaging, and publication:** generate and verify only authorized deliverables; do not rebuild unchanged products to refresh narrative evidence.
- **Closure and archival:** retain decision-bearing and non-reproducible evidence; reference rather than copy; avoid elaborate closeout for a small reversible change.
- **Durable learning:** correct the live instance first, retain only reusable
  learning, and perform consolidation, contradiction, and staleness review at an
  accumulated release or governed progression point rather than after every run.
- **Dependencies, security, privacy, rights, and recovery:** keep protections proportional but never waive a material safeguard merely because it has process cost.

Mandatory does not mean maximally elaborate. A mandatory outcome may be satisfied by a lighter mechanism when it provides equivalent evidence and protection. New process must identify its consumer, prevented failure, invalidation trigger, expected cost, and retirement or simplification condition.
