<!-- SPDX-License-Identifier: Apache-2.0 -->

# Bootstrap

Bootstrap is the low-level application step for an already approved product profile. First-use product/repository discovery and the no-mutation approval boundary are owned by [ONBOARDING.md](ONBOARDING.md). Do not invoke bootstrap to bypass a pending onboarding package, trust review, scaffold decision, or installation/binding choice.

For first use, verify and extract the release outside the target repository, open the target folder, and ask the agent to use that framework path to onboard the currently open product. After approval, choose the external or bounded pinned binding described in [Installation and Project Binding](../guides/INSTALLATION_AND_BINDING.md).

1. Copy or install the governed Dual Hat distribution and verify its manifest/license.
2. Create a product profile from `examples/product-profile.example.json`.
3. Run `python scripts/bootstrap_product.py --target <new-root> --profile <profile.json>`.
4. Populate canonical entrypoints/domain indexes, active session, roadmap, work order, validation profile, and protected assets.
5. Run `python tooling/validate_framework.py --root .` in the Dual Hat checkout and the product's own focused bootstrap tests.

Bootstrap creates the mandatory roadmap, empty planning backlog, future-work registry and planning history, session, handover, and repository-entrypoint surfaces. The distributable history template contains an illustrative row for field discovery; bootstrap deliberately omits that row so its three planning records reconcile immediately. Reconcile later planning changes with `tooling/planning_reconciliation.py`. Optional architecture, data, migration, template, and archive areas appear when first needed. The template is product-neutral; do not copy example identities or paths into production. Product-specific paths and commands belong in the profile, not in framework source.

Manual edits to a derived external framework publication are drift: stop, reconcile ownership, and publish forward from the canonical source. See [Publication](../release/PUBLICATION.md).
