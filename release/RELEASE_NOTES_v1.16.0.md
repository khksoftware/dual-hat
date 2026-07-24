<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.16.0 Release Notes

Dual Hat 1.16.0 adds three supported ways to deploy the same governed
framework: the standalone release, a Codex plugin, and a Claude plugin.

The two plugin forms share one self-contained package and one
checksum-governed framework payload. Installation executes no hooks, starts no
service, introduces no runtime dependency, and grants no authority to mutate a
product repository. Each platform invokes the same onboarding, role,
validation, and approval contracts.

The release also adds attested Dual Hat branding assets and extends canonical
export tooling to handle governed binary files. Plugin distributions are
intentionally excluded from the standalone ZIP, preventing recursive package
growth while keeping the standalone release platform-neutral.

Post-artifact release validation now accepts the recorded source-publication
commit when it remains an ancestor of the aligned published head. This
preserves exact provenance after the release-artifact commit advances `main`.

This is a backward-compatible additive minor release. Existing 1.x consumers
do not need to migrate.
