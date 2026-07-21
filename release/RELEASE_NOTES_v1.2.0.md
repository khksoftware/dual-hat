<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.2.0 Release Notes

Dual Hat 1.2.0 adds a mandatory decision contract for third-party tools,
libraries, SDKs, packages, runtimes, models, service clients, and other
dependencies. Before recommendation or adoption, both hats disclose licensing
and product implications, cost, intended-workload reliability, safety and data
movement, supply-chain exposure, hardware/platform needs, and current support
status. Multiple viable options receive a concise pros/cons comparison and an
explained recommendation.

The release also makes active-role identity visible in Integrated Mode: every
assistant-authored message begins with `[Architect Office]` or
`[Engineering Agent]`, matching the hat currently in force.

Approval is bound to the evaluated dependency and stated use. A material change
to licensing, cost, data flow, hardware, support status, or dependency class
requires a fresh evaluation and approval. Installations retain version/revision
pinning, integrity, rollback, and promised privacy controls.

This is a backward-compatible additive minor release. It does not change
existing 1.x work-item identities, authority boundaries, or readable historical
schemas, and it weakens no mandatory control.
