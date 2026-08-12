<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.17.1 Release Notes

Dual Hat 1.17.1 completes five governance items that were part of the
reconciled 1.17.0 carried-forward set but were not actually present in the
published 1.17.0 release content.

Defect closure now requires repairing both the concrete behavior and the
failed or missing prevention/detection defense that let it escape, adding
defect-sensitive executable regression evidence, checking directly analogous
instances, and obtaining independent adversarial review of the countermeasure
before closure; the implementing role cannot approve its own prevention or
detection repair.

Claims about locks, leases, ownership tokens, conditional takeover, or
coordinated restart now require executable competing-actor and adverse-timing
evidence against the actual control; structural inspection and happy-path
tests may supplement that evidence but cannot substantiate race-safety on
their own.

Consequential parallel workflows now require exactly one authoritative
orchestrator with pure bounded parallel workers, immutable leases, and
maximal-prefix checkpoint salvage with deduplicated residual retry; canonical
publication and cursor advancement occur atomically and only across a fully
validated contiguous prefix, and opaque status or heartbeats never advance
authority on their own.

The active-session record is now maintained throughout execution rather than
only at closure or switchover, and a governed chat-switchover protocol takes
a fresh authoritative snapshot, reconciles every in-flight task and owned
process, regenerates one compact handoff artifact, and gives an explicit
safe-to-switch signal without pausing healthy work.

Every hash gate now declares its byte policy -- repository-byte identity for
tracked artifacts, or UTF-8-without-BOM canonical-LF-newline text that
normalizes CRLF and rejects BOM/bare CR -- so platform checkout newlines do
not create false drift while substantive worktree changes still fail, and no
gate validates a mutable worktree input by hashing a committed copy that
could hide current drift.

This is a backward-compatible additive governance release. Existing 1.x
authority, lifecycle, schema, profile, handover, and compatibility contracts
remain unchanged.
