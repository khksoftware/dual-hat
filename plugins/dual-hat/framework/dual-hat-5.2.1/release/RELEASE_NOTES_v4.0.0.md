<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 4.0.0 Release Notes

## What changed, and why it is a major

This release replaces the framework's 36-rule set, and its four obligations that
sat outside the numbering entirely, with 15 numbered principles.

**The governing change is arming, not length.** Every principle ends with one of
exactly two lines, and both are statements of fact rather than aspiration:

- **`Armed by`** — names the executable mechanism that refuses, and where that
  mechanism has a known residual, states the residual. A residual stated there
  is a declared limit of the control, not a defect to be closed by rewording the
  principle.
- **`Advice`** — states plainly that nothing enforces this principle. It holds
  because a reasonable reader complies, and for no other reason.

**Eight are armed. Seven are advice.** That count is produced mechanically from
the file rather than asserted.

### The constraint behind it

A control that is not armed on the day it is authored is not authored. No
specification without a runner, no registry without a gate that reads it, and no
principle without either a detector or an explicit recorded admission that it is
advice.

This exists because the opposite was measured. A framework accumulates
obligations faster than it accumulates the mechanisms that enforce them, and the
gap is invisible from inside: a specified, built, tested control that is never
wired into a gate reads exactly like an enforced one, both to the reader of the
specification and to the agent obeying it. The characteristic failure is not
that a rule is broken. It is that nothing could have noticed.

### The four obligations that could not be cited

The highest-consequence obligations previously sat outside the numbering, which
meant no citation could reach them — and they are the ones with real gates
behind them. They are now principles 7, 8 and 9: the execution lease and its two
terminal conditions with its termination-preflight receipt, the dispatch
monitor-set obligation, and the evidence-defined worker-state vocabulary.

### Also in this release

**The new-chat bootstrap obligation binds to a role, not to a filename.** A
repository that folds its handover content into its active-session record is now
conformant rather than in violation, and the bootstrap role is held by exactly
one artifact wherever it lives. Validation gains the multiple-claimants case.

**Conformance Clause A is executable.** Five guarded terminal engineering
transitions fail closed without a sealed, reconciled termination-preflight
receipt: exact approved-scope dispositions, non-empty evidence for every
required result, a stop gate named in the sealed order's own stop gates, sealed
abort authority with a terminal disposition, terminal owned processes, and
receipt binding to the sealed work-order hash. Malformed evidence fails closed.

## Upgrading

**Every citation into the rule set is invalidated.** There is no arithmetic
relationship between the old numbers and the new ones, and a reference to a
retired number still reads as a valid sentence, so nothing will tell you a
citation has gone stale.

`release/UPGRADING.md` carries the governed migration and resolves every retired
rule number. Read it before updating any citation by hand.

Four breaks each force a major independently:

1. Citable surface changed meaning without changing shape.
2. A contract is removed and a gate replaced: the ledger-projection
   reproducibility rule retires, countermeasure independence is released for
   changes confined to governance text while staying mandatory wherever a defect
   could reach a consumer of the product, and the independent-reviewer gate on
   rule changes becomes the stakeholder's explicit go-ahead.
3. Two section headings consumers resolve against no longer exist.
4. A shipped tooling message changed: the absolute-local-path failure text moves
   from naming rule 35 to naming principle 14.

**No executable gate's predicate changes.** Every mechanism refuses exactly what
it refused before.

## What this release does not claim

No stability claim beyond what `release/VERSION.json` already states, and no
comparative claim against any other framework or against any prior version
beyond the migration facts recorded above.
