<!-- SPDX-License-Identifier: Apache-2.0 -->

# Platform and Toolchain Profile Contract

Dual Hat uses two tiers. The normative core is platform-agnostic. A separately governed profile may implement and strengthen the core for a concrete IDE or Editor, Agent Runtime, Language Model provider, shell, operating system, process tree, repository host, or Tooling Adapter.

A profile declares identity, supported configuration, applicability, implemented core version, monitoring and recovery mechanisms, temporary/detached behavior, authentication constraints, limitations, validation, and handoff specialization. `core_governs` and every non-weakening guarantee are mandatory. Profiles are replaceable; the core never imports or depends on them.

Before governed execution, the selected profile performs a capability preflight against the sealed work order and applicable core. It declares supported mandatory capabilities, permissions and tools, degradation, unavailable services, environment limitations, version compatibility, and uncertainty. A profile may add stronger safeguards but may never redefine a mandatory core rule as optional.

If the selected platform cannot uphold the Dual Hat contract, work stops. The limitation is shown to the user and the Architecture Office, and execution resumes only after the environment, profile, work order, or framework has been properly resolved.

This is a hard stop, not a best-effort fallback. The active role stops at the safest boundary, blocks related mutation, preserves repository and execution state, names the exact unmet requirement and limitation, records partial work and containment, and produces a resumable handoff. The report classifies the gap as unsupported, unavailable, misconfigured, temporarily degraded, permission/access, security/rights, tool defect, profile defect, or core-contract ambiguity. No profile, an ambiguous mechanism, or a runtime-discovered gap blocks execution until Architecture provides a governed disposition.

Architecture may repair or replace the profile, change the environment or mode, revise the work order without weakening the core, govern a versioned core revision, or abort with safe preservation or disposal. A platform limitation never becomes silent precedent.
