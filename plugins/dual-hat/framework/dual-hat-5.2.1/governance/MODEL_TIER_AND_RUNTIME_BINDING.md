<!-- SPDX-License-Identifier: Apache-2.0 -->

# Model Tier and Runtime Binding Governance

Portable Dual Hat policy names capabilities, never providers or product model names.

| Tier | Intended work | Capability and evidence |
| --- | --- | --- |
| Tier 0 — Scripted | Work whose correct output a fixed procedure fully determines from its declared inputs, and whose every other outcome the procedure classifies — timeout, crash, partial output, inputs changed underneath: running a declared validation population, rendering a report from a record, deriving a position from a governed queue | Bind to a script, not a model, bounded in time. Retain its complete output where the consumer can reach it, and report an index of that output, never a replacement for it. Any judgement over the result stays with the role that owns it. |
| Tier 1 — Routine | Bounded execution of a known procedure whose outcomes still need a model to read, classify, or recover from | Basic reasoning, bounded tools/context, direct validation; optimize cost and latency. |
| Tier 2 — Standard | Ordinary implementation and analysis | Repository inspection, work-item context, tests, and actionable evidence; escalate on cross-domain or unresolved risk. |
| Tier 3 — Advanced | Complex architecture and independent review | Cross-domain context, resumable handoff, strong reasoning, and independent primary-evidence review. |
| Tier 4 — Critical | Deep security, privacy, rights, release, or repository-integrity review | Complete risk boundary, detached validation where applicable, mandatory independence, and risk-first selection. |

Architecture assigns tiers to activities. A mandatory tier cannot be silently downgraded. Optional downgrade requires a recorded reason and user/Architecture confirmation; unavailable mandatory capability produces a resumable hard stop. Fallback must satisfy the same tier or remain explicitly inadequate. Evidence records the abstract requirement, concrete local selection, environment fingerprint, availability, and confirmation.

When an agent or reviewer struggles, diagnose whether the mismatch is
capability or ownership before retrying. **Re-tier** when the assigned model or
runtime lacks the reasoning depth, context, tools, or reliability required by
the same role. **Re-role** when the task's authority, method, failure axis, or
expected judgment belongs to a different role even if the current model is
capable. Do not spend model tier to compensate for a confused role, and do not
rename a role to conceal inadequate capability. Preserve the work boundary and
independence requirements across either change.

## Bind by what the output needs, not by what the work looks like

A unit of work takes the lowest tier whose executor can produce a correct result, and the test is
the output rather than the activity. **When a fixed procedure both produces the result and
classifies every way of failing to produce it, the work is Tier 0.** A mechanical test for
success is not enough on its own, because the outcomes a procedure leaves unclassified are where a
model executor was supplying judgement. Binding a model to Tier 0 work adds cost, and failure modes
of the model's own: it pays its whole start-up and grounding cost to run a procedure, and it can
decline the procedure or substitute another. A script has failure modes too. It summarises exactly
as lossily as it was written to, and it records whatever environment detail its author did not
redact. The comparison is between two sets of failure modes, never between failure and none.

**A preflight that enumerates every registry a change owes an update to is Tier 0 work for the
identical reason.** Computed against its declared inputs -- the change's own diff and the current
state of each registry -- the procedure both produces the list and classifies every way it could
fail to: a registry that does not parse, a base that moved underneath it, an obligation it cannot
resolve. Each becomes its own reported outcome rather than a silent pass. Judging whether a listed
obligation is actually owed, and any registry whose classification is not mechanical, stays with
the role that owns it; the procedure only enumerates.

**A refresh that recomputes recorded evidence is Tier 0 work only for the evidence a procedure
can itself verify.** Where a registry pairs a judgement -- a classification, a disposition --
with the content hashes that judgement was made against, a script may recompute and rewrite
those hashes, and stamp the moment and reference point it verified them at, without touching
the judgement itself: the same boundary Tier 0 already draws between producing a result and
judging it. When the recomputed evidence shows that what the judgement was made against has
since changed on a side the procedure does not own, the procedure refuses to rewrite the record
silently -- it requires the judgement to be re-supplied as an explicit argument, never inferred
from the fact that only the hashes moved. Supplying that argument, even to reaffirm the same
judgement, is the caller's own evidence that the required human re-read happened.

**A unit that mixes phases whose outputs need different things may be split, so that each phase
binds to its own tier.** Detecting what changed, or rebuilding an artifact from a record, often
passes the Tier 0 test. A survey in principle 2's sense never does. Done as one unit, all of it
binds to the tier of its hardest phase; split, the mechanical phases can run at Tier 0. Splitting
has a cost the single unit did not have: a later phase sees only what an earlier phase recorded.
So the later phase re-derives any premise it acts on rather than inheriting it. A split is a
re-binding, and it takes the admission test below.

**Batch Tier 0 work whose cost does not grow with what it carries.** When one validation pass
covers several changes about as cheaply as one, because what they select overlaps and not merely
because a start-up cost is shared, run it once over all of them. Attribute a failure by re-running
the failing checks at successive parents until the change that introduces it is found, never by
inference from which change touched what. A re-run used to attribute a failure first re-runs
at the point already suspected of producing it, more than once, before treating that point's own
result as evidence. When those repeated runs disagree, the procedure reports the disagreement and
attributes nothing: a flaky failure is an outcome the procedure fully classifies, so this check is
Tier 0 too. Skipping it to save a re-run reports a guess as a fact. When a batched pass reports on a target named in
advance, absence is a whole-run verdict, never a per-partition one: the procedure merges every
partition's observation of that target before reporting it absent, because a target merely
assigned to another partition has not been shown absent at all.

**Once a Tier 0 route exists for a step, it is the step's required path, and any other executor
for that same step is a fallback confined to the route's own declared failure classes.** A step
that qualifies for Tier 0 does not stay optional merely because a model-executed equivalent was
how it used to run: leaving both live, indefinitely interchangeable, reintroduces exactly the
judgement-substituting-for-procedure cost Tier 0 exists to remove. The fallback earns its place
only where the route itself names a class it cannot resolve -- a missing precondition, an
ambiguous input, a genuine contention it cannot wait out -- never as a standing alternative a
caller may prefer merely because it is familiar or already open.

**Losslessness is the admission test for a re-binding, not its aspiration.** Moving work down a
tier is lossless only when the new executor's output carries everything the consumer actually used
from the old one. **Establish that from the old executor's real outputs, never from its mandate.**
An executor told to decide nothing still answers the question its brief put, explains outcomes it
could not classify, and checks its instruments against each other; a consumer that relied on any
of that loses it silently. Where the replacement's output demonstrably carries every such signal,
adopt it, with the recorded reason and confirmation that any downgrade requires. Otherwise,
validate on real work first. Compare task success per completed task, including any follow-up the
change makes necessary, rather than cost per request, and keep the change only if success does not
regress. Name whatever remains unmatched as given up, including a model's occasional report of
something outside its mandate.

**Launching a script is not delegating the judgement a role retains.** When a role's own standing
obligation is to run its checks itself, a deterministic script that role launches -- and whose
complete output that role reads before deciding -- satisfies that obligation for any check a fixed
procedure fully decides (the Tier 0 admission test above). The judgement stays with the role:
reading the output and deciding acceptance are not the script's to perform, and a check the
procedure leaves unclassified is not Tier 0 work regardless of who launches the script that
attempts it.

Development adapters bind tiers using hash-verified exposed evidence only: adapter identity, tool inventory, complete runtime/platform fingerprint, supported probes, configuration, and user confirmation. Any fingerprint change invalidates capability, availability, and confirmation evidence and forces remapping. If the host cannot switch automatically, it gives adapter-specific manual switching instructions and records the user-confirmed selection. It never pretends to detect a capability the host withholds.

The host adapter and governed capability registry are the trusted provenance boundaries. Evidence must identify its source type, authority ID, observation ID, complete environment identity where applicable, and canonical evidence hash. Core routing rejects malformed, altered, or stale receipts; it does not elevate self-hashed records from an untrusted caller into provider or user authority.

Production configuration is deliberately separate. Before first production use, the user explicitly approves provider, model, effort, fallback, privacy and local/cloud preference, cost, latency, retention restrictions, permitted task classes, and unavailable-model behavior. Development detection never supplies production choices. No provider or model is silently selected or replaced.

Development or production switching occurs only at an atomic safe boundary. Mid-operation change waits while preserving state unless the operation has an explicit resumable-transfer contract. The approved production configuration contains hash-verified tier capability evidence; switching hard-stops when the requested tier is not verified even when the model is available. Unavailable or inadequate mandatory production selection stops and requests configuration.
