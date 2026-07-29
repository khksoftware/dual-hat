<!-- SPDX-License-Identifier: Apache-2.0 -->

# Installation and Project Binding

Verify a versioned release checksum, extract the framework outside the product repository, open the target folder in the agent host, and say: `Use the Dual Hat framework in <path> to onboard the repository currently open.`

**External or user-level installation** keeps the framework outside the product tree. It gives a cleaner tree and centralized updates, but the project depends on a machine-local pinned path and can drift if its version/checksum is not recorded.

**Pinned project-local binding** records a bounded `.dual-hat/` footprint with the framework identity, version/checksum, configuration, governance/handoff state, and installation metadata needed by that project. It improves reproducibility and portability, but adds repository footprint and update responsibility. It never blindly vendors the complete framework.

The onboarding approval package asks which model to use unless approved project policy already decides. Migration between models is a governed change: create a fresh plan, preserve the current binding as rollback evidence, approve the target, apply only at a safe work-item boundary, validate, then remove only manifest-owned old state.

Updates verify the new package/checksum, compare compatibility and migration notes, checkpoint project state, revise the binding, validate, and retain a rollback point. Rollback restores the prior binding record and framework version. Removal validates exact ownership and removes only the binding’s declared footprint. Re-onboarding reads current repository evidence and prior binding as context but produces a new approval package.

Binding computes the canonical path-and-content tree checksum itself and compares it with the approved expected checksum; a caller assertion that a checksum was verified is not evidence. Onboarding and removal consume distinct authority-bound approval receipts tied to the exact package or binding bytes. A name, `approved` boolean, or crafted plan cannot authorize mutation.

If the configured path is missing, checksum differs, the target version is incompatible, a linked path escapes containment, or removal ownership is ambiguous, stop. Do not guess a replacement installation or delete unknown `.dual-hat/` content.
