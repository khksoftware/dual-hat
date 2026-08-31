<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.7 Release Notes

Dual Hat 1.17.7 closes out a batch of governance-consistency and
closure-integrity gaps found during the same governed session as 1.17.6.

Two existing rules had independently drifted apart across their
restatements in the role prompts, with nothing tying the copies together:
the hypothesis-blind-execution / three-arbiter protocol
(`REASONING_AND_DECISION_REVIEW.md`) and the universal-completion-claim
rule (`CONFORMANCE_POLICY.md`). Both prompts now carry matching wording,
each pinned by an exact-substring test against the canonical document and
every restatement, so future drift is caught mechanically rather than
discovered by inspection.

Separately, `REPOSITORY_BOUNDARIES.md` has long stated that Dual Hat never
imports product, engineering, archive, or workspace state -- but nothing
in `tooling/` or `tests/` actually enforced it. `framework_completeness.py`
now scans for real Python import statements (including relative imports)
against the four forbidden top-level packages, without false-positiving on
legitimate local module names or path-string references.

This release also adds an independent closure-reconciliation-audit gate at
every capability's closing gate: before terminal disposition, a
context-isolated independent reviewer must reconcile the sealed work
order's approved scope, every incremental stakeholder request, and every
committed interim finding or bug against verified repository fact --
commit, file, test result -- rather than Engineering's own self-report.
Partially done or not-done items block closure unless the author
explicitly defers them. This adds a new `reconciliation_audit` object to
the closeout-decision schema, and it is the first Dual Hat schema change
in this release line to add a *required* field rather than an optional
one -- callers producing closeout decisions must now supply it.

Finally, `PROCESS_PROPORTIONALITY.md` gains rule 19: when investigating a
flagged defect, a stale artifact, or a "this was supposed to be done but
wasn't" gap, first determine whether the symptom is one instance of a
missing systemic mechanism -- an undocumented mandatory process step, a
check that was never made mechanical, or a pointer/cross-reference with no
enforcement keeping it synchronized -- rather than a genuine one-off, and
repair the mechanism itself when it is. This cross-references rule 15's
existing correction-to-control loop in both directions.

This is a backward-compatible governance and tooling release. The
`reconciliation_audit` addition to the closeout-decision schema is a
required-field change to that internal closeout-tooling contract (not a
consuming-project-facing API); every other change in this release is
purely additive.
