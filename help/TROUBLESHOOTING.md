<!-- SPDX-License-Identifier: Apache-2.0 -->

# Troubleshooting

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
