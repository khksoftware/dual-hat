<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository Map

Dual Hat uses responsibility-oriented top-level areas documented in the root README. No descendant repeats `dual-hat` because the root already establishes that namespace. `export/` contains exact source and readiness contracts; it is not a second framework authority.

An adopting repository normally has a product root, `engineering/`, ignored `workspace/`, and optional vendored/framework metadata. Product runtime cannot import engineering or Dual Hat. Engineering profiles may consume Dual Hat. Archives are excluded from default discovery, tests, context retrieval, and distribution.

Current authority routes through [Canonical Entrypoints](../repository/CANONICAL_ENTRYPOINTS.md) and [Canonical Domain Index](../repository/CANONICAL_DOMAIN_INDEX.md). The machine-readable [framework capability inventory](../repository/FRAMEWORK_CAPABILITY_INVENTORY.json) binds every claimed responsibility to an owning artifact and required support.
