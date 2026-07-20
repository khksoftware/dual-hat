<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat

## Choose how the roles work together

Dual Hat supports both **Integrated Mode** and **Split Mode**, with Integrated as the default. The plain-language [Integrated and Split Dual Hat Modes guide](guides/OPERATING_MODES.md) explains roles, pros and cons, approval, safe switching, recovery, review, acceptance, archival, platform profiles, and ordinary commands. The [platform-profile contract](governance/PLATFORM_PROFILE_CONTRACT.md) makes capability preflight and hard-stop behavior prominent.

Dual Hat is a product-neutral operating framework for governed software development. The Architecture Office owns intent, requirements, boundaries, trade-offs, and acceptance; the Engineering Agent owns implementation, validation, publication, cleanup, and complete exit reporting.

Start with the [operating model](architecture/OPERATING_MODEL.md), [bootstrap guide](process/BOOTSTRAP.md), and [operating guide](guides/OPERATING_GUIDE.md). The [Architecture Office guide](governance/ARCHITECTURE_OFFICE_GUIDE.md) and [Engineering Agent guide](governance/ENGINEERING_AGENT_GUIDE.md) explain role practice. [Canonical Entrypoints](repository/CANONICAL_ENTRYPOINTS.md) says where to begin; the [Canonical Domain Index](repository/CANONICAL_DOMAIN_INDEX.md) says which role owns each kind of truth. Use the [command reference](reference/COMMAND_REFERENCE.md) for standalone validation and bootstrap commands.

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
