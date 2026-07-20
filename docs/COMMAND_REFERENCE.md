<!-- SPDX-License-Identifier: Apache-2.0 -->

# Command Reference

Commands are examples for the standalone framework. A product profile supplies its own runtime, test, package, branch, and publication commands.

## Validate the framework

From the framework root:

```text
python tooling/validate_framework.py --root . --json
python -m unittest discover -s tests
```

The first command validates semantic ownership, required documentation, product-neutrality, and declared artifacts. The second validates examples and bootstrap surfaces. Both must pass in a standalone tree before publication.

## Bootstrap a product

```text
python scripts/bootstrap_product.py --profile examples/product-profile.example.json --target ../new-product --dry-run
python scripts/bootstrap_product.py --profile examples/product-profile.example.json --target ../new-product
```

Review the dry-run paths before writing. Bootstrap refuses conflicting files and is idempotent for identical inputs. After creation, replace example identity, commands, branch rules, protected assets, and publication rules in the product profile before authorizing implementation.

Dual Hat intentionally does not ship a universal push, release, or process-termination command. Those operations depend on product authority and environment ownership and must be declared by the product profile or work order.
