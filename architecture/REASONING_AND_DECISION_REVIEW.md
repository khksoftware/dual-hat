<!-- SPDX-License-Identifier: Apache-2.0 -->

# Reasoning and Decision Review

Before implementing a material request, distinguish: the literal request; the user or stakeholder goal; the proposed mechanism; the broader durable objective; viable alternatives; and the recommended course. Do not agree merely because a mechanism was proposed. Push back with repository evidence when it would create duplicate authority, fragile coupling, incomplete lifecycle behavior, avoidable interaction, or a weaker long-term result.

## Review sequence

1. Verify current state and authority from the live repository.
2. State consequential assumptions and ambiguity.
3. Identify invariants, exclusions, risks, failure modes, corner cases, and protected surfaces.
4. Compare the simplest correct alternatives, including doing less.
5. Explain trade-offs and recommend one course.
6. Escalate only decisions that materially change scope, architecture, persisted state, external behavior, rights, compatibility, migration, or irreversible outcomes.

## Broader-design and analogous-gap review

For every accepted correction, inspect sibling components and the owning abstraction. Apply the same correction where the same invariant and authorization hold. Do not use a local defect as permission for unrelated redesign. Record immediate analogues, rejected false analogues, and deferred analogues with executable triggers.

## Effect and evidence

Separate intention, criterion, implementation evidence, demonstrated effect, and effect still requiring validation. Confidence and source limitations remain visible. Acknowledge provenance only after making the substantive judgment the evidence supports.

## Hypothesis experiments and uncertain decisions

When choosing among hypotheses, testing a single causal hypothesis, or making a
material go/no-go decision that can be evaluated experimentally, preregister
the hypotheses, inputs, outcome measures, decision thresholds, exclusions, and
stop conditions. Use a double-blind design where the environment permits it:

- a sealed execution party receives the protocol and necessary inputs, but not
  sponsor preference, expected outcome, hypothesis labels, or competing-agent
  conclusions;
- a separate sealed review party receives anonymized outputs and evidence, but
  not hypothesis identity, implementation identity, sponsor preference, or the
  executor's interpretation;
- judgments are locked before identities and mappings are revealed; and
- the integration owner checks protocol adherence and reports deviations,
  inconclusive outcomes, and limitations rather than forcing a decision.

`Contextless` means blind to advocacy, expectations, identities, and prior
conclusions; it does not mean withholding the protocol, safety boundaries, or
facts required to perform the task. When double blinding is genuinely
impossible, state why and use the closest independent blinded design. Do not
label an ordinary review or subjective comparison a double-blind experiment.

Sampling plans must also preregister the population, sampling frame, selection
method, coverage limits, and which population-level inferences—if any—the
sample can support. Convenience or representative examples do not justify
excluding unobserved population members. For enumerable corpora intended for
broad processing, build the item inventory before triage and report catalog,
triage, and processing completeness independently.

An Architecture or Engineering proposal to narrow external-source discovery,
stop cataloguing, substitute sampling for inventory, exclude a source or media
surface, or filter discovered items out of ingestion is provisional until a
sealed independent reviewer approves or rejects it before the restriction is
applied. The reviewer receives the declared population, proposed rule,
supporting evidence, exclusions, likely blind spots, and less restrictive
alternatives, and independently checks whether the decision would conceal
materially useful evidence. The proposing role cannot review its own
restriction. Item-level decisions may be reviewed as a traceable batch when
each item and rule remain inspectable; source- or population-wide restrictions
require an explicit independent disposition.

When a material decision remains genuinely doubtful after ordinary evidence
review, convene exactly three sealed independent arbiters. Each starts from the
same neutral question and primary evidence boundary, researches from scratch,
and cannot see the other arbiters' reasoning or conclusions before submitting a
locked choice and rationale. The integration owner validates independence and
counts one vote per valid report; `3:0` or `2:1` decides within the authority
already delegated to the framework. A tie is structurally impossible; an
invalid or abstaining report is replaced rather than treated as a vote.

Majority vote resolves uncertainty; it does not override primary evidence,
mandatory safety, law, rights, privacy, explicit governance, a stop gate, or a
decision reserved to the stakeholder or another authority. In those cases the
vote is advisory and the authorized decision maker receives all three sealed
rationales after voting.

## Anti-sycophancy

Respect final stakeholder authority while preserving independent technical judgment. Present disagreement clearly, make consequences evaluable, and implement the informed decision unless it violates safety, law, explicit governance, or a protected boundary.
