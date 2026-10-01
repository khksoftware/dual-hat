<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 5.1.0 release notes

A minor release publishing twelve pending propagations together. Nothing is removed, nothing is renamed, and
no existing function's signature changes.

## Why minor rather than patch

Three of the twelve change what an adopter observes, and the increment follows the highest of them, not the
average:

- **Two governance additions** — three folds into existing principles, and one new rule in the session and
  handover protocol with its enforceable half in tooling. New obligations, no renumbering, no removals.
- **One validation tightening.** The core-version anti-reintroduction check goes from three subtests to
  seven. **A repository that passed the previous form can fail this one**, and that is the intended effect:
  eight independently constructed ways of defeating the old check are now closed.

That third case is worth naming because the release policy's own three change classes have no category for
a validation becoming stricter — the same tightening is arguably patch, minor or major by the policy's
words. It is classified **minor** on the ground that an adopter upgrading gets checks that can newly fail,
which is new observable behaviour rather than a bug fix. The gap in the policy is recorded against the host
repository's own backlog and is not resolved by this release.

## If you upgrade, read these first

**The anti-reintroduction check is stricter.** It now refuses any assignment to a `CORE_VERSION`-shaped name
however the value is built, scans shipped text artifacts beyond `*.json`, covers an inline dictionary inside
a test module, and matches the shipped version on version-token boundaries rather than as a substring. If
your repository pinned the core version anywhere the old check could not see, this release will find it.

**Two new predicates are opt-in and have no defaults.** The permission-vocabulary and definition-of-done
checks in `work_item_governance.py` each take their registry as a **required keyword argument**. There is no
built-in vocabulary and no built-in criteria set: the framework carries the mechanism, your repository
carries its own data. Nothing calls them for you, nothing refuses anything until you wire them, and the
work-item schema's new `definition_of_done` property is optional.

**A non-production release build is stricter about its own provenance.** `source_files()` now fails closed
when a collected path disagrees with `HEAD`. If you build packages from a working tree with uncommitted
changes, pass the explicit named parameter and know why you are passing it — the reason it exists is a
plan-only build sourced between a propagation write and its own commit, whose manifest fields are never
trusted downstream.

**Bare pushes to the approved remote are refused when your git config diverts them.** If
`remote.pushDefault` or `branch.<branch>.pushRemote` names anything other than the verified remote, the
endpoint check now refuses and names the key and its value. The runbook gives the explicit push command.
Separately, an `http` or `git` push endpoint for the approved remote is now refused outright rather than
collapsed into the approved scheme, and a non-default port is part of the remote's identity.

## What was fixed rather than added

Two concurrency defects in the framework's own tooling and tests: a finished temporary run no longer fails
because a sibling cleaned the shared base directory first, and the completeness walk's probe file no longer
collides between concurrent runs on a fixed name.

Three assertion defects in the framework's own suite, each found independently rather than by a sweep — a
misfiled obligation moved into its own test and given the canonical-text check it never had; five
host-dependent guards that could report green with only one of two flavours having run; and a containment
guard that any unrelated failure in the same fixture would have satisfied.

One correction to documented behaviour that the implementation had already stopped matching: the staging
gate's contract described a filesystem walk when the gate is git-based. Both the policy prose and the
command reference now describe the enumeration performed, say plainly that content outside it is outside the
gate's reach, and name the recovery step for a staging run that fails partway through.

## Stated limits of this release

- The single-canonical-home test convention now records, beside itself, that a mutation or assurance
  measurement scores at **test** granularity. A test counting as covered because it goes red is not the
  claim that every assertion inside it does work.
- Principle 10's new allocation-moment paragraph is **advice, not arming**: the existing mechanism checks
  closure only and never a failure to allocate in the first place, and the principle's own residual says so.
- The new sealed-order predicates are **report-first**. They are wired into nothing, and arming any of them
  is a separate decision for whoever adopts them, taken after reading their output against a real corpus.
