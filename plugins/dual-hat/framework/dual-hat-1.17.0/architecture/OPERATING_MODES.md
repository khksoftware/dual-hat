<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operating Modes and Role-State Model

Dual Hat has four independent dimensions: operating mode, active role, lifecycle state, and work-item type. They never substitute for one another.

## Modes

`integrated` is the default. Architecture and Engineering use one connected Execution Host and Repository Workspace, with explicit role transitions and a sealed work order. Shared access reduces copying but never combines authority.

`split` uses separate Architecture and Engineering Environments. Either environment may use a different IDE or Editor, Agent Runtime, Language Model, Tooling Adapter, machine, or participant. A complete Handoff Transport carries the sealed work order, hash, repository state, evidence, continuation state, and any required snapshot. Split mode is equally conformant.

Mode selection may be a product default or work-item override. A transition is allowed before drafting, after drafting, after approval but before execution, at a governed Engineering pause, after Engineering completion, before review, after acceptance, or between items. Active shared-state mutation must first reach a safe pause and seal resumable state.

## Roles and lifecycle

The active role is one of `architecture`, `engineering`, or `architecture_review`. Canonical new-item lifecycle:

`architecture -> work_order_ready -> author_approved_for_execution -> engineering -> engineering_complete | engineering_paused | engineering_blocked | engineering_aborted -> architecture_review -> accepted | accepted_with_follow_up | remediation_required | rejected -> archived`

`remediation_required` returns through a revised or still-valid sealed order to Engineering. Acceptance belongs only to Architecture. Engineering may recommend a disposition but cannot accept or archive its own work.

## Work-item types

A `capability` is a bounded product, runtime, data, workflow, or operational increment. A `gov` item is an independently bounded change to authority, lifecycle, execution protocol, shared governance schema, cross-repository contract, or role-operating model. A capability may carry tightly coupled governance necessary for product coherence; independently bounded framework work uses a GOV identity. Historical records retain their historical identifiers and schemas.

## Dependency and platform boundaries

The canonical model names Architecture Environment, Engineering Environment, Execution Host, Repository Workspace, Language Model, IDE or Editor, Agent Runtime, Tooling Adapter, Handoff Transport, and Review Context. Product profiles may document vendor-specific adapters as nonnormative examples. Dual Hat never depends on a product; product runtime never depends on Dual Hat, engineering administration, mutable workspace, or archives.

Every selected platform profile must pass preflight against the sealed work order and mandatory core requirements. If the platform cannot uphold the contract, work stops at the safest boundary; related mutation stays blocked while an explicit stop report and resumable handoff go to the user and Architecture Office. Switching mode, environment, or profile requires that governed handoff and an explicit Architecture disposition.
