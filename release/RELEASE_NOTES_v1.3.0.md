<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.3.0 Release Notes

Dual Hat 1.3.0 strengthens execution continuity and delegated-work visibility.
Long-running execution and monitoring should be assigned to a dedicated
sub-agent when independent work remains, while the primary agent retains
integration and user-communication accountability.

Before delegation, the primary agent declares the worker, scope, next
milestone, heartbeat interval, and terminal conditions. It consumes worker
messages before status and final responses, reports terminal state without
waiting for the user to ask, and does not close a workflow in a way that would
strand an invisible active worker or completed result.

Authorized work remains active until complete and reported. Before completion,
the only permitted stop or pause conditions are an explicit user instruction,
required user decision or input, a required Architecture Office decision, or
an explicitly specified stop gate. Recoverable tool failures, long waits,
delegated work, elapsed time, partial progress, context compaction, and the end
of a message are not stopping conditions. Integrated Mode routes required
Architecture decisions directly to the `[Architect Office]` hat with a
resumable checkpoint.

This is a backward-compatible additive minor release. Existing 1.x work-item,
profile, handover, and authority concepts remain available, and no mandatory
control is weakened.
