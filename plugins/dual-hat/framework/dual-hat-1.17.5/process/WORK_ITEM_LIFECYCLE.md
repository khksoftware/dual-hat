<!-- SPDX-License-Identifier: Apache-2.0 -->

# Capability and GOV Work-Item Lifecycle

New Capabilities and GOV items use the shared mode/role/state contract in [Operating Modes](../architecture/OPERATING_MODES.md). Existing archived records remain valid under their historical schemas.

Capability and GOV are the built-in registered types, not a closed schema enum. A future type such as `defect` is added through `governance/WORK_ITEM_TYPE_REGISTRY.json` with a governed identity pattern, semantic owner, classification rule, lifecycle compatibility decision, documentation, and tests. Consumers accept registered identifiers generically and reject unregistered ones; extensions cannot blur existing Capability/GOV semantics.

## Sealing

Before Engineering, persist the identifier/type, title, scope, exclusions, assumptions, stop gates, repositories/paths, mutation and destructive authority, validation, publication, approval state/time, and canonical content hash. Hash canonical content excluding the hash field. Material change returns to Architecture for revision, reapproval, and resealing; history is append-only. Ambiguous approval or a stale hash never authorizes mutation.

## Completion, review, and archival

Engineering completion moves to Architecture review, not acceptance. `accepted` archives. `accepted_with_follow_up` archives only when follow-up is explicitly non-blocking and independently recorded. `remediation_required` stays active. Deterministic archival preserves approved intent, evidence, disposition, hashes, publication references, and non-blocking follow-up pointers; relocates the work item's entire active working or tracking location, as a whole rather than only through per-artifact disposition of its contents, to the designated archive location; removes other obsolete active packages; retains only a minimal active locator; and cannot become a runtime dependency.

## Failure and recovery

Context loss reloads canonical state rather than relying on memory. Engineering interruption reaches a safe pause or records partial mutation and recovery steps. Blocked and aborted runs produce reports; Architecture never fabricates missing evidence. Missing snapshot or ignored state is an explicit limitation. Conflicting mode state, dirty transition, stale order, stale remote, incomplete report, failed archival, or failed publication blocks the affected transition. Inability to obtain independent review is disclosed and may use structured adversarial review when proportionate.

`blocked` is a governed lifecycle state, not a synonym for slow, waiting,
recoverable, or incomplete work. Enter it only at a permitted blocked boundary
when no safe in-scope action remains and the applicable blocked-state threshold
or work-order gate is satisfied. The transition records attempted work, the
exact obstacle, required capability/decision/external change, preserved state,
cleanup, recommended escalation, owner, and precise re-entry condition.
Blocked work is neither accepted nor archived. When the condition changes,
Architecture or the authorized controller returns it to the compatible active
state from the recorded checkpoint; it does not fabricate completion. `aborted`
requires explicit authority and a terminal preservation/disposition decision.
