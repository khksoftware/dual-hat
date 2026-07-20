<!-- SPDX-License-Identifier: Apache-2.0 -->

# Technical Debt Governance

Technical debt is a known gap between current implementation and the desired architecture, quality, operability, security, maintainability, or evidence standard. Discovery and backlog inspection are not remediation.

Each item records stable ID, category, severity, priority, owner, discovery source, rationale, impact, affected artifacts, accepted versus accidental status, remediation trigger, target phase or release, validation, dependencies, status, event history, and closure evidence. Valid states are proposed, accepted, scheduled, in progress, blocked, resolved, superseded, and rejected; profiles may narrow vocabulary without changing semantics.

Every transition creates a history event. Resolution requires changed implementation or an explicit accepted design correction plus validation; refreshing a timestamp does not improve status. Phase/release health reviews reconcile every unresolved item, enforce blocker budgets, and reauthorize carry-forward. Closure evidence identifies the fixing commit, tests, remaining risk, and planning links.
