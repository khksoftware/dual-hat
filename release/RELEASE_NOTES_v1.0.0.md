<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.0.0 Release Notes

Previous version: 0.2.0. Proposed version: 1.0.0. Classification: breaking major release.

## Rationale

This release makes previously implicit authority and execution assumptions explicit: Integrated and Split modes, independent roles and lifecycle states, sealed work orders, semantic Capability/GOV classification, Architecture-only acceptance, acceptance-driven archival, and a platform-neutral core implemented through replaceable profiles. These public governance contracts are incompatible with treating the 0.2 lifecycle as sufficient, so a major version is required.

## Migration

Existing historical records remain valid and are not renumbered. New work should declare mode, role, state, type, sealed approval hash, and selected profile. Products adopting 1.0.0 must map concrete tooling into a conformant Tier 2 profile, run capability preflight before mutation, use governed handoffs for mode/profile switching, and reserve acceptance and archival for Architecture.

## Compatibility and limitations

The 0.2 planning artifacts remain readable. A 0.2 execution profile is not automatically 1.0-conformant. No vendor, operating system, editor, model, runtime, shell, process, or repository host is required by the core. Profiles may specialize mechanisms but may not weaken mandatory rules. Any known or runtime-discovered mandatory gap blocks execution and conformance until governed disposition.
