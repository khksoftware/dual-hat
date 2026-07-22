<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.11.0 Release Notes

Dual Hat 1.11.0 strengthens artifact lifecycle enforcement. Active and output locations are reserved for artifacts that are currently and operationally consumed. At capability or phase closure, and whenever an artifact is superseded, scoped outputs are classified as current, historical evidence, or disposable duplication.

Current artifacts remain active. Historical evidence moves to the governed archive with enough path and hash traceability to preserve audit value. Reproducible or valueless duplicates are removed. Historical usefulness alone no longer permits capability chronology to remain mixed into current product surfaces.

This is a backward-compatible additive governance release. Existing 1.x authority, work-item lifecycle, schema, and compatibility contracts remain unchanged.
