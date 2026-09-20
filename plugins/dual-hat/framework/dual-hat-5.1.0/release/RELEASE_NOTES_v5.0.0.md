<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 5.0.0 release notes

Dual Hat 5.0.0 is a major release, and the level is derived rather than chosen. Most of its fifteen changes are additive governance text. Three are not, and each would force a major on its own: an executable gate now refuses sealed work orders it accepted at 4.6.0, an exported function lost a keyword parameter, and a shipped template was removed. [UPGRADING.md](UPGRADING.md) carries the governed migration, one group per break, and says what the release does not do.

No principle is added, removed, renumbered or reclassified.

## A sealed order is held to the schema it claims

`schemas/work-item.schema.json` has long declared a closed property set. Nothing applied that declaration to a real sealed order: the only consumer compared one example file's keys against the schema, in one direction, which cannot fail on a schema that permits more than the example uses. Measured against an adopting project's committed sealed orders, a real share already carried fields the schema does not declare, under several distinct names. The count was still growing, because nothing could refuse an addition.

`validate_sealed()` now reads the schema's declared properties at call time and refuses a `dual-hat-sealed-work-order/1.1` order carrying any top-level field outside them. An unreadable schema is itself a refusal, never a silent pass. Legacy `1.0` orders are validated exactly as before.

**The repair is forward only.** A previously sealed order is hash-pinned, and editing it to conform invalidates its own seal. So the framework neither rewrites nor exempts a historical population. An adopter that accepts historical exceptions records them in its own governance, order by order, and a count that stops matching that record is a finding.

## A seal can no longer authorize what it forbids

A sealed order could authorize a path that its own exclusions forbade, in the same document, and validate clean. Both lists were loaded and structurally validated, and neither was ever compared with the other.

The comparison is made against a new, optional, structured `excluded_paths` field, not the prose `explicit_exclusions`. That choice was established by execution. A first version that scanned the prose refused a real share of committed orders, because an exclusion sentence names paths for reasons other than forbidding them, including describing the permitted alternative. Only exact identity counts as a contradiction. Containment in either direction is the legitimate narrowing and carve-out idiom. An order with no `excluded_paths` is unaffected.

## The release package survives being killed mid-write

`release_package.build()` used to write a release directory file by file, with a rollback that only answered an in-process exception. A process killed between two replacements could leave that directory holding an ambiguous mix of old and new files.

Build and `validate_release_set()` now go through a new, generic redo journal, `tooling/cross_family_transaction.py`:
- Every target is planned and staged before any real byte changes, and a single rename is the commit point.
- A crash before that point changed nothing real, and a crash after it is always finished forward by the next caller.
- Two tests kill a real subprocess mid-transaction rather than raising an exception in process.
- The claim is bounded to process death. The module states that it is not a power-loss or filesystem-crash guarantee.

## A push publishes its whole ancestry

Naming an explicit ref protects only against publishing commits ahead of yours. Commits another writer landed behind yours are ancestors by the time you push.

Before every push to a shared branch, the commits between the remote tip and the pushed commit are enumerated and read. **Every one of them is one this session created, or the push does not happen**, because a commit another writer has not yet published may be held back deliberately. This gate is separate from the validation verdict. Where history is forward-only, the remedy is to wait for the owning writer or to escalate, never to resequence.

The rule states its own limit: where every writer commits under one identity, nothing can enforce it.

## Planning registers: reading is a disposition point, and debt is owed

**Reading an item leaves it changed.** An item that has been opened and understood leaves that reading worked, re-owned into a named queue with a named owner, corrected, or closed. Returning it unchanged is not among the outcomes, because putting it back is the cheapest option and is indistinguishable from nobody having read it. Deferral with a stated reason is not a disposition. Closing an item as irrelevant needs demonstrated grounds, not an impression. The rule binds outside review events and is classified judgement-only.

**Debt is a commitment to repay.** Technical debt governance now says so:
- A percentage allocation is named as a non-mechanism, since nothing measures the share and nothing refuses work that spent none.
- Carry-forward is an explicit reauthorization per item, or the item is reported as unmanaged.
- A register that only grows is a finding about the process.

**Every plan gets the reduction passes.** The two adversarial reduction passes now bind every plan in the widest sense: design, brief, dispatch, batch, sequence, estimate, test population or execution approach. Previously they bound only test plans and cost projections. The mechanics are unchanged, and every plan that conformed before still conforms.

## Closure states whether what it introduced is reached

A closure states, for the surface its own changes touched, whether each capability, control, rule or obligation it introduced is reached by something that actually runs. The scope is the change, never the whole estate. An unreached item is an unanswered question, not a defect, and there are four admissible answers. Fabricating a caller to clear one is forbidden. Reachability is decidable only for what an adopter's own tooling can resolve, and the dimension says so.

## Response-boundary checks, and what reach means

Principle 12 already required a hook to be armed. The framework contract now states what such a check must also satisfy on a live turn to remain a control, and principle 12 cross-references it:
- A refusal is re-evaluated on retry, bounded by a structurally counted ceiling.
- A turn-scoped window closes at every stakeholder message, however the platform stores one.
- An act is read from the platform's record of acts, never from text.

The residual is stated. A remedy the check cannot observe passes only as unverified. Corroboration proves that an act of the named kind occurred, not that it was the right one. And no such check reaches a delegated worker's own turns.

## The active-session record

**Prose is admitted per entry.** Each entry declares the kind of claim it makes. A declared kind is a check, not a label: it names what would show the entry false, and a kind with no executable falsifier does not enter the vocabulary. A kind adds a check and never exempts an entry from the checks every entry receives. Making such a declaration mandatory rewrites text other controls parse, so each of those controls is a consumer of the change and is verified to still read it.

**The record shows who holds an item.** Who is working an item is the dispatch inventory's to say. An item shown in progress says whether the primary role holds it or a registered worker does, without labelling delegated items by elimination. Prose about delegated work states policy, never inventory state. A verified-empty inventory beside prose asserting live work is refused where it is written.

## Derived values never start as placeholders

A derived value is often due before its input exists. A placeholder stored in that case passes every check when written, because re-deriving from an absent input yields the same placeholder. It then fails a later, unrelated write, far from its cause.

Repository governance now makes an unresolved input a failure of the write that needed it. It also prohibits both tempting repairs: loosening the stale-value check, and falling back to a second source for the value.

## Staging a publication that removes a file

Governed staging refused any publication that removed a file the previous publication owned. The hygiene check read the index, which still listed the deleted file, as present and unowned. With that fixed, the index validation read the staged deletion itself as unknown. A tracked path deleted from the worktree is no longer present content, and a staged deletion of a path the committed publication owned is a removal. Every refusal message is unchanged, and deleting a path no prior publication owned is still refused. One consequence is intended: a manifest-owned file deleted from disk now reads as missing rather than as present.

## Schema repair

The four `roots` patterns in `schemas/product-profile.schema.json` were under-escaped by one JSON level, so each character class never terminated. An instance validator reaching them raised instead of validating, in every release that shipped the file. They now compile and express the constraint they always intended.

## Removed

`templates/DOCUMENT_METADATA.md` had no consumer anywhere in the framework and is removed from the distribution.
