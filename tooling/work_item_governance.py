"""Work-item sealing, classification, transition, and archival controls.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import hashlib, json
from typing import Mapping

MODES = {"integrated", "split"}
TYPES = {"capability", "gov"}
TRANSITIONS = {
    "architecture": {"work_order_ready"}, "work_order_ready": {"author_approved_for_execution"},
    "author_approved_for_execution": {"engineering"},
    "engineering": {"engineering_complete", "engineering_paused", "engineering_blocked", "engineering_aborted"},
    "engineering_paused": {"engineering", "engineering_aborted"},
    "engineering_blocked": {"engineering", "engineering_aborted"},
    "engineering_complete": {"architecture_review"}, "engineering_aborted": {"architecture_review"},
    "architecture_review": {"accepted", "accepted_with_follow_up", "remediation_required", "rejected"},
    "remediation_required": {"engineering"}, "rejected": {"remediation_required"},
    "accepted": {"archived"}, "accepted_with_follow_up": {"archived"}, "archived": set(),
}
SAFE_MODE_BOUNDARIES = {"architecture", "work_order_ready", "author_approved_for_execution", "engineering_paused", "engineering_complete", "architecture_review", "accepted", "accepted_with_follow_up", "archived"}
EXECUTION_PHRASES = {"approve this work order and enter engineering mode", "execute the approved work order", "begin engineering execution"}

def canonical_hash(order: Mapping[str, object]) -> str:
    payload = {k: v for k, v in order.items() if k != "work_order_hash"}
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    return hashlib.sha256(data).hexdigest().upper()

def seal(order: Mapping[str, object]) -> dict[str, object]:
    result = dict(order); result["work_order_hash"] = canonical_hash(result); return result

def validate_sealed(order: Mapping[str, object]) -> tuple[str, ...]:
    failures: list[str] = []
    required = {"work_item_id", "work_item_type", "title", "operating_mode", "active_role", "lifecycle_state", "approved_scope", "explicit_exclusions", "stop_gates", "authorized_repositories", "authorized_mutation", "required_validation", "publication_authority", "approval_state", "approval_timestamp", "work_order_hash"}
    if required - set(order): failures.append("work order is incomplete")
    if order.get("work_item_type") not in TYPES: failures.append("unknown work-item type")
    if order.get("operating_mode") not in MODES: failures.append("unknown operating mode")
    if order.get("work_order_hash") != canonical_hash(order): failures.append("stale work-order hash")
    if order.get("approval_state") != "author_approved_for_execution": failures.append("work order is not author approved")
    return tuple(failures)

def classification_failures(order: Mapping[str, object]) -> tuple[str, ...]:
    kind = order.get("work_item_type"); product = order.get("product_increment"); governance = order.get("governance_contract_change")
    if kind == "capability" and product is not True: return ("capability lacks a bounded product increment",)
    if kind == "gov" and (governance is not True or product is True): return ("GOV item classification contradicts declared semantic effects",)
    return ()

def transition_allowed(current: str, target: str) -> bool: return target in TRANSITIONS.get(current, set())

def mode_switch_failures(package: Mapping[str, object]) -> tuple[str, ...]:
    failures: list[str] = []
    if package.get("lifecycle_state") not in SAFE_MODE_BOUNDARIES: failures.append("mode switch is not at a safe boundary")
    repo = package.get("repository", {})
    if not isinstance(repo, Mapping) or repo.get("dirty_worktree"): failures.append("dirty worktree blocks mode switch")
    for field in ("approved_work_order_hash", "completed_steps", "pending_steps", "unresolved_decisions", "required_local_artifacts", "permitted_next_action", "continuation_phrase"):
        if field not in package: failures.append(f"mode-transition package lacks {field}")
    return tuple(failures)

def execution_authorized(order: Mapping[str, object], user_text: str) -> bool:
    return not validate_sealed(order) and user_text.strip().casefold().rstrip(".") in EXECUTION_PHRASES

def architecture_direct_mutation_allowed(impact: Mapping[str, object]) -> bool:
    return impact.get("exclusive_architecture_owner") is True and all(impact.get(key) is False for key in ("external_consumer", "shared_schema", "engineering_behavior", "validator_or_generator", "publication_or_repository", "synchronized_propagation", "uncertain_reach"))

def archival_allowed(state: str, *, follow_up_blocking: bool = False, actor: str = "architecture") -> bool:
    return actor == "architecture" and (state == "accepted" or (state == "accepted_with_follow_up" and not follow_up_blocking))
