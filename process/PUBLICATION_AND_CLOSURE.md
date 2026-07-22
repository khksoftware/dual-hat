<!-- SPDX-License-Identifier: Apache-2.0 -->

# Publication and Closure

Engineering completion enters Architecture Review. Only an Architecture-owned `accepted` or non-blocking `accepted_with_follow_up` disposition authorizes deterministic archival; remediation remains active. Engineering may recommend but cannot self-accept or archive.

Branch and push behavior comes from the active work order and product profile. Use forward-only correction: do not rewrite published history, force-push, or overwrite unexplained external work. Before publication, verify branch, remotes, history, cleanliness, prior governed marker, target drift, credentials, and authorization.

When a profile uses short-lived work branches, closure integrates the accepted work into its authorized target and retires or repurposes the completed branch before unrelated work continues. Retaining a completed branch requires an explicit owner, purpose, and retirement trigger. A new work item does not silently continue on the prior item's branch.

Publication compares the candidate with the prior owned file set, reports adds/changes/removals/renames, applies only governed changes, commits transparently, pushes when authorized, fetches, and verifies HEAD/upstream alignment plus a clean worktree. A failed push leaves the local commit intact and is reported as blocked, never as success.

Closure inventory covers every created, modified, moved, split, generated, exported, archived, deleted, and temporary artifact. Reproducible staging, caches, worktrees, process logs, and export debris are removed. Rollback states which commit, migration reversal, external action, or restored marker is safe; recovery never assumes chat history.

Closure also reconciles the approved work order and conversation record for explicitly promised stakeholder-facing findings, comparisons, recommendations, reports, and decision summaries. A promised delivery is complete only when it has been proactively presented to the stakeholder, or explicitly reported as deferred or blocked; creating, committing, or archiving an artifact is not delivery. Use one compact exit-report checklist rather than a new ledger, and do not wait for the stakeholder to remember or request the promised result.
