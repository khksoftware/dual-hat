<!-- SPDX-License-Identifier: Apache-2.0 -->

# Task-Context Retrieval Guide

Retrieve the smallest authoritative context that can safely govern the task, then expand only when an identified uncertainty requires it. Begin with canonical entrypoints, active session, current handover, current work order, owning architecture or governance, and the directly affected implementation and tests.

## Retrieval procedure

1. Record task identity, candidate fingerprint, repository state, source paths, revisions, freshness, provenance, and exclusions.
2. Prefer current primary authority over summaries. Load history or archives only to answer a named lineage, migration, or regression question.
3. Detect conflicting authorities, stale paths, superseded records, and retrieved material that did not influence the decision.
4. Set file, record, byte, or token budgets. If the budget is reached, stop at a semantic boundary and record what remains unexamined.
5. Expand progressively by consumer, dependency, analogous implementation, or changed-source overlap. Never broaden recursively without a reason.
6. Regenerate the context pack when authority, branch, candidate commit, protected state, work-order scope, or source revision changes materially.

The resulting pack must distinguish authoritative sources, relevant history, current state, assumptions, exclusions, unresolved conflict, and unused retrieved context. It must be compact enough for handover but cannot omit a known governing constraint. Use the [context-pack schema](../schemas/context-pack.schema.json), [template](../templates/CONTEXT_PACK.md), and [context protocol](../process/CONTEXT_AND_RETRIEVAL.md).
