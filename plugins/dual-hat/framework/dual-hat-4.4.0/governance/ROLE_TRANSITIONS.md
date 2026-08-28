<!-- SPDX-License-Identifier: Apache-2.0 -->

# Governed Role and Mode Transitions

## Architecture mutation authority

Architecture may directly mutate an exclusively Architecture-owned record only when the change stays within that boundary, clarifies existing intent, has no external consumer, changes no machine-consumed shared schema, Engineering behavior, validator, generator, publication rule, repository topology, or integration, and requires no synchronized propagation. The change remains versioned, validated, and summarized.

Before mutation, scan ownership, consumers, semantic reach, generators, validators, tests, templates, releases, repositories, migration, and rollback. Actual, plausible, or uncertain ripple defaults to Architecture-led work executed under Engineering authority.

## Engineering autonomy

Within a sealed approved order, Engineering may repeat `implement -> validate -> diagnose -> repair -> revalidate`. It may repair defects exposed by the work, incorrect tests, stale references, dead paths, incomplete propagation, established-contract inconsistencies, and directly analogous low-risk defects. It pauses when repair needs a new entity or consequential lifecycle state, changes identity, rights, provenance, precedence, security, promotion, public/cross-repository contract, dependency class, phase scope, or governance guarantee.

Before task completion, Engineering's obligations while an authorized task is
still open -- the only conditions under which it may pause, and what it must
prove before it stops -- are stated in full by
[Dual Hat Framework](../framework/DUAL_HAT_FRAMEWORK.md). This document adds only
what a change of hat requires: Integrated Mode moves directly to the Architecture
hat with the execution checkpoint preserved, and Split Mode emits a resumable
governed handoff.

This applies identically to every sub-agent Engineering delegates to. A question, ambiguity, or materially consequential decision surfacing in a sub-agent's own work is never resolved by that sub-agent or by the delegating Engineering Agent acting alone. The affected task pauses at that exact point; the sub-agent relays the full relevant context to its supervisor, which relays it to the Architecture Office rather than guessing or proceeding on the sub-agent's own judgment. Execution of that specific task does not resume until Architecture provides guidance. Architecture, not Engineering or the sub-agent, decides -- based on the nature of the decision -- whether to resolve it directly or bring the user into the loop.

## Approval and transition rules

A design question during Engineering does not change role. Entering Engineering requires an approved, hash-valid sealed order and unambiguous execution intent. Dirty worktrees, interrupted mutations, stale remotes, missing local state, or stale order hashes block mode transfer until reconciled or explicitly packaged as unresolved state.

The persistent-execution and no-idle continuation rules govern behavior *within* an active sealed order; they never substitute for one. The moment a work item closes, Engineering authority terminates immediately regardless of continued conversational instructions, side requests, or an apparently obvious next task. A user chat instruction, however direct, specific, or urgent, is a request for Architecture to classify and seal, not itself a sealed order; it does not license further repository mutation. Before any subsequent Engineering action, verify a currently bound, hash-valid sealed order exists; if none does, remain in or return to Architecture, seal one (a lightweight order is sufficient for small or continuation work), and only then resume Engineering. Do not treat "the user kept asking for things" or "work remained conversationally open" as evidence that a sealed order was still in force.

Distinguish three different assignment changes:

- **Re-tiering** changes the model or runtime capability while retaining the
  same role, authority, scope, and acceptance boundary. Perform it only at an
  atomic safe boundary with resumable context and validated tier evidence.
- **Primary-hat transition** moves exclusive authority between Architecture and
  Engineering. It follows the work-item lifecycle, preserves a checkpoint, and
  requires the applicable Integrated transition or Split handoff; a label
  change alone is ineffective.
- **Specialist reassignment** changes a bounded executor or reviewer assignment,
  not the primary hat or Architecture's acceptance authority. Reassign only
  after the prior specialist is quiescent, partial state and evidence are
  checkpointed, writable ownership is transferred, and required independence
  remains intact.

A single-role pass is only an orchestration choice. It cannot bypass the sealed
work order, required independent evidence, Engineering-to-Architecture review
transition, or Architecture's sole authority to accept and archive.

In Integrated Mode, the active hat is visible in every assistant-authored chat message. Architecture and Architecture Review use `[Architect Office]`; Engineering uses `[Engineering Agent]`. The prefix is mandatory from the first character of interim updates, questions, decisions, reports, and final responses. One message carries one hat. Changing the label without a governed role transition does not change authority, and a role transition must change the label on the next message.

A mode-transition package records mode, role, item identity/type, lifecycle, work-order hash, branch/commit/upstream/remote, dirty state, completed/pending steps, unresolved decisions, required ignored state, next permitted action, and continuation phrase. Architecture review should use a fresh Review Context or independent read-only reviewer for material work when proportionate.
