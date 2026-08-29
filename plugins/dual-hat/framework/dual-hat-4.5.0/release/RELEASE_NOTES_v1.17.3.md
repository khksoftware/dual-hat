<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.3 Release Notes

Dual Hat 1.17.3 closes a distribution gap: the agent-host plugin bundle had
been shipping framework 1.17.0 since that release, while canonical source
moved on to 1.17.1 and then 1.17.2. 1.17.2 specifically fixed a
role-transition/authority defect ("an agent operating in Integrated Mode
continued executing Engineering-authority work after its sealed work item
closed") -- anyone installing Dual Hat through the documented plugin path
was still getting a framework build with that defect present. The plugin
bundle now tracks the current canonical version, and an automated test
asserts the bundle's `framework_version` and both plugin manifests'
`version` fields match `release/VERSION.json`, so this cannot drift
silently again.

Alongside that fix, this release also closes the remaining findings from an
independent architecture review of the standalone repository: the
secret-scanning gate that runs before every public release now recognizes
several additional common workspace-chat, cloud-console, and
payment-processor API key and bearer token formats, plus JWTs, on top of
its prior coverage; a stale README release-notes
link is fixed and now has a version-tracking regression test; two
product-leakage denylist patterns that had been reverse-engineered from one
past incident's literal numbers and path names are generalized, without
widening them into false positives against the framework's own generic
scaffold content; and the two same-basename `OPERATING_MODES.md` files now
cross-reference each other's distinct scope.

This is a backward-compatible tooling and distribution-hygiene release. No
schema, API, or required-field change accompanies it.
