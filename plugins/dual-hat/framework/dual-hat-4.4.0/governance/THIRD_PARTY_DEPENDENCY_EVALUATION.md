<!-- SPDX-License-Identifier: Apache-2.0 -->

# Third-Party Dependency Evaluation

Before recommending or introducing any third-party tool, library, SDK, package,
runtime, model, service client, or other product/project dependency, the active hat
MUST evaluate and share:

- license and the concrete implications for product use, modification, distribution,
  attribution, source disclosure, patent obligations, and commercial use;
- acquisition and ongoing cost, including usage fees and material operational cost;
- reliability for the intended workload, including known failure modes and required
  validation or human review;
- safety and security, including privacy, data movement, credentials, execution,
  supply-chain exposure, and available containment;
- minimum and recommended hardware, operating-system, runtime, storage, memory, GPU,
  and other material platform requirements; and
- support status, including current release activity, maintainer/community health,
  compatibility policy, and whether the dependency is active, stale, deprecated, or
  out of support.

The evaluation precedes the user's dependency decision and distinguishes verified
facts from inference. It uses current primary evidence when the facts may have
changed. When two or more viable options exist, present a concise pros/cons comparison
table and explain the recommendation for the product's actual constraints. A single
option may be presented without a comparison table only when alternatives are not
viable or the user explicitly constrained the choice; record that basis.

Approval binds the evaluated dependency class and stated use. Material license,
cost, data-flow, hardware, support-status, or dependency-class changes require a new
evaluation and approval. Installation records pin versions or revisions and preserve
the integrity, rollback, and offline/privacy controls promised in the evaluation.
