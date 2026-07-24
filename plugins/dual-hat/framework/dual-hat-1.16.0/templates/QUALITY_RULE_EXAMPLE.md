# Commented Quality Rule Example

Copy `QUALITY_RULES.json` to a configured user-rule source and add rule objects. JSON is the canonical editable and machine-readable source; this Markdown explains each field and is never generated over the user's file.

- `rule_id`: stable user-owned identity such as `USER-QUALITY-001`.
- `scope`: optional arrays for repositories, paths, artifact types, work-item types, and review categories; narrower matching scope wins.
- `review_tiers`: any of `light`, `standard`, and `deep`.
- `action.type`: `require`, `recommend`, `prohibit`, `ignore`, `suppress`, `replace`, `adjust_severity`, `require_evidence`, `require_manual_review`, `trigger_deeper_review`, `accept_known_tradeoff`, `defer_until_trigger`, or `exempt`.
- `action.target_rule_id`: required when overriding an Architecture rule.
- `precedence`: use `user` for user-authored rules.
- `status` and `lifecycle_state`: an automatically active rule uses `enabled` and `active`.
- `revision`, dates, provenance, rationale, owner, and conflict behavior preserve governance and traceability.

Example: to suppress `REVIEW-MAINT-001` in Light and Standard review, use those two tiers, action `suppress`, and target `REVIEW-MAINT-001`. The rule remains active in Deep review. A conflict with a non-waivable control is preserved and reported; it is never silently applied or deleted.
<!-- SPDX-License-Identifier: Apache-2.0 -->
