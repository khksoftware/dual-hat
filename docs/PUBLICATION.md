<!-- SPDX-License-Identifier: Apache-2.0 -->

# Export, Publication, and Drift

The canonical framework source may live inside an adopting source repository while a standalone repository is a derived publication. Exact source mapping, structural validation, semantic completeness, licensing, deterministic assembly, idempotence, standalone tests, target drift, and prior marker identity must pass before writing.

A prior manifest defines the owned external file set. Forward publication may add, update, rename, or remove only governed files and must report the change plan before writing. Unknown files or changed governed files fail closed. Publication creates a transparent commit, pushes without force when authorized, fetches, verifies alignment/cleanliness/manifest/marker, and records the receipt outside the generic source when it contains product or remote identity.

If independent development authority is later granted to the external repository, record that governance change explicitly before accepting manual divergence.
