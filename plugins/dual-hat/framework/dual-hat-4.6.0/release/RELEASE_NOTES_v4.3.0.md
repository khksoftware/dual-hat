<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 4.3.0 release notes

Dual Hat 4.3.0 is a minor release. No principle is renumbered or retired, no governance file is added, renamed or reorganized, and no existing citation stops resolving.

**Read the new quiescence definition first, because it is the change most likely to find an adopter already doing something else.** Four requirements in the framework already named quiescence as a precondition without defining it. The definition now states what the claim means and, more consequentially, what does not establish it: an actor's own report that it stopped, a completion or termination notification, a removed registration, a released lock, and the absence of recent output. Each of those is either authored by the actor whose stopping is in question, or records an intention rather than a state.

**That is the one place an upgrade can bite.** An adopter who has been discharging a quiescence precondition with a completion notification was already non-conformant with the four requirements that named it, but nothing said so plainly and the practice was easy to arrive at honestly. It is now plainly non-conformant. The remedy is a direct reading of the resource, or of the platform's own authoritative record, showing that no writer inside the named boundary retains write access -- and because quiescence is perishable, the proof is paired with a bar on re-entry rather than taken once and relied on later.

**Principle 8's amendment relaxes rather than tightens, and needs no adopter action.** A deliberately abandoned outcome is now expressible. Before this, a working cancel deadlocked the dispatch inventory permanently, and the only two ways out both required writing something false into the gate that checks closure. The relief is narrow on purpose: one conjunct, for one state, with a dead worker's successor requirement untouched, and the flag refused beside a completed outcome.

**Adopters who publish through `staged_publication` should expect their published file set to change if it was ever wider than their tracked set.** The file list now derives from git. If a publication was previously sweeping untracked files in, those files stop being published -- which is the point: they were content no commit contained.

**Reviewers commissioned under the code review contract have a new obligation and it is procedural rather than substantive.** Establish the population before writing findings, disposition every member, and report the denominator, marking anything uninspected as unchecked. The contract now also says where a repair's scope comes from: the review's population, not the artifact list a finding happens to name.

Schema changes are additive and optional. Tooling changes are corrective.
