<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 5.2.0 release notes

A minor release publishing thirteen pending propagations together. Nothing is removed and no existing
function's signature changes. Three test modules are renamed.

## Why minor rather than patch

- **Additive governance.** Several changes add obligations without renumbering or removing any:
  - a Tier 0 (Scripted) model tier, and the rules that follow from it;
  - vertical-slice planning;
  - a review-convergence rule;
  - the test-run authority clauses in validation and parallelism.
- **A new read-only assurance library and CLI**, with a consumer of accepted Deep baselines that fails
  closed. Pending baselines and baselines from before 5.2.0 remain compatible; only accepted Deep
  baselines created under 5.2.0 or later must carry a deep plan, an assurance basis and assurance
  evidence.
- **One tightening, classified by the release policy this release publishes.** A deep review plan is now
  refused when its subject is not the governed state its own baseline binds. A plan written for another
  subject was never within the documented contract, so refusing it is a patch-level change, not a
  breaking one.

## If you upgrade, read these first

- **Release classification.** `release/RELEASE_POLICY.md` now states how a tightening is classified. It is
  breaking when the refused input was within the documented contract, patch when it was not, and breaking
  where the contract is silent. A minor release therefore never carries a tightening.
- **Tier 0.** `governance/MODEL_TIER_AND_RUNTIME_BINDING.md` adds Tier 0 (Scripted).
  `tooling/model_routing.py` routes deterministic execution to it: `tier_for_activity` returns
  `tier_0_scripted`, outside every model binding.
- **Whole-object review assurance.** `tooling/review_assurance.py` is new, and `tooling/quality_review.py`
  consumes it for accepted Deep baselines created under 5.2.0 or later.
- **Test module names.** Three modules are renamed with a `dual_hat` prefix, so a host repository that
  collects the framework's tests beside its own meets no name collision:
  - `tests/test_cross_family_transaction.py`
  - `tests/test_repository_hygiene.py`
  - `tests/test_sibling_import_context.py`

## What changed

**Release classification.** The release policy's three change classes now come with the test they always
implied: whose contract did the refused input belong to?

**Tier 0 (Scripted).** A model tier for work a procedure fully determines and whose failures it
classifies: a time-bounded script that keeps its complete output and reports an index of it. Principle 1
gains a structure-not-instruction economy paragraph. The consequences:
- A registry preflight is Tier 0 work.
- A role that launches a deterministic script and reads its complete output has run its checks itself,
  for any check a procedure fully decides. Acceptance stays with that role.
- Once a Tier 0 route exists for a step, it is that step's required path.
- A disagreeing re-run attributes nothing.
- In a batched pass, a target's absence is a whole-run verdict.
- A refresh never rewrites judgement silently once the other side has moved.

**Planning.** The default is complete, tested, partial vertical slices, with final full-integration
acceptance still required.

**Review convergence.** Cost pressure never narrows a repair to the latest finding while sibling classes
remain in the established population.

**Validation and parallelism.** Test execution in a repository worked by concurrent agents or platforms is
a shared consequential workflow under the single-orchestrator rule:
- **Identity.** A run is identified by its tree and target set.
- **Reuse.** A held result covers a descendant tree only where the intervening change selects none of its
  targets.
- **Admission.** Admission is machine-wide, and a stopped holder leaves no live process tree.
- **Deferral.** Coalescing deferral is bounded and visible.

Full live validation also runs periodically, at a cadence the adopting profile sets.
