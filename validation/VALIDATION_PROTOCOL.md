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

The fingerprint binds base commit, complete candidate tracked-tree identity, changed-path digest, runtime/dependencies, schemas/inventories, protected assets, and profile. Caller path lists are optimization hints, never authority.

## Safe parallel validation

Define the complete validation inventory first. Assign each group exactly once with command, environment, fixtures, writable state, ports, caches, external resources, owner, counts, skips, and log. Parallelize only isolated read-only or independently writable shards. Serialize global ordering, singletons, migrations, same-host retrieval, external publication, and shared mutation. Never hide retries; rerun suspicious failures serially and reconcile one authoritative result.

## Detached and phase-end rules

Apply the detached decision in [Conformance Policy](../governance/CONFORMANCE_POLICY.md). Phase/release closure performs the test-health review in the [Phase-Run Protocol](../process/PHASE_RUN_PROTOCOL.md). Flakes are diagnosed, not normalized; obsolete tests are deleted with rationale; duplicate low-value tests are consolidated; missing semantic checks are added.
