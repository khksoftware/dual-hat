<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

## 4.1.0 - 2026-08-19

Eight accumulated changes to canonical governance and tooling, published together as one minor release.

**Governance.** Principle 3 gains a fourth systemic-gap shape: a numeric bound whose value was set at or near an observed instance's own size rather than derived from what the bounded thing legitimately needs. Such a bound is evidence about the instance that produced it, not a constraint on the thing it is meant to bound, and it passes cleanly on the exact violation it exists to catch. Principle 12's residual is sharpened: even an armed session-stop hook's coverage stops at the session it is attached to, because a delegated or sub-agent's own turn is a separate execution context no parent hook can introspect by construction. Principle 16 is added: governing content is platform-neutral, and a platform's own auto-loaded instructions file is a pointer to it, never a second home for it. Purely additive -- no principle is renumbered, retired or reworded, so every existing citation still resolves. All three governance changes are advice; the two amendments inherit their principle's existing label, and the new principle states plainly why no detector can enumerate every present and future agent platform's own auto-loaded filename.

**Tooling.** A scoped sibling-import context manager (`tooling/sibling_import_context.py`) is added, and the product-bootstrap script's permanent, unscoped `sys.path` insertion -- the exact defect class the new module exists to prevent -- is repaired in the same change, rather than shipping a fix beside an unrepaired instance of the problem it solves. `known_environment_limitations` in the platform-profile schema gains a per-entry object contract (four required fields naming what breaks, how it presents, how to detect it, and the safe alternative, plus an optional remedy), genuinely armed by the profile-conformance validator rather than left as an unenforced specification.

**Documentation.** A new guide documents the composable pre-commit gate-dispatch pattern: a no-logic shim over independently-armed, per-gate marker files, for an adopter who needs more than one write-time gate behind git's single hook slot, together with the lesson that such a gate must read a commit's actual staged content rather than the working tree. Stated as advice, since the detectors it dispatches to are necessarily project-specific.

**Also in this release**, two smaller carried-over repairs: four test-rationale comments that pinned a version literal instead of naming the condition they meant, which had silently disarmed a real release-evidence check across releases; and a stale retired rule-number citation in a tooling docstring, corrected to its successor principle's number.

Compatibility impact MINOR: an adopter gains new advisory guidance and one newly-enforced (previously unenforced) schema constraint; nothing existing is renamed, relocated or removed, and every prior citation still resolves.

## 4.0.0 - 2026-08-17

Replaces the 36-rule set and its four unnumbered obligations with 15 numbered
principles, and makes arming the governing property of the document: every
principle now ends with either an `Armed by` line naming the executable
mechanism that refuses and that mechanism's declared residual, or an `Advice`
line stating plainly that nothing enforces it. Eight are armed and seven are
advice, counted mechanically from the file.

The head matter states the constraint that produced this — a control that is not
armed on the day it is authored is not authored — and forbids both an obligation
added without an arming line and an arming line naming a mechanism nobody
invokes.

The four highest-consequence obligations that previously sat outside the
numbering become principles 7, 8 and 9: the execution lease with its two
terminal conditions and its termination-preflight receipt, the dispatch
monitor-set obligation, and the evidence-defined worker-state vocabulary. They
were the only obligations no citation could reach, and they are the ones with
real gates behind them.

Every collapse is lossless on intent. The retired rules' intents carry to named
principles, two obligations are recorded as deliberate non-carries with their
reasons, and three rules whose disposition was outright deletion are relocated
to the documents that own their step, because each had a live consumer that
deletion would have orphaned.

Also in this release: the new-chat bootstrap obligation binds to a declared role
rather than to a filename, so a repository that folds its handover content into
its active-session record is conformant rather than in violation; and Clause A
of the conformance policy becomes executable at every guarded terminal
engineering edge, where five transitions now fail closed without a sealed,
reconciled termination-preflight receipt.

BREAKING. Every citation into the rule set is invalidated: 36 numbered rules
become 15 numbered principles with no arithmetic relationship, so published
citable surface changed meaning without changing shape. A contract is removed
and a gate is replaced. Two section headings consumers resolve against no longer
exist. A shipped tooling message moves from naming rule 35 to naming principle
14. `release/UPGRADING.md` carries the governed 3.x to 4.0.0 migration and
resolves every retired rule number an older citation still names.

No executable gate's predicate changes. `transition_allowed`,
`termination_preflight_failures`, `dispatch_inventory`, `validate_sealed` and
`validate_no_embedded_absolute_local_paths` all refuse exactly what they refused
before.

## 3.0.0 - 2026-08-13

Major release. Vendored plugin-bundle version currency becomes a
publication-blocking condition rather than a detector that reports and is
shipped past.

A stale vendored bundle reached a published HEAD once while the framework's own
detector sat red, and its own comment had described the consequence in advance.
A red test is advisory and a human can ship past it, so the reinforcement is a
publication-blocking condition and deliberately not a second test asserting the
same predicate. `validate_bundle_version_currency()` is called from both
`validate_staged()` and `verify_commit_tree()`, reading through the index or the
committed tree rather than the worktree, so the condition is evaluated against
the content actually being published.

**Breaking, and it is first contact rather than a tightening.** No earlier
release carried this condition in any form, so every refusal it makes is new to
every adopter regardless of which release they are upgrading from.
`release/UPGRADING.md` carries the migration section: the three enforcement
sites including the one reached transitively inside a production release build,
the conditions refused, the equality-in-both-directions rule, the two keys added
to `validate_staged()` and `verify_commit_tree()` return shapes, the four limits
the condition deliberately does not reach, and the ordering consequence for an
adopter's own release process.

`release/PUBLICATION.md` gains a normative section stating the rule, and
reconciles it in one sentence with the existing statement that forward
publication preserves standalone-owned namespaces without claiming or mutating
them: the rule reads that content and declines to publish, never rewrites it.

The framework's own bundle-currency test now calls the condition rather than
re-asserting three of its predicates by hand, and its hardcoded vendor
enumeration is retired.

Every version declaration this distribution carries states the shipped version,
including the example adopter profile and the shipped templates. Deployment-form
manifests and superseded vendored snapshots are discovered by shape rather than
enumerated, so a form or a snapshot nobody wrote down is still handled.

## 2.0.0 - 2026-08-11

- **Major release. See `release/UPGRADING.md`, the framework's first governed
  migration document.** The version was raised to a new major because
  `release/VERSION.json`'s own stability string requires that breaking changes
  bring "a new major version and governed migration", and this release carries
  breaking changes to a public function's required arguments, to two published
  provenance records, to a published maturity vocabulary, to which adopter
  platform profiles are admitted, and to where obligation text lives. The
  migration document names each individually with the release it landed in,
  rather than as a delta from one assumed starting point.
- Fixed the publication endpoint verification, which proved only the first
  configured endpoint. `tooling/release_package.py` queried
  `git remote get-url origin` and `git remote get-url --push origin` without
  `--all`; git returns one URL from those queries and pushes to every configured
  `remote.origin.pushurl`, so a second, unapproved push endpoint was invisible
  to the check. Demonstrated offline with two bare repositories and a real push:
  the check returned a PASS record while both repositories received the identical
  commit. Both queries now use `--all` and every returned endpoint must equal the
  approved identity; an unparseable URL is kept as an empty identity rather than
  filtered out, so a malformed endpoint fails the comparison instead of
  disappearing from it. `insteadOf` rewriting was verified not to be a bypass and
  is deliberately unchanged, with a regression test now protecting it.
- Fixed the publication provenance records, which asserted a singular verified
  push endpoint the check had not established. `fetch_endpoint_identity` and
  `push_endpoint_identity` are replaced by `fetch_endpoint_identities` and
  `push_endpoint_identities`, each enumerating every configured endpoint in
  configured order, and `dual-hat-fresh-remote-state` and
  `dual-hat-remote-publication-provenance` both move to schema `/2.0`. The
  scalars are removed rather than retained, so no consumer can go on drawing the
  singular conclusion.
- Fixed `release_maturity()`, which stamped every major at or above 1 as
  `stable_1_x`. The label is now derived from the major the version carries,
  parameterised rather than enumerated per major, so `stable_2_x` here and
  `stable_<major>_x` at every later major. No 1.x value changes. The defect
  survived because `release/VERSION.json` carried the same value the function
  derived, so the existing cross-check compared two sides that agreed and were
  both wrong.
- Added standing checks for both conventions this release supersedes: a maturity
  label must agree with its own version, checked against the shipped release
  evidence, against every committed record carrying both a version and a
  maturity, and against synthetic contradictions; no module may resolve a remote
  endpoint with the single-endpoint query again; and no maturity label literal
  may survive outside the one derivation.
- Strengthened the release-identity check. A release must now carry release
  notes for its own version, a CHANGELOG head entry naming that version, and a
  governed migration section for its own major. The previous form accepted a
  version mentioned anywhere in the changelog.
- Replaced four fixture strings in `tests/test_repository_hygiene.py` that
  embedded a real machine's drive, username and directory layout, on a file the
  export allowlist ships publicly. Each replacement is asserted, not assumed, to
  still trip the detector its test exercises. This was a publication-disclosure
  concern and not a rule 35 compliance defect; the lines were already exempt by
  file shape.

## 1.18.5 - 2026-08-07

- Added `GOVERNING_PRINCIPLES.md` rule 36: survey before designing -- do not
  reinvent what already exists. Before designing a capability, proposing an
  approach another role is expected to act on, or asking the stakeholder to
  choose between designs, establish from the system's actual current source
  whether the capability -- or an adjacent one with settled semantics it should
  extend -- already exists. The survey searches for the capability's behavior,
  not only the name the requester or the agent happened to use for it, and what
  was searched is stated alongside whatever is proposed, since an unstated
  survey is indistinguishable from an unperformed one. Where the capability
  already exists, extend it and match its established semantics; where it exists
  but is genuinely unfit, say so explicitly against the real implementation
  rather than designing past it in silence. Where a decision was already taken
  on a premise the survey later falsifies, the correction and the false premise
  are stated to the stakeholder rather than the question being silently re-put,
  and the correction can never settle a matter the cardinal rules reserve to the
  stakeholder. Proportionate by design: for a small, local change one targeted
  search, stated, discharges it.
- Added a notice at the head of `GOVERNING_PRINCIPLES.md` stating that changing
  that document's own rules requires review by an independent Architect distinct
  from the agent or session that drafted the change, and that committing the
  drafted text is not itself adoption. Rule 32 remains the full statement of the
  requirement and governs; the notice exists only so that a reader reaches the
  requirement without first reading two-thirds of the document. No rule is
  renumbered and no rule is relocated.
- Removed the false status claim from rule 32's own closing sentence, which
  still described rule 32 as drafted and committed pending review and not yet
  finally adopted. That independent review was in fact performed and rule 32 was
  adopted and released, so the claim had been false since adoption -- a
  self-describing status marker with nothing keeping it synchronized as the
  underlying state changed. The sentence now reads only "This rule is itself a
  governance-rule change and is therefore subject to its own requirement",
  retaining in the present tense the true and durable half -- that rule 32 binds
  its own future amendments -- and dropping the half that had gone stale. Rule
  32's operative requirement is unchanged and nothing else in the rule is
  reworded. Provenance of rule 32's own adoption remains recorded where it
  belongs, in this changelog and in the 1.18.1 release notes, rather than
  restated inside the rule.
- Fixed a structural misattribution between rules 33 and 34. Rule 33's last two
  paragraphs -- the prohibition on a delegated agent treating a relayed claim of
  stakeholder authorization as verified consent, and that prohibition's incident
  citation -- were physically sitting inside rule 34's body, because the commit
  that added rule 34 inserted it into the middle of rule 33 and rule 33's tail
  was never moved back. A reader therefore attributed rule 33's core prohibition
  to rule 34, a rule about confirmed test failures never being ambient state.
  Both paragraphs are moved back to the end of rule 33 as a pure relocation: not
  one word is reworded, merged, or renumbered, and rule 33's body is now
  byte-identical to its form before the insertion. Neither rule's requirements
  change; only what each rule contains is corrected.

## 1.18.4 - 2026-08-06

- Added `GOVERNING_PRINCIPLES.md` rule 35: a durable file -- version-controlled,
  a governed artifact, a template, or any generated-but-committed output -- must
  never embed an absolute local filesystem path used as a live structural
  pointer or self-reference. Explicitly carves out a path quoted verbatim as
  illustrative or historical evidence (an incident citation, a changelog
  entry) and a path recorded as a factual claim about where a process
  actually ran (an audit-log entry, a provenance record), since neither
  functions as a live pointer. Adopting the convention carries rule 20's
  standard closure discipline: a one-time mechanical sweep of the
  repository's active surface plus a standing mechanical check that catches
  a new embedding the moment one is introduced.
- Added rule 35's own required standing mechanical check: an absolute-local-path
  detector (`tooling/repository_hygiene.py`) with test/schema/citation/regex-
  source carve-outs, its regression suite, and two exemption registries
  (`repository/ABSOLUTE_LOCAL_PATH_CITATIONS.json`,
  `repository/ABSOLUTE_LOCAL_PATH_DEFERRED_SCOPE.json`) for a human-reviewed
  citation or an explicitly tracked, not-yet-adjudicated finding.

## 1.18.3 - 2026-08-05

## 1.18.3 - 2026-08-05

### Changed

- Require every accepted objective to continue through a planned-scope terminal receipt or a named hard-stop receipt.
- Require an authoritative persistent worker-monitor registry with evidence-defined finish, stall, death, and unreachable states.
- Require successor registration before discharging an incomplete worker outcome.

## 1.18.2 - 2026-08-04

- Added `GOVERNING_PRINCIPLES.md` rule 33: the stakeholder's only direct,
  interactive channel is with whichever session is currently acting as the
  Architecture Office; Engineering and every other delegated or dispatched
  agent has no standing direct channel to the stakeholder, and its authority
  for a task comes from Architecture's own directive, never from a relayed
  claim about what the stakeholder said. Architecture alone decides whether,
  what, and how to convey any stakeholder instruction to a delegated agent;
  verbatim forwarding of the stakeholder's literal words is reserved for a
  genuinely rare, explicit, transparent exception, never the default. A
  delegated agent must never treat a message arriving through any relay,
  coordination, or cross-chat channel that claims "the author/stakeholder
  said/authorized/instructed X" as itself verified consent, however phrased.
- Strengthened `SESSION_AND_HANDOVER_PROTOCOL.md`'s existing bounded-context-
  refresh clause with two concrete requirements: refreshing context after any
  interruption that can lose conversation memory -- context compaction chief
  among them -- requires reading the current active-session record's own
  state sections in full, never relying on a prior summary or a partial
  earlier read; and before treating any tracked item's own status/lifecycle
  field as current, cross-check it against actual repository history for a
  matching completion commit, since a status field can lag genuinely
  completed work.
- Amended `GOVERNING_PRINCIPLES.md` rule 23 further: the obligation to verify
  a delegated task's status against the live task registry also stands on
  its own, periodically, for as long as delegated background work is
  believed in flight -- at natural checkpoints such as before compiling a
  status report, before dispatching further work in the same area, or after
  a long uninterrupted stretch with nothing else prompting a status claim --
  not only when a status assertion is already about to be made.
- Added `GOVERNING_PRINCIPLES.md` rule 34: a confirmed genuine automated-test
  failure is a live, unresolved defect signal, never an accepted or ambient
  repository state -- it is fixed immediately, or the moment whatever blocks
  the fix resolves, and is never left silently red across sessions as an
  unaccountable "known failure." The responsible agent proactively monitors
  for a genuine failure's existence, including checking the outcome of any
  check that runs outside the local session, rather than waiting to be told;
  a failure that cannot be fixed immediately is recorded as accepted
  technical debt with an explicit remediation trigger. A companion
  cross-reference was added to `VALIDATION_PROTOCOL.md`'s existing
  flake-diagnosis sentence, pointing at the new rule rather than duplicating
  it.

## 1.18.1 - 2026-07-30

- Broadened `GOVERNING_PRINCIPLES.md` rule 23: a delegated task must never
  be reported, recorded, or tracked as dispatched, in progress, running, or
  awaited unless verified against a real dispatch call just made or an
  independent task-registry check, at any point in a session -- not only
  when resuming from a context compaction or revisiting a long-running
  task's stale early read, which remain named as important covered cases.
  An interruption between deciding to delegate and actually delegating must
  leave the tracking artifact reading "not yet dispatched," never "in
  progress."
- Added `GOVERNING_PRINCIPLES.md` rule 32: any candidate governance-rule
  change, new or amending, requires review by an independent Architect
  reviewer distinct from whoever drafted the change before it counts as
  codified, adopted, or slated for propagation. Committing rule text to
  canonical source is drafting, not adoption. Generalizes the
  independence-and-evidence standard already required for Definition-of-Done
  closure and technical-debt acceptance review to the framework's own rule
  set; applies to itself.
- Added an independent-review-before-final-acceptance requirement to
  `planning/TECHNICAL_DEBT.md`'s generic technical-debt authority: a
  resolved item's status is the resolving party's own completion claim, not
  final acceptance, which additionally requires a reviewer distinct from
  the resolver to re-derive the resolution's own validation directly and
  record reviewer identity, verdict, and evidence checked separately.

## 1.18.0 - 2026-07-29

- Added `START_HERE.md` as the single required entry point for a fresh
  agent or chat session to gain full working knowledge of the framework,
  sequencing README, the operating model, onboarding, bootstrap, the
  operating guide and installation/binding guidance, both role
  guide/prompt pairs, and the work-item lifecycle and closure protocols in
  order. Replaces an assembled-by-hand reading list. `README.md` points to
  it near the top and `repository/CANONICAL_ENTRYPOINTS.md` gains a first
  row for it.
- Added an isolated design review mechanism to
  `architecture/REASONING_AND_DECISION_REVIEW.md`: for a materially
  consequential, unsettled architecture/product/workflow/UX decision, the
  Architecture Office may commission two or more isolated participants to
  independently produce candidate approaches or critique existing ones --
  blind to each other's identity and output until locked, including an
  isolated UX-perspective participant when the decision is user-facing.
  Unlike the existing three-arbiter protocol this is not a vote:
  Architecture alone synthesizes the unblinded submissions and decides,
  combines, or rejects among them, preserving the framework's
  single-authority invariant.
- Added four additive delegation rules to
  `governance/VALIDATION_AND_PARALLELISM.md`: every delegated sub-agent's
  messages begin with a brief description of its assigned role or task,
  mirroring the primary agent's own role-label convention; unless a sealed
  work order says otherwise, every sub-agent defaults to the Engineering
  Agent role and is bound by every rule that governs it; the delegating
  agent supervises rather than trusts sub-agents -- staying on standby,
  tracking progress, and treating sub-agent self-reports as unverified
  until independently checked against live evidence, while remaining
  responsive to the user without delay; and a question, ambiguity, or
  materially consequential decision surfacing in a sub-agent's own work is
  never resolved by the sub-agent -- it pauses and escalates to the
  Architecture Office.
- Added `GOVERNING_PRINCIPLES.md` rules 21 through 31:
  - Rule 21: a governance change codified during an active chat session
    takes effect immediately within that session -- for the primary
    agent's own remaining behavior and for every subagent already active
    or subsequently launched -- rather than binding only a future fresh
    session.
  - Rule 22: before authoring new procedural logic for a workflow the
    framework already governs as a repeated, structured process, an agent
    first checks for an existing canonical entry point and uses it, or
    escalates before building a parallel one.
  - Rule 23: an agent resuming across a context compaction, and an agent
    whose own single long-running task has run for an extended duration
    without revisiting a foundational fact it read only once early on,
    both re-derive their working method or belief from the actual current
    source rather than a stale prior summary or an early-and-never-
    refreshed read; a report asserting something was "verified" or
    "confirmed" must state what was actually re-checked and when.
  - Rule 24: a checkpoint report's completeness or coverage claims must
    cite the concrete mechanism used to determine the denominator, not
    just the number.
  - Rule 25: finding one instance of a defect is itself the trigger to
    actively search for sibling instances sharing the same root cause --
    both a literal search for the same pattern, name, or call shape, and
    an independent abstract-pattern search that names the defect's
    structural shape and looks for anything matching it across different
    file formats, naming conventions, or subsystems that share no literal
    string -- and to prefer a systemic, generic countermeasure over a
    collection of narrow instance-by-instance patches. The search
    performed and its result must be stated in the fix's own report.
  - Rule 26: defect remediation follows Red-Green-Refactor as the
    standing pattern -- write a test reproducing the defect and confirm it
    genuinely fails first, then fix the defect (generalized per rule 19
    and searched for siblings per rule 25), then clean the fix and its
    tests into systemic, generic form without changing verified behavior.
    An unchanged passing test suite proves nothing failed before the fix,
    only that nothing new broke.
  - Rule 27: when a mechanism generates or evaluates output per unit,
    item, or instance that is supposed to be sensitive to that instance's
    own input, verification requires comparing output across genuinely
    different instances and treating unexpected sameness as a failure,
    not only confirming per-instance self-consistency, which a
    degenerate, input-blind implementation can pass indefinitely.
  - Rule 28: a governed ledger-backed projection is not protected by its
    append-only history unless something mechanically confirms the live
    projection matches what replaying the ledger produces; add a standing
    reproducibility check, run at minimum before any further governed
    write to the same projection, that fails loudly rather than merely
    logging on divergence.
  - Rule 29: rule 25's adjacent-search mandate does not by itself protect
    the task that motivated the search. Track the original triggering
    task as a named, standing obligation distinct from whatever adjacent
    work it spawned, and treat it as still open until independently
    verified complete, regardless of how much adjacent work has finished
    in the meantime.
  - Rule 30: any pairing of a code or content change with a governed
    tracking record meant to reflect whether it happened has exactly one
    moment of genuine completion -- when both halves are verified
    together, in the same check, not two separable steps where finishing
    the first is trusted to imply the second happened.
  - Rule 31 (Definition of Done): every governed work-item type this
    framework tracks to a closed, resolved, accepted, or complete status
    must have an explicit, criterion-based, mechanically-checkable
    Definition of Done, authored and owned by the Architecture Office
    before that type's first instance opens, never invented by whoever is
    closing an instance. The performing entity may exceed but never
    narrow or skip a criterion, and must honestly report exactly which
    criterion is unmet rather than misrepresent partial success as full
    success. The recipient of a completed work item must independently
    verify the checklist itself rather than accept the report at face
    value. The DoD must be explicitly carried through every leg of a
    handover chain, with its absence itself a violation. Where a type has
    no DoD yet, closure is blocked until the Architecture Office defines
    one, though in-flight work may continue and no already-closed
    instance is retroactively reopened. Rule 30 is folded in as this
    rule's closure-time discipline; rules 24 through 28 are named as
    existing DoD-fragment instances this rule generalizes.
- Added a note near the end of `README.md`, verbatim per explicit
  stakeholder instruction: a caution that one particular assistant model
  family is more prone than others to drifting away from this framework's
  governance and needs regular reminding, described as an innate quality
  the framework itself cannot remediate. This note names a specific
  model, which is in tension with the framework's general practice
  elsewhere of not naming specific providers or models in portable source;
  implemented as explicitly instructed, with the tension noted here for
  future reconsideration.

This is a minor release: it adds a new required onboarding document, a
new architecture-review mechanism, and eleven new governing-principles
rules including a capstone Definition-of-Done requirement that changes
how closure works for every governed work-item type going forward. All
changes are additive and backward-compatible -- no existing schema,
required field, or documented contract is removed or narrowed -- but the
combination changes framework layout and contracts beyond what a patch
release covers.

## 1.17.8 - 2026-07-28

- Added `PROCESS_PROPORTIONALITY.md` rule 20: when a foundational convention
  (a path scheme, an identity/naming model, a schema version, or any other
  shared contract multiple consumers depend on) changes, the change is not
  complete until every consumer is proven, mechanically rather than by
  manual review, to have zero surviving references to the superseded
  convention, and until a standing mechanical check catches any new
  hardcoded reference to it going forward. Named as the standing defense
  for one especially common shape of rule 19's systemic mechanism gap, and
  cross-referenced with it in both directions. Pinned with a new
  exact-substring test in `test_framework.py` beside the rule 19 pinning
  test.

## 1.17.7 - 2026-07-28

- Unified two governance rules that had independently drifted apart across
  their restatements, with no test previously tying any of the copies
  together: the hypothesis-blind-execution / three-arbiter protocol
  (`REASONING_AND_DECISION_REVIEW.md`, restated in both role prompts) and
  the universal-completion-claim rule (`CONFORMANCE_POLICY.md`, restated
  in both role prompts). Both are now pinned by exact-substring tests
  across the canonical doc and every restatement.
- Added a mechanical check for a previously undocumented-only invariant:
  `REPOSITORY_BOUNDARIES.md` states Dual Hat never imports product,
  engineering, archive, or workspace state, but nothing in `tooling/` or
  `tests/` enforced it. `framework_completeness.py`'s leakage scan now
  matches real Python import statements (including relative imports)
  against the four forbidden top-level packages, pinned with a test
  exercising both violating and benign samples.
- Added an independent closure-reconciliation-audit gate at every
  capability's closing gate: before terminal disposition, a
  context-isolated independent reviewer must reconcile the sealed work
  order's approved scope, every incremental stakeholder request, and every
  committed interim finding/bug against verified repository fact, not
  Engineering self-report. Partially done or not-done items block closure
  unless explicitly deferred by the author. Adds a required
  `reconciliation_audit` object to the closeout-decision schema.
- Added `PROCESS_PROPORTIONALITY.md` rule 19: when investigating a flagged
  defect, stale artifact, or "supposed to be done but wasn't" gap, first
  determine whether the symptom is one instance of a missing systemic
  mechanism (an undocumented mandatory step, a check never made mechanical,
  or an unsynchronized pointer/cross-reference) rather than a genuine
  one-off, and repair the mechanism itself when it is. Cross-references
  rule 15's correction-to-control loop in both directions.

## 1.17.6 - 2026-07-27

- Named an exact failure mode explicitly in the turn-exit-audit
  reconciliation obligation: a delegated worker that returns from a
  bounded checkpoint (not a genuine stop condition) requires an explicit
  resume decision recorded at that moment, since pursuing a newly surfaced
  finding or user tangent instead is exactly how a completed-but-unresumed
  worker sits silently idle while believed to still be running.
- Added an explicit preference for resuming an existing paused/checkpointed
  worker over launching a new one for continuation of the same bounded
  assignment, since relaunching discards accumulated context and forces
  avoidable re-derivation of already-established state.
- Dropped the plugin manifests' independent packaging version sequence
  (bumped in lockstep with every framework refresh but never for a
  genuinely independent reason); `plugin.json`'s `version` field now
  equals the bundled framework version directly.

## 1.17.5 - 2026-07-27

- Strengthened the delegation rule from "prefer delegating long-running
  work" to a standing default: whenever the runtime supports it, keep the
  primary agent on standby to orchestrate and stay directly available for
  user interaction, delegating capability/Gov work-item execution to
  sub-agents by default regardless of stream count or duration, including
  new work an interaction surfaces mid-session, unless delegating would
  risk interfering with another active stream.
- Unified the wording of this rule across the two places it was
  independently restated (`governance/VALIDATION_AND_PARALLELISM.md`,
  `prompts/ENGINEERING_AGENT_PROMPT.md`) instead of letting them drift
  further apart.

## 1.17.4 - 2026-07-27

- Folded the Integrated Mode role-label convention into the mandatory
  turn-exit audit: both role guides now explicitly check the message
  prefix as part of the same "before every response boundary" discipline
  that already governs task-completion and stop-condition checks, instead
  of leaving it as a separate, unenforced convention.
- Named concrete resumption points (returning from a background-agent
  notification, returning from a tangent, resuming from a context-
  compaction summary) where the full turn-exit audit must explicitly
  re-run, since self-applied conventions with no code-level enforcement
  are likeliest to silently lapse exactly at those points across a long,
  multi-threaded conversation.

## 1.17.3 - 2026-07-27

- Refreshed the agent-host plugin bundle from framework 1.17.0 to the
  current canonical version; the supported plugin install path had been
  shipping a framework build with the exact role-transition/authority
  defect 1.17.2 already fixed. Added an automated version-parity test so
  the bundle cannot silently drift from `release/VERSION.json` again.
- Broadened `content_security.py`'s secret-scanning patterns (the last
  gate before public release) to also recognize several common
  workspace-chat, cloud-console, and payment-processor API key and bearer
  token formats, plus JWTs; coverage was previously limited to a smaller
  set of key/token shapes.
- Fixed a stale README release-notes link and added a version-tracking
  assertion so it cannot go stale again the same way.
- Generalized two product-leakage denylist patterns that were
  reverse-engineered from one past incident's exact numbers and path
  names, without over-broadening into false positives on the framework's
  own generic scaffold content.
- Cross-referenced the two same-basename `OPERATING_MODES.md` files
  (`architecture/` and `guides/`) so their distinct scope is clear from
  either one.
- Minor readability cleanup: split several semicolon-joined compound
  statements onto separate lines and moved two justification-free
  function-local imports to module scope.

## 1.17.2 - 2026-07-26

- Made explicit that the persistent-execution and no-idle continuation rules
  govern behavior only within an active sealed order and never substitute for
  one: a work item's closure terminates Engineering authority immediately
  regardless of continued conversational instructions, side requests, or an
  apparently obvious next task. A direct, specific, or urgent instruction is
  a request for Architecture to classify and seal, not itself a sealed order.
  Before any Engineering action, verify a currently bound, hash-valid sealed
  order covers the exact action; if none exists, return to Architecture and
  seal one before resuming.

## 1.17.1 - 2026-07-26

- Closed a defect only after repairing both the behavior and its failed or
  missing prevention/detection defense, adding defect-sensitive executable
  regression evidence, checking analogous instances, and obtaining independent
  adversarial review of the countermeasure before closure.
- Required executable competing-actor and adverse-timing evidence for any
  claimed lock, lease, ownership-token, or coordination race safety;
  structural inspection and happy-path tests alone no longer substantiate
  race-safety claims.
- Required consequential parallel workflows to use exactly one authoritative
  orchestrator with pure bounded parallel workers, immutable leases,
  maximal-prefix checkpoint salvage, deduplicated residual retry, and atomic
  publication/cursor advancement; opaque status and heartbeats never advance
  authority.
- Kept the active-session record current throughout execution rather than
  only at closure or switchover, and added a governed chat-switchover
  protocol that takes a fresh authoritative snapshot, reconciles every
  in-flight task and owned process, regenerates one compact handoff artifact,
  and gives an explicit safe-to-switch signal without pausing healthy work.
- Required every hash gate to declare repository-byte, canonical-UTF-8-text,
  or binary-output byte semantics; canonical text validation now reads
  current worktree bytes, normalizes only CRLF to LF, rejects BOM/invalid
  UTF-8/bare CR, and never hashes a committed copy that could hide worktree
  drift.

These five items were part of the reconciled 1.17.0 carried-forward set but
were not actually present in the published 1.17.0 release content; this
section completes that set. This is a backward-compatible additive
governance release; no existing authority, lifecycle, schema, or
compatibility contract changes.

## 1.17.0 - 2026-07-25

- Added optional discover/decide/deliver/single-role-pass routing without a
  mandatory pipeline.
- Required the smallest distinct-value role roster derived from actual failure
  axes, with explicit re-tier-versus-re-role diagnosis.
- Distinguished re-tiering, primary-hat transition, and specialist
  reassignment, and prohibited single-role passes from bypassing Architecture
  acceptance.
- During parallel/shared mutation, assigned one active writer at a time plus
  one integration owner to each shared artifact lane, with implicit trivial
  ownership and checkpointed reassignment; reviewers remain read-only.
- Added compact deliver-or-declare reporting only at governed blocked
  boundaries plus explicit blocked-state entry, evidence, and re-entry
  semantics.
- Added selective durable-learning retention plus accumulated-release and
  phase-progression consolidation, contradiction, and staleness review without
  a per-run ledger.
- Added proportionate pre-execution plan optimization with independent
  Architecture review only for material scale, complexity, risk, or
  irreversibility.
- Added non-disruptive checkpoint reevaluation of materially long-running or
  resource-consuming execution when observed bottlenecks, throughput, yield,
  allocation, batching, failures, cost, or wall time justify it.
- Required periodic optimization review to confirm, revise, or retire material
  embedded assumptions against current evidence rather than confusing
  unchallenged with supported, with experimentation proportional to consequence
  and uncertainty.
- Added the mandatory response-boundary turn-exit audit to both role guides.
- Consolidated carried-forward active-execution controls: termination
  preflight, active-goal response/continuation interlock, execution lease, and
  response-end watchdog.
- Consolidated carried-forward validation and transition controls: separate
  validation gate versus mutation, nonzero-test evidence, lifecycle-aware gate
  inputs, and pre-state-versus-replay transition validation.
- Consolidated carried-forward completeness and evidence controls: itemized
  adjudication readiness, identity-bound progress accounting, and
  current-capability claim verification.
- Separated portable-core ownership from standalone deployment namespaces so
  plugin artifacts, standalone release notes, and deployment provenance survive
  forward core publication without becoming portable-core content; the
  portable changelog remains byte-exact canonical content.
- Prevented ordinary Python validation, test, staging, and release commands
  from generating bytecode residue, and made governed staging clean and report
  only recognized Python cache artifacts before fail-closed mismatch checks.
- Bound release-package inputs and committed provenance to the exact
  manifest-owned portable subset of composite publications while preserving
  declared standalone deployment lanes and rejecting portable drift or loss.

The three carried-forward control groups plus the routing/role/learning and
plan/run-optimization groups account for all 13 items in the unpublished
portable 1.17.0 candidate.

This is a backward-compatible additive governance release. Existing 1.x
authority, lifecycle, schema, and compatibility contracts remain unchanged.

## 1.15.0 - 2026-07-24

- Added Architecture/Design, UX, and QA as the proportional independent
  specialist-review roster, with falsification-oriented review for material
  risks rather than routine three-gate ceremony.
- Required one-to-five-minute verified progress updates for long-running work,
  especially opaque delegated execution.
- Required universal completion claims to name and reconcile their exact
  inventory, counts, dispositions, and remainder.
- Added a correction-to-control loop: generalize called-out errors, identify
  their owning cause, apply and codify the smallest effective systemic
  countermeasure, and inspect direct analogues.
- Added preregistered hypothesis-blind execution, separate blinded result
  review, and three independent arbiters for genuinely doubtful material
  decisions.
- Prohibited population-wide conclusions from representative samples unless a
  valid preregistered sampling design supports them; enumerable broad-intake
  corpora require item inventory and separate catalog, triage, and processing
  completeness.
- Required sealed independent approval before Architecture or Engineering
  narrows external-source discovery or ingestion.

This is a backward-compatible additive governance release. Existing 1.x
authority, lifecycle, schema, and compatibility contracts remain unchanged.

## 1.14.0 - 2026-07-24

- Allowed precisely bounded categorical authorization for dependency, tool,
  and model candidates while preserving per-candidate license, cost,
  reliability, safety, hardware, support, privacy, and integrity evaluation.
- Required rejected installed candidates to be removed promptly after their
  evidence is preserved.
- Made combined phase closure and successor opening one atomic planning,
  history, session, ledger, and handover transition.
- Consolidated command reference and troubleshooting under `guides/`, removing
  the redundant top-level `help/` directory and updating all active references.

This is a backward-compatible additive governance release. Existing 1.x
authority, lifecycle, schema, and compatibility contracts remain unchanged.

## 1.13.0 - 2026-07-24

- Added proportional specialist-review separation for material work whose acceptance depends on genuinely distinct architecture, UX, security, accessibility, data, or domain judgments.
- Required isolated reviewers to inspect primary evidence independently before Architecture integrates and dispositions their findings.
- Kept routine and closely coupled work on the existing bounded-review path to avoid ceremony.
- Made capability preflight receipt reuse content-addressed and
  invalidation-driven so unchanged platform evidence is not recomputed merely
  for a new work-item identity.
- Consolidated troubleshooting and command lookup under `help/` and added the
  framework contact address to the README.

This is a backward-compatible additive governance release. Existing 1.x authority, lifecycle, schema, and compatibility contracts remain unchanged.

## 1.12.0 - 2026-07-22

- Required lightweight stakeholder discussion before unresolved consequential design is converted into an implementation-ready specification.
- Clarified that phase or capability entry authorization does not itself accept unsettled product, UX, workflow, commercial, privacy, or architectural choices.
- Required side questions to be answered concurrently with active execution, with an explicit immediate next action and continued milestone reporting.

This is a backward-compatible additive governance release. Existing 1.x authority, lifecycle, schema, and compatibility contracts remain unchanged.

## 1.11.0 - 2026-07-22

- Required active and output locations to contain only current operationally consumed artifacts.
- Required capability- and phase-scoped outputs to be classified at closure or supersession as current, historical, or disposable.
- Required historical evidence to move to governed archives with traceability and disposable duplication to be removed from current product surfaces.

This is a backward-compatible additive governance release. Existing 1.x authority, lifecycle, schema, and compatibility contracts remain unchanged.

## 1.10.0 - 2026-07-22

- Required a brief human-readable Architecture report at every governed phase or subphase transition.
- Required the report to summarize activities, outcomes, limitations or carried-forward work, and the rationale for the next destination.
- Clarified that machine closure evidence and bare status announcements do not satisfy the stakeholder-facing transition obligation.

This is a backward-compatible additive governance release. Existing 1.x authority, lifecycle, schema, and compatibility contracts remain unchanged.

## 1.9.1 - 2026-07-21

- Moved the Integrated/Split role-selection explanation before First Use so adopters choose the operating arrangement before following onboarding instructions.

This is a documentation-order patch. It changes no authority, lifecycle, schema, tooling, or compatibility contract.

## 1.9.0 - 2026-07-21

- Required forward-looking planning, backlog, debt, and trigger artifacts to be groomed at defined progression points and material changes.
- Required promised stakeholder-facing reports, comparisons, recommendations, and decision summaries to be delivered proactively before terminal disposition.
- Preferred explicit research and experimentation iterations inside one capability when the objective and governing contract remain unchanged.

This is a backward-compatible additive governance release. Existing 1.x interfaces, historical work items, authority boundaries, and mandatory safeguards remain unchanged.

## 1.8.0 - 2026-07-21

- Required every ad hoc fix to be assessed for a recurring failure class across inputs, work items, environments, or consumers.
- Prefer the smallest proportionate owning-layer systemic repair when recurrence is credible, while still repairing the current instance.
- Guarded the rule against speculative expansion: an isolated defect does not justify a broad redesign without demonstrated recurrence risk.
- Required completed short-lived work branches to be integrated and retired before unrelated work continues, unless a governed retention exception exists.

This is a backward-compatible behavioral governance release. Existing 1.x interfaces, authority boundaries, and mandatory safeguards remain unchanged.

## 1.7.0 - 2026-07-21

- Added a plain-language framework introduction before First Use.
- Required consuming projects to map abstract model tiers to evidence-backed concrete selections during onboarding and to remap when the environment or verified availability changes.
- Distinguished governance tightly coupled to a product capability from independently bounded GOV work.
- Made minimum sufficient process cardinal: defer repeat-prone steps to the latest safe point, reuse valid evidence, and prefer delta/affected-surface reruns over whole-process repetition.
- Made work-item preflight artifacts dynamically bound and self-excluding so persisted receipts remain reproducible instead of invalidating themselves.

This is a backward-compatible additive minor governance release. Existing 1.x authority, lifecycle, mode, and readable historical work-item contracts remain available; no material safeguard is weakened.

## 1.6.0 - 2026-07-21

- Made the smallest credible, risk-proportionate focused test subset the default validation scope.
- Reserved full-suite reruns for broad or uncertain impact, unexplained failures, explicit requirements, or inadequate focused coverage.
- Preserved all explicitly mandatory validation suites and stop gates.

All notable changes to Dual Hat are recorded here. The project uses Semantic Versioning; breaking core-contract changes require a major release.

## 1.5.0 - 2026-07-21

### Added

- After fully accepting a work item, the Architecture Office proposes the next work to plan, including its outcome, smallest useful scope, and principal boundaries or decisions.
- Post-acceptance planning guidance is explicitly distinct from execution authority.

This is a backward-compatible additive minor release. Existing 1.x work-item, profile, handover, and authority concepts remain available; no mandatory control is weakened.

## 1.4.0 - 2026-07-21

### Added

- Proportional, bidirectional traceability from stakeholder intent or another governed delivery basis through planning, implementation, verification, and release, with product-specific bindings supplied by profiles.

### Clarified

- Side questions and unrelated informational requests do not pause or stop already-authorized work; execution continues unless a defined stop condition is met.

This is a backward-compatible additive minor release. Existing 1.x work-item, profile, handover, and authority concepts remain available; no mandatory control is weakened.

## 1.3.0 - 2026-07-21

### Added

- Prefer dedicated sub-agent execution and monitoring for long-running tasks while the primary agent continues independent work within the current work item, with no artificial parallel work when all remaining tasks depend on the result.
- Retain primary-agent communication accountability across delegation with declared heartbeats, live-worker checks before status/final responses, immediate terminal reporting, and a prohibition on closing workflows that would strand invisible worker results.
- Require active-task conversation continuity until completion; before completion, allow stopping or pausing only on an explicit user order, required user decision/input, a required Architecture Office decision, or an explicitly specified stop gate.

This is a backward-compatible additive minor release. Existing 1.x work-item, profile, handover, and authority concepts remain available; no mandatory control is weakened.

## 1.2.0 - 2026-07-21

### Added

- Mandatory third-party dependency evaluation covering license and product implications, cost, reliability, safety and privacy, hardware/platform requirements, and active/stale/deprecated/out-of-support status.
- Required concise pros/cons comparison tables when multiple viable dependency options exist.
- Mandatory visible Integrated Mode hat labels on every assistant-authored message.

### Changed

- Dependency approval now binds the evaluated choice and use; material license, cost, data-flow, hardware, support, or dependency-class changes require renewed evaluation.

This is a backward-compatible additive minor release. Existing 1.x work-item, profile, and handover concepts remain available; no mandatory control is weakened.

## 1.1.0 - 2026-07-20

### Added

- Persistent user-defined quality rules, precedence and tier-aware suppression, effective review plans, finding closure, pending immutable baselines, and direction-aware non-regression comparison.
- Canonical containment, binary attestation and secret gates, complete work-order execution authorization, exact release-set validation, committed-tree provenance, and transactional export/release rollback.
- Independent Deep review and systemic analogous-gap evidence contracts.
- Plan-first repository/product onboarding for absent, nearly-empty, and existing projects at Quick, Standard, and Deep depths, with authority-bound approval and no mutation before approval.
- External and bounded pinned project-local binding, update/migration/rollback/removal guidance, abstract four-tier model routing, evidence-backed development binding, and explicit production provider/model approval.
- Safe Integrated/Split transitions, work-duration estimates and material revisions, continuity/full-close selection, batched publication inventories, and three local-first task-tracker semantic fixtures.

### Changed

- New executions use sealed work-order schema 1.1. Historical schema 1.0 remains readable but must be migrated, reapproved, and resealed before execution.
- Stable 1.x release manifests now identify stable maturity instead of contradictory pre-1.0 maturity.

This is a backward-compatible additive and security-strengthening minor release. No mandatory 1.x control is weakened.

## 1.0.1 - 2026-07-20

### Fixed

- Replaced the current-handover contract's Capability-only active-state field with an extensible registered `active_work_item` that represents GOV items, Capabilities, future governed types, or no active item independently from the latest completed Capability.
- Added mandatory independent Architecture boundary-conformance disposition, specific-remediation plus systemic-control obligations, and bounded analogous-gap review when a violation is found.
- Preserved read compatibility for historical handover schema 1.0 while current schema 1.1 fails closed on unregistered work-item types.

This is a backward-compatible correction to the 1.0 contracts, not a new authority model.

## 1.0.0 - 2026-07-20

### Added

- Integrated and Split operating modes with explicit role transitions, sealed work orders, resumable mode-switch handoffs, and semantic Capability/GOV classification.
- Two-tier platform governance, capability preflight, and immediate hard-stop reports for unmet mandatory core requirements.
- Architecture-only acceptance and acceptance-driven archival.

### Changed

- The formerly implicit single-environment capability lifecycle is replaced by a mode/role/state/type model. This is an intentional breaking governance change and therefore the first major release.
- Platform-specific mechanisms move into replaceable profiles; the normative core is platform-neutral.

## 0.2.0 - 2026-07-20

### Added

- Canonical planning backlog, trigger-governed future-work, and append-only planning-history schemas and templates.
- Cross-artifact planning reconciliation tooling, runnable lifecycle fixtures, bootstrap inclusion, and regression tests.

### Changed

- Newly bootstrapped products receive the three canonical planning records. Existing 0.1.0 deployments remain valid and are not rewritten; adoption of planning reconciliation is optional and requires no migration of prior states or paths. The material additive capability makes this a minor release rather than a patch.
- Standalone source publications can run deterministic release packaging from their bound export manifest when the canonical-only export control file is intentionally absent.
- Versioned release-product directories are ignored by default while preserving any already tracked historical release files.

## 0.1.0 - 2026-07-20

### Added

- Standalone Architecture Office and Engineering Agent operating framework.
- Product-profile bootstrap, schemas, templates, examples, validation, and publication tooling.
- Governed source-to-external-repository export with drift detection and manifest-owned staging.
- Canonical temporary-workspace containment for validation, export, bootstrap proof, and package assembly.
- Deterministic ZIP release packaging with content manifests and SHA-256 checksums.

### Changed

- Redistributed the former generic `docs/` collection into architecture, governance, process, repository, session, guide, help, reference, and release owners.
