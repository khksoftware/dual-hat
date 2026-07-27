"""Abstract model tiers and evidence-backed runtime binding.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence


TIERS = {
    "tier_1_routine": {"reasoning": "routine deterministic execution", "tools": ["bounded_file_or_process_tools"], "context": "bounded", "independence": "not_required", "cost_latency": "optimize"},
    "tier_2_standard": {"reasoning": "standard implementation and analysis", "tools": ["repository_inspection", "validation"], "context": "work_item", "independence": "preferred_for_review", "cost_latency": "balance"},
    "tier_3_advanced": {"reasoning": "complex architecture and cross-domain reasoning", "tools": ["repository_inspection", "validation", "resumable_handoff"], "context": "cross_domain", "independence": "required_for_architecture_review", "cost_latency": "capability_first"},
    "tier_4_critical": {"reasoning": "deep independent high-risk security or release review", "tools": ["primary_evidence", "detached_validation", "resumable_handoff"], "context": "complete_risk_boundary", "independence": "mandatory", "cost_latency": "risk_first"},
}
ORDER = tuple(TIERS)


class RoutingError(RuntimeError):
    pass


def fingerprint(evidence: Mapping[str, object]) -> str:
    encoded = (json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def verified_evidence(evidence: object, *, environment_fingerprint: str | None = None) -> bool:
    if not isinstance(evidence, Mapping) or evidence.get("source_type") not in {"adapter_probe","governed_registry"} or not evidence.get("authority_id") or not evidence.get("observation_id") or not evidence.get("evidence_hash"):
        return False
    payload=dict(evidence); claimed=payload.pop("evidence_hash")
    if claimed != fingerprint(payload):
        return False
    return environment_fingerprint is None or evidence.get("environment_fingerprint") == environment_fingerprint


def tier_for_activity(activity: str) -> str:
    mapping = {
        "deterministic_execution": ORDER[0], "standard_implementation": ORDER[1],
        "architecture": ORDER[2], "independent_review": ORDER[2],
        "security_review": ORDER[3], "release_review": ORDER[3],
    }
    if activity not in mapping:
        raise RoutingError(f"activity has no abstract-tier assignment: {activity}")
    return mapping[activity]


def bind_development_environment(
    *, adapter_identity: str, tools: Sequence[str], runtime_fingerprint: Mapping[str, object],
    configured_models: Sequence[Mapping[str, object]], prior_binding: Mapping[str, object] | None = None,
) -> dict[str, object]:
    evidence = {"adapter_identity": adapter_identity, "tools": sorted(set(tools)), "runtime": runtime_fingerprint}
    evidence_hash = fingerprint(evidence)
    mapping: dict[str, object] = {}
    candidates: dict[str, list[dict[str, object]]] = {}
    for tier in ORDER:
        eligible: list[dict[str, object]] = []
        for row in configured_models:
            capability = row.get("capability_evidence")
            availability = row.get("availability_evidence")
            confirmation = row.get("user_confirmation")
            if not verified_evidence(capability, environment_fingerprint=evidence_hash) or tier not in capability.get("verified_tiers", []):
                continue
            if not verified_evidence(availability, environment_fingerprint=evidence_hash) or availability.get("adapter_identity") != adapter_identity or availability.get("observed_available") is not True:
                continue
            candidate = dict(row)
            candidate.pop("available", None)
            candidate.pop("satisfies_tiers", None)
            eligible.append(candidate)
            confirmed = (
                isinstance(confirmation, Mapping)
                and confirmation.get("adapter_identity") == adapter_identity
                and confirmation.get("environment_fingerprint") == evidence_hash
                and confirmation.get("selection_id") == row.get("selection_id")
                and confirmation.get("confirmed") is True
                and bool(confirmation.get("confirmed_by"))
            )
            if confirmed and tier not in mapping:
                mapping[tier] = candidate
        candidates[tier] = eligible
        mapping.setdefault(tier, None)
    remapped = prior_binding is not None and prior_binding.get("environment_fingerprint") != evidence_hash
    return {
        "schema": "dual-hat-development-model-binding/1.0", "portable_policy": False,
        "detection_evidence": evidence, "environment_fingerprint": evidence_hash,
        "tier_mapping": mapping, "environment_changed": remapped,
        "eligible_candidates": candidates,
        "automatic_model_switch_supported": False,
        "manual_switch_instruction": f"In adapter '{adapter_identity}', select the recorded selection_id, then record a new confirmation bound to this adapter identity before resuming.",
    }


def require_tier(binding: Mapping[str, object], tier: str, *, mandatory: bool = True) -> dict[str, object]:
    if tier not in TIERS:
        raise RoutingError("unknown abstract tier")
    mapping = binding.get("tier_mapping", {})
    selected = mapping.get(tier) if isinstance(mapping, Mapping) else None
    if selected:
        return {"status": "satisfied", "tier": tier, "selection": selected, "evidence_required": True}
    candidates = binding.get("eligible_candidates", {})
    if isinstance(candidates, Mapping) and candidates.get(tier):
        return {"status": "confirmation_required", "tier": tier, "candidates": candidates[tier], "manual_switch_instruction": binding.get("manual_switch_instruction"), "silent_selection": False}
    if mandatory:
        return {"status": "hard_stop", "tier": tier, "missing_capability": True, "resumable": True, "safe_options": ["configure a satisfying model", "move to a capable host", "return to Architecture"]}
    lower = [name for name in ORDER[:ORDER.index(tier)] if isinstance(mapping, Mapping) and mapping.get(name)]
    return {"status": "fallback_requires_confirmation" if lower else "unavailable", "tier": tier, "fallback": lower[-1] if lower else None, "silent_downgrade": False}


def production_configuration(config: Mapping[str, object]) -> dict[str, object]:
    required = {"provider", "model", "reasoning_effort", "fallback", "privacy_preference", "local_or_cloud", "cost_sensitivity", "latency_preference", "data_retention_restrictions", "permitted_task_classes", "unavailable_model_behavior", "capability_evidence", "approved_by_user"}
    missing = sorted(field for field in required if field not in config or config[field] in (None, "", []))
    if missing or config.get("approved_by_user") is not True:
        return {"status": "hard_stop", "reason": "explicit production model configuration and user approval required", "missing": missing, "silent_provider_selection": False}
    capability = config.get("capability_evidence")
    if not verified_evidence(capability) or not capability.get("verified_tiers") or any(tier not in TIERS for tier in capability.get("verified_tiers", [])):
        return {"status":"hard_stop", "reason":"verified production tier capability evidence required", "missing":["capability_evidence"], "silent_provider_selection":False}
    approved = {"status": "approved", "schema": "dual-hat-production-model-configuration/1.0", **dict(config), "derived_from_development_detection": False}
    approved["configuration_hash"] = fingerprint(approved)
    return approved


def switch_selection(*, atomic_operation_active: bool, current: str, target: str, required_tier: str, approved_configuration: Mapping[str, object], availability_evidence: Mapping[str, object], operation_id: str) -> dict[str, object]:
    if required_tier not in TIERS:
        raise RoutingError("unknown abstract tier")
    expected_hash = approved_configuration.get("configuration_hash")
    unhashed = dict(approved_configuration); unhashed.pop("configuration_hash", None)
    if approved_configuration.get("status") != "approved" or expected_hash != fingerprint(unhashed):
        raise RoutingError("switch requires an intact approved production configuration")
    if target != approved_configuration.get("model"):
        raise RoutingError("target is not bound to the approved production configuration")
    capability = approved_configuration.get("capability_evidence")
    if not isinstance(capability, Mapping) or required_tier not in capability.get("verified_tiers", []):
        return {"status":"hard_stop", "current":current, "target":target, "required_tier":required_tier, "operation_id":operation_id, "state_preserved":True, "missing_capability":True, "silent_substitution":False}
    if atomic_operation_active:
        return {"status": "deferred_to_safe_boundary", "current": current, "target": target, "required_tier": required_tier, "operation_id": operation_id, "state_preserved": True}
    available = verified_evidence(availability_evidence) and availability_evidence.get("selection_id") == target and availability_evidence.get("observed_available") is True
    if not available:
        return {"status": "hard_stop", "current": current, "target": target, "state_preserved": True, "silent_substitution": False}
    return {"status": "switch_authorized", "current": current, "target": target, "required_tier": required_tier, "operation_id": operation_id, "approved_configuration_hash": expected_hash, "availability_evidence_hash": fingerprint(availability_evidence), "record_selection": True}
