<!-- SPDX-License-Identifier: Apache-2.0 -->

# Capability Lifecycle Compatibility

A capability is the smallest coherent authorized product change that can be implemented, validated, published, reversed, and reported as one accountable unit. Independently bounded framework/governance changes use GOV identities. New work follows [Capability and GOV Work-Item Lifecycle](WORK_ITEM_LIFECYCLE.md); this sequence remains compatible for existing capability records. Multi-capability runs preserve separate gates and commits unless the work order explicitly justifies another rollback model.

## Sequence

1. Verify branch, remotes, worktrees, current authority, protected assets, dependencies, and authorization.
2. Interpret the objective, durable goal, scope, exclusions, assumptions, ambiguity, risks, and stop gates.
3. Inventory affected artifacts, consumers, writers, analogues, transients, and validation groups.
4. Implement the simplest coherent owning-layer repair.
5. Run focused checks during development; repair defects and invalidate affected evidence.
6. Reconcile documentation, planning, debt, session, handover, and artifact disposition.
7. Run the declared final validation profile and any required committed-tree validation.
8. Commit transparently, publish only when authorized, verify alignment, and report automatically.

Stop before mutation on unexplained drift, conflicting authority, missing authorization, protected-state mismatch, or a material stakeholder decision. During implementation, stop only when safe autonomous repair cannot resolve the issue inside scope. Never treat a checkpoint, partial commit, or generated report as closure.

Parallel read-only work is encouraged when ownership is explicit and orchestration cost is justified. Shared-state mutation, migration, release, and external publication remain centrally serialized.
