<!-- SPDX-License-Identifier: Apache-2.0 -->

# Session and Handover Protocol

Every current session records operating mode, active role, work-item identity/type, lifecycle state, approved order hash, selected platform profile when one exists, current project-local model-tier mapping identity and environment fingerprint, and safe next transition. A fingerprint change marks the mapping stale and requires safe-boundary remapping before tier-dependent work resumes. Split transfers and Integrated safe-boundary mode changes use `schemas/mode-transition-package.schema.json`; context memory is never the transfer contract. The machine contract uses `active_work_item`, independently from `latest_completed_capability`; it may hold any governed registered type or `null`. Historical Capability-only records remain readable, but current generators must not overload them.

Exactly one current active-session record and one current human/machine handover pair exist per governed repository. They are generated from repository truth and replaced on update; historical copies are retained only when policy requires them.

The active-session record is maintained throughout execution, not only at closure or switchover. Update it whenever a material goal, work item, lifecycle/role, authorization, repository/publication state, execution policy, gate, risk, or next action changes. A handover must never compensate for a stale active-session source by silently overriding it.

The current Markdown handover is the sole new-chat bootstrap input. Do not create a separate continuation prompt, compatibility copy, or generated alias with overlapping authority. Other resume or interrupted-operation artifacts may exist only when they have a distinct bounded purpose and link back to the current pair.

The session records repository/product identity, current branch and commit, latest completed and active capability, phase/release state, authorization, protected assets, handover/snapshot freshness, unresolved decisions, waiting workflows, validation state, interruption recovery, and next allowed work.

The handover pair records starting, implementation, corrected implementation, detached-validation, closure-evidence, generation-input, final published, and upstream commits without conflating roles. It also records worktree, external repositories, current snapshot, boundaries, risks, decisions, and stale/superseded handovers.

Markdown and JSON must be semantically equal, schema-valid, current-path-valid, and generated from declared inputs. Update after capability closure, remediation, publication correction, phase/release change, branch/authority change, or protected-state change. Validation detects a stale fingerprint, contradictory pair, multiple active pairs, and hidden reliance on previous chat memory.

After interruption, verify live Git and external state, inspect owned child processes, recover only from committed or explicitly registered temporary state, and refresh bounded context before continuing. Session cleanup removes stale execution residue and marks abandoned work honestly.

Refreshing bounded context after any interruption that can lose conversation memory -- context compaction chief among them -- requires reading the current active-session record's own state sections in full, not relying on a prior summary of it or on a partial earlier read. A context-loss summary is lossy by construction and must never be trusted as a substitute for the active-session record it was generated alongside; the record, not the summary, is authoritative. Before treating any tracked item's own status or lifecycle field as current, cross-check it against the actual repository history for a matching completion commit -- a status field can lag genuinely completed work, and lagging status is not itself evidence that the work remains undone.

## Chat switchover

The exact trigger phrase `Ready to switch chats.` requests a governed chat switchover. Continue to the nearest safe, low-ambiguity boundary without pausing healthy background work merely to prepare the handoff. At that boundary, classify and reconcile every in-flight task, delegated agent, owned process, mutation, and review. Take a fresh authoritative snapshot at the actual handoff time; never construct the handoff from stale or assumed state.

First verify and, when needed, refresh the active-session record. Then regenerate and validate the compact current-project handoff artifact under the repository's declared handoff authority and provide a minimal copyable bootstrap instruction that directs the new chat to read, verify, and follow that artifact. The artifact—not the bootstrap instruction—contains:

- the full active goal and exact current counters or state;
- authoritative repository paths;
- relevant commits, branch/upstream state, and worktree ownership, including unrelated or concurrent mutations that must be preserved;
- healthy background execution and its ownership, identity, continuation state, and stop conditions;
- pending gates, reviews, decisions, risks, and the exact next actions; and
- standing interaction, authority, publication, and protected-state rules needed to continue safely.

Explicitly tell the user when it is safe to switch. If a clean boundary cannot be reached promptly, identify the live item preventing it and provide the safest available handoff with the ambiguity, preservation rule, and next verification action made explicit. A switchover request is not authority to cancel work, terminate processes, alter publication state, or broaden scope.

The switchover gate fails closed when the active-session source is stale, the handoff input fingerprint is stale, required live-execution or review continuity is missing, Markdown and machine companion disagree, or another artifact claims overlapping new-chat authority.
