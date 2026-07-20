<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 0.1.0 Release Notes

Dual Hat 0.1.0 is the first governed, user-ready package of the two-role Architecture Office and Engineering Agent framework. It is functional and independently testable, but intentionally pre-1.0: adopters should expect documented evolution in minor releases.

This release provides:

- role prompts and operating governance;
- bounded capability, planning, validation, handover, publication, and closure protocols;
- schemas, templates, examples, and a product-profile bootstrap;
- standalone semantic and automated validation;
- forward-only external repository export with drift detection;
- safe isolated temporary workspaces; and
- deterministic ZIP packaging with manifests and checksums.

The information architecture now places material with its owning responsibility. Cross-cutting operating guidance, help, and reference material have explicit homes; there is no generic `docs/` catch-all.

To verify an extracted package, run the commands in `reference/COMMAND_REFERENCE.md`. Apache License 2.0 applies to the framework; see `LICENSE`, `NOTICE`, and `THIRD_PARTY_NOTICES.md`.
