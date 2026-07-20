<!-- SPDX-License-Identifier: Apache-2.0 -->

# Validation and Parallelism

Validation profiles are risk-based:

- focused development validates changed owning layers and direct consumers;
- final integration validates affected regressions, schemas, dependencies, documentation, packaging, and disposition;
- full live validation runs once for a release, major migration, or high-risk candidate fingerprint;
- committed-tree validation runs after commit in a Git-aware isolated worktree;
- export validation runs in a metadata-free standalone tree and never substitutes for committed-tree validation;
- post-publication checks verify only identity, cleanliness, remote alignment, and evidence binding.

The fingerprint includes base commit, complete candidate tree, changed-path digest, runtime/tool versions, material optional dependencies, schemas, and profile identity. Changed paths optimize selection but cannot define the final candidate.

Before sharding, inventory every required group exactly once. Workers receive isolated writable state and deterministic commands. The integration owner records counts, skips, omissions, duplicates, failures, retries, and logs, then centrally reconciles one authoritative result.

All orchestrated writable state uses the canonical temporary-workspace resolver. Every shard receives a unique owner-scoped run directory below an approved operating-system temporary root; repository, author, project, instance, and repository-sibling workspaces are prohibited. A shard cleans only its own directory in guaranteed finalization, and the integration owner verifies no run directory, worktree registration, child process, cache, or raw log remains.
