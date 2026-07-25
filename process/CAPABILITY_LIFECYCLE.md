<!-- SPDX-License-Identifier: Apache-2.0 -->

# Capability Lifecycle Compatibility

A capability is the smallest coherent authorized product change that can be implemented, validated, published, reversed, and reported as one accountable unit. Independently bounded framework/governance changes use GOV identities. New work follows [Capability and GOV Work-Item Lifecycle](WORK_ITEM_LIFECYCLE.md); this sequence remains compatible for existing capability records. Multi-capability runs preserve separate gates and commits unless the work order explicitly justifies another rollback model.

## Sequence

1. Verify branch, remotes, worktrees, current authority, protected assets, dependencies, and authorization.
2. Interpret the objective, durable goal, scope, exclusions, assumptions, ambiguity, risks, and stop gates.
3. Inventory affected artifacts, consumers, writers, analogues, transients, and validation groups.
4. Optimize the execution-ready plan proportionately for value order, sequence,
   parallelism/resources, incremental checkpoints, evidence reuse, and cheaper
   equivalent controls; obtain sealed independent Architecture optimization
   review only when scale, complexity, risk, or irreversibility justifies it.
5. Implement the simplest coherent owning-layer repair.
6. Run focused checks during development; repair defects and invalidate affected evidence.
7. Reconcile documentation, planning, debt, session, handover, and artifact disposition.
8. Run the declared final validation profile and any required committed-tree validation.
9. Commit transparently, publish only when authorized, verify alignment, and report automatically.

Stop before mutation on unexplained drift, conflicting authority, missing authorization, protected-state mismatch, or a material stakeholder decision. During implementation, stop only when safe autonomous repair cannot resolve the issue inside scope. Never treat a checkpoint, partial commit, or generated report as closure.

Questions and asides run concurrently with authorized execution unless their answers genuinely block progress. Answer them, name the concrete active or immediately resumed step, and continue milestone reporting; the end of that answer is not a lifecycle transition or pause.

Parallel read-only work is encouraged when ownership is explicit and orchestration cost is justified. Shared-state mutation, migration, release, and external publication remain centrally serialized.

Research and similar evidence-generating work may contain multiple bounded iterations inside one capability. Each iteration records its hypothesis, inputs, evidence boundary, result, and next disposition, but does not require a separate capability identity when the governing objective and contract remain unchanged. A fresh sealed holdout may be required for a later iteration without turning that iteration into a new capability.
