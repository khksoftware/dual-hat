<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.8 Release Notes

Dual Hat 1.17.8 generalizes a pair of consuming-project defenses -- a
hardcoded-workspace-path scanner and a retired-convention
zero-stale-reference gate, both added after a path-scoping migration
silently broke two consumers for months before anyone noticed -- into a
standing Dual Hat governance principle rather than leaving the fix as
project-specific tooling.

`PROCESS_PROPORTIONALITY.md` gains rule 20: when a foundational convention
-- a path scheme, an identity or naming model, a schema version, or any
other shared contract multiple consumers depend on -- changes, the change
is not complete merely because its owning module or record was updated and
its own tests pass. Closure requires both halves of the gap to be closed:
first, a mechanical (not manual-review) proof that every consumer moved
with the convention, with any surviving reference to the superseded
pattern outside genuinely historical or explicitly exempted content
treated as a closure-blocking failure of the migration itself; second, a
standing mechanical check that catches any new hardcoded reference to the
superseded convention the moment it is introduced, so a contributor
unaware the convention ever changed cannot silently reintroduce it later.

Rule 20 is named as the standing defense for one especially common shape
of rule 19's systemic mechanism gap -- a pointer or convention that must
track changing state but has no enforcement keeping it synchronized --
applied specifically to convention migrations, and is cross-referenced
with rule 19 in both directions. It is pinned with a new exact-substring
test in `test_framework.py` beside the existing rule 19 pinning test,
following this repository's established pinning pattern.

This is a backward-compatible governance-documentation release. It adds
one new rule and one new pinning test; nothing consuming-facing changes.
