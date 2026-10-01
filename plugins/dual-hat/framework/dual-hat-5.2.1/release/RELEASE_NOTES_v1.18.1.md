<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.18.1 Release Notes

Dual Hat 1.18.1 closes two related gaps in delegated-work integrity and adds
an independent-review gate over the framework's own governance-rule changes.

`GOVERNING_PRINCIPLES.md` rule 23 is broadened. It previously required an
agent resuming across a context compaction, or a single long-running task
that had not revisited a foundational fact in a long time, to re-derive its
working method or belief from the current source rather than a stale prior
read. Rule 23 now states the same underlying discipline as a general
principle that applies at any point in a session, not only at those two
named trigger points: a delegated task must never be reported, recorded, or
tracked as dispatched, in progress, running, or awaited unless that status
is verified against a real dispatch call just made or an independent
task-registry check. An interruption arriving between deciding to delegate
and actually delegating must leave the tracking artifact reading "not yet
dispatched," never "in progress." No new rule number is introduced; the
context-compaction and long-running-task triggers remain named as
particularly important, still-covered cases of the same general rule.

`GOVERNING_PRINCIPLES.md` gains rule 32: any candidate governance-rule
change -- a new rule or an amendment to an existing one -- now requires
review by an independent Architect reviewer, distinct from whoever drafted
the change, before it counts as codified, adopted, or slated for
propagation. Committing rule text to canonical source is drafting, not
adoption; every tracking artifact describing a pending rule change must say
so explicitly rather than imply finality. This generalizes the
independence-and-evidence standard already required for Definition-of-Done
closure and for technical-debt acceptance review to the framework's own
rule set, including itself: rule 32 was applied to its own adoption, and to
the rule 23 broadening drafted alongside it.

`planning/TECHNICAL_DEBT.md` gains an independent-review-before-final-
acceptance requirement for the generic technical-debt authority. A resolved
item's status is the resolving party's own completion claim, not final
acceptance; final acceptance additionally requires a reviewer distinct from
whoever performed the resolution to re-derive the resolution's own
validation directly and record that verification separately -- reviewer
identity, verdict, and the evidence actually checked -- rather than accept
the resolver's narrative at face value. A consuming project binds the
reviewer role to a concrete authority and recording mechanism without
narrowing the requirement.

This is a backward-compatible governance release. It broadens one existing
rule, adds one new rule, and adds one independent-review requirement to the
technical-debt authority; nothing consuming-facing changes.
