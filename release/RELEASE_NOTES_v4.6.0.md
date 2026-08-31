<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 4.6.0 release notes

Dual Hat 4.6.0 is a minor release. Its centre is a new contract for artifacts a repository generates from other artifacts, and a matching admission about what generating them does and does not buy you.

## Derived artifacts become a governed population

An artifact produced mechanically from another artifact is a **derived artifact**, and the artifact it comes from is its **canonical record**. Until now the framework said that generated state records its inputs, method, invalidation triggers and replacement behavior — a property each generated file states about itself. That is not enough to answer whether anything re-derives it, or whether a record exists that nothing declared at all.

Repository governance now defines a **derived-artifact registry**. One entry per canonical record names every derived site and the generation method that emits the bytes, and every obligation in the contract is stated against that registry. A new schema carries the entry shape, with a worked example beside it.

The requirements are short to list and each exists because the absence of it has a characteristic failure:

- Derived artifacts of one record are written **together or not at all**, with a whole-set state stamp where atomicity is unavailable, so a partial write leaves a stamp a fresh computation cannot match.
- A **partition** across derived views is declared once, in the canonical record. Two renderers each carrying their own copy will eventually disagree without either being wrong on its own terms.
- A governed write **re-derives and diffs** against durable storage in the same act that reports success. A derivation that would change something on a fresh call, immediately after the write that should have triggered it, is a forgotten derived site.
- A runner **computes, names and asserts** the entries it does not itself re-derive, and no coverage statement is maintained by hand anywhere it appears.
- Every derived site is **enumerated by observing what the writer wrote**, not from memory.
- A canonical record with derived artifacts has a **governed writer** that validates before rendering and refuses rather than half-applying.

Two of those deserve their reason stated, because the reason is the requirement.

**Computed coverage** is written strictly because the failure it prevents is not a mechanism drifting from reality. It is a mechanism's *prose* drifting from the mechanism, in one place while another place stays correct — which a rule saying keep the documentation in step with the code does not catch, because someone did keep documentation in step with the code, just not all of it. A module stating its own coverage in three places has three chances to drift and nothing reconciling them. A module deriving it has one source and no chance.

**Observed enumeration** is written strictly because the derived site an author forgets is characteristically not a file. A closed design built specifically to eliminate multiple writers can still miss a fourth writer — a pointer the record keeps about itself — repair every file and directory it knew about, and report a clean run.

## Bounded write-back

A projection a person can also type into is the same contract with one axis added, so it is folded into repository governance rather than given a document of its own. The repository is canonical and an external tracker is a derived artifact like any other.

Inbound write-back is an **allow-list, never a deny-list**, and the reason is structural rather than stylistic: a canonical record gains fields over time, so every field added after a deny-list was written is inbound-permitted by default and the safe default degrades silently with age. An allow-list's default degrades toward refusal, which is visible.

**Status, closure and scope never flow inward.** The moment a tracker can close an item there are two answers to whether it is done, and the seam has reproduced, across a boundary no repository-side gate can observe, the exact defect it was built beside. This is a precondition, not a strong default.

When the two sides disagree the canonical record wins and **the overwritten value is reported as a named, durable event**. Silent resolution in the canonical record's favour is prohibited even though the outcome is identical: an unreported overwrite is a person's work vanishing with no evidence it existed, and after the second occurrence the seam is distrusted and worked around. A reconciliation that cannot report what it discarded has not reconciled; it has overwritten.

The framework defines what a projection with bounded write-back is. It does not know that any particular tracker exists, and an adapter for one belongs to the adopting profile.

## What the contract does not claim

Stated in the governance text itself rather than left to be inferred from silence.

**Correctness is not addressed at all.** The mechanism makes contradiction between a canonical record and its derived artifacts structurally impossible and does nothing whatever about either being wrong. A record set that is internally consistent, fully governed, fully covered and factually false satisfies every clause.

Concurrency at the canonical write, staleness between a staging area and the working tree, atomicity across a multi-file derived set, and which revision a validation binds to are each named as things this contract requires or delegates but does not supply. And a canonical record absent from the registry is invisible to every clause — which is why this release also carries the general form of that question.

## Two questions an artifact registry answers

Validating a registry asks whether the registered artifacts are internally consistent. The obligation that a new active artifact must register asks whether anything is unregistered. These are different questions, and the gap between them is invisible precisely because the implemented check passes: a registry with zero unregistered artifacts and a registry that cannot see unregistered artifacts produce identical output.

A repository now carries a detector for the second question, or states that its classification claim covers only what was already declared. The predicate is structural — tracked, under a governed path, not matching an archive or evidence convention, absent from the registry — and must not become a filename whitelist, which needs editing whenever a legitimate artifact appears and fails open by default. False positives are expected and designed for, because a detector required to be right the first time is a detector nobody arms.

## Principle 12: arming is a third act

Principle 12 already told an adopter arming the role-label hook to pin the installed artifact against its tracked source. That is now stated as necessary and **not sufficient**. A hook is a control only once three things hold: its tracked source exists, a deployed copy matches that source, and the platform's own configuration references the deployed copy so something actually invokes it.

The third is the one nothing checks, and the reassurance is what makes it expensive. Measured: a hook was tracked, deployed, byte-identical to its source, covered by its own passing tests, and referenced by nothing — so it fired on no turn, ever, while its drift check printed a clean line on every commit throughout. Neither a pinning check nor the hook's own tests can answer the third question: tests import the module and call it directly, which proves the logic and not the wiring, and that is precisely how a hook can be fully tested and entirely inert at the same time.

## Role transitions, planning, and release policy

An Engineering or delegated-worker STOP terminates only that executor's authority. The supervising office preserves the checkpoint, discharges the worker, and continues every safe read-only, design, adjudication or successor-dispatch action in the same turn. Saying that control returns to the supervising office and then ending the turn is the defect the clarification forbids — that office is already the actor responsible for the return.

Every test plan and cost projection now takes at least two adversarial reduction passes, with further challenge while any generic contingency, duplicated coverage, hour-scale allowance for a seconds-scale command, or unsupported component remains. The surviving plan records its unreduced starting population, each removal, the measured basis for every retained component, the de-duplicated proof set, the distinct risk each member owns, its nonclaims, and a hard ceiling unused allowance cannot enlarge. No mandatory safety, refusal, rollback, identity, durability or recovery evidence may be reduced by it.

A production publication requires HEAD on a local branch named `main` with an upstream resolving to `origin/main`, evaluated before any write. This was already enforced in code and stated in neither governing document, and a requirement enforced only in code is an emergent property rather than a rule.

## Tooling

Four behavior-preserving repairs on the publication path. `validate_staged`'s `unknown_staged` arm now applies the preserved-path filter its sibling arm two lines above already applied. The command-line surface passes the framework's own standalone-ownership predicate by default, so the documented stage / validate-staged / verify-commit sequence succeeds as written against a derived publication repository; a genuinely unknown file is still refused. Worktree-hygiene and HEAD-provenance computations are each extracted into reusable, explicitly-rooted forms, so both preconditions can be proven before the first write rather than after several commits have already landed.

## Migration

None. No principle is added, removed, renumbered or weakened; no existing schema's property set is widened; no gate, hook, predicate, identifier or existing citation changes. The derived-artifact contract binds a repository once it declares a registry, and an adopter that declares none is in exactly the position the contract describes as its own residual.
