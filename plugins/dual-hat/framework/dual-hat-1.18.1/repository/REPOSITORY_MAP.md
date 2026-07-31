<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository Map

Dual Hat uses responsibility-oriented top-level areas documented in the root README. No descendant repeats `dual-hat` because the root already establishes that namespace. `export/` contains exact source and readiness contracts; it is not a second framework authority.

An adopting repository normally has a product root, `engineering/`, a `workspace/` root excluded from distributable packaging and default discovery regardless of its git-tracking status, and optional vendored/framework metadata. Product runtime cannot import engineering or Dual Hat. Engineering profiles may consume Dual Hat. Archives are excluded from default discovery, tests, context retrieval, and distribution.

First-use onboarding may retain the framework outside the product repository or add one bounded `.dual-hat/binding.json` project footprint after approval. This record pins identity/version/checksum and governance state; it is not a vendored copy of the framework. The synthetic onboarding fixtures live under `fixtures/onboarding/` and contain no private or paid-service data.

Current authority routes through [Canonical Entrypoints](../repository/CANONICAL_ENTRYPOINTS.md) and [Canonical Domain Index](../repository/CANONICAL_DOMAIN_INDEX.md). The machine-readable [framework capability inventory](../repository/FRAMEWORK_CAPABILITY_INVENTORY.json) binds every claimed responsibility to an owning artifact and required support.
