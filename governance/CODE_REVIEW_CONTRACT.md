# Architecture Code Review Contract

Every Engineering handoff classifies its change as behavior-affecting, documentation/inert-data-only, mixed, or uncertain and cites the changed paths and their behavioral reach. Runtime source, scripts, generators, validators, schemas and configuration consumed by software, automation, dependencies, CI, security policy, repository mutation, publication, and release logic are behavior-affecting regardless of extension. An uncertain classification defaults to review. Architecture verifies the classification independently.

Architecture review is conditional but independent. Passing tests and Engineering self-review are evidence, not substitutes. Architecture examines the sealed work order, diff and final source, relevant tests, dependencies, generated and local effects, failure and cleanup paths, repository and remote state, effective quality-rule plan, and boundary conformance.

When material acceptance depends on genuinely distinct specialist judgments,
such as architecture, user experience, security, accessibility, data, or
domain correctness, use separate isolated read-only reviewers when the
available environment supports them and the added independence is
proportionate. Each reviewer receives the same relevant primary evidence and
scope boundary but not another specialist's conclusions. The Architecture
Office integrates, deduplicates, and dispositions the reports afterward.
Closely coupled or routine low-risk work does not require multiple reviewers;
do not turn specialist separation into ceremony when one bounded independent
review is sufficient.

Architecture/Design, UX, and QA form a reusable base roster, not a default
attendance list. Compose the smallest roster that adds distinct detection value
from the candidate's actual failure axes. Architecture/Design challenges system
boundaries, integration, extensibility, and maintainability. UX challenges
author workflows, information architecture, accessibility, presentation, and
recovery behavior. QA challenges acceptance behavior, state transitions,
failure paths, migrations, and releases. Add security, privacy, data,
accessibility, or domain specialists when those judgments are material and not
already covered independently. Omit a specialty that adds no distinct judgment;
the roster does not create mandatory gates for ordinary work.

A lane used for review is owned exactly as any other is, under
[Validation and Parallelism](VALIDATION_AND_PARALLELISM.md); review adds no
exception to it.
Specialists inspect primary evidence and return isolated read-only findings;
they do not concurrently edit the candidate, another specialist's report, or
the shared disposition. Architecture alone integrates, deduplicates, and
dispositions the findings.

Every independent specialist takes a bounded falsification-oriented posture:
actively seek disconfirming primary evidence, challenge unsupported claims and
happy-path assumptions, and exercise relevant failure paths. This is not a
license to invent hypothetical defects, expand the approved scope, or pursue
unrelated hardening.

Independent specialists and delegated agents are also subject to the
correction-to-control loop in
[Governing Principles](GOVERNING_PRINCIPLES.md). When their own error,
omission, or inaccurate claim is identified, they must correct the instance,
generalize the failure mode, identify the owning cause, apply a proportionate
reusable countermeasure, and report directly analogous current-session impact.
Architecture owns the loop's mandatory independent adversarial review of the
countermeasure before defect closure; the implementing role cannot approve its
own prevention or detection repair.

External-source scope restrictions are a mandatory prospective independent
review class. Before a proposed discovery stop, sampling substitution,
source/media exclusion, or ingestion filter is applied, a sealed reviewer
independent of the proposing Architecture or Engineering role approves or
rejects it from primary evidence. The finding binds the affected population,
selection rule, evidence, blind spots, alternatives, and item-level or
population-level disposition. Batch review is permitted only when every item
and applied rule remains traceable.

## Population before findings

An independent review establishes its population before it writes a finding.
The population is enumerated from the subject itself: its units, its tests, the
clauses of its authorizing instrument, and every previously recorded finding
still undispositioned within scope. Each enumerated member receives an explicit
disposition. A review that takes its population from a previous round's
findings can only confirm or extend that round's frame, and cannot answer how
much of the subject remains unexamined.

Every review reports its denominator: what was enumerated, what was inspected,
what was sampled and under what rule, and what was never opened. A portion that
could not be inspected is reported as unchecked. Unchecked is an absence of
evidence, and is never reported, aggregated, or summarized as a clean result. A
review that cannot establish its population reports that as its first finding
rather than proceeding against an unstated one.

A finding names the class it belongs to and not only the instance that revealed
it, and the repair it authorizes takes its scope from the review's population
rather than from the artifact list the finding happens to name. Sibling
correction is separately required of every accepted correction under
[Reasoning and Decision Review](../architecture/REASONING_AND_DECISION_REVIEW.md);
what this contract adds is where the scope of a repair comes from.

Every repair reports what it now permits that it did not permit before, and
exercises that explicitly. A repair verified only against the cases its own
finding enumerated establishes that those cases are closed, and establishes
nothing about what the repair opened.

Review rounds are bounded, and the bound is declared before the round runs.
Where a confirming round returns blocking findings, the failure to converge is
itself a reportable outcome, returned to the deciding authority rather than to
a further repair. Successive rounds that each close the artifacts a finding
named, while a later round finds the same defect in artifacts nobody named, are
evidence about the scoping of the repairs rather than about the quantity of
defects remaining.

Cost pressure, a narrow remaining budget, or a preference for the smallest
immediate patch must not narrow a repair to the latest finding while sibling
classes in the established population remain undispositioned. Optimize for
total convergence: inspect and repair the complete class, its sibling classes,
and their mapped population before the next confirming review. The relevant
cost is the expected total of repair plus review rounds, not the size or price
of the next local correction. A budget that cannot support the complete
population returns to the deciding authority; it does not authorize a cheaper
piecemeal review loop.

### Executable preservation and review-assurance checks

For a complete-object repair with mechanically extractable contracts, use
`tooling/review_assurance.py` before commissioning the confirming review.
Its basis is separate from the candidate: primary-source byte bindings,
the predecessor's complete contract inventory, explicit replacements with
before hashes and decision authority, semantic obligations, and declared
transition writes and invariant dependencies. An adapter extracts candidate
facts from the actual artifact; it must not copy expected facts into the
candidate evidence or regenerate the predecessor inventory from the repair.

The mechanism refuses unexplained contract loss, changes or additions;
duplicates keyed by semantic obligation rather than label or wording;
unaccounted predecessor obligations; and missing transition/invariant pairs
derived from intersecting writes and reads. Every required observation has a
bound witness. Scope, authorization and the meaning of equivalence remain
Architecture judgments, explicitly exposed in the basis, not judgments a
hash or a string comparison can make.

Run the same checker against a valid control and systematically damaged
copies using `--falsify`. Deleted contract units, changed layouts, omitted
obligations, renamed duplicate cases, missing interactions and observations,
and stale basis bindings must refuse. Record a missed mutation as failure of
the assurance mechanism, not as an additional clean test. Language-specific
or behavioral mechanisms also need defect-sensitive executable witnesses;
phrase presence is not evidence that the described behavior exists.

Evidence-only mutation cannot detect an extractor that never reads a contract.
Use `falsify_source_adapter` with the real extraction and admission functions to
mutate primary source bytes as well: remove complete units and individual clauses,
and change supported layouts/behavioral clauses. Include a syntactically valid
mutation so parser failure alone cannot stand in for detection. An extractor that
copies expected facts must fail this exercise. Empty, duplicate or unapplied
mutations and harness errors are failed proofs, never successful detections.

`markdown_contract_units` provides exact section/preamble preservation, including
behavioral prose, with fenced-block handling and duplicate-section refusal. Its
byte preservation proves that reviewed wording survives; it does not prove the
behavior that wording specifies. Bind the independent source basis and explicit
changes before generation; do not reconstruct expectations from generated output.

This is a read-only library and CLI, not an automatically armed hook. A
consumer's builder or acceptance path must invoke it and stop on failure;
merely shipping the source or writing a receipt establishes no enforcement.
For an Architecture-accepted Deep baseline created under Dual Hat 5.2.0 or later,
`quality_review.validate_baseline`
requires the deep-review plan, assurance basis and assurance evidence and sends
them through the actual validators. The consumer checks presence and internal
consistency, and binds the deep-review plan's `subject_sha256` to the
baseline's own `governed_state_binding.binding_hash`, case-insensitively, so a
plan computed for a different repository state is refused even when it is
otherwise well-formed; the assurance basis is not yet bound to that same
subject, which remains open. A helper-only test is insufficient: tests
must remove or corrupt each input through that acceptance entry point and prove
that accepted state is unavailable. Earlier immutable accepted baselines retain
their historical validation semantics; comparison does not retroactively erase
evidence by applying a newer acceptance prerequisite.
Independent reviewers inspect the extracted populations and dependency model
as well as the result, because an omitted requirement can be absent from both
the basis and candidate. Structural Green is not semantic acceptance, and
declared witnesses are not claims that future implementation tests ran.

Command: `python tooling/review_assurance.py <basis.json> <evidence.json> --falsify`.
The input contract and mutation mechanism live in that module; adapters keep
product names, domain rules and fixture populations outside the framework.

### Deep complete-object review: prove chains, not corresponding prose

Before an expensive or externally commissioned complete-object review, the
candidate author does not approve its own readiness merely because every known
finding has a paragraph and every paragraph has a proposed test. That pattern
correlates design, audit and tests around the same mistaken premise. A separate
local pre-review freezes the candidate and challenges each material claim as a
complete seven-link chain:

1. **authority** -- the current decision, including what it supersedes and when
   it becomes effective;
2. **producer** -- the concrete component or role that creates the fact;
3. **representation** -- exact object, primitive/nested schema, canonical bytes,
   hash and identity rules;
4. **transition** -- the only state edge the fact may open, including temporal
   order and no-op/pending behavior;
5. **consumer** -- the named component or person and real interface that uses or
   receives it;
6. **failure/recovery** -- every partial side-effect boundary, timeout,
   cancellation, retry prohibition and degraded result; and
7. **evidence** -- a source-backed positive control and disconfirming witness at
   the real seam.

An empty or abstract link -- “existing channel,” “the schema is closed,” “the
timeout is bounded,” “the caller supplies provenance” -- is a finding, not a
placeholder an implementer may fill. Claims about executable behavior are
checked against the selected source path, not against another candidate
document. Fake clocks prove arithmetic, not killability of blocking I/O. A hash
or local path proves identity or location, not delivery to its consumer.

The pre-review must also search beyond encountered findings. It explicitly
dispositions the current deep-review hazard population: authority temporality
and circular gates; producer/consumer delivery; canonical representation;
source/runtime contradiction; blocking-I/O killability; the cross-product of
partial writes and recovery; identity provenance and relabelling; resource
amplification and content encoding; time-of-check/time-of-use races;
environment, dependency and platform behavior; privacy in logs, retention and
crash artifacts; reviewer contamination and common-mode reasoning; population
denominators and exclusions; measurement/cost basis; compatibility, migration
and versioning; substantive human projection versus its machine source;
evaluation-artifact fitness and post-result tuning; external control-plane
reachability, revocation and receipt provenance; frozen-package execution side
effects and transitive imports; authority revocation during an external pause;
clock-domain expiry across restart; hostile-output renderer injection; and tool-
binary/parser supply-chain drift. `not_applicable` requires a subject-specific basis;
silence is not a disposition. This list is a mandatory search floor, never a
claim that unknown failure classes cannot exist.

For each content or provenance filter, use metamorphic attacks: place forbidden
material in every mutable allowed carrier, relabel a forbidden carrier as each
allowed role, and retain a legitimate-overlap positive control. Never subtract
the candidate being tested from its own negative population. For every action
that produces more than one durable object, enumerate the power set of valid
partial publication states or give a justified equivalence partition; prove
that paid, destructive or author-owned evidence cannot be stranded. For every
external or blocking operation, distinguish a local timeout notification from
termination of the work and prove the latter at a real local seam.

The reviewer roster is selected by distinct detection value. A deep object whose
acceptance spans architecture, end-user/domain value and source/test assurance
normally uses those three isolated lenses. Each receives the same frozen bytes
and this protocol, not sibling conclusions. Ambient memory or context that
leaks a prior verdict is disclosed as contamination; the seat either restarts
clean or treats it as untrusted and derives every finding from the frozen
population. Report destinations are pre-resolved destinations anchored to a
declared root, declared before review--never a path that inherits an unknown
working directory. The supervisor verifies each is outside every protected/shared checkout before
briefing, then copies terminal bytes into the governed candidate only after all
seats finish. Reports are persisted byte-exact immediately, so session loss or
working-directory drift cannot turn a verdict into chat reconstruction or
mutate another lane.

The frozen evidence directory itself is a no-write surface. Executable checker
or test bytes are copied by the supervisor into a separately hashed writable
execution directory; Python runs with bytecode and test-cache writes disabled.
Every transitive import required by the claimed acceptance consumer is a
manifested member. The reviewer re-verifies exact inventory and every member
after admission tooling and again before terminal verdict. A collection or
import failure, an undeclared cache file, or any member drift is failed custody,
not a partial Green. The report/progress directories remain outside the package.

Claims about external seats, UI delivery, custody brokers, schedulers or other
platform capabilities name the real producer interface and bind its returned
receipt. Local code may validate/import such a receipt but cannot manufacture
reachability or visibility. A test fake proves the import contract only; a
separately governed real-seam acceptance action proves the platform path.

Where a held-out source, oracle, benchmark or evaluation fixture carries the
substantive discriminator, byte identity and non-exposure do not establish
fitness. Before spend or release, a content-aware role independent of the
artifact author and target result applies a closed neutral admission profile;
oracle/challenge material is assessed by a distinct role. Their reports bind
exact artifact/profile identities, limitations and rejection behavior, and the
roles do not later grade the target output.

`deep_review_plan_failures()` in `tooling/review_assurance.py` supplies a
product-neutral admission check for this review-plan accounting and is mandatory
on the accepted Deep-baseline path from 5.2.0. It
requires the seven links, source anchors, positive/negative cases, reviewer
separation facts and every hazard disposition. It does not decide whether the
claims are true, whether the selected source anchors are sufficient, or whether
the hazard floor is complete. Structural Green remains only permission to start
the independent review.

## Risk-proportionate tiers

- Light: localized, narrow, low-risk behavior. Inspect the diff, clarity, established patterns, obvious correctness/error/security/lifecycle hazards, test relevance, duplication, dead code, and sealed scope.
- Standard: ordinary behavior or tooling. Add principal and degraded paths, cleanup/rollback, architecture, input/path handling, dependencies, compatibility, data and shared-state effects, realistic negative tests, security, and boundaries.
- Deep: authentication, credentials, authorization, untrusted or private input, destructive operations/migrations, cross-repository mutation, concurrency/coordination, sandbox/plugin execution, external dependency loading, security/privacy enforcement, or externally distributed systems after rollout activation. Prefer a fresh independent read-only reviewer and record the mechanism.

Internal publication or release work does not automatically require Deep review. It still receives the proportionate Light or Standard review plus deterministic generation, manifest/checksum, secrets, boundary, stale-file, remote, dependency, cleanup, and publication-authority checks. An author statement that an initial public, pilot, beta, customer, collaborator, or other external-user rollout is being prepared activates separately governed Deep review of externally relevant release, installation, update, distribution, onboarding, security, privacy, licensing, and recovery paths.

Architecture assesses correctness; architectural fit; maintainability; security; privacy, rights, and retention; dependencies and supply chain; failure, rollback, and recovery; concurrency/shared state; migration and compatibility; test relevance and blind spots; repository hygiene; and boundary conformance. Material defects require both a specific repair and the smallest proportionate systemic control when the failure class can recur.

## Findings and acceptance

Each finding records a stable ID, tier, applied rule and source, effective precedence, paths, category, severity, evidence, impact, recommendation, disposition, owner, closure evidence, and analogous-gap scope. Critical identifies exploitable, corrupting, rights/privacy, unauthorized, or mandatory-boundary failure. High is substantial risk requiring correction. Medium normally requires remediation, explicit Architecture debt, or an applicable user disposition. Low is bounded improvement; Informational is optional observation.

Unresolved Critical and High findings block acceptance. Medium findings block until remediated, validly suppressed, or recorded as accepted debt. Low and Informational findings may be documented as non-blocking. A finding produced solely by a discretionary rule that the user validly suppresses is not a failure. Non-waivable violations always block.

Before final disposition, Architecture rechecks the rule-source fingerprint. A material mid-review change invalidates and reruns affected portions; unrelated changes are recorded for the next review. Every result binds the rule-set revision and effective-plan hash it used.
<!-- SPDX-License-Identifier: Apache-2.0 -->
