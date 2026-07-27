<!-- SPDX-License-Identifier: Apache-2.0 -->

# Validation Protocol

Validation must prove profile preflight blocks known mandatory gaps, runtime gaps produce hard stops, partial work is safely preserved or rolled back, reporting reaches the user and Architecture Office, switching uses a governed handoff, profiles cannot make core rules optional, and conformance fails while any mandatory rule is unmet.

Testable products require automated unit, integration, regression, schema/contract, and appropriate end-to-end tests. Validation also includes semantic review, repository and dependency checks, documentation, migration, packaging, security, rights, and operator-visible behavior. Tests are owned by the subsystem whose defects they detect.

A test command is evidence only when the intended runner discovers and executes a nonzero expected test count. Importing or directly executing a file that merely defines tests, a successful command reporting zero collected tests, or invoking the wrong framework is not a passing result. Record the runner, collected/executed/pass/fail/skip counts, and treat unexpected zero collection or missing runner support as a validation failure until corrected.

Default to the minimal necessary, risk-proportionate focused subset that credibly validates the changed surfaces, affected contracts and direct consumers, known failure modes, and critical integrations. Do not run a full suite merely because work is reaching handoff or closure. Escalate to broader or full-suite validation only when the blast radius is broad or cannot be bounded confidently, a focused check produces an unexplained failure, an explicit work-order or release policy requires it, or the focused subset cannot provide credible coverage. An explicit mandatory suite remains mandatory until its governing work order or release policy is changed; this default does not waive a declared gate.

## Profiles

- Focused: changed owners and direct consumers during development.
- Integration: affected regressions plus repository, schema, documentation, and dependency checks for the final candidate.
- Full live: the complete governed live suite when an escalation condition or explicit mandatory gate requires it, once per unchanged validation fingerprint.
- Committed tree: clean detached checkout when risk policy requires it.
- Export/standalone: isolated distribution with no source-repository dependency.
- Post-commit/post-push: identity, cleanliness, evidence, and alignment only.

Publication validation is additionally state-specific. Before commit, validate the complete staged index against the current export manifest, inspect the staged path list, scan staged content for likely secrets, and reject unowned or generated/cache artifacts. After commit and before push, validate the exact committed tree against the bound manifest and marker. Product-specific wrappers may add checks but may not replace or weaken these generic gates.

Validation and execution gates must model each input according to its real
lifecycle and packaging class. Version-controlled executable inputs, accepted
reviews, manifests, and immutable plans may require exact committed-tree identity.
Governed runtime data, user state, external databases, secrets, and intentionally
ignored persistence must instead use exact content/version/schema guards through
their owning repository abstraction; a gate must not require such state to be Git
tracked. Every material gate requires at least one production-layout integration
test using the same tracked-versus-runtime arrangement as deployment, plus negative
tests for drift in both classes. An all-fixture layout that accidentally commits
runtime state is insufficient evidence.

State-transition commands classify authoritative state before selecting gates.
Before first mutation, validate current executable inputs against the accepted
pre-execution review. After a committed transition, read-only replay validates the
immutable execution evidence and exact resulting runtime state before consulting
current implementation identity; later maintenance commits must not invalidate
historical evidence or make verified replay impossible. Tests cover both the true
pre-state mutation path and the true post-state replay path through the public
command surface, including drift rejection and proof that replay changes no state.

The fingerprint binds base commit, complete candidate tracked-tree identity, changed-path digest, runtime/dependencies, schemas/inventories, protected assets, and profile. Caller path lists are optimization hints, never authority.

Every hash binding declares its byte policy. Use repository-byte identity for
tracked artifacts whose exact stored bytes are authoritative. A governed text
binding may instead declare UTF-8 without BOM and canonical LF newlines; its
validator reads the worktree file, rejects invalid encoding, BOM, and bare CR,
normalizes CRLF to LF, and hashes the resulting bytes so platform checkout
newlines do not create false drift while substantive worktree changes still
fail. Binary outputs, archives, databases, and release products always use
exact raw bytes. Never validate a mutable worktree input by hashing `git show`
or another committed copy that would hide current drift.

## Temporary workspace containment

Validation orchestration, detached worktrees, export checks, bootstrap proof, package assembly, temporary reports, logs, and subprocess state use `tooling/temporary_workspace.py`. Its default is a unique owner-marked run below the operating-system temporary directory. A profile may supply an absolute alternate root only when it does not overlap the source repository, an author/project/instance workspace, or a repository-sibling workspace. Relative, parent-traversing, and ambiguous caller roots are rejected.

Each run owns only its unique directory. Cleanup executes after success, failure, interruption, and child-process failure, verifies absence, and never removes another active shard. Compact durable evidence is promoted explicitly to a governed evidence surface; raw temporary state is never made durable by leaving it in a workspace. Small in-process unit-test fixtures may call the language runtime's secure temporary-directory primitive directly, but orchestration and reusable framework operations may not invent a second path policy.

## Safe parallel validation

Define the complete validation inventory first. Assign each group exactly once with command, environment, fixtures, writable state, ports, caches, external resources, owner, counts, skips, and log. Parallelize only isolated read-only or independently writable shards. Serialize global ordering, singletons, migrations, same-host retrieval, external publication, and shared mutation. Never hide retries; rerun suspicious failures serially and reconcile one authoritative result.

## Detached and phase-end rules

Apply the detached decision in [Conformance Policy](../governance/CONFORMANCE_POLICY.md). Phase/release closure performs the test-health review in the [Phase-Run Protocol](../process/PHASE_RUN_PROTOCOL.md). Flakes are diagnosed, not normalized; obsolete tests are deleted with rationale; duplicate low-value tests are consolidated; missing semantic checks are added.
