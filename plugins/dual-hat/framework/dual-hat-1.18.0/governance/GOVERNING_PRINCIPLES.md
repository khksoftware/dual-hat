<!-- SPDX-License-Identifier: Apache-2.0 -->

# Governing Principles

Avoid over-bureaucratization. Dual Hat uses the lightest process that provides enough authority, safety, traceability, recovery, and confidence for the actual risk. A ceremony, artifact, gate, rerun, handoff, reconciliation, or check is justified only when it prevents or detects a material failure more effectively than a simpler control.

## Cardinal rules

1. Prefer one short authoritative record over multiple overlapping artifacts.
2. Reuse still-valid evidence. Do not rerun, rehash, regenerate, re-review, or repackage solely because unrelated or presentational state changed.
3. Combine adjacent checks and handoffs when their authority, inputs, timing, and audience are the same.
4. Escalate depth only for demonstrated risk, uncertainty, changed inputs, unexplained failure, or an explicit governing requirement.
5. Do not create a new protocol, schema, ledger, manifest, report, or approval surface when an existing record or a concise field is sufficient.
6. Keep explanations of omitted work proportionate; a one-line rationale is enough for an obvious focused choice.
7. Treat process wall time, repeated operator attention, and maintenance burden as engineering costs. When they become material, simplify the owning control instead of normalizing the overhead.
8. Preserve human decisions for material judgment, authority, consent, irreversibility, safety, rights, and meaningful loss risk. Do not require interaction merely to advance routine process state.
9. Schedule a lifecycle step at the latest safe point when performing it earlier would predictably require the same step to be repeated before its evidence can be used. Do not defer a step past the point where it protects a material decision or prevents costly rework.
10. When changed inputs genuinely require renewed validation, review, reconciliation, packaging, or repository checks, assess the delta and affected surface first. Rerun the whole process only when impact cannot be bounded reliably or a material risk or governing requirement demands it.
11. For every ad hoc fix, assess whether the failure class can recur across inputs, work items, environments, or consumers. When it can, prefer the smallest proportionate repair in the owning layer that prevents recurrence, while still correcting the current instance. Do not turn an isolated defect into a broad redesign without demonstrated recurrence risk.
12. When research, experimentation, tuning, or similar repeated work pursues one bounded objective under the same authority and acceptance contract, prefer explicit iterations within the same capability. Do not create a sequence of capabilities merely to number successive attempts. Open a new capability only when the objective, authority, product boundary, rollback unit, or acceptance contract materially changes.
13. Capability preflight evidence is content-addressed and invalidation-driven. Reuse a passing receipt when its evidence bytes, interpreter/tool identity, applicable profile rule, environment fingerprint, and governed consumer boundary remain valid. Rerun only receipts invalidated by a changed input or expired condition, and record reused versus refreshed evidence. Do not recompute an unchanged catalog merely to bind a new work-item identifier.
14. A stakeholder may grant standing authorization for a precisely bounded class of dependencies, models, tools, or equivalent candidates. Reuse that authority while every candidate satisfies its declared license, cost, reliability, safety, hardware, support, privacy, integrity, and scope conditions; re-escalate only when a condition is absent or exceeded. Preserve rejected-candidate evidence and remove rejected installed candidates promptly instead of retaining them until a replacement exists.
15. When a stakeholder or another agent identifies a real mistake, omission,
inaccuracy, or process failure, the responsible role must not stop at
acknowledgment or instance repair. A defect closes only after the concrete
behavior is fixed; the error mode and owning root cause are generalized; the
failed or missing prevention/detection defense and the reason it let the defect
escape are identified; that defense is repaired with proportional executable
regression evidence; directly analogous instances receive a bounded check; and
reusable guidance is codified at the narrowest appropriate authority. Where
practical, the new regression must be shown to fail against the defective
state. The countermeasure itself then receives independent adversarial review:
the reviewer attempts falsification, verifies the regression's defect
sensitivity, and checks new failure modes and disproportionate runtime or
maintenance cost. Review depth is proportional, but independence is mandatory.
Trivial slips may use a lightweight behavioral defense and review unless they
reveal a recurring or materially harmful class; do not create speculative
controls or unrelated scope. Behavior and its detection/prevention gap must
both be addressed before closure. See rule 19 when the failure to prevent or
detect this defect is itself evidence of a missing systemic mechanism rather
than a one-off gap.
16. Before asserting that a current product, platform, tool, subscription, or
runtime can or cannot support a proposed operation, verify the claim against
current authoritative documentation and, when locally testable, the installed
surface and its actual authentication or capability state. Distinguish an
unsupported capability from a supported capability that is merely unconfigured,
logged out, unavailable under the current entitlement, or blocked by the present
environment.
17. Persist a lesson only when it is reusable beyond the immediate correction or
materially improves a governing control. Prefer the existing owning authority,
finding, decision, debt, or planning record; do not require a per-run lesson
ledger. At an accumulated framework release or governed phase progression,
consolidate duplicates, resolve contradictions, review staleness and scope, and
promote a lesson across contexts only when evidence supports the broader claim.
Retire or narrow stale guidance instead of preserving it as folklore.
18. Once a design or plan is execution-ready and before mutation, perform a
proportionate optimization pass. Consider whether the same authorized outcome
can avoid brute force, deliver value earlier, improve dependency sequencing,
allocate parallelism or resources better, execute incrementally with useful
checkpoints, improve evidence reuse, or use a cheaper equivalent control. Apply
only improvements that preserve authority, acceptance, safety, and recovery.
Require a sealed independent Architecture optimization review only when scale,
complexity, risk, or irreversibility makes its distinct judgment worthwhile;
straightforward work needs no separate review ritual.
For ongoing long-running or materially resource-consuming execution,
reevaluate proportionately at meaningful checkpoints when duration, scale, or
observed change warrants it. Check changed bottlenecks, throughput, failures,
value yield, allocation, batching, cost, and wall time, and apply only bounded
improvements whose expected benefit exceeds disruption and revalidation cost.
Retest material assumptions or hypotheses embedded in the current design or
plan against current evidence and explicitly confirm, revise, or retire them;
an unchallenged assumption is not a supported one. Scale experimentation to the
assumption's consequence and uncertainty.
Do not pause healthy work merely to inspect it or turn periodic reevaluation
into ceremony.
19. When investigating a flagged defect, a stale artifact, or a "this was
supposed to be done but wasn't" gap, first determine whether the symptom in
front of you is actually one instance of a missing systemic mechanism rather
than a genuine one-off. A systemic mechanism gap takes one of three shapes: a
process step that was never documented as mandatory; a check that was never
made mechanical, so correctness depended only on an agent remembering to do it
(for example, a handover artifact that went stale because nothing mechanically
checked its freshness); or a pointer, cross-reference, or "current state"
marker that must track changing state but has no enforcement keeping it
synchronized as that state changes (for example, repeated closures that each
failed to update the same navigation pointer or archive the same superseded
document, because no documented step and no mechanical check ever required
it). Treat a run of superficially distinct misses that share one of these
shapes as evidence of one shared systemic cause, not as independent bad luck;
do not close the investigation after explaining away each occurrence
separately. When the root cause is systemic, the fix must repair the
mechanism itself — document the missing step, or add the missing mechanical
enforcement, so the defect class becomes structurally hard to ship — not
merely correct the instance in front of you; an instance-only fix leaves the
same defect free to recur at the next occasion the pattern applies. This
complements rule 15's correction-to-control loop: recognizing that a defect's
owning root cause is systemic, rather than local to the current instance, is a
precondition for generalizing that root cause correctly, not a substitute for
it.

20. When a foundational convention -- a path scheme, an identity or naming
model, a schema version, or any other shared contract multiple consumers
depend on -- changes, the change is not complete merely because its owning
module or record was updated and its own tests pass. Close both halves of
the gap before treating the change as done. First, prove with a mechanical
check, not manual review, that every consumer moved with the convention:
scan the repository's active surface for the superseded pattern and treat
any surviving match outside genuinely historical or explicitly exempted
content as a closure-blocking failure of the migration itself, not a
follow-up item. Second, add a standing mechanical check that catches any new
hardcoded reference to the superseded convention the moment it is
introduced, so a contributor who does not know the convention ever changed
cannot silently reintroduce it later. This is the standing defense for one
especially common shape of rule 19's systemic mechanism gap -- a pointer or
convention that must track changing state but has no enforcement keeping it
synchronized -- applied specifically to convention migrations: without both
halves, a migration can look complete while one or more secondary consumers
keep resolving the retired convention indefinitely, with nothing to signal
the drift until an unrelated investigation finds it by accident, months
later.

"Every consumer" in the preceding paragraph includes data a generator
already produced before it was fixed, not only code call-sites that
invoke the generator going forward. Fixing a generator's logic closes
the code half of the gap and does nothing to the artifacts it already
wrote to disk under the old, broken logic -- those artifacts keep
reflecting the defect indefinitely unless someone deliberately
regenerates or backfills them, and nothing about the code fix itself
does that automatically. Treat "does every already-produced artifact
reflect this fix" as its own required check, separate from and no less
mandatory than "does every code call-site use the fixed function" --
confirmed necessary by a real incident: a guidance-resolution defect
was root-caused and fixed at the code level, correctly verified against
new test data, while the 37 already-produced output artifacts that
motivated finding the bug in the first place kept showing zero results
from the newly-added registry for a full further session, because the
one task that would have applied the fix to them (a queued "backfill"
step) was repeatedly deferred in favor of newly-discovered adjacent
work and never actually finished. The code fix being correct is not
evidence the already-produced data reflects it; check the data
directly.

21. A governance change codified during an active chat session takes effect
immediately within that same session, not only for a future fresh session
that reads the updated files from scratch. The moment a rule is codified,
the primary agent applies it to its own remaining behavior from that point
onward, and to every subagent or delegated worker already active or
subsequently launched in that session -- by updating standing delegation
briefs, relaying the new rule to any subagent still running when practical,
and applying it to every newly launched subagent regardless of whether that
subagent itself ever reads the underlying framework files. Do not treat a
mid-session codification as advisory until the next onboarding; a rule that
binds only future sessions while the current one continues under the old
behavior defeats the purpose of codifying it the moment the gap was found.

22. Before authoring new procedural logic for a workflow this framework
already governs as a repeated, structured process -- evaluating a unit,
resolving applicable guidance, generating or validating a packet,
recording coverage, propagating a publication -- first determine whether a
canonical, committed entry point for that exact process already exists. If
one exists, use it; do not construct a parallel implementation, however
faithful, since a second implementation is a second place the same
invariant can silently diverge from the first. If none exists, escalate to
Architecture before building one rather than treating its absence as
license to improvise privately: a governed, consequential workflow gets
exactly one implementation, not as many as the agents who have touched it.
This is preventive; it does not replace rule 20's after-the-fact migration
closure, which still applies once a canonical entry point is introduced and
existing parallel implementations must be found and retired.

23. An agent whose own context has been compacted, who is resuming a
long-running task across a gap, or whose own run has simply continued
long enough that an early read of something could plausibly have
changed underneath it, re-derives its working method for any governed
mechanism or standing fact it is about to rely on from the actual
current source -- the real module, its docstring, its tests, the real
governance file -- rather than from its own prior summary or an early
read cached for the rest of the run. A summary or a stale early read
preserves what an agent believed at that moment, not what is actually
true now, and a defect introduced or already present before that point
survives unexamined every time the old belief is trusted instead of a
fresh check against the source. This is not limited to compaction: a
single long-running task with no compaction event can just as easily
read a foundational fact once near its start and never revisit it for
the rest of a run spanning hours and hundreds of tool calls, then report
a "verified" conclusion at the end that is actually a stale memory
misdescribed as a fresh check -- the same failure shape, a different
trigger. Re-verification is due once per resumed session or once per
sufficiently long uninterrupted run at first (or first renewed) use of
the mechanism or fact, not on every subsequent call within that same
window; a report that asserts something was "verified" or "confirmed"
states what was actually re-checked and when, not merely that the agent
believes it to be so. This applies equally to the liveness of a
delegated worker, not only to facts and mechanisms: an agent resuming
from a context-compaction summary re-verifies, immediately and before
any other action, whether every worker it believed active is still
tracked and reachable, rather than carrying forward a pre-compaction
belief that delegated work is still running unexamined until something
else forces the check. Where a worker's tracking handle no longer
resolves, the agent immediately falls back to direct evidence-based
verification of that worker's actual product -- the real files,
commits, or other output it was assigned to produce -- rather than
waiting for a user question to force it.

24. A checkpoint report for a governed, repeated process states, for any
completeness or coverage claim it makes (e.g., "N of M applicable items
evaluated"), the concrete mechanism used to determine the denominator --
the exact function or canonical script consulted, not a description of
the intended behavior. A number without its source is not verifiable by
whoever reads the report, and the framework's supervision model depends on
completeness claims being checkable at the point they are made, not only
after an unrelated investigation happens to test them.

25. Finding one instance of a defect is itself the trigger to actively
search for sibling instances before considering the fix complete -- not
merely to notice a pattern if further instances later surface on their
own. Rule 19 governs recognizing that a defect already in front of you is
systemic rather than one-off; this rule governs what happens next; once
that root cause is identified, search for other instances sharing it.
Two distinct kinds of search satisfy this, and finding one does not
excuse skipping the other. The literal kind -- a repository-wide search
for the relevant name, pattern, or call shape -- catches copies of the
same concrete bug and is usually cheap. The abstract kind requires first
naming the defect's structural pattern independent of its original
surface form (e.g. not "this specific file has a stale date," but "a
document that claims current state with nothing keeping it
synchronized as the underlying reality changes"), then searching for
anything else matching that pattern however differently it is expressed
-- different file formats, naming conventions, or subsystems that share
the same abstract shape without sharing any literal string. The abstract
search is the one that gets shortchanged by default, because it is
harder to scope and easy to satisfice by checking only the one or two
other instances already known about; treat it as requiring the same
rigor as the literal search, not as an afterthought bullet folded into
the fix task. Conduct the abstract search as its own pass with its own
reported result (what pattern was searched for, what was checked, what
was found or ruled out), not merely as a sub-step whose thoroughness
depends on how much attention the surrounding task happened to give it.
Prefer a systemic, generic countermeasure that makes the defect class
structurally impossible (a mandatory function with no partial-input call
shape, an enforced schema constraint, a validator wired into the write
path) over a collection of narrow, pinpointed patches applied instance by
instance as each is separately discovered -- the pinpointed-patch pattern
is itself how a systemic gap keeps looking fixed while continuing to
recur elsewhere. State the adjacent-area search performed and its result
(found N more instances and fixed them, or searched and found none) as
part of the fix's own report, not as an unstated assumption a reader must
take on faith.

26. Addressing a defect follows red-green-refactor, not a fix first and
test after: Red -- first write an automated test that reproduces the
defect and confirm it genuinely fails because of the defect, not by
construction error, a wrong fixture, or an unrelated failure. Green --
implement the fix, generalized per rule 19 and searched for siblings per
rule 25 rather than patched only for the originally reported case, and
confirm the red test now passes. Refactor -- with the suite green,
clean up the fix and its tests into the systemic, generic form rules 19
and 25 call for (removing duplication, replacing a narrow patch with the
proper structural countermeasure) without changing verified behavior,
then re-confirm the suite is still green afterward. Coverage added in
Refactor targets the systemic countermeasure itself -- the mandatory
function, enforced constraint, or validator that makes the whole defect
class structurally impossible -- not a separate narrow test per instance
the defect happened to be found in. A test suite that accumulates one
test per discovered occurrence is testing in patchwork, the exact
anti-pattern rule 25 already rejects for the fix itself; prefer the
smallest number of tests that exercise the general invariant directly,
so the same coverage also protects instances never yet discovered,
over enumerating every known case as its own test. A fix is not complete
until its own regression test exists, is demonstrated to have failed
before the fix, and passes after; "the existing test suite still
passes" is a necessary check on its own, not a substitute for this
cycle -- an unchanged passing suite proves nothing failed before the
fix, only that nothing new broke. This is the framework's standing,
extensible pattern for defect remediation: a project or domain may add
further phase-local steps (e.g. a distinct coverage-audit step within
Refactor) without displacing the three-phase Red-Green-Refactor
structure itself, and the same structure applies unchanged to
implementation work more broadly, not only to defects already reported
by name.

27. When a mechanism generates or evaluates output per unit, item, or
instance that is supposed to be sensitive to that instance's own input,
verification is not complete on a per-instance self-consistency check
alone -- confirming that re-running the same instance twice produces
the same result says nothing about whether the mechanism is actually
responding to its input at all. It also requires comparing output
across genuinely different instances and treating unexpected sameness
as a failure. A degenerate implementation that always returns the same
result regardless of input can pass every per-instance determinism
check indefinitely -- exactly as one did across five capabilities of
this framework's own use, undetected until an unrelated investigation
happened to compare instances against each other rather than each
instance against only itself. Where full cross-instance comparison is
expensive at scale, checking a representative sample at each new
generation cycle is the minimum bar, not an occasional audit; per rule
22, this check belongs in the standing pipeline that produces the
output, not only in an after-the-fact review.

28. A governed ledger-backed projection -- a current-state file whose
correctness is supposed to be guaranteed by an append-only history of
chained events behind it -- is not actually protected by that history
unless something mechanically confirms the live file matches what
replaying the ledger would produce. Absent that check, the projection
can drift from its own ledger through a direct edit that bypasses the
governed write path entirely, and nothing detects the gap until an
unrelated investigation happens to compare the two -- as happened to
eleven items in one such ledger within a single capability, including
edits made directly by the orchestrating agent itself, who had every
reason to know the governed path existed and used it anyway only
inconsistently. Add a standing reproducibility check for each such
ledger -- run at minimum before any further governed write to the same
projection, and ideally on a recurring schedule independent of any
particular write -- that replays the ledger and diffs the result
against the live file, failing loudly rather than merely logging on
divergence.

29. Rule 25 requires actively searching for adjacent instances of a
found defect's root cause; it does not by itself protect the task that
motivated the search in the first place. A single triggering defect can
legitimately spawn many newly-discovered adjacent problems -- an
in-progress systemic audit repeatedly did exactly this in one capability
-- and each individual deferral of the original task in favor of a
freshly-found adjacent one can be locally reasonable while the
cumulative effect is that the original task never actually finishes: a
guidance-resolution defect was fixed at the code level while the
already-produced artifacts that motivated finding it in the first place
went unbackfilled for a full further session of otherwise-productive
adjacent work, each deferral individually justified, none of them
revisiting the original obligation. When a fix spawns further work
beyond itself (per rule 25, or otherwise), track the original
triggering task as a named, standing obligation distinct from whatever
adjacent work it spawned, and treat it as still open and outstanding
-- not implicitly superseded or satisfied -- until it is itself
verified complete, independent of how much adjacent work has been
completed in the meantime. Breadth of investigation earned by rule 25
is not a substitute for finishing what the investigation was originally
for.

30. Any pairing of a code or content change with a governed tracking
record meant to reflect whether that change has happened -- a
technical-debt item's status, a backlog entry's own completion marker,
a historical ledger's row, or any other such pairing this framework or
a project built on it establishes, including ones that do not exist yet
-- has exactly one moment of genuine completion: the moment both halves
are verified together, in the same check, not two separable steps where
finishing the first is trusted to imply the second happened. Do not
report, believe, or act on a tracked item being "done" based on
remembering that its code or content half was finished at some earlier
point; the tracking-record half must be confirmed current, through its
own governed mechanism, in the same moment the completion claim is
made. This rule is deliberately general rather than scoped to any one
artifact pairing named above, because three separate artifact-specific
fixes, for three separate instances of this same underlying behavior
found within one session -- a technical-debt lifecycle ledger bypassed
by direct hand-edits, a completed backlog entry left unmoved to its
historical record, and completed code work whose own backlog item's
status was never touched at all -- did not prevent a fourth instance
from surfacing in a still-different location in that same session. The
mechanism is what must be guarded, not the specific artifact pair it
was most recently caught in: this rule binds every governed
code-change/tracking-record pairing a project establishes from the
moment each is established, present or future, not only the ones
enumerated here.

31. Every governed work-item type this framework tracks to a closed,
resolved, accepted, or complete status -- now or in the future -- must
have an explicit Definition of Done (DoD): a fixed, criterion-based
checklist, all of which must hold before that type's status may
change. A DoD is not a narrative agreement; each criterion must be
mechanically checkable or independently verifiable (a test, a
validator, a direct source or record read), and a closure claim must
cite the exact check performed against each criterion (rule 24), not
merely assert the outcome. A type's DoD is authored and owned by the
Architecture Office, fixed at or before that type's first instance is
opened for work. The Engineering hat verifies against the standing
DoD; it does not decide what the DoD is on the way out the door. A
closure accepted against an ad hoc, local reading of completeness
improvised at the moment of closure -- rather than checked against one
standing definition -- is exactly the failure mode this rule exists to
close off. Amending an existing type's DoD requires the same explicit
codification process as any other rule in this document (proposed,
confirmed, committed) and explicit stakeholder approval; it cannot be
loosened quietly under pressure to close something, nor tightened
after the fact to excuse a miss. The entity performing the work may
always apply a more rigid standard than the DoD it was given --
expanding its own validation beyond the checklist's criteria -- but may
never discard, skip, or narrow any criterion on that checklist. Where
it cannot fully satisfy every criterion, it must report that honestly
and specifically to whoever invoked it, naming which criterion is
unmet and why, rather than report completion, treat partial success as
full success, or otherwise misrepresent the checklist's state to its
invoker. The recipient of a completed work item -- whether the
Architecture Office receiving from Engineering, or Engineering
receiving from a subagent -- carries its own obligation: to actually
verify the DoD checklist itself, criterion by criterion, and
substantiate each claim independently, rather than accept the
performer's report at face value. A recipient who accepts a "done"
claim without checking it against the DoD has committed the same
violation as a performer who reports "done" without having checked. A
type's DoD must be explicitly carried in every handover of work it
governs -- from the Architecture Office into a sealed work order, from
Engineering into any subagent delegation, from a subagent back in its
completion report, and from Engineering back to the Architecture
Office in its own closure report. A handover or report that omits the
applicable DoD, or that claims "done" without checking that claim
against each DoD criterion by name, is itself incomplete -- the
omission is a DoD violation in its own right, not a separate
documentation gap. Where a work-item type has no DoD yet established,
that absence blocks closure of any instance of it until the
Architecture Office defines one. It is never license for whoever is
closing the instance to construct criteria in the moment. This applies
to every governed work-item type already in use, not only to types
introduced after this rule's adoption -- work already in flight under
such a type may continue, but no instance of it may be marked closed,
resolved, accepted, or complete until its DoD exists. Establishing a
DoD for such a type does not, by itself, reopen or invalidate
instances of that type already closed before this rule existed. All of
a DoD's criteria for a given instance are verified together, in the
same check, before status changes -- rule 30 is this rule's
closure-time discipline, not a separate concern. Where the work-item
type is defect remediation, its DoD criteria include at minimum the
Red-Green-Refactor discipline (rule 26) and the abstract-pattern
adjacent-search pass reported as its own result (rule 25); where the
type is a ledger-backed projection, its DoD includes the
reproducibility check (rule 28); where the type is a per-instance
generative mechanism, its DoD includes the cross-instance sameness
check (rule 27). These are not new obligations bolted alongside DoD --
they are existing rules this one names and generalizes.

## Common application areas

- **Planning and sealing:** scale work orders to the change; avoid duplicating roadmap, backlog, decision, and scope prose.
- **Pre-execution optimization:** improve value order, sequencing, resource use,
  checkpointing, evidence reuse, and control cost only where the expected
  benefit justifies the review.
- **Handoffs in both directions:** update only information needed to resume or decide; do not restate repository history or evidence already referenced.
- **Preflight and repository state:** check boundaries affected by the work; reuse environment evidence until a defined invalidation trigger occurs.
- **Validation and independent review:** default to the smallest credible affected set; expand for risk or unexplained results, not ceremony.
- **Status and monitoring:** report meaningful milestones, changed state, blockers, and terminal outcomes; compact unchanged heartbeats.
- **Documentation and reconciliation:** repair the owning authority and only downstream projections that are actually affected.
- **Release, packaging, and publication:** generate and verify only authorized deliverables; do not rebuild unchanged products to refresh narrative evidence.
- **Closure and archival:** retain decision-bearing and non-reproducible evidence; reference rather than copy; avoid elaborate closeout for a small reversible change.
- **Durable learning:** correct the live instance first, retain only reusable
  learning, and perform consolidation, contradiction, and staleness review at an
  accumulated release or governed progression point rather than after every run.
- **Dependencies, security, privacy, rights, and recovery:** keep protections proportional but never waive a material safeguard merely because it has process cost.

Mandatory does not mean maximally elaborate. A mandatory outcome may be satisfied by a lighter mechanism when it provides equivalent evidence and protection. New process must identify its consumer, prevented failure, invalidation trigger, expected cost, and retirement or simplification condition.
