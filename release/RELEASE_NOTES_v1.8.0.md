<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.8.0 Release Notes

Dual Hat 1.8.0 adds a product-neutral systemic-repair rule. Every ad hoc fix is
assessed for a failure class that could recur across inputs, work items,
environments, or consumers. When recurrence is credible, the preferred repair
is the smallest proportionate control in the owning layer, alongside correction
of the current instance.

The rule is deliberately bounded. It does not authorize speculative hardening,
broad redesign, or new process merely because generalization is imaginable.
The systemic repair must be justified by plausible recurrence and remain
proportionate to the material risk.

The release also closes a lifecycle gap for projects that use short-lived work
branches. Accepted work is integrated into its authorized target and the
completed branch is retired before unrelated work continues. A retained branch
needs an explicit owner, purpose, and retirement trigger; a new work item does
not silently inherit the prior item's branch.

This is a backward-compatible minor governance release. Existing 1.x
interfaces, authority boundaries, historical work items, and mandatory safety
controls remain valid.
