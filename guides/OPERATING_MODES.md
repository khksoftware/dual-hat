<!-- SPDX-License-Identifier: Apache-2.0 -->

# Integrated and Split Dual Hat Modes

## What Dual Hat is

Dual Hat keeps design authority and implementation accountability distinct. Architecture decides what should be built, its boundaries, and whether the result is accepted. Engineering inspects the repository, executes an approved work order, validates and publishes it, and reports evidence. The hats may share tools, but never authority informally.

Four independent terms matter: **operating mode** is Integrated or Split; **active role** is Architecture, Engineering, or Architecture Review; **lifecycle state** records progress; **work-item type** is a product Capability or governance GOV item.

## Integrated Dual Hat Mode

Integrated mode is the default. Architecture and Engineering use one connected Execution Host or Repository Workspace. The user approves a sealed work order, explicitly enters Engineering, and explicitly returns to Architecture Review. Direct repository evidence and current local state remain available without copying.

Advantages: reduced copying; direct repository evidence; faster remediation loops; smoother pause/resume; lower stale-snapshot risk; easier automated handoff and archival.

Risks: role contamination; self-review bias; accidental Architecture-mode mutation; inherited Engineering assumptions during review; dependence on strong transition and authorization controls.

For material work, mitigate review risk with a fresh Architecture Review Context, independent read-only reviewer, or structured adversarial review when stronger separation is unavailable or disproportionate.

## Split Dual Hat Mode

Split mode places Architecture and Engineering in separate environments. They may use different IDEs or Editors, Agent Runtimes, Language Models, Tooling Adapters, machines, or people. A sealed work order and structured Handoff Transport replace shared context.

Advantages: clearer operational separation; naturally stronger review independence; reduced cross-role mutation risk; compatibility with different tools, models, machines, or people; useful isolation for high-risk work.

Disadvantages: more handoff work; slower remediation; stale prompts, reports, or snapshots; omitted local or ignored state; higher user ceremony; risk of executing an outdated order.

Neither mode is inherently more conformant. Integrated is the usability default; Split may be stronger where independence or isolation matters more.

## Integrated workflow

1. Architecture defines item type, scope, exclusions, assumptions, stop gates, repositories, validation, and publication authority.
2. Persist and hash the complete work order.
3. The user approves that exact sealed order.
4. Explicitly enter Engineering; a design question alone does not switch roles.
5. Engineering implements, validates, diagnoses, repairs established-contract defects, revalidates, publishes when authorized, and reports.
6. Engineering declares complete, paused, blocked, or aborted and seals resumable state when needed.
7. Explicitly enter Architecture Review, preferably fresh for material work.
8. Architecture accepts, accepts with non-blocking follow-up, requires remediation, or rejects.
9. Only accepted work archives; required remediation stays active.

## Split workflow

1. Architecture creates and seals the same complete order.
2. Package its hash, repository state, dirty-state declaration, expected ignored state, validation/publication authority, and continuation instruction.
3. Engineering verifies the package against the live repository before mutation.
4. Engineering executes and returns commits, validation evidence, exit report, handover, and snapshot or equivalent evidence when required.
5. Architecture verifies the complete evidence and freshness, not a summary alone.
6. Remediation uses a new or confirmed sealed order and another transfer. Acceptance remains Architecture-only.

## Approval, role entry, pause, and return

Ordinary natural language is sufficient when intent is unambiguous and a complete sealed order exists:

- “Use Integrated Dual Hat Mode for this work item.”
- “Use Split Dual Hat Mode for this work item.”
- “Make Integrated Dual Hat Mode my default.”
- “Keep this work item in Split Dual Hat Mode.”
- “Approve this work order and enter Engineering mode.”
- “Execute the approved work order.”
- “Begin Engineering execution.”
- “Pause Engineering and return to Architecture mode.”
- “Stop at the next safe boundary and return control to Architecture.”
- “Engineering is complete. Enter Architecture review.”

Execution language authorizes mutation only when the sealed hash is current, approval and intent are explicit, paths/actions are authorized, and no stop gate is active. Ambiguity fails closed.

## Mode switching

Safe boundaries are before drafting, after drafting, after approval before execution, at an Engineering pause, after Engineering completion, before review, after acceptance, or between items. Never switch during shared-state mutation; first finish the safe step and seal resumable state.

Suggested requests:

- “Prepare a handoff and switch this work item to Split Dual Hat Mode.”
- “Resume this work item in Integrated Dual Hat Mode.”
- “Complete the current safe step, seal execution state, and switch to Split Dual Hat Mode.”
- “Start Architecture review in a fresh integrated context.”

The transition package records mode, role, type, lifecycle, approved hash, repository/remote/dirty state, completed/pending steps, decisions, required local artifacts, next action, and continuation phrase.

## Review, disposition, and archival

Engineering may recommend but cannot decide disposition. Architecture may say:

- “Accept this work item and archive it.”
- “Accept this work item with non-blocking follow-up and archive it.”
- “Require remediation and keep it active.”
- “Reject the work item and return it for remediation.”

Accepted-with-follow-up archives only when follow-up is explicitly non-blocking and separately tracked. Required remediation remains active. Archival preserves intent, evidence, disposition, hashes, commits, and publication references; removes obsolete active packages; retains a minimal pointer; and never becomes a runtime dependency.

## Capability versus GOV item

A Capability is a bounded increment to product runtime, data, workflow, operational behavior, or user-visible functionality. A GOV item is independently bounded framework work affecting authority, protocol, lifecycle, shared governance schema, cross-repository contract, or role-operating model. Necessary framework support may accompany a Capability; separable framework work uses GOV identity. Historical archives are not mass-rewritten.

## Architecture-local change and Engineering repair

Architecture may directly update an exclusively Architecture-owned record only after an impact scan proves no shared schema, external consumer, Engineering behavior, validator, generator, publication, topology, integration, or synchronized propagation effect. Uncertain reach defaults to Engineering execution.

Engineering may iterate within approved architecture and repair current-work defects, stale references, dead paths, incorrect validators/tests, incomplete propagation, and directly analogous low-risk defects. It returns to Architecture for new entities, consequential lifecycle states, changed identity/rights/security/provenance/promotion/precedence, new dependencies/services, phase expansion, public-contract changes, or weakened guarantees.

## Recovery and degraded behavior

- Architecture context loss: reload decisions, sealed order, repository state, and planning—not memory alone.
- Engineering context loss: verify order hash and repository/dirty state, then resume from the sealed handoff.
- Dirty transition: pause and record or clean owned changes; never hide them.
- Interrupted mutation: report partial state, rollback/resume actions, and invalidated validation.
- Blocked or aborted execution: preserve a blocker/abort report and partial disposition.
- Missing report, snapshot, or ignored state: Architecture records the gap and never fabricates evidence.
- Stale hash or remote: stop, reconcile, and reseal or refresh.
- Failed archival or publication: retain active state and report failure.
- Independent review unavailable: disclose it and use structured adversarial review only when proportionate.

## Two-tier platform governance

Tier 1 is the platform-agnostic Dual Hat core: roles, lifecycle, modes, evidence, monitoring intent, validation, recovery, and conformance without dependency on a particular IDE, Editor, plugin, Language Model, Agent Runtime, shell, operating system, process/executable, repository host, or cloud provider.

Tier 2 is an optional replaceable platform/toolchain profile. It declares supported configuration, core version compatibility, process/session identification, monitoring cadence, host commands, temporary roots, authentication constraints, detached behavior, recovery, limitations, validation, and handoff specialization. Core governs and the profile may only strengthen or implement it. Without a profile, core still applies; use the safest reasonable mechanism and surface ambiguity rather than silently disabling safeguards.

Before governed execution, a selected profile must prove that every mandatory requirement can be upheld. If no conformant profile or implementation can do so, or if a gap appears during execution, work stops at the safest boundary. The limitation is shown to the user and Architecture Office, partial work is preserved or safely rolled back, and a resumable handoff records the exact gap and state. Work resumes only after explicit governed disposition. A profile cannot call a mandatory rule optional or claim partial conformance.

## Platform-neutral implementation example

An Architecture Environment may be a document workspace with repository read access; an Engineering Environment may be an IDE or Editor plus an Agent Runtime and shell. They may share an Execution Host in Integrated mode or exchange a hashed Handoff Transport in Split mode. Concrete vendor names belong in nonnormative profiles and do not change the core contract.
