<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.5 Release Notes

Dual Hat 1.17.5 strengthens the delegation rule for parallelizable work.
The prior rule ("prefer delegating long-running execution and monitoring
to a dedicated sub-agent") only applied once work was already known to be
long-running, and only covered continuing independent tasks while it
completed. The rule now sets a standing default: whenever the runtime
supports it, keep the primary agent on standby to orchestrate and remain
directly available for user interaction, rather than itself performing the
bulk of hands-on work-item execution. Any capability or governance
work item, regardless of how many streams it is divided into, delegates to
sub-agents by default -- not only work already identified as long-running.
New work or investigation a user interaction surfaces mid-session
delegates the same way, unless doing so is reasonably believed to
interfere with another already-active stream.

This rule had been independently restated at full length in two places
(`governance/VALIDATION_AND_PARALLELISM.md` and
`prompts/ENGINEERING_AGENT_PROMPT.md`); both now carry matching wording for
the strengthened rule rather than drifting further apart, with a
regression test checking the shared phrasing in both.

This is a backward-compatible governance clarification. No schema, API, or
required-field change accompanies it.
