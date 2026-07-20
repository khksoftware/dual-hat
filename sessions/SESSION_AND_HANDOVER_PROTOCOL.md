<!-- SPDX-License-Identifier: Apache-2.0 -->

# Session and Handover Protocol

Every current session records operating mode, active role, work-item identity/type, lifecycle state, approved order hash, selected platform profile when one exists, and safe next transition. Split transfers and Integrated safe-boundary mode changes use `schemas/mode-transition-package.schema.json`; context memory is never the transfer contract.

Exactly one current active-session record and one current human/machine handover pair exist per governed repository. They are generated from repository truth and replaced on update; historical copies are retained only when policy requires them.

The current Markdown handover is the sole new-chat bootstrap input. Do not create a separate continuation prompt, compatibility copy, or generated alias with overlapping authority. Other resume or interrupted-operation artifacts may exist only when they have a distinct bounded purpose and link back to the current pair.

The session records repository/product identity, current branch and commit, latest completed and active capability, phase/release state, authorization, protected assets, handover/snapshot freshness, unresolved decisions, waiting workflows, validation state, interruption recovery, and next allowed work.

The handover pair records starting, implementation, corrected implementation, detached-validation, closure-evidence, generation-input, final published, and upstream commits without conflating roles. It also records worktree, external repositories, current snapshot, boundaries, risks, decisions, and stale/superseded handovers.

Markdown and JSON must be semantically equal, schema-valid, current-path-valid, and generated from declared inputs. Update after capability closure, remediation, publication correction, phase/release change, branch/authority change, or protected-state change. Validation detects a stale fingerprint, contradictory pair, multiple active pairs, and hidden reliance on previous chat memory.

After interruption, verify live Git and external state, inspect owned child processes, recover only from committed or explicitly registered temporary state, and refresh bounded context before continuing. Session cleanup removes stale execution residue and marks abandoned work honestly.
