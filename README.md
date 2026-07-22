<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat

Dual Hat is a product-neutral operating framework for governed, AI-assisted software development. It separates two complementary responsibilities: the **Architecture Office** defines intent, requirements, boundaries, trade-offs, sequencing, and acceptance; the **Engineering Agent** implements, validates, publishes, and reports the work. One agent can wear both hats in Integrated Mode, or separate agents can perform the roles in Split Mode.

Use Dual Hat when a software project needs more than code generation: explicit authority, bounded work orders, traceable decisions, safe repository mutation, proportional validation, independent review, resumable execution, and reliable closure. It can onboard an existing repository, a nearly empty repository, or a project that does not yet have a repository, then adapt through a product-specific profile without weakening the framework's core controls.

Dual Hat is not an application runtime, programming library, hosted service, or substitute for the product's own architecture and toolchain. It does not make product decisions automatically or grant an agent unrestricted authority. It provides the governance, planning, execution, validation, continuity, and publication structure within which the user, Architecture Office, and Engineering Agent build the product.

## Choose how the roles work together

Dual Hat supports both **Integrated Mode** and **Split Mode**, with Integrated as the default. The plain-language [Integrated and Split Dual Hat Modes guide](guides/OPERATING_MODES.md) explains roles, pros and cons, approval, safe switching, recovery, review, acceptance, archival, platform profiles, and ordinary commands. The [platform-profile contract](governance/PLATFORM_PROFILE_CONTRACT.md) makes capability preflight and hard-stop behavior prominent.

Start with the [operating model](architecture/OPERATING_MODEL.md), [onboarding workflow](process/ONBOARDING.md), [bootstrap guide](process/BOOTSTRAP.md), and [operating guide](guides/OPERATING_GUIDE.md). The [Architecture Office guide](governance/ARCHITECTURE_OFFICE_GUIDE.md) and [Engineering Agent guide](governance/ENGINEERING_AGENT_GUIDE.md) explain role practice. [Canonical Entrypoints](repository/CANONICAL_ENTRYPOINTS.md) says where to begin; the [Canonical Domain Index](repository/CANONICAL_DOMAIN_INDEX.md) says which role owns each kind of truth. Use the [command reference](reference/COMMAND_REFERENCE.md) for standalone validation and bootstrap commands.

## First use

1. Obtain a versioned Dual Hat release package and its published checksum.
2. Verify the package checksum before extraction.
3. Extract the package outside the product repository you want to work on.
4. Open the target product repository—or the intended project folder when no repository exists—in a supported agent environment.
5. Tell the agent, in natural language: `Use the Dual Hat framework in <path> to onboard the repository currently open.`

Do not copy or dump the whole extracted release package into the product repository. During onboarding, choose either an external/user-level installation or a bounded pinned project-local binding such as `.dual-hat/`; the approval package explains reproducibility, path-dependency, update, migration, and repository-footprint tradeoffs before any product mutation.

Read [Repository and Product Onboarding](process/ONBOARDING.md) for the three repository scenarios and approval boundary, [Installation and Project Binding](guides/INSTALLATION_AND_BINDING.md) for setup/update/rollback/removal, and [Troubleshooting](help/TROUBLESHOOTING.md) when detection or binding stops safely.

First-use map: [no-repository, nearly-empty, and existing-project onboarding](process/ONBOARDING.md#three-repository-scenarios); [Integrated Mode and Split Mode](guides/OPERATING_MODES.md); [external and pinned project binding](guides/INSTALLATION_AND_BINDING.md); [model tiers and runtime binding](governance/MODEL_TIER_AND_RUNTIME_BINDING.md); [third-party dependency evaluation](governance/THIRD_PARTY_DEPENDENCY_EVALUATION.md); [update, rollback, and removal](guides/INSTALLATION_AND_BINDING.md); [troubleshooting](help/TROUBLESHOOTING.md); and [1.9.1 release notes](release/RELEASE_NOTES_v1.9.1.md).

## Framework areas

- `architecture/`: authority, reasoning, decisions, requirements, and invariants.
- `governance/`: conformance, repository boundaries, profiles, lifecycle, and human-decision rules.
- `planning/`: roadmap, reconciled backlog/history, phases, milestones, future-work triggers, and technical debt.
- `process/`: capability/phase execution, context retrieval, publication, closure, and recovery.
- `repository/`: blueprint, entrypoints, domain ownership, and completeness inventory.
- `sessions/`: active-session and current-handover maintenance.
- `validation/`: test strategy, detached/standalone validation, parallelism, and process watchdog.
- `prompts/`, `templates/`, `schemas/`, `tooling/`, and `examples/`: executable adoption assets.
- `guides/`, `help/`, and `reference/`: cross-cutting guidance, troubleshooting, and lookup material whose responsibility does not belong to one operating domain.
- `release/`: version, release policy, release notes, packaging, and publication rules.

The framework is Apache-2.0 licensed. Product profiles may add or narrow rules without duplicating or weakening generic authority. A source repository may remain canonical while an external Dual Hat repository is a forward-only derived publication; see [publication](release/PUBLICATION.md).
