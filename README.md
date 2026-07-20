<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat

Dual Hat is a product-agnostic framework for governed software development through two accountable roles: an Architecture Office that owns intent, boundaries, and acceptance, and an Engineering Agent that owns implementation, validation, publication, and complete exit reporting.

Framework authority is declared by governed publication metadata; never infer it merely from the checkout being viewed. In a standalone distribution, see `docs/PUBLICATION_AND_DRIFT.md`. Product-specific policy belongs in a profile outside the framework source.

## Start here

Use [the quick-start guide](docs/BOOTSTRAP.md) to initialize a neutral product repository. The [repository map](docs/REPOSITORY_MAP.md) explains ownership and dependency direction. The [framework contract](framework/DUAL_HAT_FRAMEWORK.md) is normative; the focused governance contracts explain [repository boundaries](governance/REPOSITORY_BOUNDARIES.md), [validation and sub-agents](governance/VALIDATION_AND_PARALLELISM.md), and [handover, publication, and rollback](governance/HANDOVER_PUBLICATION_AND_ROLLBACK.md).

## Repository map

- `framework/DUAL_HAT_FRAMEWORK.md`: role, reasoning, capability, execution, recovery, and closure rules.
- `governance/`: repository, validation, handover, publication, rollback, and artifact-lifecycle contracts.
- `schemas/`: machine-readable product profile, artifact classification, and export-manifest contracts.
- `templates/`: product-neutral work-order, handover, and conformance templates.
- `docs/`: bootstrap, repository map, operation, and troubleshooting guidance.
- `examples/`: schema-valid neutral product profile.
- `scripts/`: standard-library-only bootstrap and standalone validation tools.
- `export/EXPORT_READINESS.json`: governed source-to-export and exclusion design for deterministic publication.

## License and contributions

Dual Hat code, schemas, templates, prompts, governance, documentation, and first-party examples are licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) and [third-party notices](THIRD_PARTY_NOTICES.md). Contributions intentionally submitted for inclusion are accepted under Apache-2.0 unless explicitly marked otherwise; incompatible, missing, or ambiguous licensing is rejected.
