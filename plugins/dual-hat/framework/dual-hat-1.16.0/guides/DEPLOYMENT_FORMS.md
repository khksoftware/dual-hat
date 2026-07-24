<!-- SPDX-License-Identifier: Apache-2.0 -->

# Deployment Forms

Choose one entry form. All three converge on the same canonical onboarding workflow, operating modes, product-profile rules, approval boundaries, and validation contracts.

| Form | Choose it when | Initial action |
| --- | --- | --- |
| Standalone release | You want a platform-neutral, checksum-verifiable installation or do not use a supported plugin host. | Verify and extract a versioned release outside the product repository. |
| Codex plugin | You use Codex and want a self-contained `use-dual-hat` skill available in new threads. | Add the repository-local Codex marketplace and install `dual-hat`. |
| Claude plugin | You use Claude Code and want the self-contained namespaced `/dual-hat:use-dual-hat` skill. | Add the repository as a Claude marketplace and install `dual-hat`, or use `--plugin-dir` for local testing. |

The plugin package contains a read-only, checksum-governed extraction of the published Dual Hat 1.16.0 release. It contains no hooks, MCP servers, plugin executables, service clients, credentials, or telemetry. Installing it does not authorize repository mutation, binding, dependency introduction, publication, or destructive work.

## Convergent onboarding

1. Resolve a verified Dual Hat framework root. The standalone form uses its extracted release; either plugin uses its bundled payload by default. An explicit compatible external override is optional.
2. Open the target product repository or intended project folder.
3. With the standalone form, ask the agent to use the framework at that path. With a plugin form, invoke `use-dual-hat`; it verifies and selects the bundled framework automatically.
4. Follow [Onboarding](../process/ONBOARDING.md). Inspect first, choose Integrated or Split Mode, generate the approval package, and wait for required approval before material mutation.
5. Bind the project only through [Installation and Project Binding](INSTALLATION_AND_BINDING.md). The resulting product profile and canonical framework contracts govern subsequent work regardless of entry form.

## Install and upgrade

For the standalone form, use [Installation and Project Binding](INSTALLATION_AND_BINDING.md) for install, update, migration, rollback, and removal.

For Codex, add the Dual Hat repository root as a marketplace, install the
plugin, and start a new thread:

```text
codex plugin marketplace add <path-to-dual-hat-repository>
codex plugin add dual-hat@personal
```

For Claude Code local testing, use
`claude --plugin-dir ./plugins/dual-hat`. For a marketplace installation, run:

```text
/plugin marketplace add ./path/to/dual-hat
/plugin install dual-hat@dual-hat
/reload-plugins
```

The repository's
[plugin guide](https://github.com/khksoftware/dual-hat/blob/main/plugins/dual-hat/README.md)
contains the complete platform-specific invocation and upgrade commands.
Plugin and bundled-framework versions are independent metadata, but a plugin
upgrade carries its authorized framework payload with it. Verify the selected
framework path, payload hashes, and version before governed mutation. Re-run
profile compatibility checks when an upgrade changes framework contracts or
paths.

Do not treat a marketplace refresh, plugin reinstall, or plugin version bump as project approval. Treat a changed bundled framework version as a framework update and apply its compatibility and migration rules. Roll back a plugin through its host's normal version/install controls; roll back a project binding only through the canonical binding guide.
