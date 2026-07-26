<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

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
