<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.14.0 Release Notes

Dual Hat 1.14.0 reduces repeated authorization overhead without weakening
dependency controls. A stakeholder may authorize a precisely bounded class of
dependencies, tools, or models once. Each candidate still requires evidence
for licensing and product implications, cost, reliability, safety and privacy,
hardware, support status, integrity, and fit to the authorized scope.
Candidates outside those conditions require a new decision. Rejected installed
candidates are removed promptly after their evidence is preserved.

Phase transitions are also more coherent. When a phase closes as its successor
opens, current planning, historical state, the successor capability ledger,
session state, and handover update as one transaction. Contradictory
current/unopened or active/history representations are rejected.

Finally, command lookup and troubleshooting now live beside the other
cross-cutting operating guides under `guides/`. The redundant top-level
`help/` directory is removed, and active documentation, inventory, tests,
publication guidance, and export manifests use the consolidated paths.

This is a backward-compatible additive governance release. Existing 1.x
authority, lifecycle, schema, and compatibility contracts remain unchanged.
