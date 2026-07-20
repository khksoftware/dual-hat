<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 1.0.1 Release Notes

Dual Hat 1.0.1 corrects two narrow omissions in 1.0.0. Current handovers now use a generic registered `active_work_item` rather than the Capability-only `active_capability`. Type identifiers are extensible through the governed registry—so a future type such as `defect` can be added without rewriting every handover schema—while unregistered identifiers fail closed.

Architecture review now requires an independent authority-boundary disposition against primary evidence. A material violation blocks acceptance and creates both a specific-remediation obligation and a systemic-control-strengthening obligation, plus a bounded analogous-gap review. Passing tests and Engineering self-report cannot satisfy this review by themselves.

Historical `dual-hat-current-handover/1.0` records remain valid. Current templates emit 1.1. No role, lifecycle, mode, or existing Capability/GOV semantic rule changed, so this is patch release 1.0.1.
