<!-- SPDX-License-Identifier: Apache-2.0 -->

# Bootstrap a product

Prerequisites are Git and Python 3.10+; the bootstrap uses only the Python standard library.

1. Initialize an empty product repository.
2. Copy or install this derived Dual Hat publication without changing its governed files.
3. Review `examples/product-profile.example.json` against `schemas/product-profile.schema.json`.
4. Preview: `python scripts/bootstrap_product.py --profile examples/product-profile.example.json --target <repository> --dry-run`.
5. Apply: `python scripts/bootstrap_product.py --profile examples/product-profile.example.json --target <repository>`.
6. Create the first bounded work order from `templates/WORK_ORDER.md`.
7. Implement, validate, record conformance with `templates/CONFORMANCE_REVIEW.md`, and generate a handover from `templates/CURRENT_HANDOVER.md`.

The command creates only absent governed directories and `engineering/product-profile.json`. It fails on conflicting content and is idempotent. See the [repository map](REPOSITORY_MAP.md), [boundary contract](../governance/REPOSITORY_BOUNDARIES.md), and [troubleshooting guide](TROUBLESHOOTING.md).
