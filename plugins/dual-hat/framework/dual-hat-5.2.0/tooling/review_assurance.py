# SPDX-License-Identifier: Apache-2.0
"""Read-only, product-neutral whole-object review admission and falsification.

Adapters extract facts from primary artifacts. A separately bound basis declares
authorized replacements, semantic equivalence and dependency effects. This code
checks accounting; it cannot discover omitted requirements or authenticate the
human authority named by an adapter. A structural Green is never acceptance.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Callable

BASIS_SCHEMA = "dual-hat-review-basis/1.0"
EVIDENCE_SCHEMA = "dual-hat-review-evidence/1.0"
REVIEW_PLAN_SCHEMA = "dual-hat-deep-review-plan/1.0"

CLAIM_CHAIN_STAGES = (
    "authority",
    "producer",
    "representation",
    "transition",
    "consumer",
    "failure_recovery",
    "evidence",
)

DEEP_REVIEW_HAZARDS = (
    "authority_temporality_and_circular_gates",
    "producer_consumer_delivery",
    "canonical_representation_and_hashing",
    "source_runtime_contradiction",
    "blocking_io_and_killability",
    "partial_write_and_recovery_cross_product",
    "identity_provenance_and_relabelling",
    "resource_amplification_and_content_encoding",
    "time_of_check_to_time_of_use",
    "environment_dependency_and_platform",
    "privacy_retention_logs_and_crash_artifacts",
    "reviewer_contamination_and_common_mode",
    "population_denominator_and_exclusions",
    "measurement_basis_and_cost",
    "compatibility_migration_and_versioning",
    "substantive_human_projection_and_machine_source_divergence",
    "evaluation_artifact_fitness_and_post_result_tuning",
    "external_control_plane_reachability_revocation_and_receipts",
    "frozen_package_execution_side_effects_and_transitive_imports",
    "authority_revocation_during_external_pause",
    "multi_clock_expiry_and_restart_semantics",
    "renderer_injection_and_hostile_model_output",
    "tool_binary_and_parser_supply_chain_drift",
)


def canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("ascii")).hexdigest()


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: object) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value) and len(set(value)) == len(value)


def _key(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(_text(part) for part in value):
        raise ValueError("obligation key must be a nonempty string tuple")
    return tuple(value)


def deep_review_plan_failures(plan: dict) -> tuple[str, ...]:
    """Validate admission accounting for an expensive complete-object review.

    This prevents a reviewer from beginning with unnamed seams or a inherited
    finding list as its whole search space. It does not establish that prose is
    true, that the hazard list is universally complete, or that the review ran.
    Reviewers must challenge both the plan and the candidate from primary bytes.
    """
    errors = []
    try:
        if set(plan) != {"schema", "tier", "subject_sha256", "separation",
                         "claims", "hazard_dispositions"}:
            raise ValueError("review plan fields")
        if plan["schema"] != REVIEW_PLAN_SCHEMA or plan["tier"] != "deep_complete_object":
            raise ValueError("review plan schema/tier")
        digest = plan["subject_sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("subject digest")

        separation = plan["separation"]
        required_separation = {
            "candidate_frozen",
            "candidate_author_separate",
            "sibling_findings_hidden",
            "ambient_context_disclosed",
            "durable_report_target_predeclared",
            "package_no_write",
            "tooling_execution_copy_separate",
            "post_tool_inventory_verified",
            "transitive_imports_manifested",
        }
        if set(separation) != required_separation or any(separation[key] is not True
                                                         for key in required_separation):
            errors.append("reviewer separation is incomplete")

        claims = plan["claims"]
        if not isinstance(claims, list) or not claims:
            raise ValueError("claim population empty")
        seen = set()
        for claim in claims:
            if set(claim) != {"id", "assertion", "risk", "chain",
                              "source_anchors", "falsification_cases"}:
                raise ValueError("claim fields")
            if not all(_text(claim[key]) for key in ("id", "assertion", "risk")):
                raise ValueError("claim identity")
            if claim["id"] in seen:
                errors.append("duplicate review claim:" + claim["id"])
            seen.add(claim["id"])
            chain = claim["chain"]
            if not isinstance(chain, dict) or set(chain) != set(CLAIM_CHAIN_STAGES) or \
                    any(not _text(chain[stage]) for stage in CLAIM_CHAIN_STAGES):
                errors.append("incomplete claim chain:" + claim["id"])
            anchors = claim["source_anchors"]
            if not isinstance(anchors, list) or not anchors:
                errors.append("missing source anchor:" + claim["id"])
            else:
                anchor_ids = set()
                for anchor in anchors:
                    if set(anchor) != {"id", "sha256"} or not _text(anchor["id"]) or not \
                            isinstance(anchor["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", anchor["sha256"]):
                        raise ValueError("source anchor")
                    if anchor["id"] in anchor_ids:
                        errors.append("duplicate source anchor:" + claim["id"] + ":" + anchor["id"])
                    anchor_ids.add(anchor["id"])
            cases = claim["falsification_cases"]
            if not isinstance(cases, list) or len(cases) < 2 or not all(
                    isinstance(case, dict) and set(case) == {"id", "polarity", "witness"}
                    and _text(case["id"]) and case["polarity"] in {"positive", "negative"}
                    and _text(case["witness"]) for case in cases):
                errors.append("invalid falsification cases:" + claim["id"])
            elif {case["polarity"] for case in cases} != {"positive", "negative"}:
                errors.append("falsification polarity incomplete:" + claim["id"])
            elif len({case["id"] for case in cases}) != len(cases):
                errors.append("duplicate falsification case:" + claim["id"])

        dispositions = plan["hazard_dispositions"]
        if not isinstance(dispositions, list):
            raise ValueError("hazard dispositions")
        found = set()
        for row in dispositions:
            if set(row) != {"hazard", "status", "basis"} or row["hazard"] not in DEEP_REVIEW_HAZARDS \
                    or row["status"] not in {"applicable", "not_applicable"} or not _text(row["basis"]):
                raise ValueError("hazard disposition")
            if row["hazard"] in found:
                errors.append("duplicate hazard disposition:" + row["hazard"])
            found.add(row["hazard"])
        if found != set(DEEP_REVIEW_HAZARDS):
            errors.append("deep-review hazard population differs")
        canonical_digest(plan)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        errors.append("invalid deep review plan:" + str(exc))
    return tuple(errors)


def markdown_contract_units(markdown: str) -> dict[str, str]:
    """Inventory complete level-two sections, including prose and preamble.

    This is preservation, not interpretation: whitespace and every clause are
    retained. Fenced headings do not divide sections. Duplicate headings and
    unterminated fences refuse so an ambiguous source cannot lose a unit.
    The caller owns the scope of the supplied document and its separate basis.
    """
    if not isinstance(markdown, str) or not markdown:
        raise ValueError("contract document is empty")
    result, key, lines, fence = {}, "preamble", [], None
    for line in markdown.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
        elif marker:
            fence = marker[1]
        else:
            heading = re.match(r"^ {0,3}##[ \t]+([^\r\n]+)", line)
            if heading:
                if lines:
                    result[key] = "".join(lines)
                key = "section:" + heading[1].strip()
                if key in result:
                    raise ValueError("duplicate contract section:" + key)
                lines = []
        lines.append(line)
    if fence:
        raise ValueError("unterminated contract fence")
    if key in result:
        raise ValueError("duplicate contract section:" + key)
    result[key] = "".join(lines)
    return result


def markdown_contract_inventory(markdown: str) -> dict:
    """Preserve section order explicitly, including when JSON keys are sorted."""
    units = markdown_contract_units(markdown)
    return {"section-order": list(units), **units}


def falsify_source_adapter(basis: dict, sources: dict[str, bytes],
                          extractor: Callable, mutations,
                          checker: Callable = None) -> dict:
    """Re-extract damaged *primary bytes*, then invoke the real admission check.

    Mutations are (unique ID, complete damaged source mapping) pairs, usually
    generated from independently selected source units. Reports bind changed
    bytes without retaining potentially large/private source content. A copied
    expected inventory fails this test even when evidence-only mutants pass.
    No mutation, unapplied mutation, bad control or harness failure earns Green.
    """
    checker = validate_assurance if checker is None else checker
    report = {"green": False, "baseline_errors": [], "mutants": [], "errors": [],
              "limits": "Tests the supplied source mutation population and extractor; not semantic correctness or completeness of the selected source basis."}

    def valid_sources(value):
        return isinstance(value, dict) and bool(value) and all(_text(k) and isinstance(v, bytes) for k, v in value.items())

    def inspect(value):
        try:
            extracted = extractor(dict(value))
        except (KeyError, ValueError, SyntaxError, UnicodeError) as exc:
            return ("source extraction refused:" + str(exc),), "extraction"
        errors = checker(copy.deepcopy(basis), extracted)
        if not isinstance(errors, (tuple, list)) or not all(_text(error) for error in errors):
            raise TypeError("checker must return an error sequence")
        return tuple(errors), "admission"

    try:
        if not valid_sources(sources):
            raise ValueError("invalid source mapping")
        original = dict(sources)
        report["baseline_errors"] = list(inspect(original)[0])
        if report["baseline_errors"]:
            return report
        seen = set()
        for name, damaged in mutations:
            if not _text(name) or name in seen or not valid_sources(damaged):
                raise ValueError("invalid or duplicate source mutation")
            seen.add(name)
            changed = sorted(key for key in set(original) | set(damaged)
                             if original.get(key) != damaged.get(key))
            if not changed:
                raise ValueError("source mutation was not applied:" + name)
            identities = {key: {
                "before_sha256": hashlib.sha256(original[key]).hexdigest() if key in original else None,
                "after_sha256": hashlib.sha256(damaged[key]).hexdigest() if key in damaged else None,
            } for key in changed}
            errors, stage = inspect(damaged)
            report["mutants"].append({"mutation": name, "sources": identities,
                                      "rejected": bool(errors), "stage": stage})
        if not seen:
            raise ValueError("source mutation population is empty")
        if not any(row["stage"] == "admission" for row in report["mutants"]):
            raise ValueError("source mutations exercised extraction failure only")
        report["green"] = all(row["rejected"] for row in report["mutants"])
    except Exception as exc:
        # A broken harness is an unsuccessful proof, never a detected defect.
        report["errors"].append(type(exc).__name__ + ":" + str(exc))
    return report


def python_carrier_inventory(markdown: str, *, metadata: bool = False) -> dict:
    """Extract literal top-level class field layouts from Python fenced blocks.

This language adapter does not decide which classes ought to exist. Duplicate
definitions and invalid Python are refused instead of silently overwritten.
"""
    result = {}
    for block in re.findall(r"```python\n(.*?)\n```", markdown, flags=re.S):
        for node in ast.parse(block).body:
            if isinstance(node, ast.ClassDef):
                if node.name in result:
                    raise ValueError("duplicate carrier:" + node.name)
                result[node.name] = [(field.target.id, ast.unparse(field.annotation))
                                     for field in node.body if isinstance(field, ast.AnnAssign)
                                     and isinstance(field.target, ast.Name)]
                if metadata:
                    result[node.name] = {
                        "decorators": [ast.dump(value, include_attributes=False) for value in node.decorator_list],
                        "bases": [ast.dump(value, include_attributes=False) for value in node.bases],
                        "keywords": [ast.dump(value, include_attributes=False) for value in node.keywords],
                        "defaults": {field.target.id: ast.dump(field.value, include_attributes=False)
                                     for field in node.body if isinstance(field, ast.AnnAssign)
                                     and isinstance(field.target, ast.Name) and field.value is not None},
                        "other_members": [ast.dump(member, include_attributes=False) for member in node.body
                                          if not isinstance(member, ast.AnnAssign)],
                    }
    return result


def semantic_duplicates(cases: list[dict]) -> tuple[str, ...]:
    """Identity is an explicit semantic key, never the label or witness wording."""
    seen, errors = set(), []
    for row in cases:
        key = _key(row["obligation"])
        if key in seen:
            errors.append("duplicate semantic obligation:" + "/".join(key))
        seen.add(key)
    return tuple(errors)


def required_interactions(basis: dict) -> dict[tuple[str, str], list[str]]:
    """Derive affected invariant/transition pairs from declared dependency edges."""
    transitions, invariants = basis["transitions"], basis["invariants"]
    if not isinstance(transitions, list) or not isinstance(invariants, list):
        raise ValueError("transition/invariant populations must be arrays")
    seen_t, seen_i = set(), set()
    for row in transitions:
        if set(row) != {"id", "writes"} or not _text(row["id"]) or not _strings(row["writes"]) or not row["writes"]:
            raise ValueError("invalid transition")
        if row["id"] in seen_t:
            raise ValueError("duplicate transition")
        seen_t.add(row["id"])
    for row in invariants:
        if set(row) != {"id", "reads", "observations"} or not _text(row["id"]) or not _strings(row["reads"]) or not row["reads"] or not _strings(row["observations"]) or not row["observations"]:
            raise ValueError("invalid invariant")
        if row["id"] in seen_i:
            raise ValueError("duplicate invariant")
        seen_i.add(row["id"])
    return {(transition["id"], invariant["id"]): invariant["observations"]
            for transition in transitions for invariant in invariants
            if set(transition["writes"]) & set(invariant["reads"])}


def validate_assurance(basis: dict, evidence: dict) -> tuple[str, ...]:
    """Fail closed for malformed inputs, unexplained loss and incomplete proof accounting."""
    errors = []
    try:
        if set(basis) != {"schema", "source_bindings", "contract", "changes", "source_obligations", "obligations", "transitions", "invariants"} or basis["schema"] != BASIS_SCHEMA:
            raise ValueError("basis schema")
        if set(evidence) != {"schema", "basis_sha256", "source_bindings", "contract", "cases", "witnesses", "interactions"} or evidence["schema"] != EVIDENCE_SCHEMA:
            raise ValueError("evidence schema")
        if evidence["basis_sha256"] != canonical_digest(basis):
            errors.append("basis binding differs")
        sources = basis["source_bindings"]
        if not isinstance(sources, dict) or not sources or any(not _text(k) or not isinstance(v, str) or len(v) != 64 or any(c not in "0123456789abcdef" for c in v) for k, v in sources.items()):
            raise ValueError("source bindings invalid")
        if evidence["source_bindings"] != sources:
            errors.append("primary source bindings differ")
        expected, actual = copy.deepcopy(basis["contract"]), evidence["contract"]
        if not isinstance(expected, dict) or not expected or not isinstance(actual, dict):
            raise ValueError("contract inventories must be nonempty objects")
        if any(not _text(key) for key in (*expected, *actual)):
            raise ValueError("contract identity invalid")
        changes = basis["changes"]
        if not isinstance(changes, list):
            raise ValueError("changes must be an array")
        changed = set()
        for change in changes:
            if set(change) != {"id", "before_sha256", "after", "disposition", "authority", "reason"} or not all(_text(change[key]) for key in ("id", "authority", "reason")):
                raise ValueError("invalid replacement declaration")
            key = change["id"]
            if key in changed:
                raise ValueError("duplicate replacement declaration")
            changed.add(key)
            before = canonical_digest(expected[key]) if key in expected else None
            if change["before_sha256"] != before:
                errors.append("replacement predecessor differs:" + key)
            if change["disposition"] == "remove":
                if key not in expected or change["after"] is not None:
                    raise ValueError("invalid removal")
                del expected[key]
            elif change["disposition"] in {"replace", "add"}:
                if (change["disposition"] == "add") == (key in expected):
                    raise ValueError("replacement/addition existence differs")
                if key in expected and canonical_digest(expected[key]) == canonical_digest(change["after"]):
                    raise ValueError("meaningless unchanged replacement")
                expected[key] = change["after"]
            else:
                raise ValueError("unknown replacement disposition")
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual or canonical_digest(expected[key]) != canonical_digest(actual[key]):
                errors.append("contract differs:" + key)

        if not _strings(basis["source_obligations"]):
            raise ValueError("source obligation inventory invalid")
        wanted = [_key(row) for row in basis["obligations"]]
        if not wanted or len(set(wanted)) != len(wanted):
            raise ValueError("required obligations empty or duplicated")
        seen, ids, coverage = set(), set(), []
        errors.extend(semantic_duplicates(evidence["cases"]))
        for row in evidence["cases"]:
            if set(row) != {"id", "obligation", "witness", "covers"} or not _text(row["id"]) or not _text(row["witness"]) or not _strings(row["covers"]):
                raise ValueError("case contract invalid")
            key = _key(row["obligation"])
            if row["id"] in ids:
                errors.append("duplicate case identity:" + row["id"])
            seen.add(key)
            ids.add(row["id"])
            coverage.extend(row["covers"])
        if seen != set(wanted):
            errors.append("semantic obligation population differs")
        if len(coverage) != len(set(coverage)) or set(coverage) != set(basis["source_obligations"]):
            errors.append("predecessor obligation accounting differs")

        witnesses = {}
        for row in evidence["witnesses"]:
            if set(row) != {"id", "observations"} or not _text(row["id"]) or not isinstance(row["observations"], dict) or not row["observations"] or not all(_text(k) and _text(v) for k, v in row["observations"].items()):
                raise ValueError("interaction witness invalid")
            if row["id"] in witnesses:
                errors.append("duplicate interaction witness:" + row["id"])
            witnesses[row["id"]] = row["observations"]
        required = required_interactions(basis)
        seen_pairs, used_witnesses = set(), set()
        for row in evidence["interactions"]:
            if set(row) != {"transition", "invariant", "witness_id"} or not all(_text(v) for v in row.values()):
                raise ValueError("interaction evidence invalid")
            pair = (row["transition"], row["invariant"])
            if pair in seen_pairs:
                errors.append("duplicate interaction:" + "/".join(pair))
            seen_pairs.add(pair)
            used_witnesses.add(row["witness_id"])
            if pair not in required or set(witnesses.get(row["witness_id"], {})) != set(required.get(pair, [])):
                errors.append("interaction observations differ:" + "/".join(pair))
        if seen_pairs != set(required):
            errors.append("dependency-derived interaction population differs")
        if used_witnesses != set(witnesses):
            errors.append("orphaned or missing interaction witness")
        canonical_digest(evidence)  # Reject noncanonical/non-JSON values as well.
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        errors.append("invalid assurance input:" + str(exc))
    return tuple(errors)


def falsify_checker(basis: dict, evidence: dict,
                    checker: Callable = validate_assurance) -> dict:
    """Exercise the actual checker on valid control plus systematic damaged copies."""
    baseline = checker(basis, evidence)
    if baseline:
        return {"green": False, "baseline_errors": list(baseline), "mutants": []}
    mutants = []

    def attempt(name, edit):
        damaged = copy.deepcopy(evidence)
        edit(damaged)
        if canonical_digest(damaged) == canonical_digest(evidence):
            raise ValueError("falsification mutation was not applied:" + name)
        rejected = bool(checker(basis, damaged))
        mutants.append({"mutation": name, "rejected": rejected})

    for key in sorted(evidence["contract"]):
        attempt("remove-contract:" + key, lambda d, key=key: d["contract"].pop(key))
        attempt("change-contract:" + key, lambda d, key=key: d["contract"].__setitem__(key, {"corrupted_original": d["contract"][key]}))
    for index in range(len(evidence["cases"])):
        attempt("omit-obligation:" + str(index), lambda d, index=index: d["cases"].pop(index))
    def duplicate(d):
        row = copy.deepcopy(d["cases"][0])
        row.update(id="different-label", witness="Different wording must not create another obligation", covers=[])
        d["cases"].append(row)
    attempt("renamed-duplicate", duplicate)
    for index in range(len(evidence["interactions"])):
        attempt("omit-interaction:" + str(index), lambda d, index=index: d["interactions"].pop(index))
    for index, witness in enumerate(evidence["witnesses"]):
        for observation in sorted(witness["observations"]):
            attempt("omit-observation:" + str(index) + ":" + observation,
                    lambda d, index=index, observation=observation: d["witnesses"][index]["observations"].pop(observation))
    attempt("stale-basis", lambda d: d.__setitem__("basis_sha256", "0" * 64))
    return {"green": bool(mutants) and all(row["rejected"] for row in mutants),
            "baseline_errors": [], "mutants": mutants,
            "limits": "Proves detection of these mutations against this supplied basis, not completeness of the basis or correctness of proposed behavior."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("basis", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--falsify", action="store_true")
    args = parser.parse_args()
    try:
        basis = json.loads(args.basis.read_text(encoding="utf-8"))
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
        errors = validate_assurance(basis, evidence)
        result = {"green": not errors, "errors": list(errors)}
        if args.falsify and not errors:
            result = falsify_checker(basis, evidence)
    except (OSError, ValueError) as exc:
        result = {"green": False, "errors": [str(exc)]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
