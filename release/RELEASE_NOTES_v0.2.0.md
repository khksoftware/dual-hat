<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 0.2.0 Release Notes

Dual Hat 0.2.0 completes the framework's minimum executable planning lifecycle. Adopters now receive canonical backlog, trigger-governed future-work, and append-only planning-history contracts, templates, bootstrap outputs, examples, reconciliation tooling, and tests.

The reconciler verifies unique current IDs, complete item and trigger fields, unique events, continuous status transitions, chronological per-item history, current/history agreement, and supersession semantics. It deliberately does not authorize implementation; a work order or equivalent decision remains required.

## Version decision

- Previous version: `0.1.0`
- Selected version: `0.2.0`
- Classification: backward-compatible additive framework capability
- Affected public contracts: planning schemas, templates, bootstrap output,
  standalone validation, help, and the export allowlist
- Compatibility: existing `0.1.0` repository content and lifecycle states remain
  valid; no prior schema, template, command, or path was removed or reinterpreted
- Migration requirement: none for existing deployments; adopters opt into planning
  reconciliation by adding the new files from the templates
- Rationale: first-class backlog, future-trigger, planning-history, and
  reconciliation support is a material new capability, so a patch would understate
  the change; no incompatible contract warrants a major increment

The `0.2.0` bootstrap creates the three new planning files for newly bootstrapped
products. Existing products are not silently rewritten.

## Known limitations

Planning reconciliation validates declared state, traceability, transitions,
supersession, and closure agreement. It does not prioritize work, authorize a
capability, mutate planning records, schedule execution, or replace product-specific
roadmap policy.

Release packaging now uses the canonical export allowlist in the development
repository and the bound export manifest in the standalone source publication.
Both routes select the same canonical source set; generated publication controls
and prior release products remain excluded.

Versioned release-product directories are ignored by default. This release remains
local and release-ready unless a separate authority explicitly permits repository
release publication; historical tracked release products are not rewritten.

To verify the included lifecycle fixture, run the planning reconciliation command in `examples/planning-lifecycle.example.md`, followed by the standalone commands in `reference/COMMAND_REFERENCE.md`.
