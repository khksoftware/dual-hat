<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.18.4 Release Notes

This compatible governance release adds rule 35: a durable file -- version-controlled, a governed artifact, a template, or any generated-but-committed output, as distinct from a genuinely transient file local to one machine's own working state -- must never embed an absolute local filesystem path used as a live structural pointer or self-reference. A machine-specific drive letter, home directory, or install location silently breaks for any other clone, checkout, or contributor, including a file's own self-reference to its own location. Use a path relative to the repository root, or another already-established, durably meaningful anchor, instead.

The rule carves out a machine-specific path quoted verbatim as illustrative or historical evidence, and a path recorded as a factual claim about where a specific process actually ran, from its scope -- neither functions as a live pointer something depends on resolving. Adopting the convention carries rule 20's standard closure discipline: a one-time mechanical sweep of the repository's active surface for existing live-pointer embeddings, plus a standing mechanical check that catches a new one the moment it is introduced.

This release also adds that standing mechanical check itself: an absolute-local-path detector with structural exemptions for test/fixture files, JSON Schema example values, and markdown evidence citations, plus two human-reviewed exemption registries for anything else -- one for confirmed-legitimate citations, one for findings this check's own construction explicitly declined to adjudicate rather than silently pass. Both registries start empty in this repository.
