<!-- SPDX-License-Identifier: Apache-2.0 -->

# Technical Debt Governance

Debt records do not authorize either a Capability or GOV item. A trigger selects the correct work-item type from semantic effect rather than title keywords and requires a sealed order before Engineering mutation.

Technical debt is a known gap between current implementation and the desired architecture, quality, operability, security, maintainability, or evidence standard. Discovery and backlog inspection are not remediation.

Each item records stable ID, category, severity, priority, owner, discovery source, rationale, impact, affected artifacts, accepted versus accidental status, remediation trigger, target phase or release, validation, dependencies, status, event history, and closure evidence. Valid states are proposed, accepted, scheduled, in progress, blocked, resolved, superseded, and rejected; profiles may narrow vocabulary without changing semantics.

Every transition creates a history event. Resolution requires changed implementation or an explicit accepted design correction plus validation; refreshing a timestamp does not improve status. Phase/release health reviews reconcile every unresolved item, enforce blocker budgets, and reauthorize carry-forward. Closure evidence identifies the fixing commit, tests, remaining risk, and planning links.

A resolved item's status is the resolving party's own completion claim, not final acceptance. Final acceptance additionally requires an independent reviewer -- distinct from whoever performed the resolution, never the same agent, session, or delegated worker that authored the fix -- to re-derive the resolution's own validation directly and record that verification separately from the resolver's own closure claim: reviewer identity, verdict, and the evidence actually checked. A resolution lacking this independent verification record does not carry final acceptance, however complete its own resolution narrative reads. Profiles bind the reviewer role to a concrete authority (e.g. an Architecture Office) and a concrete recording mechanism without narrowing this requirement.
