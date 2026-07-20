<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository map

| Path | Owner | Purpose |
| --- | --- | --- |
| `product/` | product runtime | code, runtime assets, product contracts, adjacent verification |
| `dual-hat/` | framework | installed Dual Hat publication |
| `engineering/` | product engineering | profile, roadmap, handovers, evidence, migrations, archive |
| `workspace/` | operator or instance | ignored mutable state |
| `.dual-hat/` | exporter | manifest and published-state marker in a derived publication |

Dual Hat does not depend on the adopting product. Product runtime does not depend on Dual Hat, engineering state, or archives. Engineering may specialize Dual Hat and inspect archives explicitly. Path never replaces stable identity. See the [artifact schema](../schemas/artifact-classification.schema.json) and [bootstrap guide](BOOTSTRAP.md).
