<!-- SPDX-License-Identifier: Apache-2.0 -->

# Validation and Parallelism

Validation profiles are risk-based:

- focused development validates changed owning layers and direct consumers;
- final integration validates affected regressions, schemas, dependencies, documentation, packaging, and disposition;
- full live validation runs once for a release, major migration, or high-risk candidate fingerprint;
- committed-tree validation runs after commit in a Git-aware isolated worktree;
- export validation runs in a metadata-free standalone tree and never substitutes for committed-tree validation;
- post-publication checks verify only identity, cleanliness, remote alignment, and evidence binding.

The fingerprint includes base commit, complete candidate tree, changed-path digest, runtime/tool versions, material optional dependencies, schemas, and profile identity. Changed paths optimize selection but cannot define the final candidate.

Before sharding, inventory every required group exactly once. Workers receive
isolated writable state and deterministic commands. During parallel or shared
mutation, every shared artifact lane has one active writer at a time and one
integration owner; trivial serial work may use its primary owner implicitly.
Reassign a lane only at a checkpoint after the prior writer is quiescent and
partial state is handed off. Reviewers and other workers are read-only on that
lane and return nonoverlapping findings or candidate outputs. The integration
owner records counts, skips, omissions, duplicates, failures, retries, and
logs, then centrally reconciles one authoritative result.

When implementation code claims concurrency safety through locks, leases,
ownership tokens, conditional takeover, worker tracking, or coordinated
restart, validation must execute competing actors and adverse timing against
the actual control. Select interleavings proportionally from the control's real
failure axes, such as simultaneous acquisition, token replacement between
observation and mutation, stale-owner finalization, process-identity reuse, or
delayed child appearance. Structural inspection, required-string assertions,
and happy-path tests may supplement that evidence but cannot substantiate
race-safety. This requirement applies only where an actual concurrency control
exists; ordinary serial logic does not acquire a synthetic race-test burden.

Hypothesis experiments and three-arbiter decisions follow
[Reasoning and Decision Review](../architecture/REASONING_AND_DECISION_REVIEW.md).
Keep blinded executors, blinded result reviewers, and arbiters isolated until
their judgments are locked. Give every party the protocol, primary evidence,
authority, safety constraints, and neutral question needed to work, but
withhold sponsor preference, expected answer, hypothesis or implementation
identity when it can bias the role, and every other party's conclusions.
Shared writable state, message leakage, or premature unblinding invalidates the
affected result.

Prefer delegating long-running execution and monitoring to a dedicated sub-agent so the primary agent can continue independent tasks within the current work item. The primary agent retains integration ownership and must not manufacture parallel work: when every remaining task is blocked on the long-running result, monitor or await that result instead. Delegation must preserve the original authority, safety, privacy, writable-boundary, evidence, and cleanup requirements.

## Delegated progress visibility

Delegation never transfers user-communication accountability. Before launch, the primary agent states the delegated task, scope, owner, expected next milestone, heartbeat interval, and terminal conditions. It then:

- keeps the active workflow open or uses a product-supported persistent watcher that can surface updates automatically;
- does not send a final response that would make an active worker's progress or completion invisible, unless the user explicitly requests background execution or the platform guarantees automatic resume and notification;
- polls at the platform-required cadence or, when none exists, at least every five minutes;
- reports launch, material milestones or scope changes, abnormal resource behavior, intervention, completion, failure, and cancellation; unchanged heartbeats stay compact;
- reports a terminal event at the next available message boundary and no later than one heartbeat interval, without waiting for the user to ask;
- drains worker messages and checks live worker state before every status or final response; and
- if monitoring or notification fails, immediately reconstructs state, reports the visibility gap, and resumes from verified evidence.

Never report only that a task or worker is "stalled." Name the exact run/unit, its intended work, last successful stage and timestamp, expected signal that is absent or unchanged, observed parent/child process health and resource activity, downstream work blocked by it, configured automatic recovery behavior and deadline, and whether bounded intervention is required or merely optional.

When the execution environment permits it, long-running delegated workers expose a bounded two-way status channel. A supervisor probes the exact owned run before declaring a stall; the worker answers with its stage, current operation, last completed unit, active child, blocker, and next expected update. A missing response within the probe deadline, an explicit blocker, or repeated responsive probes without productive evidence distinguishes a genuine stall from merely slow work. Proven stalls are diagnosed, terminated at the narrowest verified ownership boundary, checked for process-tree quiescence, and retried without waiting for an unrelated global timeout. The global timeout remains a hard ceiling for responsive long work. Status and probe messages are diagnostic and never substitute for durable result validation.

The primary agent remains responsible for reconciliation, evidence, cleanup, and truthful status even when a sub-agent executes and monitors the task.

Consequential delegated execution must not be opaque. Initialization binds the
authoritative repository/workspace identity, prohibited stale locations, exact
lease or task identity, writable boundary, tool/runtime paths, expected
checkpoints, and terminal result contract; the orchestrator verifies those
bindings before accepting output. For a shared consequential workflow, exactly
one orchestrator owns allocation, retries, recovery, cleanup, quiescence,
deduplication, publication, and authoritative cursor/state advancement.
Parallel workers are pure bounded executors: they consume immutable leases,
write owner-scoped immutable checkpoints and candidate outputs, return one
structured terminal result, and exit. They never allocate follow-on work,
relaunch/reset a failed operation, mutate shared cursors or canonical products,
clean another lane, terminate peers, or improvise recovery strategy.

Partial failure does not require discarding valid work or granting workers
shared-state authority. The orchestrator validates the maximal contiguous
checkpoint prefix, retains later valid ranges behind gaps, rejects the invalid
or incomplete tail, deduplicates exact identities, records retry lineage, and
issues only the residual immutable lease after quiescence. A salvageable
checkpoint contains or immutably references the complete recoverable unit
payload and binds its deterministic content hash; a hash-only receipt cannot
justify skipping reprocessing or advancing authority. Canonical
publication and cursor advancement occur atomically and only across a fully
validated contiguous prefix; opaque status, heartbeats, and noncontiguous
completion never advance authority.

Long-running recovery is inactivity-based, not an opaque wall-clock kill.
Only validated item/chunk completion, an advancing governed byte/item counter,
an approved reasoned external-wait transition, or a verified owned-child
CPU/I/O delta resets inactivity. Stdout/stderr churn does not. A proportionate
default probes suspected idleness near two minutes and terminates near five
minutes; a recorded operation-specific external wait may extend to ten minutes
without becoming productivity. At the deadline the orchestrator freezes and
adopts the valid prefix, terminates at the exact containment boundary, proves
quiescence, and issues the residual lease. Actively productive work has no
ordinary wall-clock kill. Any emergency ceiling is a last-resort invariant,
not normal recovery or a substitute for meaningful-activity telemetry.

Every numeric progress report defines and preserves the identity of its counted
unit, denominator population, and completion predicate. The integration owner
reconciles completed identities against the frozen population; secondary evidence,
provenance rows, retries, routed/split extras, and multiple records for one assigned
identity do not advance completion unless the work order explicitly defines them as
the unit. If the artifact tracks both assigned outcomes and supporting entries,
report both counters separately and validate uniqueness, coverage, and cursor
arithmetic before publishing the percentage or fraction. A proxy row count must
never be presented as outcome completion. Tests for a living progress ledger derive
mutable counts, latest-wave identities, and current revisions from the same
authoritative evidence graph as the ledger; hard-coded expectations are reserved
for stable contract invariants, not yesterday's checkpoint.

All orchestrated writable state uses the canonical temporary-workspace resolver. Every shard receives a unique owner-scoped run directory below an approved operating-system temporary root; repository, author, project, instance, and repository-sibling workspaces are prohibited. A shard cleans only its own directory in guaranteed finalization, and the integration owner verifies no run directory, worktree registration, child process, cache, or raw log remains.
