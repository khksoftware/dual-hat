<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat

Dual Hat is a product-neutral operating framework for governed software development. The Architecture Office owns intent, requirements, boundaries, trade-offs, and acceptance; the Engineering Agent owns implementation, validation, publication, cleanup, and complete exit reporting.

Start with the [operating model](architecture/OPERATING_MODEL.md), [bootstrap guide](docs/BOOTSTRAP.md), and [operating guide](docs/OPERATING_GUIDE.md). The [Architecture Office guide](docs/ARCHITECTURE_OFFICE_GUIDE.md) and [Engineering Agent guide](docs/ENGINEERING_AGENT_GUIDE.md) explain role practice. [Canonical Entrypoints](repository/CANONICAL_ENTRYPOINTS.md) says where to begin; the [Canonical Domain Index](repository/CANONICAL_DOMAIN_INDEX.md) says which role owns each kind of truth. Use the [command reference](docs/COMMAND_REFERENCE.md) for standalone validation and bootstrap commands.

## Framework areas

- `architecture/`: authority, reasoning, decisions, requirements, and invariants.
- `governance/`: conformance, repository boundaries, profiles, lifecycle, and human-decision rules.
- `planning/`: roadmap, backlog, phases, milestones, triggers, and technical debt.
- `process/`: capability/phase execution, context retrieval, publication, closure, and recovery.
- `repository/`: blueprint, entrypoints, domain ownership, and completeness inventory.
- `sessions/`: active-session and current-handover maintenance.
- `validation/`: test strategy, detached/standalone validation, parallelism, and process watchdog.
- `prompts/`, `templates/`, `schemas/`, `tooling/`, `examples/`, and `docs/`: executable adoption assets.

The framework is Apache-2.0 licensed. Product profiles may add or narrow rules without duplicating or weakening generic authority. A source repository may remain canonical while an external Dual Hat repository is a forward-only derived publication; see [publication](docs/PUBLICATION.md).
