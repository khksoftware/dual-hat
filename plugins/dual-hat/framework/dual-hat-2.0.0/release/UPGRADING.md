<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat governed migration guide

`release/VERSION.json` states the contract this document exists to honour:

> Mandatory core contracts are stable; breaking changes require a new major
> version **and governed migration**.

One section per major. A major version that ships without its section leaves
the framework's own stability contract unmet, and
`tests/test_release_package.py` fails the release when that happens.

**Every breaking change is named individually, with the release it actually
landed in.** It is deliberately not written as a delta from one assumed
starting point: an adopter who tracked every patch has a different upgrade than
an adopter who has been on an older line, and a document that names only the
gap from the immediately preceding release is wrong for everyone except the
first group.

## 1.x -> 2.0.0

Five groups. The first three change signatures or published data; the fourth
changes which adopter profiles are admitted; the fifth changes **where
obligation text lives**, and is the one most likely to be missed.

### 1. `select_closeout()` gained three required keyword-only arguments, in three different releases

`tooling/continuity_closeout.py`'s `select_closeout()` is exported, documented
public surface. Three required keyword-only parameters have been added to it in
total. **Only one of them is new at 2.0.0.** Which of the three affects you
depends entirely on where you are upgrading from, which is why all three are
listed with the release each landed in.

| Argument | Landed | `VERSION.json` at the time | First published in |
|---|---|---|---|
| `continuity_evidence` | `c6155daa`, 2026-07-20 | 1.1.0 | The module was authored the same day, at the same version (`f3db9091`). No published build carried `select_closeout()` without it. |
| `reconciliation_audit` | `274388e1`, 2026-07-28 | 1.17.6 | **v1.17.7 — a patch release.** See the correction below. |
| `dispatch_inventory` | `4d25fa42`, 2026-08-10 | 1.18.5 | **2.0.0. New in this release.** |

The current signature is:

```python
def select_closeout(*, same_stream_next: bool, triggers: Sequence[str],
                    continuity_count: int,
                    continuity_evidence: Mapping[str, object],
                    reconciliation_audit: Mapping[str, object],
                    dispatch_inventory: Mapping[str, object],
                    user_requested_publication: bool = False) -> dict[str, object]:
```

**None of the three has a default and none will be given one.** A default would
mean a caller who never passes the argument silently skips the control the
argument exists to enforce. A fail-open gate is not a gate, and the weakening
would be invisible in these notes.

#### Correction: `reconciliation_audit` shipped inside a PATCH release, described as backward-compatible

This is stated as a correction to a published claim rather than quietly folded
in. **v1.17.7's own release notes say:**

> "This is a backward-compatible governance and tooling release. The
> `reconciliation_audit` addition to the closeout-decision schema is a
> required-field change to that internal closeout-tooling contract (not a
> consuming-project-facing API); every other change in this release is purely
> additive."

The notes correctly identified it as a required-field change and still
classified the release as backward-compatible, on the ground that the closeout
tooling was internal. **For any adopter calling `select_closeout()` directly it
was a breaking change, and it went out in a patch increment from 1.17.6.**

If you upgraded across 1.17.7 and your calls still work, you are either not
calling `select_closeout()` directly or you already adapted. If you skipped
that line, treat `reconciliation_audit` as new to you now.

The absence of any mechanism validating a change's declared classification
against the change itself is a known governance gap. It is recorded and routed;
it is **not** repaired by this release, and nothing here should be read as
having closed it.

### 2. The publication provenance records changed shape, and their schema versions moved

Both records are published provenance an adopter may be parsing.

| Record | Was | Now |
|---|---|---|
| Fresh remote state | `dual-hat-fresh-remote-state/1.0` | `dual-hat-fresh-remote-state/2.0` |
| Publication provenance | `dual-hat-remote-publication-provenance/1.0` | `dual-hat-remote-publication-provenance/2.0` |

In both records:

| Field | Was | Now |
|---|---|---|
| `fetch_endpoint_identity` | a single string | **removed** |
| `push_endpoint_identity` | a single string | **removed** |
| `fetch_endpoint_identities` | — | a list, one entry per configured endpoint, in configured order, not deduplicated |
| `push_endpoint_identities` | — | the same |

The `not_applicable_nonpublishable_plan` placeholder carries the same `/2.0`
schema string.

**Why the scalars were removed rather than kept alongside.** The endpoint
verification queried `git remote get-url --push origin` without `--all`. Git
returns one URL from that query and pushes to *every* configured
`remote.origin.pushurl`, so a second, unapproved push endpoint was invisible to
the check — demonstrated offline with two bare repositories and a real push, in
which the check returned a PASS record while both repositories received the
identical commit. The record then wrote that unverified endpoint into the
publication provenance **as a singular verified fact**.

A scalar cannot state how many endpoints an assurance covers, so it reads as
complete whether it is or not. The plural field enumerates every endpoint
proven and its own length is the verified-endpoint count. Keeping the scalar
would have left a consumer able to go on drawing the singular conclusion the
repair exists to make impossible, which is why the field is gone rather than
deprecated.

**If you parse these records:** read `*_endpoint_identities` and expect a list.
A consumer reading the old scalar will find it absent rather than stale — also
deliberate, so the change surfaces as a failure rather than as a silently
missing value.

### 3. The maturity vocabulary is now derived from the major, so new values exist

`release_maturity()` stamped **every** major at or above 1 as `stable_1_x`. It
now derives the label from the major the version actually carries.

| Version | Was | Now |
|---|---|---|
| `0.9.0` | `functional_pre_1_0` | `functional_pre_1_0` (unchanged) |
| any `1.x` | `stable_1_x` | `stable_1_x` (unchanged) |
| `2.0.0` | `stable_1_x` | **`stable_2_x`** |
| `3.4.1` | `stable_1_x` | **`stable_3_x`** |
| `10.0.0` | `stable_1_x` | **`stable_10_x`** |

`maturity` appears in `release/VERSION.json` and in the release manifest
(`dual-hat-<version>.release.json`). **Anything matching it against a fixed set
of two strings stops matching at this release.** Match on the pattern
`stable_<major>_x`, or derive the expected label from the version, rather than
enumerating.

Nothing changes at any 1.x version, so this is invisible until a 2.x or later
release — which is precisely why it survived: `VERSION.json` carried the same
value the function derived, so the two agreed and were both wrong.

### 4. Adopter platform profiles are admitted against the shipped version, not a constant

The active core version is now resolved from `release/VERSION.json` at call
time. It was previously a hardcoded `1.11.0`, which had been wrong for seven
minor releases.

**An adopter profile that passed only because it copied the shipped example
will now fail.** That is the defect surfacing, not a regression. Set
`dual_hat_core_version` in your platform profile to the version you actually
installed.

**A known limitation, stated rather than left to be discovered.** The
comparison is exact string equality on the full semantic-version triple, so
**every patch release invalidates every adopter profile.** Whether that is the
right contract is an open policy question; it is recorded and is deliberately
not answered by this release. Expect to update your profile's declared core
version on every upgrade until it is.

### 5. Obligation text moved between framework files

**This is the group a migration document that names only signature changes
would miss, and it is not hypothetical.** An adopter test that asserts framework
text lives in a particular file is exactly what this repository's own tests
were: two separate changes in this release exist solely to re-point **twenty**
such tests, and twelve of those twenty were in nobody's inventory when the work
started. If you followed this framework's testing practice faithfully, you are
the adopter most affected here.

Obligations that were duplicated across files are now single-sourced, with the
other locations deferring by reference:

| Obligation | Sole home now | Now defers by reference |
|---|---|---|
| Active-task continuity | `framework/DUAL_HAT_FRAMEWORK.md` | `governance/ROLE_TRANSITIONS.md` |
| Dispatch monitor-set duty | `GOVERNING_PRINCIPLES.md` | `governance/CONFORMANCE_POLICY.md` |
| Turn-exit audit, role-neutral body | `framework/DUAL_HAT_FRAMEWORK.md` | `governance/ENGINEERING_AGENT_GUIDE.md`, `governance/ARCHITECTURE_OFFICE_GUIDE.md` — each keeps only its own item 0, the role-label check |

Eight further duplicated sites were single-sourced across
`governance/CODE_REVIEW_CONTRACT.md`, `guides/OPERATING_MODES.md`,
`planning/PLANNING_MODEL.md` and `process/PHASE_RUN_PROTOCOL.md`. Three
sentences were deliberately **not** removed, because each states something its
canonical home does not.

Also relocated or re-pointed: `START_HERE.md`'s required sequence now loads its
own governance documents; `README.md`'s Framework-areas list and release pointer
changed; and `prompts/ENGINEERING_AGENT_PROMPT.md`'s cross-reference to
`framework/DUAL_HAT_FRAMEWORK.md` moved with the text it points at.

**Recommended adaptation:** assert on an obligation's presence *in the corpus*,
not in a named file. The framework will keep consolidating duplicated
obligations, and a test pinned to a filename will keep breaking. A test that
searches the governed document set for the obligation's substance survives
relocation; one that reads a specific file does not.

### What this release does NOT do

Stated so none of it is inferred from the fact that a major version shipped.

- It does **not** change any governing rule's text, numbering, or wording.
- It does **not** resolve the exact-equality profile-conformance question in
  group 4.
- It does **not** add validation of a change's declared backward-compatibility
  classification, the gap that let group 1's second entry ship in a patch
  release.
- It does **not** change `insteadOf` handling in the endpoint check. URL
  rewriting is reported by `git remote get-url`, so the identity comparison
  fails closed. That is correct behaviour and is now protected by a regression
  test.
