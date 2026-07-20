<!-- SPDX-License-Identifier: Apache-2.0 -->

# Changelog

All notable changes to Dual Hat are recorded here. The project uses Semantic Versioning; breaking core-contract changes require a major release.

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
