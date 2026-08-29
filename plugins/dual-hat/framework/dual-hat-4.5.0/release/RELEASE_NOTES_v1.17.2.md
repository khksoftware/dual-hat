<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.2 Release Notes

Dual Hat 1.17.2 closes a role-transition gap discovered in production use: an
agent operating in Integrated Mode continued executing Engineering-authority
work after its sealed work item closed, because the framework's own
persistent-execution and no-idle continuation rules could be read as covering
that gap when conversational instructions kept arriving.

Those continuation rules now explicitly govern behavior only within an
active sealed order; they never substitute for one. A work item's closure
terminates Engineering authority immediately, regardless of continued
conversational instructions, side requests, or an apparently obvious next
task. A direct, specific, or urgent user instruction is a request for
Architecture to classify and seal -- not itself a sealed order. Before any
Engineering action, the framework now requires verifying that a currently
bound, hash-valid sealed order covers the exact action about to be taken; if
none exists, the agent returns to Architecture and seals one (a lightweight
order is sufficient for small or continuation work) before resuming.

This is a backward-compatible governance clarification. No schema, API, or
required-field change accompanies it.
