<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 4.4.0 release notes

Dual Hat 4.4.0 is a minor release carrying one change. No principle is renumbered or retired, no governance file is added, renamed or reorganized, no schema, gate or tool changes, and no existing citation stops resolving.

**The change makes the Pareto principle explicit as a design-and-assurance heuristic, and says plainly what it is not.** Principle 1 already asked for proportionate process; it did not say how to decide what proportionate coverage looks like when a matrix could be multiplied indefinitely. It now does, in three places that each own a different part of the answer: principle 1 states the heuristic, the planning model states what a plan must enumerate before it selects a matrix, and the validation protocol states how the resulting proof is composed.

**Read the prohibition before the permission, because the permission is the half that gets quoted.** 80/20 is named as a heuristic and **never as a numeric coverage quota**. Nothing here licenses leaving an arbitrary remainder untested, and the release does not introduce a coverage percentage anywhere. The obligation added is to *enumerate first*: the materially distinct failure modes, decision branches, owners or protected boundaries, and risk classes — and only then to choose the smallest defect-sensitive representative set that exercises every one of those classes.

**The part most likely to change what an adopter actually does is where breadth is allowed to live.** Where a large combinatorial or scale population repeats the same semantics, its breadth belongs in the cheapest sound layer — analytical, simulated, in-memory, property-based — **after** establishing that layer's semantic equivalence to the production logic, inputs and oracle. Real end-to-end, integration and durability anchors are retained for the properties that cheaper layer cannot prove. An adopter who has been paying for a full cross-product to establish something a property test would establish more cheaply now has explicit framework support for moving it; an adopter who substitutes a proxy whose behaviour or oracle differs from the property being claimed is now explicitly outside the rule.

**Two obligations come with it, and they are what keep the heuristic honest.** A proof states the cross-products it omitted and the claims it is therefore not making, so focused evidence cannot later be read as exhaustive evidence. And exhaustive execution stays required where each cell owns materially distinct semantics, where impact cannot be bounded reliably, where a material safety or integrity risk applies, or where an explicit semantic-release authority requires it.

**Nothing is traded away for cost.** Refusal, rollback, identity, durability, safety, recovery evidence and every declared mandatory gate remain non-negotiable, and the release states that rather than leaving it to be inferred from a heuristic about spending less.

**Adopter action: none is required.** This is advice-tier guidance with no detector behind it, consistent with how the principle set labels its own enforcement. An adopter already sizing test matrices this way is already conformant; an adopter reading 80/20 as a coverage target should stop, because the text now forecloses that reading explicitly.
