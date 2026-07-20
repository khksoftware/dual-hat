<!-- SPDX-License-Identifier: Apache-2.0 -->

# Publication and drift

This repository is a derived publication. The canonical framework source is currently `dual-hat/` in the EOS repository; this checkout is not yet an independent development authority.

Publication inventories the exact canonical allowlist, validates semantic completeness and licensing, assembles deterministically, validates without the EOS tree, compares the prior marker-owned files, and applies only a clean forward update. Manual edits cause drift validation to fail. Reconcile them in canonical source or explicitly change the authority model; never force-push or silently overwrite them.

The generic publication gate in `tooling/staged_publication.py` owns manifest-bounded staging, staged-index inspection and secret scanning, cache/bytecode rejection, and committed-tree verification before push. EOS invokes that gate through its thin export wrapper and adds only EOS-specific source, target, receipt, remote-alignment, and conformance evidence. Neither layer may use `git add -A` for publication.

If Dual Hat becomes independently developed, governance must name the new authority, migration point, compatibility policy, contribution workflow, and synchronization or replacement rule before independent edits are accepted.

All first-party content is Apache-2.0. See [README](../README.md), [LICENSE](../LICENSE), [NOTICE](../NOTICE), and [third-party notices](../THIRD_PARTY_NOTICES.md).
