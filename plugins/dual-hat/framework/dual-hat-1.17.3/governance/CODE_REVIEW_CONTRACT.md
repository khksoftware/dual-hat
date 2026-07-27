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

During parallel or shared mutation, every shared artifact lane used for review
has one active writer at a time and one integration owner. Trivial serial work
uses its primary owner implicitly; checkpointed reassignment requires the prior
writer to be quiescent and partial state to be handed off.
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
[Process Proportionality](PROCESS_PROPORTIONALITY.md). When their own error,
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
