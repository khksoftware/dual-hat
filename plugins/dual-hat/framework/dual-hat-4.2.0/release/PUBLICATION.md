<!-- SPDX-License-Identifier: Apache-2.0 -->

# Export, Publication, and Drift

The canonical source owns only the portable Dual Hat core. A standalone
distribution repository may own disjoint deployment-specific plugin manifests,
wrappers, installation projections, and package artifacts. Portable-core source
must not carry a `plugins/` tree or another standalone deployment artifact;
forward publication preserves those standalone-owned namespaces without
claiming or mutating them.
The portable `CHANGELOG.md` remains a byte-exact canonical-source file.
Standalone-only deployment history is retained in standalone-owned release
notes or provenance rather than merged into the portable changelog.

The canonical framework source may live inside an adopting source repository while a standalone repository is a derived publication. Exact source mapping, structural validation, semantic completeness, licensing, deterministic assembly, idempotence, standalone tests, target drift, and prior marker identity must pass before writing.

A prior manifest defines the owned external file set. Forward publication may add, update, rename, or remove only governed files and must report the change plan before writing. Unknown files or changed governed files fail closed. Publication creates a transparent commit, pushes without force when authorized, fetches, verifies alignment/cleanliness/manifest/marker, and records the receipt outside the generic source when it contains product or remote identity.

## Governed staging and push gate

After applying and validating a forward export, inspect `git status --short` and use the manifest-owned staging command in the [Command Reference](../guides/COMMAND_REFERENCE.md). Publication must not use an unbounded staging command such as `git add -A`. The staging gate:

- scans the bounded publication tree while excluding `.git`;
- removes and reports only recognized contained Python bytecode/cache residue before staging, then rejects unowned files, missing governed files, any remaining cache content, and common build or tool caches, including ignored residue;
- stages only paths owned by the current manifest and exact governed removals from the prior manifest;
- inspects the resulting staged path list and complete index;
- verifies content hashes, marker-to-manifest binding, and staged content for likely secrets;
- refuses a publication whose vendored plugin bundle is not current with the shipped framework version.

## Vendored version currency

A vendored plugin bundle must declare the version the publication ships, by exact equality in both directions: a bundle ahead of the shipped version is refused on the same terms as one behind it.

A publication carrying a bundle payload must also carry `release/VERSION.json`. That file is the authority the bundle is checked against, and a publication that omits it is refused rather than passed unchecked. The same publication must carry the bundled framework tree for the shipped version, and that tree's own `release/VERSION.json` must declare that same version. A superseded snapshot must not remain beside the current one.

The payload must bind the shipped version in the version it declares, in the framework root it points at, and in the archive it names. Every deployment-form plugin manifest inside the bundle root must declare it too; those manifests are discovered by their `<bundle root>/<form>/plugin.json` shape rather than enumerated, so a deployment form added later is covered the day it appears and no agent platform is named in normative core. A manifest outside the bundle root is not reached by this rule.

The payload must carry no token naming a framework version other than the shipped one, in any field, prose included. A payload's narrative description of its own origin is an authority like any other field: a bundle whose machine-readable fields are all correct while its generation note still describes an earlier extraction is stale and is refused, because the defect this exists to catch is a generator that rebinds what it knows about and leaves the rest behind. A token counts only where it names the framework — `dual-hat-X.Y.Z` or `Dual Hat X.Y.Z` — so a payload stays free to carry a schema version, a minimum runtime version, or a cited release note. Matching bare digits instead would refuse a current bundle and report it as a stale one, sending the operator to hunt a bundle that does not exist; a gate whose message misdescribes its own cause is worse than no gate.

Vendored content declaring a core version is refused when it disagrees, and that check is narrower than the sentence sounds. It reads only `.json` files under the bundle root, only a key named exactly `dual_hat_core_version`, and only a value that is exactly three numeric segments. A constraint expression such as `>=X.Y.Z`, a two-segment or pre-release version, and a stale version stated in bundled Markdown or YAML or in a manifest description are all outside it and publish today. That limit is stated here so no reader takes broader coverage on trust; widening the walk is a change to this rule, not an implementation detail.

Refusing a publication on the content of a standalone-owned namespace is consistent with preserving that namespace without claiming or mutating it. This rule reads that content and declines to publish; it never rewrites it, and the correction stays the owning repository's to make.

Currency is enforced at the publication gate, not only by a test. The marketplace install path is documented and supported, so a stale bundle ships whatever governance or continuity defects the current framework has already fixed, to every adopter installing through it. A detector that reports a stale bundle without blocking leaves shipping it a matter of whether someone read the output; the staging and committed-tree gates refuse it outright, evaluated against the content actually being published rather than the worktree.

Review the reported staged paths before committing. After the transparent commit, run committed-tree verification against the exact commit and review its file count and identity before pushing. Do not push if the committed tree contains an unowned, missing, forbidden, hash-mismatched, or secret-bearing file. After pushing, fetch and verify local/remote alignment and a clean worktree.

If independent development authority is later granted to the external repository, record that governance change explicitly before accepting manual divergence.

## Release packages

The derived source-control publication and a downloadable release are separate publication products. Release content, versioning, exclusions, deterministic layout, checksums, and authorization boundaries are governed by [Release Policy](RELEASE_POLICY.md). A release package is assembled from the canonical source allowlist, never by copying the external checkout. Creating a release-ready local ZIP does not create or imply a tag, hosted release entry, public asset upload, or stability claim.

The canonical product location is `release/v<version>/` within the standalone Dual Hat repository, outside an adopting product repository. The ZIP, release manifest, and checksum stay together there. Before authorization they are local generated products; when repository publication is explicitly authorized, those exact three files may be committed and pushed as a distinct release commit. Version directories remain excluded from source-export, source-drift, and package-input classification so a release cannot ingest itself or masquerade as source publication content.
