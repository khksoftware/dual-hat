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
