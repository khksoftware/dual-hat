<!-- SPDX-License-Identifier: Apache-2.0 -->

# Profile Composition and Precedence

The platform-neutral core is Tier 1. Replaceable implementation profiles are Tier 2 and may specialize mechanisms or add stronger safeguards only. Profile precedence is always core-governs. Profile selection requires compatible versioning and capability preflight; absence, ambiguity, or failure of a mandatory implementation is a hard stop.

Dual Hat is the generic authority. A product profile binds neutral roles to concrete paths, commands, protected assets, branch policy, validation suites, release rules, and extensions.

A profile may add or narrow requirements. It may not weaken an invariant or duplicate the complete generic text. Every extension states its generic authority, additions, deliberate overrides, rationale, compatibility effect, validation, and retirement trigger. When framework and profile conflict, fail closed and resolve the conflict explicitly; do not infer that product proximity wins.

Profiles never introduce a framework dependency into product runtime. Generated prompts, work orders, sessions, and handovers are assembled from the generic contract plus the active profile, and identify both inputs.
