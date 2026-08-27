<!-- SPDX-License-Identifier: Apache-2.0 -->

# Model Tier and Runtime Binding Governance

Portable Dual Hat policy names capabilities, never providers or product model names.

| Tier | Intended work | Capability and evidence |
| --- | --- | --- |
| Tier 1 — Routine | Deterministic bounded execution | Basic reasoning, bounded tools/context, direct validation; optimize cost and latency. |
| Tier 2 — Standard | Ordinary implementation and analysis | Repository inspection, work-item context, tests, and actionable evidence; escalate on cross-domain or unresolved risk. |
| Tier 3 — Advanced | Complex architecture and independent review | Cross-domain context, resumable handoff, strong reasoning, and independent primary-evidence review. |
| Tier 4 — Critical | Deep security, privacy, rights, release, or repository-integrity review | Complete risk boundary, detached validation where applicable, mandatory independence, and risk-first selection. |

Architecture assigns tiers to activities. A mandatory tier cannot be silently downgraded. Optional downgrade requires a recorded reason and user/Architecture confirmation; unavailable mandatory capability produces a resumable hard stop. Fallback must satisfy the same tier or remain explicitly inadequate. Evidence records the abstract requirement, concrete local selection, environment fingerprint, availability, and confirmation.

When an agent or reviewer struggles, diagnose whether the mismatch is
capability or ownership before retrying. **Re-tier** when the assigned model or
runtime lacks the reasoning depth, context, tools, or reliability required by
the same role. **Re-role** when the task's authority, method, failure axis, or
expected judgment belongs to a different role even if the current model is
capable. Do not spend model tier to compensate for a confused role, and do not
rename a role to conceal inadequate capability. Preserve the work boundary and
independence requirements across either change.

Development adapters bind tiers using hash-verified exposed evidence only: adapter identity, tool inventory, complete runtime/platform fingerprint, supported probes, configuration, and user confirmation. Any fingerprint change invalidates capability, availability, and confirmation evidence and forces remapping. If the host cannot switch automatically, it gives adapter-specific manual switching instructions and records the user-confirmed selection. It never pretends to detect a capability the host withholds.

The host adapter and governed capability registry are the trusted provenance boundaries. Evidence must identify its source type, authority ID, observation ID, complete environment identity where applicable, and canonical evidence hash. Core routing rejects malformed, altered, or stale receipts; it does not elevate self-hashed records from an untrusted caller into provider or user authority.

Production configuration is deliberately separate. Before first production use, the user explicitly approves provider, model, effort, fallback, privacy and local/cloud preference, cost, latency, retention restrictions, permitted task classes, and unavailable-model behavior. Development detection never supplies production choices. No provider or model is silently selected or replaced.

Development or production switching occurs only at an atomic safe boundary. Mid-operation change waits while preserving state unless the operation has an explicit resumable-transfer contract. The approved production configuration contains hash-verified tier capability evidence; switching hard-stops when the requested tier is not verified even when the model is available. Unavailable or inadequate mandatory production selection stops and requests configuration.
