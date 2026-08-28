<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 2.0.0 Release Notes

Dual Hat 2.0.0 is a **major** release. It is the first release of this project
to carry a governed migration document, and the version was raised to a new
major specifically because the framework's own stability contract requires one:

> Mandatory core contracts are stable; breaking changes require a new major
> version and governed migration.

**Read `release/UPGRADING.md` before upgrading.** These notes summarise what
changed; the migration document names every breaking change individually,
together with the release each one actually landed in, because an adopter's
starting point is not uniform and a delta from the immediately preceding
release is wrong for anyone not already on it.

## Why a major version

Three of the changes below alter published contracts: a public function's
required arguments, the shape and schema version of two published provenance
records, and the vocabulary of a published maturity label. A fourth changes
which adopter platform profiles are admitted. A fifth moves obligation text
between framework files, which breaks adopter tests that assert framework text
by filename.

Some of those breaks are not new. One of them shipped inside a **patch**
release described in its own notes as backward-compatible. This release names
it rather than continuing past it — see the migration document's correction
under group 1.

## The publication endpoint verification now proves every configured endpoint

`tooling/release_package.py` verified the publication remote with
`git remote get-url origin` and `git remote get-url --push origin`, neither
carrying `--all`. Git returns a single URL from those queries and pushes to
*every* configured `remote.origin.pushurl`. A second, unapproved push endpoint
was therefore invisible to the check.

This was demonstrated offline rather than argued: with two local bare
repositories and a real push, the check returned a PASS record while both
repositories received the identical commit.

Both queries now use `--all`, and every returned endpoint must equal the
approved identity. A blank line is dropped, but an unparseable URL is kept as an
empty identity rather than filtered out, so a malformed endpoint fails the
comparison instead of disappearing from it.

### The provenance record can no longer assert what the check did not establish

This is a separate defect from the query, and the more serious of the two. The
verified endpoint was written into the fresh-remote-state record and copied into
the publication provenance record **as a singular verified fact**. The framework
did not merely fail to detect a second endpoint — it signed a positive assurance
that the push endpoint had been verified and was this one.

Both records now enumerate every endpoint proven, and both schema versions move
to `/2.0`. The scalar fields are removed rather than retained, so no consumer
can go on drawing the singular conclusion. See the migration document for the
exact field changes.

URL rewriting through `insteadOf` was verified **not** to be a bypass and is
deliberately unchanged: `git remote get-url` reports the rewritten URL, so the
identity comparison fails closed. That was correct behaviour that nothing
protected; a regression test now does.

## Maturity is derived from the version's own major

`release_maturity()` stamped every major at or above 1 as `stable_1_x`, so this
release would have shipped labelled `stable_1_x`. The label is now derived from
the major the version actually carries, producing `stable_2_x` here and
`stable_<major>_x` at every later major.

The derivation is parameterised on the major rather than enumerating a boundary
per major. That shape is deliberate: the 0.x-to-1.x boundary was written by hand
with nothing keeping it synchronized, the identical contradiction reappeared at
1.x-to-2.x, and a third hand-written boundary would have guaranteed a third
recurrence at 3.0.0.

**Why no test caught it.** `release/VERSION.json` carried the same value the
function derived, so the existing cross-check compared two sides that agreed and
were both wrong. A fixture consistent with a defect does not merely fail to
catch it; it manufactures a passing signal. The standing check added here is
anchored on the major the version itself carries, never on the derivation it
guards, and it is proved to fire on deliberately contradictory labels rather
than assumed to.

## Standing checks added

- A release must carry release notes for its own version, a CHANGELOG head
  entry naming that version, and a governed migration section for its own
  major. The previous check accepted a version mentioned anywhere in the
  CHANGELOG; it now requires the head entry.
- A maturity label must agree with its own version — checked against the
  shipped release evidence, against every committed record carrying both a
  version and a maturity, and against synthetic contradictions.
- No module may resolve a remote endpoint with the single-endpoint query again,
  and no maturity label literal may survive outside the one derivation.

## Publication-disclosure fix

Four fixture strings in `tests/test_repository_hygiene.py`, which ships through
the export allowlist, embedded a real machine's drive, username and directory
layout. All four are now synthetic. Each replacement is asserted — not assumed —
to still trip the detector its test exercises, because a fixture that quietly
stopped matching would leave its test green while testing nothing.

This was a publication-disclosure concern and not a rule 35 compliance defect:
the lines were already exempt by file shape and the check was not failing on
them.

## Upgrading

1. Read `release/UPGRADING.md` in full. Identify which of the five groups apply
   to the version you are upgrading **from**, not merely from 1.18.5.
2. If you call `select_closeout()` directly, supply all three required
   keyword-only arguments.
3. If you parse the publication provenance records, move to the plural
   `*_endpoint_identities` fields.
4. If you match on `maturity`, stop enumerating a two-value set.
5. Set your platform profile's `dual_hat_core_version` to the version you
   actually installed.
6. If any of your tests assert framework obligation text by filename, re-point
   them at the corpus rather than at a file.
