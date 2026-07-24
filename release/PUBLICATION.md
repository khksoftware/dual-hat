<!-- SPDX-License-Identifier: Apache-2.0 -->

# Export, Publication, and Drift

The canonical framework source may live inside an adopting source repository while a standalone repository is a derived publication. Exact source mapping, structural validation, semantic completeness, licensing, deterministic assembly, idempotence, standalone tests, target drift, and prior marker identity must pass before writing.

A prior manifest defines the owned external file set. Forward publication may add, update, rename, or remove only governed files and must report the change plan before writing. Unknown files or changed governed files fail closed. Publication creates a transparent commit, pushes without force when authorized, fetches, verifies alignment/cleanliness/manifest/marker, and records the receipt outside the generic source when it contains product or remote identity.

## Governed staging and push gate

After applying and validating a forward export, inspect `git status --short` and use the manifest-owned staging command in the [Command Reference](../help/COMMAND_REFERENCE.md). Publication must not use an unbounded staging command such as `git add -A`. The staging gate:

- scans the bounded publication tree while excluding `.git`;
- rejects unowned files, missing governed files, bytecode, `__pycache__`, and common build or tool caches, including ignored residue;
- stages only paths owned by the current manifest and exact governed removals from the prior manifest;
- inspects the resulting staged path list and complete index;
- verifies content hashes, marker-to-manifest binding, and staged content for likely secrets.

Review the reported staged paths before committing. After the transparent commit, run committed-tree verification against the exact commit and review its file count and identity before pushing. Do not push if the committed tree contains an unowned, missing, forbidden, hash-mismatched, or secret-bearing file. After pushing, fetch and verify local/remote alignment and a clean worktree.

If independent development authority is later granted to the external repository, record that governance change explicitly before accepting manual divergence.

## Release packages

The derived source-control publication and a downloadable release are separate publication products. Release content, versioning, exclusions, deterministic layout, checksums, and authorization boundaries are governed by [Release Policy](RELEASE_POLICY.md). A release package is assembled from the canonical source allowlist, never by copying the external checkout. Creating a release-ready local ZIP does not create or imply a tag, hosted release entry, public asset upload, or stability claim.

The canonical product location is `release/v<version>/` within the standalone Dual Hat repository, outside an adopting product repository. The ZIP, release manifest, and checksum stay together there. Before authorization they are local generated products; when repository publication is explicitly authorized, those exact three files may be committed and pushed as a distinct release commit. Version directories remain excluded from source-export, source-drift, and package-input classification so a release cannot ingest itself or masquerade as source publication content.
