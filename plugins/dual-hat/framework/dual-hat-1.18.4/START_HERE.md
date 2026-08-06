<!-- SPDX-License-Identifier: Apache-2.0 -->

# Start Here

This is the single required entry point for a fresh agent or chat session to gain full working knowledge of the Dual Hat framework before operating within any product. It replaces assembling a reading list by hand: read this file, then follow it in order, in full, before touching role-specific guidance, a product's own profile, or any work item.

Do not skip ahead to a role prompt, a product's extension layer, or the active session/roadmap/work order until this sequence is complete. Framework fluency comes first; task context comes after.

## Required sequence

1. [`README.md`](README.md) -- what Dual Hat is, Integrated and Split modes, first use, framework areas.
2. [`architecture/OPERATING_MODEL.md`](architecture/OPERATING_MODEL.md) -- the authority split between Architecture and Engineering, the authority stack, and the operational invariants everything else builds on.
3. [`process/ONBOARDING.md`](process/ONBOARDING.md) -- how a product or repository is brought under the framework, and the no-mutation approval boundary. Read this even when the current product is already onboarded and bound: it explains the approval model this session must continue to honor.
4. [`process/BOOTSTRAP.md`](process/BOOTSTRAP.md) -- the low-level application step for an already-approved product profile.
5. [`guides/OPERATING_GUIDE.md`](guides/OPERATING_GUIDE.md) together with [`guides/INSTALLATION_AND_BINDING.md`](guides/INSTALLATION_AND_BINDING.md) -- day-to-day operating guidance, and how the framework is installed, bound, updated, rolled back, and removed. Read together per [`repository/CANONICAL_ENTRYPOINTS.md`](repository/CANONICAL_ENTRYPOINTS.md).
6. Both role documents, regardless of which single role this session expects to hold at first -- Integrated Mode requires fluency in both, and even a Split-Mode session must recognize the other role's authority and expectations: [`governance/ARCHITECTURE_OFFICE_GUIDE.md`](governance/ARCHITECTURE_OFFICE_GUIDE.md) with [`prompts/ARCHITECTURE_OFFICE_PROMPT.md`](prompts/ARCHITECTURE_OFFICE_PROMPT.md), and [`governance/ENGINEERING_AGENT_GUIDE.md`](governance/ENGINEERING_AGENT_GUIDE.md) with [`prompts/ENGINEERING_AGENT_PROMPT.md`](prompts/ENGINEERING_AGENT_PROMPT.md).
7. [`process/WORK_ITEM_LIFECYCLE.md`](process/WORK_ITEM_LIFECYCLE.md) and [`process/PUBLICATION_AND_CLOSURE.md`](process/PUBLICATION_AND_CLOSURE.md) -- how Capability and GOV work items are sealed, executed, reviewed, closed, archived, and published.
8. If the current product layers a Dual Hat profile on top of this generic source, read that product's own designated extension entrypoint next -- check the product's root and its own canonical-entrypoints reference for the pointer. Only after that layer is read is this session ready to load the active session, roadmap, and bounded work order and begin operating.

## What this file is not

This is the fresh-session knowledge sequence, not a standing lookup table. Once framework fluency is established, use [`repository/CANONICAL_ENTRYPOINTS.md`](repository/CANONICAL_ENTRYPOINTS.md) for "where do I begin" by task type, and [`guides/COMMAND_REFERENCE.md`](guides/COMMAND_REFERENCE.md) for standalone validation and bootstrap commands. It also does not replace a product's own extension entrypoint (step 8): this file ends where product-specific onboarding begins.
