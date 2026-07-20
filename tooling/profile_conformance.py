"""Validate a platform profile without making the core depend on it.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable, Mapping

GUARANTEES = {"monitoring_not_weakened", "recovery_not_weakened", "security_not_weakened", "validation_not_weakened", "evidence_not_weakened"}
GAP_KINDS = {"unsupported_capability", "unavailable_capability", "misconfigured_capability", "temporarily_degraded_capability", "permission_or_access_failure", "security_or_rights_restriction", "tool_defect", "profile_defect", "core_contract_ambiguity"}

def validate_profile(profile: Mapping[str, object], core_version: str) -> tuple[str, ...]:
    failures: list[str] = []
    if profile.get("dual_hat_core_version") != core_version: failures.append("platform profile is incompatible with active Dual Hat core")
    if profile.get("precedence") != "dual_hat_core_governs_profile_specializes": failures.append("platform profile precedence is invalid")
    guarantees = profile.get("guarantees", {})
    if not isinstance(guarantees, Mapping) or any(guarantees.get(key) is not True for key in GUARANTEES): failures.append("platform profile weakens or omits a core guarantee")
    for field in ("profile_id", "profile_version", "supported_configuration", "applicability", "mandatory_capabilities", "monitoring", "temporary_workspace", "detached_validation", "authentication", "recovery", "architecture_boundary_review", "validation"):
        if not profile.get(field): failures.append(f"platform profile lacks {field}")
    capabilities = profile.get("mandatory_capabilities", {})
    if isinstance(capabilities, Mapping) and any(value is not True for value in capabilities.values()): failures.append("platform profile marks a mandatory core capability unsupported")
    return tuple(failures)

def capability_preflight(profile: Mapping[str, object] | None, required: Iterable[str], core_version: str) -> dict[str, object]:
    required_set = tuple(dict.fromkeys(required))
    failures = ["no conformant platform profile selected"] if profile is None else list(validate_profile(profile, core_version))
    capabilities = {} if profile is None else profile.get("mandatory_capabilities", {})
    if not isinstance(capabilities, Mapping): failures.append("mandatory capability declaration is invalid"); capabilities = {}
    for requirement in required_set:
        if capabilities.get(requirement) is not True: failures.append(f"mandatory capability unavailable: {requirement}")
    uncertainties = [] if profile is None else profile.get("uncertainties_requiring_architecture_review", [])
    degraded = [] if profile is None else profile.get("degraded_features", [])
    unavailable = [] if profile is None else profile.get("unavailable_external_services", [])
    if uncertainties: failures.append("platform capability uncertainty requires Architecture review")
    if any(item in required_set for item in degraded): failures.append("a mandatory capability is degraded")
    if any(item in required_set for item in unavailable): failures.append("a mandatory external service is unavailable")
    unique = tuple(dict.fromkeys(failures))
    return {"execution_authorized": not unique, "hard_stop": bool(unique), "required": required_set, "failures": unique}

def runtime_gap_stop_report(*, gap_kind: str, unmet_requirement: str, limitation: str, handoff: Mapping[str, object]) -> dict[str, object]:
    if gap_kind not in GAP_KINDS: raise ValueError("unknown platform-contract gap kind")
    required = {"active_role", "operating_mode", "work_item_id", "sealed_work_order_hash", "platform_profile", "repository_and_remote_state", "dirty_worktree_state", "completed_steps", "pending_steps", "partial_outputs", "temporary_and_ignored_state", "containment_actions", "permitted_next_action"}
    missing = sorted(required - set(handoff))
    if missing: raise ValueError(f"incomplete resumable handoff: {missing}")
    return {"status":"hard_stop", "mutation_blocked":True, "gap_kind":gap_kind, "exact_unmet_requirement":unmet_requirement, "platform_or_profile_limitation":limitation, "architecture_disposition_required":True, "notifications":{"user":"required", "architecture_office":"required"}, "handoff":dict(handoff)}

def load_and_validate(path: str | Path, core_version: str) -> tuple[dict[str, object], tuple[str, ...]]:
    profile = json.loads(Path(path).read_text(encoding="utf-8")); return profile, validate_profile(profile, core_version)

def resolve_profile(profile: Mapping[str, object] | None, core_version: str) -> dict[str, object]:
    if profile is None: raise ValueError("no conformant platform profile selected; preflight hard stop")
    failures = validate_profile(profile, core_version)
    if failures: raise ValueError("; ".join(failures))
    return {"selection": profile["profile_id"], "core_applies": True, "fallback": None}
