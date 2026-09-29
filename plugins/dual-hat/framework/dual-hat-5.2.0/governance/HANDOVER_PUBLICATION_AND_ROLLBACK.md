<!-- SPDX-License-Identifier: Apache-2.0 -->

# Handover, Publication, and Rollback

A platform-contract stop handoff records role, mode, work-item identity, sealed hash, profile identity/version, repository/remotes and dirty state, completed/pending steps, partial outputs, temporary/ignored continuation state, containment or rollback, and the sole permitted next action. Publication remains blocked until Architecture disposition resolves the mandatory gap.

The current handover is a replacement-maintained human artifact with a machine companion. It identifies current product state, active and completed capability state, open decisions, publication expectations, evidence locations, and exact continuation boundaries. Generated companions bind canonical inputs and rendered content; they do not become an independent source of truth.

Default publication uses a short-lived capability branch, bounded interim commits when they aid recovery, synchronization with the canonical branch, candidate validation, one coherent capability publication commit, committed-tree validation, push, remote-alignment verification, and branch deletion. A work order may authorize another transparent forward-only policy. Never amend, force-push, reset, or conceal a published correction.

Rollback requires explicit authority, a recorded target, affected-state inventory, compatibility and data-loss analysis, a reversible execution plan, and full validation afterward. Unexpected external divergence fails closed and requires reconciliation before publication.
