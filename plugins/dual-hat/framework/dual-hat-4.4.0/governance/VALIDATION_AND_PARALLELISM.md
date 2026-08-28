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

Whenever the runtime supports it, keep the primary agent on standby to orchestrate and remain immediately available for user interaction, rather than itself performing the bulk of hands-on work-item execution. For any capability or governance work item, regardless of how many streams it is divided into, delegate execution to sub-agents by default; reserve direct primary-agent action for orchestration itself, genuine immediate user interaction, and small already-in-flight actions where stopping mid-step to delegate would cost more than finishing them. New work or investigation surfaced by a user interaction during active execution is also delegated to a (new or resumed) sub-agent, provided it is reasonably believed not to interfere with other active streams; only fold it into direct primary-agent action when delegating would itself risk that interference. The primary agent retains integration ownership and must not manufacture parallel work: when every remaining task is blocked on a delegated result, monitor or await that result instead. Delegation must preserve the original authority, safety, privacy, writable-boundary, evidence, and cleanup requirements.

Unless a sealed work order explicitly assigns a sub-agent a different role, every delegated sub-agent operates under the Engineering Agent role and is bound by every rule that governs it -- authority boundary, sealed-order entry, stop gates, evidence, validation, and reporting. Delegation does not grant a sub-agent Architecture's acceptance or archival authority merely by virtue of being spawned to help. Every message a sub-agent produces begins with a brief description of its assigned role or task, mirroring the primary agent's own role-label convention, so a reader can identify which delegated stream produced any given output without cross-referencing launch records. The delegating agent acts as orchestrator and supervisor: it stays on standby rather than performing hands-on execution itself, tracks each sub-agent's progress, and treats a sub-agent's self-reported results and findings as unverified claims -- never as settled fact -- until independently checked against live repository evidence, the same evidentiary skepticism Architecture applies when reviewing Engineering's own reports. It remains immediately available to respond to the user without delay throughout. See [Governing Principles](GOVERNING_PRINCIPLES.md) principle 11 for how a governance change codified mid-session applies to already-active and subsequently launched sub-agents.

When delegation declares an isolation, scope, or authority boundary -- a separate worktree, a restricted path set, a read-only mode -- the orchestrator confirms that boundary actually took mechanical effect (e.g., the worktree genuinely exists as a separate checkout) before trusting work performed under it; a requested boundary that silently did not hold is a delegation failure requiring reconciliation, not evidence the work is safely isolated. Every delegated report additionally states what it assumed or did not independently verify, alongside what it confirmed -- an orchestrator cannot catch a gap a worker itself never surfaced as uncertain. See [Governing Principles](GOVERNING_PRINCIPLES.md) principles 2, 6 and 5 for the companion requirements that a governed repeated workflow have exactly one canonical implementation, that a resumed or post-compaction worker re-derive its method from source rather than its own summary, and that completeness claims cite their concrete verification mechanism.

## Delegated progress visibility

Delegation never transfers user-communication accountability. Before launch, the primary agent states the delegated task, scope, owner, expected next milestone, heartbeat interval, and terminal conditions. It then:

- keeps the active workflow open or uses a product-supported persistent watcher that can surface updates automatically;
- does not send a final response that would make an active worker's progress or completion invisible, unless the user explicitly requests background execution or the platform guarantees automatic resume and notification;
- polls at the platform-required cadence or, when none exists, at least every five minutes;
- reports launch, material milestones or scope changes, abnormal resource behavior, intervention, completion, failure, and cancellation; unchanged heartbeats stay compact;
- reports a terminal event at the next available message boundary and no later than one heartbeat interval, without waiting for the user to ask;
- drains worker messages and checks live worker state before every status or final response; and
- if monitoring or notification fails, immediately reconstructs state, reports the visibility gap, and resumes from verified evidence.

A delegated worker that returns because it completed a bounded checkpoint or partial scope, rather than because it hit a genuine stop condition, requires an explicit resume decision recorded at that moment: either reactivate it (or launch its successor) toward the full assigned outcome, or state plainly why not. Pursuing a newly surfaced finding, side investigation, or user tangent instead, without recording that decision, is exactly how a completed-but-unresumed worker sits silently idle while it is believed to still be running — the gap surfaces only when someone asks for a status update much later.

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

## Quiescence

Quiescence is a property of a named boundary at a named instant: nothing inside
that boundary can still write to the resource whose authority is about to move.
Lane reassignment, termination at a containment boundary, residual-lease
issuance, and the single orchestrator's ownership of quiescence above each
require it as a precondition, as does specialist reassignment in
[Role Transitions](ROLE_TRANSITIONS.md); the same lane obligation is restated
for the roles that carry it in the Engineering Agent Guide and in both role
prompts. It is stated here once so those uses do not each acquire their own
reading.

Name the boundary before asserting quiescence, and assert it of everything
inside. A stopped root does not make a live descendant quiescent, and a lane
whose named writer stopped is not quiescent while an unnamed one retains write
access. Where the inside of a boundary cannot be enumerated, that boundary is
the wrong one: widen it until it can be, or the claim is unavailable.

Quiescence is a claim about capability, not about observed inactivity. An idle
actor can resume, so an idleness reading is evidence of idleness and never of
quiescence. The inactivity regime above decides when to suspect a stall and when
to terminate; quiescence is what must then be established about the boundary
that was terminated. Silence, an unanswered probe, an empty output stream, and
an elapsed threshold are each consistent with an actor about to write.

The party that needs quiescence proves it, and these do not discharge that
proof: an actor's own report that it stopped, a completion or termination
notification, a removed registration, a released lock, or the absence of recent
output. Each is authored or mediated by the actor whose stopping is in question,
or records an intention rather than a state. Proof is a direct reading of the
resource, or of the platform's own authoritative record, showing that no writer
inside the boundary retains write access.

Quiescence is perishable and is paired with a bar on re-entry. Established at
one instant it says nothing about the next unless something prevents the
boundary being re-entered, so authority moves in the same guarded step that
proves it -- withdraw the prior writer's access, or bind the successor's lease
to a state the prior writer can no longer advance -- and a proof taken earlier
and acted on later is retaken.

Where the boundary's writers are governed roles rather than platform-controlled
processes, a third proof is admitted, and it is the checkpoint-and-handoff step
the reassignment obligations already require rather than a relaxation of them:
quiescence is proved by a checkpoint the retiring role wrote, a second party
validated, and that party adopted. Four conditions, all of them necessary:

- Every writer inside the boundary is a governed role. A process, shard or
  descendant that can write the resource independently of one is proved as
  above, or the boundary is the wrong one.
- The platform exposes neither admitted reading for this boundary. Where a
  direct reading of the resource or of the platform's authoritative record is
  available it governs, and this proof is unavailable rather than alternative:
  a last resort, never a cheaper route to the same claim.
- The checkpoint is durable and salvageable in the sense above -- it names the
  boundary and the stopping point, and contains or immutably references the
  complete recoverable partial state. A statement that work stopped is not a
  checkpoint.
- The party that needs quiescence, never the retiring role, validates that
  checkpoint against primary evidence, rejects an invalid or incomplete tail,
  and records its adoption of what survives. The retiring role's assignment and
  writable ownership are withdrawn in the same guarded step, and the
  successor's authority binds to the adopted point.

This admits none of the discharges excluded above, because each of those
arrives without the retiring party having produced anything a second party
could check: a report, a notification, a removed registration, a released lock
and a silence are readings taken of the actor, not artifacts validated against
the work. A role that stops without a checkpoint produces none of what this
proof requires, so the case those exclusions exist for is unchanged and still
blocks. The validation is what makes this a proof, not the fact that the writer
is a role -- remove the second party and it collapses into the actor's own say
so, which is why adoption is a condition and not a description of practice.

State the residual rather than arguing it away: this proves that nothing was
written beyond the adopted point, not that the retiring role has lost the
capability to write. A governed role writing after its writable ownership is
withdrawn is a governance failure, visible in the resource's own history, and
the lane is then reconciled from the adoption record. It is the one place in
this definition where capability is established by obligation rather than read,
and it is admitted only where the platform offers nothing to read.

Unprovable quiescence blocks; it does not pass. Where the boundary's contents
cannot be enumerated, or the platform exposes no reading distinguishing a
stopped actor from a slow one and no validated handoff above establishes the
claim either, reassignment, lease issuance, and retry do not happen and the
obstacle is reported. A wrong quiescent claim puts two writers on one resource,
which is the failure single-writer ownership exists to prevent; a
wrong not-quiescent claim costs a wait. A platform that cannot supply the
distinguishing reading declares that as a known limitation of the platform
rather than assuming the property.

Nothing enforces this definition. Its consumers are the lane-reassignment,
containment-boundary, residual-lease and single-orchestrator obligations above
and the specialist-reassignment obligation in
[Role Transitions](ROLE_TRANSITIONS.md), which name quiescence as a
precondition and cannot be armed against a term meaning whatever its reader
assumes; the failure it prevents is a second writer admitted to a resource whose
first writer was inferred to have stopped; its cost is one paragraph of reading
and, where the distinguishing reading is unavailable, a validated handoff or --
where the writers are not governed roles -- a blocked reassignment that
previously proceeded on assumption. It is invalidated by a platform whose
authoritative record makes write capability inside a boundary directly readable,
and it retires into that platform's own check when one exists and is armed.
