<!-- SPDX-License-Identifier: Apache-2.0 -->

# Technical Debt Governance

Debt records do not authorize either a Capability or GOV item. A trigger selects the correct work-item type from semantic effect rather than title keywords and requires a sealed order before Engineering mutation.

Technical debt is a known gap between current implementation and the desired architecture, quality, operability, security, maintainability, or evidence standard. Discovery and backlog inspection are not remediation.

Each item records stable ID, category, severity, priority, owner, discovery source, rationale, impact, affected artifacts, accepted versus accidental status, remediation trigger, target phase or release, validation, dependencies, status, event history, and closure evidence. Valid states are proposed, accepted, scheduled, in progress, blocked, resolved, superseded, and rejected; profiles may narrow vocabulary without changing semantics.

Every transition creates a history event. Resolution requires changed implementation or an explicit accepted design correction plus validation; refreshing a timestamp does not improve status. Phase/release health reviews reconcile every unresolved item, enforce blocker budgets, and reauthorize carry-forward. Closure evidence identifies the fixing commit, tests, remaining risk, and planning links.

A resolved item's status is the resolving party's own completion claim, not final acceptance. Final acceptance additionally requires an independent reviewer -- distinct from whoever performed the resolution, never the same agent, session, or delegated worker that authored the fix -- to re-derive the resolution's own validation directly and record that verification separately from the resolver's own closure claim: reviewer identity, verdict, and the evidence actually checked. A resolution lacking this independent verification record does not carry final acceptance, however complete its own resolution narrative reads. Profiles bind the reviewer role to a concrete authority (e.g. an Architecture Office) and a concrete recording mechanism without narrowing this requirement.

## Debt is owed, and carry-forward is an act rather than a default

**An unresolved debt item is a commitment to repay, not a permanent register entry.** The register exists to make the obligation visible so it can be discharged at the earliest convenience; a record that is read, understood and left unchanged has been handled zero times, however often it has been looked at.

**Reading a debt item is a disposition point**, per the item-level rule in `planning/PLANNING_MODEL.md`: it leaves that act worked, re-owned, corrected or closed, and returning it unchanged is not among the outcomes. That rule is general to every planning register and is not restated here; what is specific to debt is that the obligation it disposes of is one somebody is owed.

**A percentage allocation is not a mechanism.** The obvious way to force repayment is a rule that some share of each unit of work is spent on debt. That rule has no runner: nothing measures the share, nothing refuses a unit of work that spent none, and a project discovers years later that the convention either never operated or drifted immediately. **An obligation stated as a proportion, with no detector, decays into an aspiration** — which is this framework's own arming constraint applied to planning rather than to principles. Where a repayment expectation is adopted, it is attached to a moment something already performs: a closure, a release gate, a health review that genuinely runs. If no such moment exists, the honest statement is that repayment is unenforced and depends on the stakeholder asking.

**Carry-forward is authorized explicitly or it is not carry-forward.** An item that survives a review because the review reauthorized it is managed. An item that survives because no review ran is unmanaged, and the two are indistinguishable from the register alone. A review therefore records the reauthorization per item, and an item with no such record from its most recent review is reported as unmanaged rather than as carried.

**The register's size is itself evidence, and it is read in a direction.** A backlog that only grows is not a backlog being managed proportionately; it is one whose repayment side never runs. Growth without a matching closure rate is a finding about the process rather than about any individual item.

**Advice.** Nothing in this framework's shipped source enforces any of this. There is no detector for an item put back unchanged, none for a review that did not run, and none for a register that only grows — the register, the reviews and the queues are all the adopting project's. It holds because a reasonable agent reads it and complies, and because the stakeholder who owns the debt is the one who notices when it has not been repaid.
