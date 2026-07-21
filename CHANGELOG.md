<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

All notable changes to Dual Hat are recorded here. The project uses Semantic Versioning; breaking core-contract changes require a major release.

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
