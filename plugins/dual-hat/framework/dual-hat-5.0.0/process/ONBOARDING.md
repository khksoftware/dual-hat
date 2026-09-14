<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository and Product Onboarding

Onboarding is plan-first. Inspection and product discovery produce a deterministic approval package; creating a repository, replacing a scaffold, binding Dual Hat, accepting technical debt, or changing product implementation waits for explicit user approval of that package.

## Three repository scenarios

1. **No repository.** Discover the product first. Propose a technology-neutral structure, implementation options, a minimal first milestone, roadmap, and work-item sequence. Create the repository or files only after approval. Until then the user can revise or abandon the plan without cleanup.
2. **Empty or nearly empty repository.** Inspect metadata and initial files without treating scaffolding as authoritative. Discover the product, then propose retaining, replacing, or migrating the scaffold. Material mutation waits for approval.
3. **Existing project.** Begin read-only. Inventory purpose clues, structure, architecture, entry points, dependencies, tests, deployment, documentation, persistence, security/privacy/rights/compliance boundaries, defects, debt, migrations, stale or duplicate authorities, planning state, and implementation/vision mismatches. Classify hooks and scripts; do not execute them or install dependencies during trust review.

Quick depth supports small low-risk exploration; Standard is the default practical assessment; Deep is for large, mature, risky, regulated, externally distributed, or poorly understood systems. Risk may require deeper review, but the package explains why. Known repository evidence is reused and questions are limited to missing decisions.

Deep performs bounded content-aware subsystem, purpose, deployment, persistence, rights, privacy/security/compliance, dependency, migration, operations, implementation/vision mismatch, and debt assessment. Credential-like names and secret-bearing configuration are excluded before semantic inspection. Suspicious executable content or unresolved script risk creates material uncertainty and blocks approval until resolved.

## Product discovery and approval output

Discovery covers purpose, users, problem, vision, outcomes and measures, pain points, commitments, technical and business constraints, non-negotiable behavior, security, privacy, rights/licensing, compliance, deployment, environments, external services, dependencies, ownership, roadmap, risk, relevant cost/latency/operations limits, and the concrete models or host-managed selections available to satisfy Dual Hat's abstract model tiers.

The approval package contains the product and stakeholder models; protected characteristics; scenario and depth; operating-mode and framework-binding recommendations; an evidence-backed project-local model-tier mapping; architecture; risks; quality-rule discovery hashes; proposed rather than silently accepted debt; roadmap and next work items; triggers, dependencies, assumptions, unresolved decisions, mutation plan, and rollback. The mapping records each abstract tier, concrete selection or explicit unavailability, capability and availability evidence, environment fingerprint, confirmation, switching mechanism, and safe fallback or hard-stop behavior. Onboarding is incomplete when tiers remain abstract without a consuming-project mapping.

The project owns this mapping; portable Dual Hat source never names its providers or models. A changed adapter, host, provider/model inventory, model configuration, tool inventory, operating environment, capability evidence, availability, or material project risk invalidates the affected mapping. Regenerate and reapprove the mapping before governed work that depends on it; do not carry a stale selection forward because it happened to work previously. A stale or changed approval package must likewise be regenerated and reapproved.

Approval is an authority receipt bound to the exact package hash and source, not a caller-supplied boolean. Repository-detected debt enters the package as proposed-not-accepted evidence. Binding and removal use separate exact-operation receipts.

The trusted host adapter is the authority-receipt issuer boundary. It records a user-interaction event ID, authority identity, adapter identity, exact decision-payload hash, and evidence hash. Core onboarding validates that structure and binding; it does not claim that an untrusted caller-created mapping proves a human decision. Deployments must keep these mutation APIs behind the trusted adapter boundary.

The metadata inspector stays inside the authorized root, rejects symlink/reparse traversal, excludes credential-like files from general input, does not execute repository code, does not install dependencies, and does not upload content. Suspicious or materially uncertain existing projects stop for trust review.

After approval, the low-level bootstrap remains available for previously approved product profiles. Onboarding does not silently reinterpret that command as user approval.
