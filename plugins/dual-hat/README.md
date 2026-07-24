<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat agent plugin

![Dual Hat agent mascot wearing two top hats](assets/dual-hat-agent-640x320.png)

This package exposes one shared `use-dual-hat` skill to Codex and Claude Code and includes an exact, checksum-governed extraction of the published Dual Hat 1.16.0 release. It executes no plugin hook, starts no service, and replaces no framework authority. The skill verifies and uses the bundled framework by default, so a separate standalone installation is not required.

## Codex

Add this repository root as a non-default local/team marketplace, then install the scaffolded plugin:

```text
codex plugin marketplace add <path-to-dual-hat-repository>
codex plugin add dual-hat@personal
```

Start a new thread after installation so the skill is discovered. For an upgrade, update the marketplace checkout to an authorized newer plugin release, run `codex plugin add dual-hat@personal` again, and start another new thread. Confirm that `.codex-plugin/plugin.json` and `framework-payload.json` contain the expected plugin and framework versions before use.

Invoke the skill as `$use-dual-hat`. You may explicitly select a compatible external framework root; otherwise the bundled 1.16.0 root is authoritative for the session.

## Claude Code

For local testing, start Claude Code with:

```text
claude --plugin-dir ./plugins/dual-hat
```

For marketplace installation, add this repository root and install:

```text
/plugin marketplace add ./path/to/dual-hat
/plugin install dual-hat@dual-hat
/reload-plugins
```

Invoke `/dual-hat:use-dual-hat`. To upgrade, run `/plugin marketplace update dual-hat`, then `/plugin update dual-hat@dual-hat` and `/reload-plugins`. The explicit manifest version is the update cache key and must change for each published plugin release.

Use the installation scope appropriate to the project. Project-scope content remains subject to Claude Code's workspace trust and component approval controls.

## Framework payload

`framework-payload.json` identifies the bundled framework root, source release, and source ZIP checksum. The extracted payload retains its release content manifest and per-file checksums. Plugin and framework versions are independent; a future plugin release must regenerate this directory from an authorized framework release rather than hand-editing the copied governance.
