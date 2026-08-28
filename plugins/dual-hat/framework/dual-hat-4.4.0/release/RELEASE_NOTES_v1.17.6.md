<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.6 Release Notes

Dual Hat 1.17.6 closes two related gaps in delegated-worker discipline,
both caught live in a governed session. A worker completed a bounded
checkpoint and stopped exactly as instructed; the primary agent was then
pulled into a newly surfaced finding without first resuming it, and the
worker sat idle for an extended stretch while believed to still be
running. Separately, three continuations of the same assignment were each
launched as fresh workers instead of resumptions of the existing one,
discarding accumulated context and forcing repeated, avoidable
re-derivation of already-established state before any new work could
begin.

The turn-exit-audit reconciliation obligation ("before every final
response, reconcile... delegated workers") already existed but didn't
survive contact with a competing, more salient new thread: a lengthy
response addressing the new thread satisfied the letter of "before every
final response" without the reconciliation actually happening. This
release names the failure mode explicitly rather than relying on the
general principle alone, and adds an explicit preference for resuming an
existing worker over launching a new one for continuation work.

Separately, this release drops the plugin manifests' independent packaging
version sequence. It was bumped in lockstep with every prior framework
refresh but never for a genuinely independent packaging-only reason, which
made it redundant with `framework_version` and an easy field to forget to
update. Both agent-host plugin manifests' `version` fields now simply equal
the bundled framework version.

This is a backward-compatible governance clarification. No schema, API, or
required-field change accompanies it.
