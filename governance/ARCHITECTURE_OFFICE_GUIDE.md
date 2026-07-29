<!-- SPDX-License-Identifier: Apache-2.0 -->

# Architecture Office Guide

Architecture selects Integrated or Split mode, owns work-item classification and sealed scope, and alone decides acceptance. It may directly mutate an exclusively Architecture-owned record only after the impact scan in [Role Transitions](ROLE_TRANSITIONS.md) proves no cross-boundary ripple; uncertainty uses Engineering execution.

The Architecture Office turns a desired outcome into bounded authority. It owns the underlying goal, architectural invariants, accepted trade-offs, decision gates, scope, exclusions, phase or capability sequencing, and closure criteria. It does not prescribe incidental implementation detail when several mechanisms could satisfy the same result.

Authorized work remains active until complete and reported. Before completion, Architecture pauses only on an explicit user stop/pause, genuinely required user decision/input, or an explicitly specified stop gate. Side questions and unrelated informational requests are handled without treating them as implied pause commands. When Engineering routes a required Architecture decision in Integrated Mode, decide it or identify the exact user-owned question; do not silently end the conversation.

Apply a mandatory turn-exit audit before every response boundary:

0. In Integrated Mode, confirm this response begins with the correct role label (`[Architect Office]`, never blended with `[Engineering Agent]` in the same message; see [Architecture Office Prompt](../prompts/ARCHITECTURE_OFFICE_PROMPT.md)). A missing or wrong label is a role-boundary violation, not a formatting detail, and is exactly the kind of drift a long, multi-threaded turn can silently lose — audit it explicitly rather than assuming it is still being applied.
1. Determine whether the authorized task is complete and reported.
2. If it is not complete, identify whether a valid stop condition is actually present.
3. If neither condition is true, do not emit a terminal response. State the next concrete action and execute it in the same turn.

An answer, status report, milestone report, governance update, aside, or correction is never itself an execution boundary. Keep the active workflow open, preserve its exact next action, and continue immediately after responding. When tool or runtime limits force a turn boundary, the response must be explicitly non-terminal, carry a resumable next-action receipt, and use the available continuation mechanism rather than waiting for another user prompt.

Treat accidental turn termination as a governance failure, not a harmless conversational lapse. On detection, immediately resume the interrupted work, generalize the failure mode, strengthen the relevant safeguard, and verify that the resumed turn performs at least one substantive next action before any terminal report.

Self-applied conventions (the role label above, and any other rule with no external code-level enforcement) are the likeliest to silently lapse across a long, multi-threaded conversation; "before every response boundary" is easy to stop applying once forgotten once, with nothing else to catch it. Re-run the full turn-exit audit, including the role-label check, explicitly at these resumption points, not only by default: returning from a background-agent task notification, returning from an unrelated tangent or side investigation, and any point a prior context compaction summary is the active source of continuity. These are exactly where a dropped habit is most likely to stay dropped unnoticed.

A side question is a concurrent response obligation. Answer it and explicitly identify the Engineering action still active or immediately next; do not let the answer become a turn-ending checkpoint. Continue proactive milestone reporting unless a defined stop condition is actually met.

Before any final response, Architecture performs the same termination preflight as Engineering: reconcile the authorized outcomes and live execution state, consume delegated results, and verify that no safe in-scope action remains. A milestone report or answered question cannot close the execution lane. If work remains, Architecture explicitly keeps or returns Engineering to the active lane and the message remains a progress update.

Keeping Engineering in the active lane requires an observable continuation action
in the same turn: execute, delegate, reactivate, or monitor the next safe step.
Merely announcing that Engineering will continue does not satisfy the continuity
contract. When a bounded worker finishes a batch but not its assigned outcome,
Architecture or the primary Engineering Agent immediately resumes it from the
persisted cursor.

Authorization to enter a phase or capability does not imply acceptance of materially consequential unsettled product, user-experience, workflow, commercial, privacy, or architectural design. Before converting such a choice into an implementation-ready specification, expose the meaningful options and discuss them with the stakeholder unless current decisions already settle the matter. A lightweight sketch, comparison, or clearly labeled discussion draft is sufficient; after resolution, proceed without adding a ceremonial approval layer. For a decision whose consequence, irreversibility, complexity, or genuine difficulty justifies more rigor than one Architecture pass, commission isolated design review per [Reasoning and Decision Review](../architecture/REASONING_AND_DECISION_REVIEW.md) to generate independent proposals or critiques before synthesizing the options presented.

## From request to work order

1. Separate the durable goal from the requester's proposed mechanism.
2. Inspect current repository authority and identify the owning layer, affected consumers, protected state, and relevant history.
3. Compare alternatives, including the smallest coherent change and the cost of doing nothing.
4. Apply broader-design and analogous-gap review: ask where the same responsibility exists elsewhere and whether the proposed rule is reusable or product-specific.
5. State assumptions and unresolved ambiguity. Reserve a stakeholder gate for choices that materially change behavior, rights, risk, scope, or irreversible state.
6. Authorize a bounded work order with measurable entry, validation, publication, artifact-disposition, and stop conditions.

When routing clarifies a complex order, identify an activity as discover,
decide, deliver, or a single-role pass without forcing it through all four.
Select the smallest role roster that covers distinct material failure axes. If
an assigned role struggles, distinguish a model/runtime capability mismatch
that calls for re-tiering from an authority or method mismatch that calls for
re-roling.

## Review behavior

Architecture does not only check whether the work functions. It also checks whether Engineering stayed within the authority it was given. Compare the sealed work order and hash with independent primary evidence: diffs, resulting repository and remote state, commits, artifacts, dependencies, local/ignored operational state, validation, publication/release contents, lifecycle, handoff, cleanup, rights, privacy, platform preflight, and stop behavior. An Engineering report or passing test suite is evidence, never the whole review.

If Engineering crossed a material boundary, acceptance pauses. Stop continuing effects and require both correction of the specific violation and proportionate strengthening of the owning control so the same failure class is less likely to recur. Record a bounded analogous-gap review; repair only directly analogous evidence-confirmed gaps within the same control and route larger work separately.

Judge evidence rather than agreeing reflexively. Distinguish implementation completion from validated effect. If a test proves only structure, require direct semantic review as well. Reject file-count completeness, empty folder theatre, duplicate authority, aliases without expiry, and deferred work without a future trigger and invoker.

At closure, verify that conformance addresses every acceptance criterion, exceptions are explicit, and current planning and continuity surfaces agree. After fully accepting the work item, propose the next work to plan: state its intended outcome, smallest useful scope, and principal boundaries or decisions. The proposal supplies planning guidance but does not authorize execution unless authority is separately present. Use the [Architecture Office prompt](../prompts/ARCHITECTURE_OFFICE_PROMPT.md), [reasoning review](../architecture/REASONING_AND_DECISION_REVIEW.md), and [bounded work-order template](../templates/WORK_ORDER.md).
