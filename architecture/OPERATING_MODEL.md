<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operating Model

Dual Hat separates architectural authority from execution accountability without creating two competing sources of truth. The Architecture Office owns intent, requirements, invariants, trade-offs, boundaries, and acceptance. The Engineering Agent owns repository inspection, implementation, validation, migration, publication, cleanup, and complete reporting. A stakeholder retains final informed authority where the decision is genuinely theirs.

Integrated and Split operation are coequal first-class modes governed by [Operating Modes](OPERATING_MODES.md). Integrated is the usability default. Mode, role, lifecycle state, and work-item type remain independent; shared context never permits Engineering self-acceptance or informal role blending.

## Authority stack

1. The live repository and its declared canonical artifacts are authoritative.
2. A bounded work order authorizes change; planning alone does not.
3. Architecture decisions and requirements constrain implementation.
4. Product profiles may narrow or add constraints but cannot silently redefine framework terms.
5. Generated projections, handovers, reports, and archives never outrank their inputs.

Every product declares canonical locations for decisions, requirements, models, ontology, terminology, schemas, specifications, storage design, workflows, planning, validation, sessions, and historical evidence. Dependency direction is framework -> product engineering profile -> product implementation. Product runtime must not depend on framework administration, engineering history, mutable workspace state, or archives.

## Architecture work

Architectural work records the problem, underlying goal, proposed mechanism, durable objective, alternatives, trade-offs, chosen direction, rejected directions, invariants, affected consumers, migration, validation, and reversal strategy. Decisions use stable identities and explicit supersession rather than silent replacement. Requirements are testable, trace to plans and validation, and distinguish normative behavior from examples.

Models define meaning and state; schemas validate representation; specifications define algorithms or interfaces; workflows define actor-visible sequences and failures. A schema cannot substitute for a semantic model, and a prose promise cannot substitute for an implemented or explicitly non-code control.

## Operational invariants

- One active authority exists per exclusive role.
- Every active artifact has an owner, consumer, lifecycle, update trigger, and disposition.
- Every deferred process has a trigger, bounded selector, invoker, retry/terminal behavior, and history—or is honestly planning-only.
- Changes repair the owning layer and revalidate downstream projections.
- Historical evidence is immutable context, never an active dependency.
- Human interaction is reserved for decisions, ambiguity, consent, irreversibility, safety, or meaningful loss risk.

The [reasoning review](REASONING_AND_DECISION_REVIEW.md) governs proposal evaluation. The [Engineering Blueprint](../repository/ENGINEERING_BLUEPRINT.md) applies this model to repository ownership.
