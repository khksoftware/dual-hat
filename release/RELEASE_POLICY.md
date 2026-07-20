<!-- SPDX-License-Identifier: Apache-2.0 -->

# Release Policy

Dual Hat uses Semantic Versioning. Before 1.0.0, a minor release may change framework contracts or layout when the change is documented in the changelog and release notes; a patch release fixes defects without intentionally breaking the documented minor-line contract. Version 1.0.0 requires an Architecture Office determination that the public framework surface is stable enough for ordinary compatibility expectations.

A release candidate is assembled only from the canonical source allowlist in `export/EXPORT_SOURCES.json`. The source repository, derived Git publication, and downloadable release artifact are distinct products:

- the canonical source is the development authority;
- the external Git repository is a forward-only derived source publication;
- the ZIP is a deterministic user-ready distribution assembled from a named canonical commit.

The ZIP includes framework code, governance, prompts, schemas, templates, examples, tests, and user documentation. Tests remain included because they are the standalone installation and extension-safety proof. It excludes Git metadata, source-repository-only engineering state, external publication markers, credentials, machine-local dependencies, caches, bytecode, and validation residue.

Each ZIP has one top-level directory named `dual-hat-<version>/`. It contains `.dual-hat-release/content-manifest.json` and `.dual-hat-release/SHA256SUMS`. A companion release manifest records the ZIP hash, canonical source commit, external publication commit, and all archive-entry hashes without creating a self-referential hash cycle.

Creating a package does not authorize a Git tag, GitHub Release, public upload, or stable-API claim. Those actions require explicit publication authority.
