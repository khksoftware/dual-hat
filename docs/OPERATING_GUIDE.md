<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operating Guide

## Roles and change flow

The Architecture Office converts goals into bounded, testable authority and challenges weak mechanisms. The Engineering Agent verifies repository state, inventories consumers and risks, implements the owning-layer correction, validates the complete candidate, reconciles operational surfaces, publishes only as authorized, cleans residue, and reports automatically. Use the [reasoning review](../architecture/REASONING_AND_DECISION_REVIEW.md) and [Engineering Agent prompt](../prompts/ENGINEERING_AGENT_PROMPT.md).

Role-specific application guidance is in the [Architecture Office guide](ARCHITECTURE_OFFICE_GUIDE.md) and [Engineering Agent guide](ENGINEERING_AGENT_GUIDE.md).

Work begins from the active session, roadmap, bounded work order, and owning domain—not archives or previous chat memory. Use [context retrieval](../process/CONTEXT_AND_RETRIEVAL.md) and product-bound [entrypoints](../repository/CANONICAL_ENTRYPOINTS.md). Capabilities follow the [capability lifecycle](../process/CAPABILITY_LIFECYCLE.md); multi-capability phases follow the [phase-run protocol](../process/PHASE_RUN_PROTOCOL.md).

For bounded loading and freshness rules, follow the [task-context retrieval guide](TASK_CONTEXT_RETRIEVAL.md). Runnable standalone examples are in the [command reference](COMMAND_REFERENCE.md).

## Planning and debt

The [planning model](../planning/PLANNING_MODEL.md) separates roadmap, backlog, future triggers, phases, milestones, and capability authorization. [Technical debt](../planning/TECHNICAL_DEBT.md) requires stable ownership, lifecycle events, remediation triggers, validation, and closure evidence. Phase closure reviews test health and debt instead of optimizing for test count.

## Validation and operations

The [validation protocol](../validation/VALIDATION_PROTOCOL.md) covers automated tests, semantic checks, risk-based detached validation, standalone export, safe sharding, evidence, flake handling, and phase-end suite health. The [process watchdog](../validation/PROCESS_WATCHDOG.md) bounds I/O, monitors owned processes, and prevents orphaned scans. Suspicious parallel failures rerun serially; one integration owner reconciles all results.

## Repository, sessions, and closure

Use the [Engineering Blueprint](../repository/ENGINEERING_BLUEPRINT.md) and [repository governance](../governance/REPOSITORY_GOVERNANCE.md) for product/framework/engineering/workspace/archive separation, scan-first migrations, namespace rules, artifact lifecycle, packaging, and generated state. Use the [session/handover protocol](../sessions/SESSION_AND_HANDOVER_PROTOCOL.md) for one current machine/human pair and interruption recovery.

[Conformance](../governance/CONFORMANCE_POLICY.md) is semantic, not a test-count claim. [Publication and closure](../process/PUBLICATION_AND_CLOSURE.md) are forward-only, drift-aware, fully disposed, and accurately reported. Product extensions use [profile composition](../governance/PROFILE_COMPOSITION.md). Bootstrap and examples are described in [Bootstrap](BOOTSTRAP.md); failures are routed in [Troubleshooting](TROUBLESHOOTING.md).
