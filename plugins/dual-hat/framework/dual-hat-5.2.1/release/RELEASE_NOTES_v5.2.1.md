<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 5.2.1

A patch release. It changes the framework's own tests and one changelog heading, and nothing an adopter runs.

## What changed

- **A leaner test suite.** Every framework test was asked to prove its need: a live subject, a behaviour something relies on, a regression that could realistically happen and would do real harm, no other test already catching it, and an assertion that can actually fail. Tests that failed any of those were removed. That covered assertions on documentation wording, echoes of constants and schema shapes, and duplicate angles on a single behaviour.
- **Changelog.** The 5.2.0 entry had a stray undated heading beside its dated one. It is removed.
- **Quality-review test.** It no longer assumes the shipped version sits below the assurance threshold.

## Upgrading

Nothing to do. No governance text, schema, gate or tool behaviour changed.
