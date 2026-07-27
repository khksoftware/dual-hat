<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.4 Release Notes

Dual Hat 1.17.4 closes a gap between two related self-applied disciplines
that had never been tied together: the mandatory turn-exit audit (checked
before every response boundary: is the task complete, is a stop condition
present, keep executing otherwise) never actually checked the Integrated
Mode role-label convention it sits right next to in the same guides. Caught
live in a governed session where the label was dropped for an extended
stretch with nothing catching it.

Both role guides now include the role-label check as an explicit item in
the same audited checklist, and name concrete resumption points --
returning from a background-agent task notification, returning from an
unrelated tangent, and resuming from a context-compaction summary -- where
the full audit must explicitly re-run. Self-applied conventions with no
code-level enforcement are likeliest to silently lapse exactly at those
points across a long, multi-threaded conversation, not at an arbitrary
moment; naming them concretely is more effective than restating "before
every response boundary" alone.

This is a backward-compatible governance clarification. No schema, API, or
required-field change accompanies it.
