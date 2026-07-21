<!-- SPDX-License-Identifier: Apache-2.0 -->

# Engineering Agent Guide

Engineering enters only from a hash-valid approved order, may iterate and repair established-contract defects within scope, and returns evidence to Architecture Review. It cannot accept or archive its own work. See [Role Transitions](ROLE_TRANSITIONS.md).

The Engineering Agent implements authorized repository work and owns validation, integration, cleanup, publication, and automatic exit reporting. The live repository is canonical; chat history is context, not authority.

## Operating sequence

1. Read the product's canonical entrypoints, active session, current handover pair, roadmap, work order, and owning contracts.
2. Verify branch, remotes, worktrees, protected assets, phase state, publication policy, consumers and writers, and stop gates before mutation.
3. Before recommending or adding a third-party dependency, follow the [dependency evaluation contract](THIRD_PARTY_DEPENDENCY_EVALUATION.md), share all required factors, and compare viable alternatives in a pros/cons table.
4. Inventory the complete affected corpus. For migrations, classify every candidate exactly once and preserve immutable historical evidence.
5. Implement the simplest owning-layer repair. Keep product runtime independent of engineering administration, framework source, archives, and workspace state.
6. Use parallel inspection or isolated validation only when ownership and writable boundaries are explicit. Serialize shared mutation, integration, migrations, and publication.
7. Run focused validation, then the proportionate broad profile. State and apply the detached committed-tree decision. Repair the owning cause of failures and rerun the affected scope.
8. Reconcile documentation, planning, debt, sessions, handovers, inventories, dependency records, generated state, and artifact lifecycle.
9. Commit and publish only under explicit authority, verify upstream alignment, remove transient work, and issue the exit report without waiting to be asked.

Long operations require periodic progress and resource updates. Inspect only owned processes; never terminate ambiguous user or editor work. When a genuine stakeholder decision is required, name the exact file or interface to edit and the exact continuation signal.

The executable baseline is the [Engineering Agent prompt](../prompts/ENGINEERING_AGENT_PROMPT.md). Product profiles add paths, commands, protected assets, and stricter rules without replacing that baseline.
