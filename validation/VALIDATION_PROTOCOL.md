<!-- SPDX-License-Identifier: Apache-2.0 -->

# Validation Protocol

Testable products require automated unit, integration, regression, schema/contract, and appropriate end-to-end tests. Validation also includes semantic review, repository and dependency checks, documentation, migration, packaging, security, rights, and operator-visible behavior. Tests are owned by the subsystem whose defects they detect.

## Profiles

- Focused: changed owners and direct consumers during development.
- Integration: affected regressions plus repository, schema, documentation, and dependency checks for the final candidate.
- Full live: the complete governed live suite once per unchanged validation fingerprint.
- Committed tree: clean detached checkout when risk policy requires it.
- Export/standalone: isolated distribution with no source-repository dependency.
- Post-commit/post-push: identity, cleanliness, evidence, and alignment only.

Publication validation is additionally state-specific. Before commit, validate the complete staged index against the current export manifest, inspect the staged path list, scan staged content for likely secrets, and reject unowned or generated/cache artifacts. After commit and before push, validate the exact committed tree against the bound manifest and marker. Product-specific wrappers may add checks but may not replace or weaken these generic gates.

The fingerprint binds base commit, complete candidate tracked-tree identity, changed-path digest, runtime/dependencies, schemas/inventories, protected assets, and profile. Caller path lists are optimization hints, never authority.

## Temporary workspace containment

Validation orchestration, detached worktrees, export checks, bootstrap proof, package assembly, temporary reports, logs, and subprocess state use `tooling/temporary_workspace.py`. Its default is a unique owner-marked run below the operating-system temporary directory. A profile may supply an absolute alternate root only when it does not overlap the source repository, an author/project/instance workspace, or a repository-sibling workspace. Relative, parent-traversing, and ambiguous caller roots are rejected.

Each run owns only its unique directory. Cleanup executes after success, failure, interruption, and child-process failure, verifies absence, and never removes another active shard. Compact durable evidence is promoted explicitly to a governed evidence surface; raw temporary state is never made durable by leaving it in a workspace. Small in-process unit-test fixtures may call the language runtime's secure temporary-directory primitive directly, but orchestration and reusable framework operations may not invent a second path policy.

## Safe parallel validation

Define the complete validation inventory first. Assign each group exactly once with command, environment, fixtures, writable state, ports, caches, external resources, owner, counts, skips, and log. Parallelize only isolated read-only or independently writable shards. Serialize global ordering, singletons, migrations, same-host retrieval, external publication, and shared mutation. Never hide retries; rerun suspicious failures serially and reconcile one authoritative result.

## Detached and phase-end rules

Apply the detached decision in [Conformance Policy](../governance/CONFORMANCE_POLICY.md). Phase/release closure performs the test-health review in the [Phase-Run Protocol](../process/PHASE_RUN_PROTOCOL.md). Flakes are diagnosed, not normalized; obsolete tests are deleted with rationale; duplicate low-value tests are consolidated; missing semantic checks are added.
