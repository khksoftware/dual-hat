<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.18.0 Release Notes

Dual Hat 1.18.0 is a minor release. It adds a new required onboarding
entry point, a new architecture decision-review mechanism, and eleven new
governing-principles rules culminating in a capstone Definition-of-Done
requirement that changes how every governed work-item type reaches
closure going forward. Every change is additive and backward-compatible,
but the combination changes framework layout and contracts beyond what a
patch release is scoped to cover -- consistent with this project's
release policy, under which a minor release may change framework
contracts or layout when documented here and in the changelog.

## Single fresh-session entry point

`START_HERE.md` is now the single required entry point for a fresh agent
or chat session to gain full working knowledge of the framework before
touching role-specific guidance, a product's own profile, or any work
item. It sequences the existing foundational documents in the order they
must be read -- README, the operating model, onboarding, bootstrap, the
operating guide together with installation and binding, both role
guide/prompt pairs, and the work-item lifecycle and closure protocols --
replacing an assembled-by-hand reading list. `README.md` points to it near
the top, and `repository/CANONICAL_ENTRYPOINTS.md` gains a first row for
it.

## Isolated design review

`architecture/REASONING_AND_DECISION_REVIEW.md` gains a new isolated
design review mechanism. For a materially consequential, unsettled
architecture, product, workflow, or UX decision, the Architecture Office
may commission two or more isolated participants to independently produce
candidate approaches or critique existing ones -- blind to each other's
identity and output until locked, including an isolated UX-perspective
participant when the decision is user-facing, mirroring the existing
specialist roster's UX inclusion. Unlike the existing hypothesis-blind
three-arbiter protocol, this is not a vote: Architecture alone synthesizes
the unblinded submissions and decides, combines, or rejects among them,
preserving the framework's single-authority invariant.

## Delegation and sub-agent supervision

`governance/VALIDATION_AND_PARALLELISM.md` gains four additive delegation
rules: every delegated sub-agent's messages begin with a brief
role/task description mirroring the primary agent's own role-label
convention; sub-agents default to the Engineering Agent role and its full
rule set unless a sealed work order says otherwise; the delegating agent
supervises rather than trusts -- staying on standby, tracking progress,
and treating sub-agent self-reports as unverified until independently
checked against live evidence, while remaining responsive to the user
without delay; and a question, ambiguity, or materially consequential
decision surfacing in a sub-agent's own work pauses that work and escalates
to the Architecture Office rather than being resolved by the sub-agent
itself.

## Eleven new governing-principles rules

`governance/GOVERNING_PRINCIPLES.md` gains rules 21 through 31:

- **Rule 21** -- a governance change codified mid-session takes effect
  immediately for the rest of that session, including already-active and
  subsequently launched sub-agents, rather than binding only a future
  fresh session.
- **Rule 22** -- before authoring new procedural logic for a workflow the
  framework already governs, an agent checks for an existing canonical
  entry point and uses it, or escalates before building a parallel one.
- **Rule 23** -- an agent resuming across a context compaction, or one
  whose own long-running task never revisited a foundational fact after
  reading it once early on, re-derives its working method or belief from
  current source rather than a stale summary or early, unrefreshed read;
  a report asserting something was verified must state what was actually
  re-checked and when.
- **Rule 24** -- a checkpoint report's completeness claims must cite the
  concrete mechanism used to determine the denominator, not just the
  number.
- **Rule 25** -- finding one defect instance triggers an active search
  for siblings sharing the same root cause, both a literal pattern search
  and an independent abstract-pattern search naming the defect's
  structural shape, preferring a systemic countermeasure over
  instance-by-instance patches; the search and its result must be stated
  in the fix's own report.
- **Rule 26** -- defect remediation follows Red-Green-Refactor: a test
  reproducing the defect that genuinely fails first, then a generalized
  fix searched for siblings, then a refactor into systemic form without
  changing verified behavior. An unchanged passing suite proves only that
  nothing new broke, not that anything was fixed.
- **Rule 27** -- verifying a per-instance generative or evaluative
  mechanism requires comparing output across genuinely different
  instances and treating unexpected sameness as a failure, not only
  confirming per-instance self-consistency.
- **Rule 28** -- a governed ledger-backed projection needs a standing
  reproducibility check confirming the live projection matches what
  replaying the ledger produces, failing loudly rather than merely
  logging on divergence.
- **Rule 29** -- the original task that triggered a rule-25 adjacent
  search is tracked as its own standing obligation, separate from
  whatever adjacent work the search spawned, and stays open until
  independently verified complete.
- **Rule 30** -- a code/content change paired with a governed tracking
  record has exactly one moment of genuine completion: when both halves
  are verified together, in the same check.
- **Rule 31, Definition of Done** -- every governed work-item type must
  have an explicit, criterion-based, mechanically-checkable Definition of
  Done, authored by the Architecture Office before that type's first
  instance opens. The performing entity may exceed but never narrow or
  skip a criterion, and must honestly name any unmet criterion rather than
  misrepresent partial success as full. The recipient of a completed work
  item must independently verify the checklist rather than accept the
  report at face value, and the DoD must be carried explicitly through
  every leg of a handover chain. A type with no DoD yet blocks closure of
  new instances until the Architecture Office defines one; in-flight work
  may continue, and no already-closed instance is retroactively reopened.
  Rule 30 is folded in as this rule's closure-time discipline, and rules
  24 through 28 are named as existing DoD-fragment instances this rule
  generalizes rather than duplicates.

## Documentation note

`README.md` gains a note near its end, added verbatim per explicit
stakeholder instruction: a caution that one particular assistant model
family is more prone than others to drifting away from this framework's
governance and needs regular reminding, described as an innate quality
the framework itself cannot remediate. This note names a specific model,
which is in tension with this project's general practice elsewhere of not
naming specific providers or models in portable source. It is included
here exactly as instructed; the tension is noted for future
reconsideration rather than resolved unilaterally.
