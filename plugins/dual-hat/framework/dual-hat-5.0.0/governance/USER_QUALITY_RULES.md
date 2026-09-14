# User-Defined Quality Rules

Users may persist quality rules without writing code. A rule can require evidence or review, prohibit or recommend a pattern, adjust severity, accept a known trade-off, trigger deeper review, defer to a trigger, exempt a defined scope, or suppress/replace an Architecture discretionary rule. It can apply globally or to selected repositories, paths, artifact types, work-item types, review categories, and tiers.

The precedence chain is: non-waivable legal, rights, privacy, authorization, security-boundary, repository-integrity, destructive-operation, external-publication, and mandatory Dual Hat core controls; explicit user rules; repository/project Architecture rules; Architecture defaults; reviewer heuristics. Within user rules, narrower matching scope wins, explicit tier selection wins, an explicit suppression wins inherited activation, and a later valid revision supersedes an earlier one. Equally specific conflicting rules are reported and stop the affected review.

A valid `enabled`/`active` manual rule becomes active automatically at the next review. Draft, suspended, superseded, and archived rules remain traceable but inactive. Invalid syntax, missing fields, ambiguous scope, unresolved equal-precedence conflict, or a conflicting non-waivable action is reported with the exact file/rule and fails closed when material. The source is preserved; Architecture does not silently delete, reinterpret, or weaken it.

## Files and refresh

Products configure common-schema sources with `QUALITY_RULE_SOURCES.json`. Canonical user-editable JSON files use `quality-rule.schema.json`; generated discovery inventories and effective plans are separate outputs and are never the edit target. The supplied empty template and commented Markdown example are safe starting points.

Before every review, the profile recursively discovers configured JSON sources, compares both filesystem metadata and SHA-256 content, detects addition/removal/rename/modification, parses and validates changed files, and rebuilds the effective set. Timestamps alone never establish freshness. The plan shows the tier, defaults, repository rules, user rules, suppressed/replaced rules, severity adjustments, conflicts, non-waivable controls, and hashes. Manual edits require no ingestion command; `quality_review.py reload` is an optional forced refresh.

Tier-aware suppression is literal. If a rule targets `REVIEW-MAINT-001` with `suppress` for Light and Standard, that rule produces no finding in those tiers but remains active in Deep. Audit evidence may show it as inactive, never as a failure. User preferences take precedence over Architecture discretion, but cannot silently disable rights, privacy, credentials, authorization, mandatory security boundaries, path containment, repository authority, platform hard stops, destructive/external publication gates, Architecture-only acceptance, sealing, or evidence integrity. Changing those requires separate governed framework work.
<!-- SPDX-License-Identifier: Apache-2.0 -->
