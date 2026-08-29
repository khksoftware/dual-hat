<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository Boundaries

Adopting products define a product profile with four conceptual domains:

- `product/`: production source, runtime data, production schemas, product documentation, and deliberately adjacent verification;
- `dual-hat/`: the canonical generic framework source or installed framework boundary;
- `engineering/`: product-specific framework extensions, capability and roadmap state, migrations, validation, conformance, and audit history;
- `workspace/`: mutable operator, customer, project, instance, or local execution state.

Every artifact is classified at creation as product, generic framework, product engineering, workspace, archive/audit, or test/development fixture. Mixed artifacts are split: generic rules move to Dual Hat, product specialization remains in engineering, and the relationship is explicit.

Allowed dependency direction is `engineering -> dual-hat` and `engineering -> product` for build, test, audit, or migration work. Product runtime never imports Dual Hat, engineering state, or archives. Dual Hat never imports product, engineering, archive, or workspace state. Workspace never becomes generic source merely because a workflow created it.

Package manifests are allowlists. Path scans are insufficient: validators inspect imports, file opens, templates, schemas, scripts, help, and generated projections. Archives require explicit audit mode and cannot silently satisfy runtime identity.
