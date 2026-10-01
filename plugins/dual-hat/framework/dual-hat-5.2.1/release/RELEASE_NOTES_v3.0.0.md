<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 3.0.0 Release Notes

Dual Hat 3.0.0 is a **major** release, and it carries one change. That change
alters what a publication is allowed to be, which is why it takes a major
version rather than a minor one.

`release/UPGRADING.md` carries the governed migration section for this release
and is the authority for what an upgrade requires. These notes state what
changed and why; that document states what you have to do.

## The change

**A vendored plugin bundle that disagrees with the shipped framework version now
fails the publication closed.**

It was previously detected and not enforced. The framework's own test asserted
the predicate correctly and fired correctly, and its comment described the
consequence in advance — a stale bundle silently ships whatever governance or
continuity defects the current framework has already fixed. It was red at a
published HEAD and the release shipped anyway.

The gap was never a missing test. **A red test is advisory and a person can ship
past it**, so the reinforcement is a publication-blocking condition rather than a
second test asserting the same predicate. Two mechanisms for one rule is the
defect, not the fix.

`validate_bundle_version_currency()` is called from `validate_staged()` and from
`verify_commit_tree()`, reading through the index or the committed tree rather
than the worktree, so the condition is evaluated against the content actually
being published rather than against whatever happens to be in the directory.

## Read this before the detail

**This is first contact, not a tightening.** No earlier release carried this
condition in any form. Every refusal it makes is therefore new to you regardless
of which release you are upgrading from, and none of it can be reasoned about as
a delta from behaviour you have observed.

A reader who scopes it as a delta will look for bundles that are behind. Several
of the conditions refuse bundles that are not: a bundle **ahead** of the shipped
version is refused on the same terms as one behind it, a correct bundle with a
missing shipped-version authority is refused rather than passed unchecked, and a
deliberate multi-version vendoring window is refused with no override.

## What the condition does not reach

Stated here rather than left to be taken on trust, because a reader who assumes
broader coverage will rely on a check that is not running.

The core-version walk reads only `.json` files under the bundle root, only a key
named exactly `dual_hat_core_version`, and only a value of exactly three numeric
segments. Constraint expressions, two-segment and pre-release versions, and a
stale version stated in bundled Markdown or YAML or in a manifest description
are all outside it.

A version token counts only where it names the framework, so a schema version, a
minimum runtime version and a cited release-note filename stay free — and, in the
other direction, a stale bare version token that does not name the framework is
not caught. Matching bare digits instead would refuse a current bundle and report
it as a stale one, sending an operator to hunt a bundle that does not exist. A
gate whose message misdescribes its own cause is worse than no gate.

A manifest outside the bundle root is not reached.

## Also in this release

`release/PUBLICATION.md` gains a normative section stating the rule, and
reconciles it with the existing statement that forward publication preserves
standalone-owned namespaces without claiming or mutating them. There is no
contradiction: the rule reads that content and declines to publish, never
rewrites it, and the correction stays the owning repository's to make.

The framework's own bundle-currency test now calls the condition rather than
re-asserting three of its predicates by hand, and the hardcoded vendor
enumeration it carried is retired. The condition itself is proven by control
rather than by assertion — a gate never observed refusing is the failure being
repaired — with a positive control confirming a current bundle still publishes
and eleven negative controls each asserting the exact failure rows its condition
produces.

Every version declaration this distribution carries states the shipped version,
including the example adopter profile and the shipped templates. Deployment-form
manifests and superseded vendored snapshots are discovered by shape rather than
enumerated, so a deployment form or a stranded snapshot that nobody wrote down
is handled the day it appears rather than skipped silently.

## What this release does not do

Stated so none of it is inferred from the fact that a major version shipped.

- It does **not** change any governing rule's text, numbering, or wording.
- It does **not** give any refusal an override, a warning mode, or an escape
  hatch.
- It does **not** widen the core-version walk or the token match beyond the
  limits stated above.
- It does **not** resolve the exact-equality profile-conformance question the
  previous major left open.
- It makes **no** stability, security, portability, durability or comparative
  claim of any kind. A new major version is a statement about compatibility and
  nothing else.
