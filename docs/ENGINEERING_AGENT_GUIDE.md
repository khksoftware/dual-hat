<!-- SPDX-License-Identifier: Apache-2.0 -->

# Engineering Agent Guide

The Engineering Agent implements authorized repository work and owns validation, integration, cleanup, publication, and automatic exit reporting. The live repository is canonical; chat history is context, not authority.

## Operating sequence

1. Read the product's canonical entrypoints, active session, current handover pair, roadmap, work order, and owning contracts.
2. Verify branch, remotes, worktrees, protected assets, phase state, publication policy, consumers and writers, and stop gates before mutation.
3. Inventory the complete affected corpus. For migrations, classify every candidate exactly once and preserve immutable historical evidence.
4. Implement the simplest owning-layer repair. Keep product runtime independent of engineering administration, framework source, archives, and workspace state.
5. Use parallel inspection or isolated validation only when ownership and writable boundaries are explicit. Serialize shared mutation, integration, migrations, and publication.
6. Run focused validation, then the proportionate broad profile. State and apply the detached committed-tree decision. Repair the owning cause of failures and rerun the affected scope.
7. Reconcile documentation, planning, debt, sessions, handovers, inventories, dependency records, generated state, and artifact lifecycle.
8. Commit and publish only under explicit authority, verify upstream alignment, remove transient work, and issue the exit report without waiting to be asked.

Long operations require periodic progress and resource updates. Inspect only owned processes; never terminate ambiguous user or editor work. When a genuine stakeholder decision is required, name the exact file or interface to edit and the exact continuation signal.

The executable baseline is the [Engineering Agent prompt](../prompts/ENGINEERING_AGENT_PROMPT.md). Product profiles add paths, commands, protected assets, and stricter rules without replacing that baseline.
