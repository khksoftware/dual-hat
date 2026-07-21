<!-- SPDX-License-Identifier: Apache-2.0 -->

# Troubleshooting

## Onboarding or model binding stopped

An onboarding stop normally protects one of four boundaries: the approval package changed, a path crosses a symlink/reparse point, executable content has not passed trust review, or the requested abstract tier cannot be evidenced. Keep the generated package or handoff, correct the path or configuration, obtain the required approval or model capability, and resume from the recorded hash. Do not bypass the stop by directly running project scripts, installing dependencies, copying the full framework into the repository, selecting a production provider implicitly, or lowering a mandatory tier.

If an external framework path is unavailable, restore the exact version/checksum or approve a governed migration. If `.dual-hat/` contains unknown files, do not use automatic removal; classify ownership first.

- Conflicting mode or role: stop mutation, compare the sealed order and transition package, and return to the last safe boundary.
- Stale work-order hash or ambiguous approval: do not enter Engineering; revise/reapprove/reseal or obtain unambiguous intent.
- Context loss: reload repository state and governed handoff; never reconstruct authorization from memory.
- Failed archival: retain controlled active state, report failure, and retry only after repair.

- Conflicting rules: identify generic authority and product profile; fail closed and correct composition.
- Missing domain owner: add or consolidate an operational owner, then update the capability inventory; a vague overview sentence is insufficient.
- Clean-checkout-only failure: reproduce in detached validation, repair packaging/path/discovery ownership, and retain the regression.
- Excessive disk activity: stop duplicate scans, inspect owned process trees and I/O, exclude archives/workspace/caches, clean orphans, then resume bounded work.
- Stale handover/session: regenerate both human and machine state from live repository inputs and validate parity.
- External drift: do not overwrite; compare prior manifest ownership, reconcile manual changes with the stakeholder, and publish forward.
- Deferred item never wakes: implement trigger, selector, invoker, history, retry/terminal behavior, and tests—or label it planning-only.
- Planning reconciliation fails: preserve the history, correct the earliest broken transition or current projection, and rerun `tooling/planning_reconciliation.py`; never rewrite a valid prior event to hide drift.
- Documentation mismatch: block closure until commands, paths, schemas, templates, and behavior converge.
- Failed publication: preserve the local commit, report exact remote/auth state, and never claim success or force-push.
