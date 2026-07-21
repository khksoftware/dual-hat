<!-- SPDX-License-Identifier: Apache-2.0 -->

# Release Policy

Dual Hat uses Semantic Versioning. Before 1.0.0, a minor release may change framework contracts or layout when the change is documented in the changelog and release notes; a patch release fixes defects without intentionally breaking the documented minor-line contract. Version 1.0.0 requires an Architecture Office determination that the public framework surface is stable enough for ordinary compatibility expectations.

A production publication claim requires fresh remote evidence immediately before and after publication. The fetch and push endpoints are canonicalized independently and must resolve to the approved host, namespace, and repository even when they use different transports. Cached tracking refs and a successful push exit code are insufficient. Local HEAD, cached upstream, freshly queried remote branch, committed tree, export manifest, publication marker, release manifest, and checksums must reconcile exactly; credentials embedded in endpoint URLs are never retained in evidence. An unavailable or ambiguous remote blocks publication rather than falling back to cached state.

A release candidate is assembled only from the canonical source allowlist in `export/EXPORT_SOURCES.json`. The source repository, derived Git publication, and downloadable release artifact are distinct products:

- the canonical source is the development authority;
- the external Git repository is a forward-only derived source publication;
- the ZIP is a deterministic user-ready distribution assembled from a named canonical commit.

The ZIP includes framework code, governance, prompts, schemas, templates, examples, tests, and user documentation. Tests remain included because they are the standalone installation and extension-safety proof. It excludes Git metadata, source-repository-only engineering state, external publication markers, credentials, machine-local dependencies, caches, bytecode, and validation residue.

Canonical release products belong to the standalone Dual Hat repository. Each versioned ZIP and its companion manifest and checksum are written under `release/v<version>/` in that repository, outside any adopting product repository. Versioned release directories are ignored by default and remain local generated products unless explicit release-publication authority permits an exact three-file release set to be force-added, committed, and pushed separately from the manifest-owned source publication. Previously tracked release products remain historical source-repository facts and are not rewritten by this default. Release products are never recursive inputs to the canonical source allowlist. An adopting product's engineering space may retain compact conformance and publication evidence that points to them, but it does not own or contain the Dual Hat distributable.

Each ZIP has one top-level directory named `dual-hat-<version>/`. It contains `.dual-hat-release/content-manifest.json` and `.dual-hat-release/SHA256SUMS`. A companion release manifest records the ZIP hash, canonical source commit, external publication commit, and all archive-entry hashes without creating a self-referential hash cycle.

Creating a package does not authorize a repository commit, source-control tag, hosted release entry, public upload, or stable-API claim. Each action requires explicit publication authority. A repository release commit must contain only the ZIP, its release manifest, and its checksum; package validation and staged-path inspection must pass before push.
