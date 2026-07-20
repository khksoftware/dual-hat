<!-- SPDX-License-Identifier: Apache-2.0 -->

# Architecture Office Guide

Architecture selects Integrated or Split mode, owns work-item classification and sealed scope, and alone decides acceptance. It may directly mutate an exclusively Architecture-owned record only after the impact scan in [Role Transitions](ROLE_TRANSITIONS.md) proves no cross-boundary ripple; uncertainty uses Engineering execution.

The Architecture Office turns a desired outcome into bounded authority. It owns the underlying goal, architectural invariants, accepted trade-offs, decision gates, scope, exclusions, phase or capability sequencing, and closure criteria. It does not prescribe incidental implementation detail when several mechanisms could satisfy the same result.

## From request to work order

1. Separate the durable goal from the requester's proposed mechanism.
2. Inspect current repository authority and identify the owning layer, affected consumers, protected state, and relevant history.
3. Compare alternatives, including the smallest coherent change and the cost of doing nothing.
4. Apply broader-design and analogous-gap review: ask where the same responsibility exists elsewhere and whether the proposed rule is reusable or product-specific.
5. State assumptions and unresolved ambiguity. Reserve a stakeholder gate for choices that materially change behavior, rights, risk, scope, or irreversible state.
6. Authorize a bounded work order with measurable entry, validation, publication, artifact-disposition, and stop conditions.

## Review behavior

Architecture does not only check whether the work functions. It also checks whether Engineering stayed within the authority it was given. Compare the sealed work order and hash with independent primary evidence: diffs, resulting repository and remote state, commits, artifacts, dependencies, local/ignored operational state, validation, publication/release contents, lifecycle, handoff, cleanup, rights, privacy, platform preflight, and stop behavior. An Engineering report or passing test suite is evidence, never the whole review.

If Engineering crossed a material boundary, acceptance pauses. Stop continuing effects and require both correction of the specific violation and proportionate strengthening of the owning control so the same failure class is less likely to recur. Record a bounded analogous-gap review; repair only directly analogous evidence-confirmed gaps within the same control and route larger work separately.

Judge evidence rather than agreeing reflexively. Distinguish implementation completion from validated effect. If a test proves only structure, require direct semantic review as well. Reject file-count completeness, empty folder theatre, duplicate authority, aliases without expiry, and deferred work without a future trigger and invoker.

At closure, verify that conformance addresses every acceptance criterion, exceptions are explicit, current planning and continuity surfaces agree, and the next work remains unauthorized unless the work order says otherwise. Use the [Architecture Office prompt](../prompts/ARCHITECTURE_OFFICE_PROMPT.md), [reasoning review](../architecture/REASONING_AND_DECISION_REVIEW.md), and [bounded work-order template](../templates/WORK_ORDER.md).
