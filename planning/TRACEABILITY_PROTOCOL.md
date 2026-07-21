<!-- SPDX-License-Identifier: Apache-2.0 -->

# Intent-to-Delivery Traceability Protocol

## Purpose

Products preserve enough bidirectional traceability to explain why planned and delivered work exists, what requirement or maintenance need it serves, how it was verified, and where it reached a product or release surface. Traceability is governance infrastructure, not a demand for duplicate documents or a link on every trivial edit.

## Minimum chain

The normal chain is:

```text
stakeholder intent or operating need
  -> use case, requirement, decision, defect, debt, or maintenance basis
    -> roadmap, backlog, future trigger, or work item
      -> architecture and implementation artifacts
        -> verification and acceptance evidence
          -> release, export, migration, or deployed product surface
```

Not every change needs every entity. A small repair may begin at a defect or maintenance basis; research may remain exploratory; intentionally deferred work ends in an explicit defer decision. Missing intermediate links are acceptable when the remaining chain still explains intent, authority, implementation, and outcome.

## Required behavior

- Give traceable entities stable identities within their owning system.
- Every scheduled work item names at least one upstream basis; every upstream requirement selected for delivery reaches a work item or explicit defer decision.
- Implementation and verification evidence identify the authorized work item and affected requirement, invariant, defect, debt, or maintenance basis.
- Completion reconciles affected roadmap, backlog, requirement, debt, future-trigger, session, handover, and release projections without creating competing current-state authorities.
- Moves, supersession, and archival preserve redirects or provenance where active links depend on them. Trace records are superseded or waived with rationale rather than silently erased.
- Relationships use clear semantics such as `derives_from`, `satisfies`, `implements`, `verifies`, `depends_on`, `supersedes`, `revisits`, `governs`, and `exports_to`.

## Trigger points

Review affected trace links when requirements or use cases materially change, work is scheduled or deferred, a phase opens or closes, implementation or verification completes, an authoritative artifact moves, or a release/export/productization boundary is crossed. Routine edits that do not change intent, authority, status, or delivery do not require ceremonial trace updates.

## Waivers and validation

A material missing link records the affected identities, rationale, owner, review or revisit condition, and status. Profiles bind the canonical registries and validators. Validation should detect material orphans and contradictions while avoiding archive-wide scans and false failures for legitimately compact chains.

This protocol defines the product-neutral contract. Product profiles may add entity types, relationship rules, paths, schemas, and stricter gates without weakening it.
