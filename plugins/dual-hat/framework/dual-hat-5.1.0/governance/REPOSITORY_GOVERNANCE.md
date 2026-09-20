<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository Governance

A repository root establishes the primary namespace. Descendants state responsibility and do not repeat the root, product, or domain name unless an external language, packaging, or interoperability contract requires it. Every exception records the constraint and validation.

## Roles and boundaries

Classify each artifact as product, framework, engineering state, mutable workspace, historical evidence, test/fixture, generated projection, or transient. Declare owner, canonical source, consumers, dependencies, packaging class, lifecycle, update trigger, and supersession. Exclusive roles have exactly one active authority.

Production code cannot depend on engineering administration, framework source, archives, or mutable workspace. Framework code cannot depend on a product or its archives. Profiles may depend on the framework. Archives are excluded from routine discovery, validation, context retrieval, and packaging.

### An artifact registry answers two different questions, and only one of them is usually implemented

Validating a registry asks *are the registered artifacts internally consistent?* The obligation
that a new active artifact must register asks *is anything unregistered?* **These are different
questions, and the gap between them is invisible precisely because the implemented check passes:
a registry with zero unregistered artifacts and a registry that cannot see unregistered artifacts
produce identical output.** A repository therefore carries a detector for the second question, or
states that it does not and that its classification claim covers only what was already declared.

**The two shapes an unregistered artifact actually takes are both plausible, which is why review
does not catch them.** One is invented mid-session in a reasonable place with no owner, lifecycle,
update trigger or entry — and can go as far as recording in its own opening lines that it ought
not to exist, which is as close to self-detection as prose gets, with nothing firing. The other is
created for a reason that was genuinely true at the moment of creation and kept in use after that
reason expired. **The second is the more dangerous, because the justification is real when the act
is taken** and nothing revisits it afterwards.

**The predicate is structural, and it must not become a list of filenames.** A whitelist needs
editing every time a legitimate artifact appears and fails open by default, which inverts the
property wanted. The tractable form is a conjunction over what the repository already knows: a
file that is tracked, that lives under a governed path, that does not match an archive or
evidence convention, and that is absent from the registry. **Expect false positives and design
for them** — a detector required to be right the first time is a detector nobody arms, and an
unarmed detector is worth less than a noisy one.

This is the general form of the residual stated under *Derived artifacts* below, where a canonical
record absent from the registry is invisible to every clause of that contract. The two are one
question asked at two scopes, and a repository that answers it once answers it for both.

**Classification:** adopter-delegated.

**Armed by** the adopting repository's own detector over its own governed paths, which this
framework specifies as a predicate and does not supply: what counts as a governed path, an
archive convention, or an evidence convention is a property of the adopting repository's layout,
and a detector enumerating layouts this framework does not ship would report clean for every
adopter it did not anticipate. **Residual:** a repository with no such detector satisfies every
other classification obligation while remaining unable to observe the population those obligations
are stated over, and the passing consistency check is what conceals it.

## Structural change

Path-heavy work is scan-first: inventory sources, writers, readers, imports, manifests, schemas, tests, docs, generated state, histories, rollback, and unknowns before mutation. Produce a source-to-destination map, verify authorization, migrate atomically, rebind active consumers, preserve historical references, and avoid aliases without a demonstrated time-bounded consumer.

## Artifact lifecycle

At closure, retain active only with an ongoing consumer and trigger; archive only with audit, rollback, legal, provenance, or occasional-consultation value; otherwise delete reproducible transients. A name such as `legacy`, `migration`, `current`, or `durable` does not establish lifecycle. Completed capability artifacts do not remain in active paths by omission: a work item's own active tracking or working location relocates to the archive location in full as one closure step, not merely through per-artifact disposition of its contents.

Generated state records its authoritative inputs, deterministic method, invalidation triggers, and replacement behavior. Superseded output is removed once required lineage and rollback evidence are preserved.

## Derived artifacts

An artifact produced mechanically from another artifact is a **derived artifact**, and the artifact it is produced from is its **canonical record**. This section extends the generated-state sentence above from a property each generated file records about itself into a governed population, because a generated file that records its own inputs still cannot say whether anything re-derives it.

A repository governed by this framework maintains a **derived-artifact registry**: for each canonical record that has any derived artifact, one entry declaring the canonical record's path, every derived artifact's path, and the generation method. **The registry is the population.** Every obligation below is stated against it, and a claim about derived-artifact health is meaningless except against a named registry. The entry's required fields and their meanings are `schemas/derived-artifact-registry.schema.json`, with a worked entry at `examples/derived-artifact-registry.example.json`.

### The generation method names the writer, not a path to it

A generation method must resolve to the callable or executable that emits the derived bytes. **A reference that resolves to something real is not a reference that resolves to the correct something**, and a validator that only checks resolvability will accept an entry point that merely calls the writer, a script that happens to run it last, or a module that supersedes it. Where an adopter can check only resolvability, it says so and does not report the weaker check under the stronger name.

### Derived artifacts of one canonical record are written together or not at all

The writer takes every derived path in the entry as a required input, so no caller can regenerate a subset. Where a set of derived artifacts cannot be written as one atomic act, each member carries a state stamp computed over the whole canonical record set, so a partially completed write leaves a stamp that cannot match a fresh computation and the next validation fails closed. **A state stamp computed over a subset of fields is not a state stamp over the record**, and an entry that claims one while computing the other is a false declaration; a stamp's field coverage is part of what the entry declares.

### A partition across derived views is declared once, in the canonical record

Where derived artifacts partition the canonical record between them — an active view and a history view, a current set and a closed set — the predicate that partitions them is declared once, in the canonical record itself, and every renderer reads it from there. A partition living only in the writer's code cannot be validated against the record it partitions, and two renderers that each carry their own copy will eventually disagree without either being wrong on its own terms.

### After a canonical write, re-derive and diff, in the same act that reports success

A governed write to a canonical record re-runs every declared derivation for that record immediately, against the record as it now sits in durable storage rather than against the in-memory value the writer holds, and compares the result byte-for-byte with what is stored. Disagreement fails the write's own report. **"The write succeeded" and "the derived state matches" are reported together or not at all.** A derivation that would change something on a fresh call, immediately after the write that should already have triggered it, is a forgotten derived site — caught by execution rather than by a reviewer rereading a diff.

### A derivation whose input does not exist yet fails the write; it is never stored as a placeholder

A derived value is often due before the artifact it derives from exists: an item entered into a projection before its own record is written, a field derived from a file not yet created. A writer that stores a placeholder in that case has written a value that **passes every check at the moment it is stored, because re-deriving from an absent input yields the same placeholder** — stored and re-derived agree only because both are empty. The agreement expires when the input is written, and the next governed write that re-derives, typically an unrelated one on a different item much later, finds a stale value and refuses, far from the omission that caused it, while the write that stored the placeholder reported success.

So an input that does not resolve is a failure of the write that needed it, never a value. The writer refuses before anything is stored, naming the input and whether it is missing or present but unreadable. Two repairs are prohibited. Loosening the stale-value check to admit the placeholder retires a working control to save one ordering rule. Falling back to a second source for the value — an earlier snapshot of the same fact captured somewhere else — creates a second authority that nothing keeps in step with the first, which is the pointer-with-no-synchronization gap principle 3 names. The residual: this binds writes made through the governed writer. An input removed or corrupted after its derivation succeeded is the re-derive-and-diff case above, and a hand edit of the record reaches neither.

### The coverage claim is computed and asserted, never narrated, anywhere it appears

A derived-artifact runner covers some registry entries and not others. It must therefore compute the set of registry entries it does not independently re-derive, from the registry and its own covered set, at run time; report that set by name in its output, never as a count and never as an omission; and assert it, so that a pinned expectation changes when a newly declared entry is covered by nothing and cannot be added silently.

**No statement of coverage may be maintained by hand anywhere it appears** — not in a comment, not in a docstring, not in a release note, not in a design document. Where a human-readable account of coverage is wanted, it is generated from the same computation.

The failure this prevents is not a mechanism drifting from reality. It is a mechanism's prose drifting from the mechanism, in one place while another place stays correct — which a rule saying *keep the prose in step with the code* does not catch, because someone did keep prose in step with the code, just not all of it. **A module that states its own coverage in three places has three chances to drift and nothing reconciling them. A module that derives it has one source and no chance.**

An entry whose writer cannot be re-run safely is declared uncovered and the reason recorded. It is never listed as covered on the strength of a different integrity mechanism, however much stronger that mechanism is. **Coverage by name with nothing re-running by execution is the exact false claim this requirement exists to forbid, and it is most likely to appear inside the mechanism built to prevent it.**

### A canonical record with derived artifacts has a governed writer

The floor is a single governed writer for the canonical record, which validates the record before rendering anything, guards against a concurrent writer having moved the record since this run read it, and refuses rather than half-applying.

Without it the rest of this contract governs only the second half of the problem. Generating the views from the record removes contradiction between views; it does nothing about an invalid record, and an invalid record renders into a faithful view of the wrong thing — which is precisely what nobody re-reads. **A repository that generates its views and hand-edits its canonical record has moved the unvalidated edit one layer down, not removed it.**

An adopter not yet meeting this floor declares that per entry rather than omitting it, so the registry states the maturity it actually has. The declaration is the honest form; silence is not.

### Every derived site is enumerated by observation, not by recollection

A derived site is any location a generation method writes: files whose entire content is derived; fields inside the canonical record itself that the writer derives and writes back; per-item markers, pointers, and paths embedded in records; and directory locations whose name or position encodes derived state.

The enumeration is verified by running the writer against a scratch copy and comparing the observed write set with the declaration. A writer that touches an undeclared site fails; a declared site nothing writes fails.

**An author enumerating from memory will miss one, and the one missed is characteristically not a file.** A closed design built specifically to eliminate multiple writers can still miss a fourth writer — a pointer the record keeps about itself — repair every file and directory it knew about, and leave that pointer dangling while reporting a clean run. Requiring the enumeration to be derived from the writer's own observed behaviour is the only form of this requirement that survives contact with an adopter's fourth place.

Related and distinct: a derivation whose result is computed but never persisted is indistinguishable from no derivation at all. Re-derive-and-diff catches it; this requirement is what puts the site in scope to be caught.

### Bounded write-back

A projection a person can also type into is the same contract with one axis added. It is a derived artifact, appears in the registry as one, and everything above applies to it unchanged.

**Direction.** The repository is canonical. An external tracker is a derived artifact, exactly as a generated view is.

**Write-back is an allow-list, never a deny-list.** The permitted inbound field set is enumerated positively in the registry entry, and a field not named is prohibited. A deny-list is wrong here for a structural rather than a stylistic reason: the canonical record gains fields over time, and every field added after the deny-list was written is inbound-permitted by default, so the safe default degrades silently with age. An allow-list's default degrades toward refusal, which is visible. The admissible members are the fields a person genuinely manipulates and that no mechanism derives; ordering and priority are the archetype.

**Status, closure and scope never flow inward.** No inbound path may set, clear, or influence a canonical record's lifecycle state. **The moment a tracker can close an item there are two answers to "is this done?"** — and the seam has reproduced, across a boundary no repository-side gate can observe, the exact defect it was built beside. This is not a strong default; it is the seam's precondition, and a deployment permitting it is not a configured seam but a different and ungoverned thing.

**A derived field is never inbound-writable**, independently of the allow-list. The two overlap deliberately: an allow-list can be got wrong by an adopter enumerating optimistically, and this clause is checkable against the registry's own derivation declarations.

**Reconciliation: the canonical record wins, and the loss is reported.** When the two sides disagree the canonical record wins and the projection is overwritten, and the overwritten value is reported as a named, durable event — what was overwritten, on which field, at which time, from which side. Silent resolution in the canonical record's favour is prohibited even though the outcome is identical. The outcome is not the point: an unreported overwrite is a person's work vanishing with no evidence it existed, and after the second occurrence the seam is distrusted and worked around, which is worse than the disagreement. **A reconciliation that cannot report what it discarded has not reconciled; it has overwritten.**

**The seam's own coverage claim is computed.** A tracker projection the runner cannot re-derive — the ordinary case, since re-deriving means a network round trip — is declared uncovered and named, with its alternative integrity mechanism recorded. It is never listed as covered because the adapter reports having synced. A remote system's self-report is the weakest possible evidence of agreement.

This framework defines what a projection with bounded write-back is. It does not know any particular tracker exists, and an adapter for one belongs to the adopting profile.

### What this contract does not provide

Stated rather than left to be inferred from silence, because a guarantee implied is worse than a nonclaim stated.

**Correctness is not addressed, at all.** The mechanism makes contradiction between a canonical record and its derived artifacts structurally impossible and does nothing whatever about either being wrong. A record set that is internally consistent, fully governed, fully covered and factually false satisfies every clause above.

**Concurrency at the canonical write is not solved here.** A write that regenerates a whole shared record can silently erase another writer's in-flight entries while a pair-consistency check certifies the result healthy, because both views agree by construction. Pair consistency is not a loss detector. The governed-writer floor requires a guard and the registry requires the control to be declared; neither supplies one.

**Staleness between a staging area and the working tree is not addressed.** Where writers share one staging area, a staged snapshot can keep a derived value the working tree has since moved past, and it presents as consistent from two directions at once: the snapshot is internally coherent, and the consistency check passes against the working tree. Re-derive-and-diff reads durable storage and says nothing about a staging area.

**Which revision a validation binds to is a requirement, not a guarantee.** A validator that proves a derived artifact is a faithful render by re-rendering and comparing bytes will, by default, re-render using the writer in the working tree rather than the writer in the revision under judgement, so a revision whose derived member was produced by an uncommitted writer validates clean while the committed pair is self-inconsistent. The registry makes the binding declarable and this contract requires validation to be evaluated against the revision under judgement. It cannot enforce it: this framework ships no version-control integration and must not grow one for this.

**Atomicity across a multi-file derived set is not provided.** Where a derivation writes many files with no staging or rename across the set, a crash mid-loop leaves some repaired and some not. That is idempotent by construction, not atomic — a second run converges rather than compounding — and the two are different properties an adopter reading "reconciler" will merge. The whole-set stamp makes the partial state detectable; it does not make the write atomic.

**Re-runnability is a precondition, not a property this contract can confer.** Some legitimate writers have no convergent call shape; an append-only, hash-chained event emitter is the clean example, because re-appending the identical event raises and a materially no-op continuation genuinely appends a second event. An append-only event log is not a projection, and such an entry is declared uncovered with its real integrity mechanism recorded rather than covered on that mechanism's strength.

**A canonical record absent from the registry is invisible to every clause here**, and no clause here discovers one. The registry does not make an adopter's declaration true. This residual is not closed by anything in this section; it is the same question *An artifact registry answers two different questions* asks above, at the narrower scope, and it is closed only by an adopter that carries the detector that section specifies. A declared-population contract with no way to observe what was never declared is honest about its own reach and no wider.

### What this contract delegates to the adopter

Distinguished from the nonclaims above because these are things an adopter can and should build, where this framework correctly declines to ship a mechanism. The concurrency control at the canonical write: the contract requires one and requires it declared, and a read-back-and-refuse guard is sufficient and cheap. The version-control binding of validation: requiring it is portable, performing it is not. The governed writer itself: this framework states the floor and the refusal semantics, and the writer belongs to the domain. The renderers, as pure functions over the canonical record, safe to run against a scratch location — re-derive-and-diff and observed enumeration both depend on that purity, and an adopter whose renderer has side effects has an uncoverable entry, declared uncovered rather than quietly excluded. And atomicity across a large derived set, where the domain needs it rather than idempotence.

### Arming

**Armed by** `schemas/derived-artifact-registry.schema.json`, against which an adopter's registry is validated: the schema fails closed on a missing field, and every field is required including the ones whose honest value is a declared absence, so an absent declaration and a declared absence remain distinguishable. That is the whole of the computed-coverage requirement applied to the declaration itself.

**Residual, and it is the larger half.** This framework ships the contract, the schema and a worked example; it ships no registry, no runner, and no discovery. Nothing here detects a canonical record that was never declared, verifies that a generation method names the writer that actually emits the bytes rather than one that resolves, or runs the re-derivation whose result the computed-coverage requirement governs. Those are the adopter's, and an adopter that declares this contract without them has a schema-valid registry and no control. The computed-coverage requirement is the one clause that binds whatever mechanism an adopter already has rather than obligating a new one, and it is stated in that form deliberately.
