<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 4.1.0 Release Notes

## What changed

Eight accumulated changes, published together as one minor release: five governance and
tooling additions plus three smaller carried-over repairs.

### A fourth systemic-gap shape (Principle 3)

Principle 3 already named three shapes a systemic gap can take: an undocumented mandatory
step, a check never made mechanical, and a pointer or current-state marker with nothing
keeping it synchronized. It now names a fourth: **a numeric bound whose value was set at or
near an observed instance's own size rather than derived from what the bounded thing
legitimately needs.** Such a bound is evidence about the instance that produced it, not a
constraint on the thing it is meant to bound -- it is satisfied at birth, and structurally
incapable of ever firing on the case that motivated it. This is a distinct shape from the
other three: the mechanism exists and is armed, and what is wrong is its calibration, which
none of the first three shapes reaches.

Ships as advice, inheriting principle 3's existing label -- no arming line is added, matching
the framework's own arming constraint that an obligation without a detector must say so
rather than claim one nothing invokes.

### A sharper residual for the session-boundary hook (Principle 12)

Principle 12's Residual paragraph previously stated only that this framework ships no
session-stop hook and that an adopter who wires one arms the control. True, but incomplete:
**even an armed hook's coverage stops at the session it is attached to.** A delegated or
sub-agent's own turn is a separate execution context the parent's hook cannot introspect, by
construction, on any supervisor/worker agent architecture whose hook model looks like this
one -- not a fact about any one platform, a fact about what a turn-boundary hook can see from
where it is attached. So the labeling obligation this principle places on every message a
role *or delegated worker* produces has, for the delegated half, no possible automated
arming at all: only the dispatching brief can carry it.

No new arming line. This narrows what the existing Residual paragraph claims; it neither adds
nor removes an obligation.

### A scoped sibling-import context manager, and a repaired consumer

`tooling/sibling_import_context.py` is new: `sibling_directory_on_path`, a context manager
that puts a directory on `sys.path` only for the duration of a `with` block and removes it
again in `finally`, only if that call is what inserted it; and
`_load_module_by_path_with_sibling_context`, the by-path-load form built on it. Stdlib only,
zero framework-specific dependencies.

The product-bootstrap script carried the exact defect this module exists to prevent: a
permanent, unscoped `sys.path.insert` of its tooling directory, executed at import time and
never removed, polluting every subsequent import for the rest of the process's life. Repaired
in the same change -- a helper shipped beside an unrepaired instance of the defect it fixes is
the shape Principle 3 forbids. Proven by a red/green regression: an isolated-subprocess test
confirmed the tooling directory left on `sys.path` against the pre-repair script, and confirmed
absent against the repaired one, before either state was accepted.

### A genuinely armed per-entry contract for `known_environment_limitations`

The platform-profile schema's `known_environment_limitations` moves from a bare
`{"type": "array"}` to an items schema requiring an object with four required string fields
(naming what breaks, how it presents, how to detect it, and the safe alternative) plus an
optional `remedy`. Wired into the profile-conformance validator's central `validate_profile`
function, so every capability-preflight call inherits it -- confirmed genuinely enforced by a
red/green regression rather than shipped as an unenforced specification: a bare string, a
missing required field, and a blank-string field or remedy all previously passed validation
and now correctly fail.

### A composable pre-commit gate-dispatch pattern, documented

A new guide describes how an adopter composes more than one independent write-time gate behind
git's single `hooks/pre-commit` slot: an installed shim holding no logic of its own, only
dispatch; each gate owning its own independently-armable marker file, checked and predicated on
independently; marker names imported from each gate's own module rather than re-typed in the
shim, so the two cannot drift apart. States the accompanying lesson as its own section: a
write-time gate must read a commit's actual staged content through the version-control system's
own index plumbing, never the working tree. States the bypass paths explicitly rather than
hiding them, and closes with a generic, non-importable illustrative skeleton.

This is the concrete answer to a residual Principle 14 already states and does not close on its
own: an adopter that does not wire the detector into a commit or closure gate has the detector
and not the control. Advice, stated as such in the guide's own text -- the detectors it
dispatches to are necessarily project-specific, so there is no generic, shippable module to
hand an adopter, only the composition shape and the reasoning behind it.

### Two smaller carried-over repairs

Four test-rationale comments named a version literal where they meant a condition -- true of
one release and stale at the next, disarming a real release-evidence check across releases
without anyone deciding to. Reworded to name the condition instead of the instance, which fixes
it permanently rather than once per release.

A tooling docstring cited a rule number the successor principle set had already retired.
Corrected to the principle number that now carries the same obligation. The neutrality
constraint is unaffected -- the sentence names a consuming project generically, and continues
to.

## Compatibility

**MINOR.** An adopter gains new advisory guidance (the principle 3 and principle 12
amendments, and the new guide) and one newly-enforced, previously unenforced schema constraint
(`known_environment_limitations` entry shape). Nothing existing is renamed, relocated or
removed. No principle is renumbered. Every citation issued against the prior release still
resolves.
