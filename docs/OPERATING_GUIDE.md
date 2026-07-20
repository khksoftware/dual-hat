<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operating guide

The Architecture Office owns intent, boundaries, trade-offs, capability authorization, and acceptance. The Engineering Agent owns implementation, validation, evidence, publication, and the automatic exit report. Both roles follow the normative [framework contract](../framework/DUAL_HAT_FRAMEWORK.md).

A capability proceeds through: explicit opening; preflight; bounded implementation; owning-layer repair; focused and integration validation; conformance evidence; forward-only publication; handover; and closure. Stop gates do not broaden authority. Independent read-only validation may run in parallel, but shared mutation, reconciliation, Git publication, and the final user response remain centralized.

Every artifact receives one primary role and a lifecycle disposition. Every completed run reports outcome, boundaries, validation, publication, debt, required operator action, and the exact next gate.
