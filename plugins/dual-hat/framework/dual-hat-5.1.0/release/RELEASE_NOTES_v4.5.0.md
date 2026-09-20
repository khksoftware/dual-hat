<!-- SPDX-License-Identifier: Apache-2.0 -->

# Dual Hat 4.5.0 release notes

Dual Hat 4.5.0 is a minor release that makes the enforcement location of every governing principle visible without changing what any principle requires.

Each numbered principle now carries exactly one of three classifications:

- **mechanically armed** means the framework names a resolvable executable mechanism;
- **adopter-delegated** means an adopting project or platform must supply the mechanism; and
- **judgement-only** means no executable detector exists and the principle relies on its explicit Advice paragraph.

The classification is intentionally short. It never repeats a mechanism name or residual. The existing Armed-by or Advice paragraph remains authoritative for what exists, where it runs, what invokes it, and what it cannot prove. In particular, mechanically armed does not imply that every adopter has installed or invoked the named mechanism.

The current population is six mechanically armed principles, two adopter-delegated principles, and eight judgement-only principles. That population is derived from the canonical document rather than trusted from a prose total. The companion census proves that each principle has one approved classification; that the classification agrees with the distinct Armed-by or Advice structure; that a judgement-only principle has exactly one canonical Advice paragraph; and that mechanically armed file and symbol references resolve.

The proof has an explicit limit: structural classification and reference resolution cannot establish semantic equivalence between a principle's prose and a mechanism's behavior. That remains review and judgement, and the release does not claim otherwise.

No principle is added, removed, renumbered, or weakened. No gate, hook, predicate, schema, tool, runtime behavior, identifier, or existing citation changes. Adopters need take no migration action; the added labels make the enforcement boundary easier to inspect.
