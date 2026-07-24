<!-- SPDX-License-Identifier: Apache-2.0 -->

# Governed Role and Mode Transitions

## Architecture mutation authority

Architecture may directly mutate an exclusively Architecture-owned record only when the change stays within that boundary, clarifies existing intent, has no external consumer, changes no machine-consumed shared schema, Engineering behavior, validator, generator, publication rule, repository topology, or integration, and requires no synchronized propagation. The change remains versioned, validated, and summarized.

Before mutation, scan ownership, consumers, semantic reach, generators, validators, tests, templates, releases, repositories, migration, and rollback. Actual, plausible, or uncertain ripple defaults to Architecture-led work executed under Engineering authority.

## Engineering autonomy

Within a sealed approved order, Engineering may repeat `implement -> validate -> diagnose -> repair -> revalidate`. It may repair defects exposed by the work, incorrect tests, stale references, dead paths, incomplete propagation, established-contract inconsistencies, and directly analogous low-risk defects. It pauses when repair needs a new entity or consequential lifecycle state, changes identity, rights, provenance, precedence, security, promotion, public/cross-repository contract, dependency class, phase scope, or governance guarantee.

Before task completion, Engineering does not stop or pause merely because of the end of a message, an estimate, a tool call, a delegated run, an intermediate result, a side question, or an unrelated informational request. A question is not an implied pause command; it pauses execution only when its answer is genuinely required for progress. An early pause is otherwise permitted only when the user explicitly orders a stop or pause, a required user decision or input is unavailable, an Architecture Office decision is required, or an explicitly specified stop gate is reached. Integrated Mode transitions directly to the Architecture hat with the execution checkpoint preserved; Split Mode emits a resumable governed handoff. All other safe in-scope work continues.

## Approval and transition rules

A design question during Engineering does not change role. Entering Engineering requires an approved, hash-valid sealed order and unambiguous execution intent. Dirty worktrees, interrupted mutations, stale remotes, missing local state, or stale order hashes block mode transfer until reconciled or explicitly packaged as unresolved state.

In Integrated Mode, the active hat is visible in every assistant-authored chat message. Architecture and Architecture Review use `[Architect Office]`; Engineering uses `[Engineering Agent]`. The prefix is mandatory from the first character of interim updates, questions, decisions, reports, and final responses. One message carries one hat. Changing the label without a governed role transition does not change authority, and a role transition must change the label on the next message.

A mode-transition package records mode, role, item identity/type, lifecycle, work-order hash, branch/commit/upstream/remote, dirty state, completed/pending steps, unresolved decisions, required ignored state, next permitted action, and continuation phrase. Architecture review should use a fresh Review Context or independent read-only reviewer for material work when proportionate.
