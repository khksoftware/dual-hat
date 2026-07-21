<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.6.0 Release Notes

Dual Hat 1.6.0 makes the smallest credible, risk-proportionate focused test
subset the default. Validation should cover the changed behavior, its direct
integration boundaries, and the most plausible regressions without routinely
rerunning unrelated suites.

A full-suite run remains required when impact is broad or uncertain, a focused
run exposes an unexplained failure, focused coverage cannot establish adequate
confidence, or a work order, release gate, or governing policy explicitly
requires it. Suites explicitly marked mandatory remain mandatory.

This is a backward-compatible minor governance release. It changes the default
validation decision, not existing framework interfaces or mandatory controls.
