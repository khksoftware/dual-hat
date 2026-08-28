<!-- SPDX-License-Identifier: Apache-2.0 -->

# Engineering Blueprint

A governed product repository separates product, engineering, framework integration, workspace, and archive responsibilities. Product contains distributable architecture, governance, data, runtime, tests, and templates. Engineering contains agents, product profiles, handoffs, planning, process, repository metadata, sessions, validation, migrations, thin scripts, and audit history. Workspace is mutable, local, ignored state. Framework is generic and independently exportable.

Current authority is explicit; historical state is isolated. Product packages use allowlists and cannot consume engineering, framework, archive, or workspace paths. Engineering profiles depend on Dual Hat; Dual Hat never depends on the product. Every surface declares owner, lifecycle, packaging role, entrypoint, and validation.

Use responsibility-oriented paths. Language-required package names are the smallest exception and are documented. Thin command entrypoints call importable owning modules; one-time migrations retire after closure. Bootstrap creates only mandatory directories and creates optional domains when their trigger occurs.

See [Canonical Entrypoints](CANONICAL_ENTRYPOINTS.md) for where to begin and [Canonical Domain Index](CANONICAL_DOMAIN_INDEX.md) for authority by domain.
