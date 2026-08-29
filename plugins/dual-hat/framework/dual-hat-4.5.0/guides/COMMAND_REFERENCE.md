<!-- SPDX-License-Identifier: Apache-2.0 -->

# Command Reference

## Plan-first onboarding

The portable onboarding API is `tooling/onboarding.py`. Generate and inspect an onboarding package without writing the target, obtain explicit user approval of its hash, then build and apply a bounded binding plan. Direct `scripts/bootstrap_product.py` remains the compatible low-level command for an already approved product-profile 1.0; its `--dry-run` mode shows planned files.

Model routing is provided by `tooling/model_routing.py`; concrete development choices remain local operational state, while production configuration must be explicitly user-approved. Closeout selection and estimate records are provided by `tooling/continuity_closeout.py`.

## Human role and mode requests

Use ordinary requests such as “Use Integrated Dual Hat Mode for this work item,” “Approve this work order and enter Engineering mode,” “Pause Engineering and return to Architecture mode,” “Prepare a handoff and switch this work item to Split Dual Hat Mode,” or “Engineering is complete. Enter Architecture review.” They act only against a complete current sealed order; ambiguous words do not grant mutation. Architecture alone may say “Accept this work item and archive it.”

Commands are examples for the standalone framework. A product profile supplies its own runtime, test, package, branch, and publication commands.

## Validate the framework

From the framework root:

```text
python tooling/validate_framework.py --root . --json
python tooling/run_tests.py
```

The first command validates semantic ownership, required documentation, product-neutrality, and declared artifacts. The bytecode-safe test entrypoint validates examples and bootstrap surfaces without leaving Python cache residue. Both must pass in a standalone tree before publication.

## Reconcile planning state

After changing a backlog, future-work registry, or planning history, run:

```text
python tooling/planning_reconciliation.py --backlog <planning-backlog.json> --future-work <future-work.json> --history <planning-history.jsonl> --json
```

The command rejects incomplete items or triggers, duplicate current IDs or event IDs, broken status chains, non-monotonic per-item timestamps, missing history, and disagreement between current projections and the latest events. It validates planning consistency; it does not grant work authorization.

## Build and verify a release package

From the framework root, first run the deterministic and extraction self-test:

```text
python tooling/release_package.py self-test
```

A governed source repository may then call `build` with an authorized output directory, canonical source commit, and external publication commit. The output is a deterministic ZIP, companion release manifest, and SHA-256 checksum file. Package creation alone does not authorize a tag, hosted release entry, or public upload.

## Stage and verify a governed publication

From the derived publication repository, after applying and validating the export:

```text
git status --short
python tooling/staged_publication.py stage --root .
git diff --cached --name-status
python tooling/staged_publication.py validate-staged --root .
```

The `stage` action stages only manifest-owned paths and exact governed removals. It rejects unknown files, common generated artifacts and caches (even when ignored), missing governed files, content-hash drift, marker drift, and likely secrets. Do not substitute `git add -A` or another unbounded staging command.

After reviewing the staged paths and creating a transparent commit, validate the exact committed tree before push:

```text
python tooling/staged_publication.py verify-commit --root . --revision HEAD
```

Only then push without force, fetch, and confirm branch alignment and cleanliness. A product profile may wrap these generic commands but must not weaken their checks.

## Bootstrap a product

```text
python scripts/bootstrap_product.py --profile examples/product-profile.example.json --target ../new-product --dry-run
python scripts/bootstrap_product.py --profile examples/product-profile.example.json --target ../new-product
```

Review the dry-run paths before writing. Bootstrap refuses conflicting files and is idempotent for identical inputs. After creation, replace example identity, commands, branch rules, protected assets, and publication rules in the product profile before authorizing implementation.

Dual Hat intentionally does not ship a universal push, release, or process-termination command. Those operations depend on product authority and environment ownership and must be declared by the product profile or work order.
