<!-- SPDX-License-Identifier: Apache-2.0 -->

# Context Packs and Task Retrieval

Begin with canonical entrypoints, identify the owning domain, and load current authoritative artifacts before generated projections or history. Follow explicit dependencies. History is loaded only for a named decision, regression, migration, rollback, or provenance question that current state cannot answer.

A context pack records task identity, authoritative sources, source revisions, current state, relevant history, dependencies, provenance, exclusions, record/token budgets, progressive expansion, conflicts, retrieved-but-unused items, freshness, and regeneration triggers. It is advisory and cannot replace its sources.

## Retrieval algorithm

1. Resolve task class and owning domain from canonical indexes.
2. Load the smallest current authority set.
3. Verify paths, revisions, provenance, and conflicts.
4. Apply exclusions and a bounded context budget.
5. Expand only when a concrete gap blocks the task.
6. Distinguish normative, operational, generated, historical, and illustrative material.
7. Stop when sufficient context is assembled; record justified unused retrieval.

Avoid archive-wide scans, ignored workspace walks, and hidden reliance on prior agent memory. Prefer indexes, manifests, Git identities, and bounded searches. Regenerate the pack when an authoritative input, task scope, dependency, or profile changes.

Examples: a narrow code change loads its owning module/tests/contract; a migration adds consumers, writers, manifests, rollback, and path governance; phase closure adds planning, health, debt, and release state; an incident adds current telemetry and bounded history; governance work loads exclusive-role metadata; external publication adds source map, prior marker, licensing, drift, and remote state.
