# SPDX-License-Identifier: Apache-2.0
"""Deterministic quality-rule discovery, review planning, and baseline helpers."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from path_containment import ContainmentError, contained, is_reparse


TIERS = ("light", "standard", "deep")
LIFECYCLES = {"draft", "active", "suspended", "superseded", "archived"}
ACTIONS = {
    "require", "recommend", "prohibit", "ignore", "suppress", "replace",
    "adjust_severity", "require_evidence", "require_manual_review",
    "trigger_deeper_review", "accept_known_tradeoff", "defer_until_trigger", "exempt",
}
PRECEDENCE = {"architecture_default": 10, "repository_architecture": 20, "user": 30, "non_waivable": 40}
BLOCKING_SEVERITIES = {"critical", "high"}


class QualityReviewError(ValueError):
    pass


def _json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QualityReviewError(f"{path}: invalid JSON: {exc}") from exc


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _canonical_hash(value: object) -> str:
    return _digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=root, capture_output=True, text=True)
    if result.returncode:
        raise QualityReviewError(f"cannot derive governed Git state: {' '.join(args)}")
    return result.stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    result = subprocess.run(("git", *args), cwd=root, capture_output=True)
    if result.returncode:
        raise QualityReviewError(f"cannot derive governed Git content: {' '.join(args)}")
    return result.stdout


def _contained_json(root: Path, relative: object, label: str) -> tuple[Path, Mapping[str, object]]:
    if not isinstance(relative, str) or not relative:
        raise QualityReviewError(f"baseline state resolver lacks {label}")
    try: path = contained(root, relative, must_exist=True, kind="file")
    except ContainmentError as exc: raise QualityReviewError(f"baseline state resolver {label} escapes the governed root") from exc
    payload = _json(path)
    if not isinstance(payload, Mapping): raise QualityReviewError(f"baseline state resolver {label} is not an object")
    return path, payload


def validate_rule(rule: Mapping[str, object], path: str = "<rule>") -> tuple[str, ...]:
    failures: list[str] = []
    required = {
        "rule_id", "title", "source", "owner", "rationale", "status", "scope",
        "review_tiers", "action", "precedence", "created_date", "modified_date",
        "revision", "provenance", "conflict_behavior", "lifecycle_state",
    }
    missing = sorted(required - set(rule))
    if missing:
        failures.append(f"{path}: missing fields: {', '.join(missing)}")
        return tuple(failures)
    unknown = sorted(set(rule) - required - {"validity"})
    if unknown: failures.append(f"{path}: unknown fields: {', '.join(unknown)}")
    if not isinstance(rule.get("rule_id"),str) or not rule["rule_id"].strip(): failures.append(f"{path}: rule_id is empty or not a string")
    for field in ("title", "source", "owner", "rationale", "provenance"):
        if not isinstance(rule.get(field), str) or not str(rule[field]).strip(): failures.append(f"{path}: {field} is empty")
    parsed_dates: dict[str, date] = {}
    for field in ("created_date", "modified_date"):
        try: parsed_dates[field] = date.fromisoformat(rule[field]) if isinstance(rule.get(field), str) else date.min
        except ValueError: parsed_dates[field] = date.min
        if parsed_dates[field] == date.min: failures.append(f"{path}: {field} is not a real ISO date")
    if all(value != date.min for value in parsed_dates.values()) and parsed_dates["modified_date"] < parsed_dates["created_date"]: failures.append(f"{path}: modified_date precedes created_date")
    if rule["lifecycle_state"] not in LIFECYCLES: failures.append(f"{path}: invalid lifecycle_state")
    if rule["status"] not in {"enabled", "disabled"}: failures.append(f"{path}: invalid status")
    tiers = rule["review_tiers"]
    if not isinstance(tiers, list) or not tiers or len(tiers) != len(set(tiers)) or any(tier not in TIERS for tier in tiers):
        failures.append(f"{path}: review_tiers must contain light, standard, or deep")
    scope = rule["scope"]
    scope_keys = {"repositories", "paths", "artifact_types", "work_item_types", "review_categories", "triggers"}
    if not isinstance(scope, Mapping) or any(key not in scope_keys for key in scope):
        failures.append(f"{path}: scope is not interpretable")
    elif any(not isinstance(value, list) or len(value) != len(set(value)) or any(not isinstance(item, str) or not item for item in value)
             for value in scope.values()):
        failures.append(f"{path}: scope values must be string arrays")
    action = rule["action"]
    action_fields = {"type", "target_rule_id", "severity", "replacement"}
    if not isinstance(action, Mapping) or action.get("type") not in ACTIONS or set(action) - action_fields:
        failures.append(f"{path}: invalid action")
    elif action["type"] in {"ignore", "suppress", "replace", "adjust_severity", "accept_known_tradeoff", "defer_until_trigger", "exempt"} and (not isinstance(action.get("target_rule_id"), str) or not action["target_rule_id"].strip()): failures.append(f"{path}: action requires target_rule_id")
    elif action["type"] == "replace" and (not isinstance(action.get("replacement"), str) or not action["replacement"].strip()): failures.append(f"{path}: replace action requires replacement")
    elif action["type"] == "adjust_severity" and action.get("severity") not in {"critical","high","medium","low","informational"}: failures.append(f"{path}: adjust_severity action requires severity")
    else:
        expected={"type"}
        if action["type"] in {"ignore","suppress","replace","adjust_severity","accept_known_tradeoff","defer_until_trigger","exempt"}: expected.add("target_rule_id")
        if action["type"]=="replace": expected.add("replacement")
        if action["type"]=="adjust_severity": expected.add("severity")
        if set(action)!=expected: failures.append(f"{path}: action contains fields inapplicable to its type")
    if rule["precedence"] not in PRECEDENCE: failures.append(f"{path}: invalid precedence")
    if not isinstance(rule["revision"], int) or isinstance(rule["revision"],bool) or rule["revision"] < 1: failures.append(f"{path}: revision must be positive")
    if rule["conflict_behavior"] not in {"surface", "fail_closed"}: failures.append(f"{path}: invalid conflict_behavior")
    validity = rule.get("validity", {})
    if validity:
        validity_dates = {}
        if not isinstance(validity, Mapping) or any(key not in {"from", "until"} for key in validity): failures.append(f"{path}: validity is invalid")
        else:
            for key, value in validity.items():
                try: validity_dates[key] = date.fromisoformat(value) if isinstance(value, str) else date.min
                except ValueError: validity_dates[key] = date.min
            if any(value == date.min for value in validity_dates.values()) or ("from" in validity_dates and "until" in validity_dates and validity_dates["from"] > validity_dates["until"]): failures.append(f"{path}: validity is invalid")
    return tuple(failures)


def load_rules(path: str | Path) -> list[dict[str, object]]:
    source = Path(path)
    payload = _json(source)
    if not isinstance(payload, Mapping) or set(payload) - {"$comment", "schema", "rules"} or payload.get("schema") != "dual-hat-quality-rules/1.0": raise QualityReviewError(f"{source}: top-level quality-rule source contract is invalid")
    rows = payload.get("rules")
    if not isinstance(rows, list):
        raise QualityReviewError(f"{source}: top-level rules array is required")
    failures = [failure for row in rows if isinstance(row, Mapping) for failure in validate_rule(row, str(source))]
    if any(not isinstance(row, Mapping) for row in rows): failures.append(f"{source}: every rule must be an object")
    identities = [(str(row.get('rule_id')), row.get("revision")) for row in rows if isinstance(row, Mapping)]
    if len(set(identities)) != len(rows): failures.append(f"{source}: duplicate rule_id and revision")
    if failures: raise QualityReviewError("; ".join(failures))
    return [dict(row) for row in rows]


def discover_rule_files(repository: str | Path, source_config: str | Path,
                        prior_inventory: Mapping[str, object] | None = None) -> dict[str, object]:
    root = Path(repository).resolve()
    config_path = Path(source_config)
    if not config_path.is_absolute(): config_path = root / config_path
    config = _json(config_path)
    sources = config.get("sources") if isinstance(config, Mapping) else None
    if not isinstance(sources, list): raise QualityReviewError(f"{config_path}: sources array is required")
    files: list[dict[str, object]] = []
    rules: list[dict[str, object]] = []
    errors: list[str] = []
    for source in sources:
        if not isinstance(source, Mapping) or not isinstance(source.get("path"), str):
            errors.append(f"{config_path}: invalid source entry"); continue
        try:
            source_root = contained(root, str(source["path"]), must_exist=False)
        except ContainmentError:
            errors.append(f"{config_path}: rule source escapes repository or crosses a link: {source['path']}"); continue
        required = bool(source.get("required", False))
        if not source_root.exists():
            if required: errors.append(f"{source_root}: required rule source is absent")
            continue
        linked = [path for path in source_root.rglob("*") if is_reparse(path)] if source_root.is_dir() else []
        if linked:
            errors.extend(f"{path}: linked/reparse rule source entry is prohibited" for path in linked)
            continue
        candidates = sorted(source_root.rglob("*.json")) if source_root.is_dir() else [source_root]
        for path in candidates:
            if path.name.startswith("."): continue
            try: path = contained(root, path.relative_to(root), must_exist=True, kind="file")
            except (ContainmentError, ValueError):
                errors.append(f"{path}: rule file escapes repository or crosses a link"); continue
            raw = path.read_bytes()
            record = {
                "path": path.relative_to(root).as_posix(), "bytes": len(raw),
                "mtime_ns": path.stat().st_mtime_ns, "sha256": _digest_bytes(raw),
                "source_id": source.get("source_id", "user"),
            }
            files.append(record)
            try:
                for rule in load_rules(path):
                    rule["_source_path"] = record["path"]
                    rules.append(rule)
            except QualityReviewError as exc: errors.append(str(exc))
    old = {row["path"]: row for row in (prior_inventory or {}).get("files", []) if isinstance(row, Mapping)}
    new = {row["path"]: row for row in files}
    added = sorted(set(new) - set(old)); removed = sorted(set(old) - set(new))
    modified = sorted(path for path in set(old) & set(new)
                      if old[path].get("sha256") != new[path]["sha256"] or old[path].get("mtime_ns") != new[path]["mtime_ns"])
    old_by_hash = {row.get("sha256"): path for path, row in old.items() if row.get("sha256")}
    renames = [{"from": old_by_hash[new[path]["sha256"]], "to": path} for path in added
               if new[path]["sha256"] in old_by_hash and old_by_hash[new[path]["sha256"]] in removed]
    inventory = {"schema": "dual-hat-quality-rule-inventory/1.0", "files": files,
                 "changes": {"added": added, "removed": removed, "modified": modified, "renamed": renames},
                 "errors": errors}
    inventory["source_inventory_hash"] = _canonical_hash({"files": [{"path": row["path"], "sha256": row["sha256"], "mtime_ns": row["mtime_ns"]} for row in files]})
    selected_rules: list[dict[str, object]] = []
    by_id: dict[str, list[dict[str, object]]] = {}
    for row in rules: by_id.setdefault(str(row["rule_id"]), []).append(row)
    for rule_id, revisions in by_id.items():
        numbers = [int(row["revision"]) for row in revisions]
        if len(numbers) != len(set(numbers)):
            errors.append(f"duplicate rule revision across sources: {rule_id}")
            continue
        selected_rules.append(max(revisions, key=lambda row: int(row["revision"])))
    normalized_rules = [
        {key: value for key, value in row.items() if key != "_source_path"}
        for row in sorted(selected_rules, key=lambda value: (str(value.get("rule_id")), int(value.get("revision", 0))))
    ]
    inventory["rule_set_hash"] = _canonical_hash(normalized_rules)
    inventory["normalized_rules"] = normalized_rules
    inventory["rules"] = selected_rules
    return inventory


def _applies(rule: Mapping[str, object], tier: str, context: Mapping[str, str]) -> bool:
    if rule.get("status") != "enabled" or rule.get("lifecycle_state") != "active" or tier not in rule.get("review_tiers", []):
        return False
    scope = rule.get("scope", {})
    validity = rule.get("validity", {})
    current_date = context.get("date", "")
    if isinstance(validity, Mapping):
        if validity.get("from") and (not current_date or current_date < str(validity["from"])): return False
        if validity.get("until") and (not current_date or current_date > str(validity["until"])): return False
    fields = (("repositories", "repository"), ("paths", "path"), ("artifact_types", "artifact_type"),
              ("work_item_types", "work_item_type"), ("review_categories", "review_category"),
              ("triggers", "trigger"))
    for scope_key, context_key in fields:
        patterns = scope.get(scope_key, []) if isinstance(scope, Mapping) else []
        context_value = context.get(context_key, "")
        if patterns and context_value != "*" and not any(fnmatch.fnmatch(context_value, pattern) for pattern in patterns): return False
    return True


def _specificity(rule: Mapping[str, object], tier: str, context: Mapping[str, str]) -> tuple[int, int, int, int, int, int]:
    scope = rule.get("scope", {})
    patterns_by_dimension = [[str(item) for item in values] for values in scope.values()
                             if values and not any(re.fullmatch(r"[*?]+",str(item)) for item in values)] if isinstance(scope, Mapping) else []
    patterns_by_dimension = [values for values in patterns_by_dimension if values]
    patterns = [item for values in patterns_by_dimension for item in values]
    all_exact = int(bool(patterns) and all(not any(token in item for token in "*?[") for item in patterns))
    alternative_penalty = sum(max(0, len(values)-1) for values in patterns_by_dimension)
    literal_width = sum(max((len(re.sub(r"[?*\[\]]", "", item)) for item in values), default=0) for values in patterns_by_dimension)
    wildcard_count = sum(min((sum(item.count(token) for token in "*?[") for item in values), default=0) for values in patterns_by_dimension)
    explicit_tier = int(rule.get("review_tiers") == [tier])
    return -alternative_penalty, all_exact, literal_width, -wildcard_count, len(patterns_by_dimension), explicit_tier


def effective_review_plan(architecture_rules: Sequence[Mapping[str, object]], user_rules: Sequence[Mapping[str, object]],
                          tier: str, context: Mapping[str, str], rule_set_hash: str,
                          discovery_errors: Sequence[str] = ()) -> dict[str, object]:
    if tier not in TIERS: raise QualityReviewError(f"unknown review tier: {tier}")
    all_rules = [dict(row) for row in (*architecture_rules, *user_rules)]
    failures = [*discovery_errors, *(failure for row in all_rules for failure in validate_rule(
        {key:value for key,value in row.items() if key != "_source_path"},
        str(row.get("_source_path", row.get("rule_id"))))) ]
    applicable = [row for row in all_rules if _applies(row, tier, context)]
    architecture = {str(row["rule_id"]): row for row in applicable if row.get("precedence") in {"architecture_default", "repository_architecture", "non_waivable"}}
    user = sorted((row for row in applicable if row.get("precedence") == "user"),
                  key=lambda row: (_specificity(row, tier, context), int(row["revision"])), reverse=True)
    conflicts: list[dict[str, object]] = []
    grouped: dict[tuple[str, tuple[int, int, int, int, int, int]], list[dict[str, object]]] = {}
    for row in user:
        target = str(row.get("action", {}).get("target_rule_id", row["rule_id"]))
        grouped.setdefault((target, _specificity(row, tier, context)), []).append(row)
    for (target, specificity), rows in grouped.items():
        signatures = {_canonical_hash(row.get("action")) for row in rows}
        if len(rows) > 1 and len(signatures) > 1:
            conflicts.append({"type": "equally_specific_user_rules", "target_rule_id": target,
                              "specificity": specificity, "rule_ids": sorted(str(row["rule_id"]) for row in rows)})
    suppressed: list[dict[str, object]] = []; replaced: list[dict[str, object]] = []
    adjusted: list[dict[str, object]] = []; applied_user: list[dict[str, object]] = []
    handled_targets: set[str] = set()
    for row in user:
        action = row["action"]; target = str(action.get("target_rule_id", row["rule_id"]))
        if target in handled_targets: continue
        handled_targets.add(target)
        target_rule = architecture.get(target)
        action_type = action["type"]
        if target_rule and target_rule.get("precedence") == "non_waivable" and action_type in {"ignore", "suppress", "replace", "exempt", "accept_known_tradeoff", "defer_until_trigger"}:
            conflicts.append({"type": "non_waivable_conflict", "target_rule_id": target,
                              "user_rule_id": row["rule_id"], "governing_requirement": target_rule.get("title")})
            continue
        applied_user.append(row)
        if target_rule and action_type in {"ignore", "suppress", "exempt"}:
            suppressed.append({"underlying_rule_id": target, "user_rule_id": row["rule_id"], "tier": tier,
                               "rationale": row["rationale"]})
        elif target_rule and action_type == "replace":
            replaced.append({"underlying_rule_id": target, "user_rule_id": row["rule_id"], "tier": tier,
                             "replacement": action.get("replacement")})
        elif target_rule and action_type == "adjust_severity":
            adjusted.append({"underlying_rule_id": target, "user_rule_id": row["rule_id"],
                             "severity": action.get("severity")})
    inactive_ids = {row["underlying_rule_id"] for row in (*suppressed, *replaced)}
    active_architecture = [row for key, row in architecture.items() if key not in inactive_ids]
    plan: dict[str, object] = {
        "schema": "dual-hat-effective-review-plan/1.0", "tier": tier, "context": dict(context),
        "rule_set_revision": rule_set_hash[:12], "rule_set_hash": rule_set_hash,
        "active_architecture_rules": active_architecture, "active_user_rules": applied_user,
        "suppressed_rules": suppressed, "replaced_rules": replaced, "severity_adjustments": adjusted,
        "non_waivable_controls": [row for row in architecture.values() if row.get("precedence") == "non_waivable"],
        "conflicts": conflicts, "validation_failures": failures,
        "review_authorized": not failures and not conflicts,
    }
    plan["effective_plan_hash"] = _canonical_hash(plan)
    return plan


def governed_state_binding_hash(binding: Mapping[str, object]) -> str:
    return _canonical_hash({key: value for key, value in binding.items() if key != "binding_hash"})


def _reproducible_inventory_projection(inventory: Mapping[str, object], *, repository: Path | None = None) -> dict[str, object]:
    """Return only checkout-stable rule evidence used by governed-state resolution.

    Discovery timestamps and the change summary remain useful operational metadata,
    but neither is a content identity and both can legitimately differ after a clean
    checkout.  Baseline authority is therefore bound to paths, bytes, content hashes,
    source identities, normalized rules, and the content-derived rule-set hash.
    """

    files = inventory.get("files", [])
    stable_files: list[dict[str, object]] = []
    if isinstance(files, list):
        for row in files:
            if not isinstance(row, Mapping): continue
            stable = {key: row.get(key) for key in ("path", "bytes", "sha256", "source_id")}
            if repository is not None:
                path = row.get("path")
                if not isinstance(path, str) or not path:
                    raise QualityReviewError("quality-rule inventory contains an invalid committed path")
                committed = _git_bytes(repository, "show", f"HEAD:{path}")
                stable.update({"bytes": len(committed), "sha256": _digest_bytes(committed)})
            stable_files.append(stable)
    return {
        "schema": inventory.get("schema"),
        "files": stable_files,
        "errors": inventory.get("errors"),
        "rule_set_hash": inventory.get("rule_set_hash"),
        "normalized_rules": inventory.get("normalized_rules"),
        "rules": inventory.get("rules"),
    }


def derive_governed_baseline_state(repository: str | Path, resolver_config: str | Path) -> dict[str, object]:
    """Derive a baseline binding from primary governed state, never caller assertions."""

    root = Path(repository).resolve(strict=True)
    actual_git_root = Path(_git(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if actual_git_root != root: raise QualityReviewError("baseline repository root is not the exact governed Git root")
    dirty = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if dirty: raise QualityReviewError("dirty repository bytes cannot be represented as committed baseline state")
    try: config_path = contained(root, Path(resolver_config), must_exist=True, kind="file")
    except (ContainmentError, ValueError) as exc: raise QualityReviewError("baseline resolver configuration escapes the governed root") from exc
    config = _json(config_path)
    required = {"schema", "repository_identity", "profile", "dual_hat_version", "rule_sources", "rule_inventory", "architecture_rules", "effective_plan", "sealed_work_order", "current_handover"}
    if not isinstance(config, Mapping) or set(config) - {"$comment"} != required or config.get("schema") != "dual-hat-baseline-state-sources/1.0":
        raise QualityReviewError("baseline resolver configuration is incomplete or ambiguous")
    profile_path, profile = _contained_json(root, config["profile"], "active profile")
    version_path, version = _contained_json(root, config["dual_hat_version"], "Dual Hat version")
    inventory_path, inventory_projection = _contained_json(root, config["rule_inventory"], "rule inventory")
    plan_path, plan_projection = _contained_json(root, config["effective_plan"], "effective plan")
    seal_path, seal = _contained_json(root, config["sealed_work_order"], "sealed work order")
    handover_path, handover = _contained_json(root, config["current_handover"], "current handover")
    rule_sources = str(config["rule_sources"])
    architecture_rules_path = contained(root, str(config["architecture_rules"]), must_exist=True, kind="file")
    inventory = discover_rule_files(root, rule_sources)
    if inventory.get("errors"): raise QualityReviewError("active quality-rule discovery failed")
    if _reproducible_inventory_projection(inventory, repository=root) != _reproducible_inventory_projection(inventory_projection):
        raise QualityReviewError("quality-rule inventory content projection is stale or irreproducible")
    context = plan_projection.get("context")
    tier = plan_projection.get("tier")
    if not isinstance(context, Mapping) or not all(isinstance(key, str) and isinstance(value, str) for key, value in context.items()):
        raise QualityReviewError("effective review plan context is invalid")
    architecture = load_rules(architecture_rules_path)
    plan = effective_review_plan(architecture, inventory["rules"], str(tier), context, str(inventory["rule_set_hash"]), inventory["errors"])
    if plan != plan_projection or not plan.get("review_authorized"):
        raise QualityReviewError("effective review plan is stale, mismatched, or unauthorized")
    from work_item_governance import validate_sealed
    seal_failures = validate_sealed(seal)
    if seal_failures: raise QualityReviewError("sealed work item is invalid: " + "; ".join(seal_failures))
    active = handover.get("active_work_item")
    if not isinstance(active, Mapping): raise QualityReviewError("current handover lacks an active work item")
    expected_work_item = {"work_item_id":seal.get("work_item_id"), "work_order_revision":seal.get("current_revision"), "work_order_hash":seal.get("work_order_hash")}
    if any(active.get(key) != value for key, value in expected_work_item.items()):
        raise QualityReviewError("current lifecycle projection contradicts the sealed work item")
    repository_commit = _git(root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", repository_commit): raise QualityReviewError("repository HEAD is not a commit identity")
    dual_hat_version = version.get("version")
    if not isinstance(dual_hat_version, str) or not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", dual_hat_version):
        raise QualityReviewError("canonical Dual Hat version is invalid")
    from profile_conformance import validate_profile
    profile_failures = validate_profile(profile, dual_hat_version)
    if profile_failures: raise QualityReviewError("active platform profile is invalid: " + "; ".join(profile_failures))
    profile_id, profile_version = profile.get("profile_id"), profile.get("profile_version")
    if not isinstance(profile_id, str) or not profile_id or not isinstance(profile_version, str) or not profile_version:
        raise QualityReviewError("active platform profile identity is invalid")
    binding = {
        "schema": "dual-hat-governed-state-binding/1.0",
        "repository_identity": config["repository_identity"],
        "repository_commit": repository_commit,
        "dual_hat_commit": repository_commit,
        "dual_hat_version": dual_hat_version,
        "active_platform_profile": {"profile_id": profile_id, "profile_version": profile_version,
                                    "profile_sha256": _digest_bytes(profile_path.read_bytes())},
        "rule_set_hash": inventory["rule_set_hash"], "effective_plan_hash": plan["effective_plan_hash"],
        "work_item_id": seal["work_item_id"], "work_order_revision": seal["current_revision"],
        "sealed_work_order_hash": seal["work_order_hash"], "lifecycle_state": active.get("lifecycle_state"),
        "architecture_disposition_state": ("accepted" if active.get("lifecycle_state") in {"accepted", "accepted_with_follow_up"}
                                             else "pending_architecture_acceptance"),
        "source_paths": {"resolver_config": config_path.relative_to(root).as_posix(), "profile": profile_path.relative_to(root).as_posix(),
                         "version": version_path.relative_to(root).as_posix(), "rule_inventory": inventory_path.relative_to(root).as_posix(),
                         "effective_plan": plan_path.relative_to(root).as_posix(), "sealed_work_order": seal_path.relative_to(root).as_posix(),
                         "current_handover": handover_path.relative_to(root).as_posix()},
    }
    binding["binding_hash"] = governed_state_binding_hash(binding)
    return binding


def classify_change(paths: Iterable[str], behavior_patterns: Sequence[str], documentation_patterns: Sequence[str]) -> str:
    rows = tuple(paths)
    if not rows: return "documentation_or_inert_data_only"
    behavior = [path for path in rows if any(fnmatch.fnmatch(path, pattern) for pattern in behavior_patterns)]
    documentation = [path for path in rows if any(fnmatch.fnmatch(path, pattern) for pattern in documentation_patterns)]
    if len(behavior) == len(rows): return "code_or_behavior_affecting"
    if len(documentation) == len(rows): return "documentation_or_inert_data_only"
    if behavior and len(behavior) + len(documentation) == len(rows): return "mixed"
    return "uncertain"


def select_review_tier(risk_signals: Iterable[str], internal_release_only: bool = False) -> str:
    signals = set(risk_signals)
    deep = {"authentication", "credentials", "authorization", "untrusted_input", "private_data", "file_deletion",
            "destructive_migration", "cross_repository_mutation", "concurrency", "sandbox", "plugin_execution",
            "external_dependency_loading", "security_enforcement", "privacy_sensitive", "external_rollout"}
    if signals & deep: return "deep"
    if "publishing_or_release" in signals and internal_release_only: return "standard"
    return "standard" if signals else "light"


def review_acceptance_blockers(findings: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    blockers: list[str] = []
    for row in findings:
        severity = str(row.get("severity", "")).casefold(); disposition = str(row.get("disposition", ""))
        if severity in BLOCKING_SEVERITIES and disposition not in {"remediated", "false_positive", "validly_suppressed"}:
            blockers.append(str(row.get("finding_id", "unknown finding")))
        if severity == "medium" and disposition not in {"remediated", "accepted_debt", "validly_suppressed", "false_positive"}:
            blockers.append(str(row.get("finding_id", "unknown finding")))
    return tuple(blockers)


def baseline_hash(payload: Mapping[str, object]) -> str:
    material = {key: value for key, value in payload.items() if key != "baseline_hash"}
    return _canonical_hash(material)


def _baseline_binding(payload: Mapping[str, object]) -> dict[str, object]:
    return {key: payload.get(key) for key in ("repository_commit", "dual_hat_commit", "dual_hat_version", "rule_set_hash", "effective_plan_hash", "active_platform_profile")}


def governed_state_binding_failures(binding: object) -> tuple[str, ...]:
    required = {"schema", "repository_identity", "repository_commit", "dual_hat_commit", "dual_hat_version", "active_platform_profile", "rule_set_hash", "effective_plan_hash", "work_item_id", "work_order_revision", "sealed_work_order_hash", "lifecycle_state", "architecture_disposition_state", "source_paths", "binding_hash"}
    failures: list[str] = []
    if not isinstance(binding, Mapping) or set(binding) != required: return ("governed-state binding is incomplete or contains unknown fields",)
    if binding.get("schema") != "dual-hat-governed-state-binding/1.0": failures.append("governed-state binding schema is invalid")
    for field in ("repository_commit", "dual_hat_commit"):
        if not re.fullmatch(r"[A-Fa-f0-9]{40}", str(binding.get(field, ""))): failures.append(f"governed-state {field} is invalid")
    for field in ("rule_set_hash", "effective_plan_hash", "sealed_work_order_hash", "binding_hash"):
        if not re.fullmatch(r"[A-F0-9]{64}", str(binding.get(field, ""))): failures.append(f"governed-state {field} is invalid")
    if not isinstance(binding.get("source_paths"), Mapping) or not binding["source_paths"]: failures.append("governed-state source paths are absent")
    if binding.get("binding_hash") != governed_state_binding_hash(binding): failures.append("governed-state binding hash mismatch")
    return tuple(failures)


def validate_baseline(payload: Mapping[str, object]) -> tuple[str, ...]:
    required = {"baseline_id", "repository_commit", "date", "review_scope", "exclusions", "selected_review_tier",
                "active_platform_profile", "user_rule_sources", "rule_set_hash", "effective_plan_hash", "review_methods",
                "tool_versions", "principal_metrics", "risk_areas", "accepted_exceptions", "user_approved_tradeoffs",
                "unresolved_findings", "debt_references", "validation_evidence", "baseline_hash", "architecture_disposition_state",
                "dual_hat_commit", "dual_hat_version", "suppressed_architecture_rules", "replaced_rules",
                "severity_adjustments", "rule_conflicts", "non_waivable_controls", "preliminary_findings_mapping",
                "final_findings", "remediated_findings", "residual_risk", "governed_state_binding"}
    failures: list[str] = []
    if required - set(payload): failures.append("baseline lacks required fields")
    if set(payload) - required - {"$comment"}: failures.append("baseline contains unknown fields")
    if payload.get("selected_review_tier") != "deep": failures.append("initial repository baseline must use Deep review")
    if payload.get("baseline_hash") != baseline_hash(payload): failures.append("baseline hash mismatch")
    for field in ("repository_commit", "dual_hat_commit"):
        if not re.fullmatch(r"[A-Fa-f0-9]{40}", str(payload.get(field, ""))): failures.append(f"baseline {field} is not a commit identity")
    try: date.fromisoformat(str(payload.get("date", "")))
    except ValueError: failures.append("baseline date is not a real ISO date")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(payload.get("dual_hat_version", ""))): failures.append("baseline Dual Hat version is invalid")
    for field in ("rule_set_hash", "effective_plan_hash", "baseline_hash"):
        if not re.fullmatch(r"[A-F0-9]{64}", str(payload.get(field, ""))): failures.append(f"baseline {field} is not a SHA-256 identity")
    profile = payload.get("active_platform_profile")
    if (not isinstance(profile, Mapping) or set(profile) != {"profile_id", "profile_version", "profile_sha256"}
            or not all(isinstance(profile.get(field), str) and profile[field] for field in ("profile_id", "profile_version"))
            or not re.fullmatch(r"[A-F0-9]{64}", str(profile.get("profile_sha256", "")))): failures.append("baseline active platform profile binding is invalid")
    if not isinstance(payload.get("tool_versions"), Mapping) or any(not isinstance(key, str) or not isinstance(value, str) or not value for key,value in payload.get("tool_versions",{}).items()): failures.append("baseline tool versions are invalid")
    metrics = payload.get("principal_metrics")
    if not isinstance(metrics, Mapping) or any(not isinstance(row, Mapping) or set(row) != {"value","desired_direction"} or not isinstance(row.get("value"),(int,float)) or isinstance(row.get("value"),bool) or row.get("desired_direction") not in {"increase","decrease","stable"} for row in metrics.values()): failures.append("baseline principal metrics are invalid")
    array_fields = {"review_scope", "exclusions", "user_rule_sources", "suppressed_architecture_rules", "replaced_rules", "severity_adjustments", "rule_conflicts", "non_waivable_controls", "review_methods", "risk_areas", "accepted_exceptions", "user_approved_tradeoffs", "unresolved_findings", "debt_references", "validation_evidence", "preliminary_findings_mapping", "final_findings", "remediated_findings", "residual_risk"}
    for field in array_fields:
        if not isinstance(payload.get(field), list): failures.append(f"baseline {field} must be an array")
    def findings(field: str) -> list[Mapping[str, object]]:
        rows = payload.get(field)
        if not isinstance(rows, list): return []
        result = []
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping) or not str(row.get("finding_id", "")).strip() or str(row.get("severity", "")).casefold() not in {"critical", "high", "medium", "low", "informational"} or not str(row.get("disposition", "")).strip():
                failures.append(f"baseline {field} item {index} is not a typed finding")
            else: result.append(row)
        if len({str(row.get("finding_id")) for row in result}) != len(result): failures.append(f"baseline {field} contains duplicate finding IDs")
        return result
    unresolved, final, remediated = findings("unresolved_findings"), findings("final_findings"), findings("remediated_findings")
    blockers = review_acceptance_blockers([*unresolved, *final])
    if blockers: failures.append("baseline contains unresolved blocking findings: " + ", ".join(dict.fromkeys(blockers)))
    final_by_id = {str(row["finding_id"]): row for row in final}
    for row in unresolved:
        if final and str(row["finding_id"]) not in final_by_id: failures.append("unresolved finding is absent from final findings")
    unresolved_ids = {str(row["finding_id"]) for row in unresolved}; remediated_ids = {str(row["finding_id"]) for row in remediated}
    if unresolved_ids & remediated_ids: failures.append("a finding cannot be both unresolved and remediated")
    for row in remediated:
        corresponding = final_by_id.get(str(row["finding_id"]))
        if not corresponding or str(corresponding.get("disposition")) != "remediated": failures.append("remediated finding is absent or contradictory in final findings")
    if isinstance(payload.get("rule_conflicts"), list) and payload.get("rule_conflicts"): failures.append("baseline contains unresolved rule conflicts")
    for field, label in (("non_waivable_controls", "non-waivable controls"), ("review_methods", "review methods"), ("validation_evidence", "validation evidence")):
        rows = payload.get(field)
        if not isinstance(rows, list) or not rows or any(not isinstance(row, str) or not row.strip() for row in rows): failures.append(f"baseline lacks typed {label}")
    if payload.get("architecture_disposition_state") not in {"pending_architecture_acceptance", "accepted", "superseded"}:
        failures.append("baseline disposition state is invalid")
    if payload.get("architecture_disposition_state") == "accepted" and (unresolved or blockers or payload.get("rule_conflicts")): failures.append("accepted baseline contains unresolved review state")
    binding = payload.get("governed_state_binding")
    failures.extend(governed_state_binding_failures(binding))
    if isinstance(binding, Mapping):
        for key, value in _baseline_binding(payload).items():
            if binding.get(key) != value: failures.append(f"baseline {key} contradicts its immutable governed-state binding")
        if binding.get("architecture_disposition_state") != payload.get("architecture_disposition_state"):
            failures.append("baseline disposition contradicts its immutable governed-state binding")
    return tuple(failures)


def validate_baseline_against_state(payload: Mapping[str, object], actual_state: Mapping[str, object], *,
                                    caller_assertion: Mapping[str, object] | None = None,
                                    require_acceptance: bool = False) -> tuple[str, ...]:
    failures = list(validate_baseline(payload))
    failures.extend(governed_state_binding_failures(actual_state))
    if not failures:
        baseline_binding = payload.get("governed_state_binding")
        if baseline_binding != actual_state: failures.append("baseline does not match internally derived governed repository state")
        if _baseline_binding(payload) != {key: actual_state.get(key) for key in _baseline_binding(payload)}:
            failures.append("baseline fields do not match internally derived governed repository state")
    if caller_assertion is not None and dict(caller_assertion) != dict(actual_state):
        failures.append("caller assertion disagrees with internally derived governed repository state")
    if require_acceptance and payload.get("architecture_disposition_state") != "accepted":
        failures.append("baseline is not Architecture-accepted")
    return tuple(dict.fromkeys(failures))


def validate_baseline_from_repository(payload: Mapping[str, object], repository: str | Path, resolver_config: str | Path, *,
                                      caller_assertion: Mapping[str, object] | None = None,
                                      require_acceptance: bool = False) -> tuple[str, ...]:
    try: actual = derive_governed_baseline_state(repository, resolver_config)
    except QualityReviewError as exc: return (f"actual governed-state derivation failed: {exc}",)
    return validate_baseline_against_state(payload, actual, caller_assertion=caller_assertion, require_acceptance=require_acceptance)


def compare_baselines(accepted: Mapping[str, object], candidate: Mapping[str, object], *,
                      repository: str | Path, resolver_config: str | Path,
                      caller_assertion: Mapping[str, object] | None = None) -> dict[str, object]:
    """Compare immutable historical evidence with a candidate bound to current primary state."""

    historical_failures = list(validate_baseline(accepted))
    if accepted.get("architecture_disposition_state") != "accepted": historical_failures.append("historical baseline is not Architecture-accepted")
    try:
        candidate_state = derive_governed_baseline_state(repository, resolver_config)
        candidate_state_failures: list[str] = []
    except QualityReviewError as exc:
        candidate_state = {}
        candidate_state_failures = [f"actual governed-state derivation failed: {exc}"]
    candidate_failures = list(validate_baseline_against_state(candidate, candidate_state, caller_assertion=caller_assertion)) if candidate_state else []
    regressions: list[dict[str, object]] = []
    old_metrics = accepted.get("principal_metrics", {})
    new_metrics = candidate.get("principal_metrics", {})
    if isinstance(old_metrics, Mapping) and isinstance(new_metrics, Mapping):
        for name, old in old_metrics.items():
            new = new_metrics.get(name)
            if not isinstance(old, Mapping) or not isinstance(new, Mapping):
                continue
            old_value, new_value = old.get("value"), new.get("value")
            direction = old.get("desired_direction")
            regressed = (
                isinstance(old_value, (int, float)) and isinstance(new_value, (int, float))
                and ((direction == "increase" and new_value < old_value)
                     or (direction == "decrease" and new_value > old_value)
                     or (direction == "stable" and new_value != old_value))
            )
            if regressed:
                regressions.append({"metric": name, "accepted": old_value, "candidate": new_value, "desired_direction": direction})
    accepted_debt = set(map(str, accepted.get("debt_references", ())))
    candidate_debt = set(map(str, candidate.get("debt_references", ())))
    new_debt = sorted(candidate_debt - accepted_debt)
    unresolved = candidate.get("unresolved_findings", ())
    new_blockers = [str(row.get("finding_id", "unknown")) for row in unresolved
                    if isinstance(row, Mapping) and str(row.get("severity", "")).casefold() in BLOCKING_SEVERITIES]
    rule_policy_change = (accepted.get("rule_set_hash") != candidate.get("rule_set_hash")
                          or accepted.get("effective_plan_hash") != candidate.get("effective_plan_hash"))
    repository_state_mismatch = bool(candidate_state and candidate.get("repository_commit") != candidate_state.get("repository_commit"))
    result = {
        "schema": "dual-hat-baseline-comparison/1.0", "accepted_baseline_id": accepted.get("baseline_id"),
        "candidate_baseline_id": candidate.get("baseline_id"), "metric_regressions": regressions,
        "new_debt": new_debt, "new_blocking_findings": new_blockers,
        "invalid_historical_baseline_evidence": historical_failures,
        "invalid_candidate_state": [*candidate_state_failures, *candidate_failures],
        "rule_policy_change": rule_policy_change, "repository_state_mismatch": repository_state_mismatch,
    }
    result["validation_failures"] = [*historical_failures, *candidate_state_failures, *candidate_failures]
    result["non_regression_passed"] = not any((regressions, new_debt, new_blockers, result["validation_failures"], rule_policy_change, repository_state_mismatch))
    result["comparison_hash"] = _canonical_hash(result)
    return result


def write_generated_json(repository: str | Path, relative_output: str | Path, payload: object) -> Path:
    """Atomically persist a generated review artifact inside the selected repository."""

    root = Path(repository).resolve()
    output = (root / relative_output).resolve()
    if not output.is_relative_to(root):
        raise QualityReviewError("generated review output escapes repository")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temporary, output)
    finally:
        if temporary.exists(): temporary.unlink()
    return output


def _main() -> int:
    parser = argparse.ArgumentParser(description="Validate and resolve Dual Hat quality rules.")
    sub = parser.add_subparsers(dest="command", required=True)
    reload_cmd = sub.add_parser("reload", help="discover and validate configured rule files")
    reload_cmd.add_argument("--repository", type=Path, required=True); reload_cmd.add_argument("--sources", required=True)
    reload_cmd.add_argument("--output", type=Path)
    plan_cmd = sub.add_parser("plan", help="generate an effective review plan")
    plan_cmd.add_argument("--repository", type=Path, required=True); plan_cmd.add_argument("--sources", required=True)
    plan_cmd.add_argument("--architecture-rules", required=True); plan_cmd.add_argument("--tier", choices=TIERS, required=True)
    plan_cmd.add_argument("--context", required=True, help="JSON object")
    plan_cmd.add_argument("--output", type=Path)
    baseline_cmd = sub.add_parser("validate-baseline"); baseline_cmd.add_argument("path", type=Path)
    baseline_cmd.add_argument("--repository", type=Path); baseline_cmd.add_argument("--resolver-config", type=Path)
    args = parser.parse_args()
    if args.command == "validate-baseline":
        baseline = _json(args.path)
        if not isinstance(baseline, Mapping): failures = ("baseline is not an object",)
        elif baseline.get("architecture_disposition_state") == "accepted" or args.repository or args.resolver_config:
            if not args.repository or not args.resolver_config: failures = ("accepted baseline validation requires governed repository and resolver configuration",)
            else: failures = validate_baseline_from_repository(baseline, args.repository, args.resolver_config,
                                                                require_acceptance=baseline.get("architecture_disposition_state") == "accepted")
        else: failures = validate_baseline(baseline)
        print(json.dumps({"valid": not failures, "failures": failures}, indent=2)); return int(bool(failures))
    inventory = discover_rule_files(args.repository, args.sources)
    if args.command == "reload":
        if args.output: write_generated_json(args.repository, args.output, inventory)
        else: print(json.dumps(inventory, indent=2, sort_keys=True))
        return int(bool(inventory["errors"]))
    architecture = load_rules(args.repository / args.architecture_rules)
    plan = effective_review_plan(architecture, inventory["rules"], args.tier, json.loads(args.context), inventory["rule_set_hash"], inventory["errors"])
    if args.output: write_generated_json(args.repository, args.output, plan)
    else: print(json.dumps(plan, indent=2, sort_keys=True))
    return int(not plan["review_authorized"])


if __name__ == "__main__":
    raise SystemExit(_main())
