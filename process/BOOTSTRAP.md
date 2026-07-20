<!-- SPDX-License-Identifier: Apache-2.0 -->

# Bootstrap

1. Copy or install the governed Dual Hat distribution and verify its manifest/license.
2. Create a product profile from `examples/product-profile.example.json`.
3. Run `python scripts/bootstrap_product.py --target <new-root> --profile <profile.json>`.
4. Populate canonical entrypoints/domain indexes, active session, roadmap, work order, validation profile, and protected assets.
5. Run `python tooling/validate_framework.py --root .` in the Dual Hat checkout and the product's own focused bootstrap tests.

Bootstrap creates the mandatory roadmap, empty planning backlog, future-work registry and planning history, session, handover, and repository-entrypoint surfaces. The distributable history template contains an illustrative row for field discovery; bootstrap deliberately omits that row so its three planning records reconcile immediately. Reconcile later planning changes with `tooling/planning_reconciliation.py`. Optional architecture, data, migration, template, and archive areas appear when first needed. The template is product-neutral; do not copy example identities or paths into production. Product-specific paths and commands belong in the profile, not in framework source.

Manual edits to a derived external framework publication are drift: stop, reconcile ownership, and publish forward from the canonical source. See [Publication](../release/PUBLICATION.md).
