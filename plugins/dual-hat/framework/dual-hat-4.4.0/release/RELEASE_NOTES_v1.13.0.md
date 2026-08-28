<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.13.0 Release Notes

Dual Hat 1.13.0 adds proportional specialist-review separation.

When material acceptance genuinely depends on distinct specialist judgments,
such as architecture and user experience, projects should use separate
isolated read-only reviewers when the environment supports it. Each specialist
reviews relevant primary evidence without receiving another specialist's
conclusions; Architecture integrates and dispositions the reports afterward.

The rule is deliberately proportional. Routine, closely coupled, and low-risk
work does not require multiple reviewers when one bounded independent review
is sufficient.

User-support documentation is also simplified: command lookup and
troubleshooting now share the `help/` tree instead of occupying separate
top-level `reference/` and `help/` folders. The documents remain separate,
focused pages.

Capability preflight is now explicitly content-addressed and
invalidation-driven. A project profile reuses still-valid evidence, identifies
the reuse basis, and reruns only receipts invalidated by changed evidence,
tools, rules, environment, consumer boundary, or validity period. A new
work-item identifier alone does not justify recomputing an unchanged evidence
catalog.

The README now lists `khksoftware@gmail.com` for questions and framework
feedback.

This is a backward-compatible additive governance release. Existing 1.x
authority, lifecycle, schema, and compatibility contracts remain unchanged.
