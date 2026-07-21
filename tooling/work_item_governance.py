"""Work-item sealing, classification, transition, and archival controls.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Mapping

from profile_conformance import capability_evidence_digest, validate_profile

MODES = {"integrated", "split"}
BUILTIN_TYPES = {"capability", "gov"}
DUAL_HAT_CORE_VERSION = "1.8.0"
BUILTIN_REGISTRY = {
    "capability": {"identity_pattern": r"^Capability [0-9]+$", "semantic_owner": "bounded product increment", "classification_rule": "product_increment true; independently bounded governance_contract_change false; tightly coupled governance may use extension_classification.coupled_governance_change", "classification": {"required_true": ["product_increment"], "required_false": ["governance_contract_change"]}, "compatible_execution_lifecycles": ["author_approved_for_execution", "engineering", "remediation_required", "engineering_complete", "architecture_review"]},
    "gov": {"identity_pattern": r"^GOV-[0-9]{4}$", "semantic_owner": "bounded governance change", "classification_rule": "governance_contract_change true and product_increment false", "classification": {"required_true": ["governance_contract_change"], "required_false": ["product_increment"]}, "compatible_execution_lifecycles": ["author_approved_for_execution", "engineering", "remediation_required", "engineering_complete", "architecture_review"]},
}
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

def registry_failures(rows: object) -> tuple[str, ...]:
    failures: list[str] = []
    if not isinstance(rows, Mapping): return ("work-item type registry is invalid",)
    required = {"identity_pattern", "semantic_owner", "classification_rule", "classification", "compatible_execution_lifecycles"}
    for name, definition in rows.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", str(name)): failures.append(f"work-item type identifier is invalid: {name}"); continue
        if not isinstance(definition, Mapping) or required - set(definition): failures.append(f"work-item type lacks governed definition: {name}"); continue
        if not str(definition.get("semantic_owner", "")).strip() or not str(definition.get("classification_rule", "")).strip(): failures.append(f"work-item type lacks semantic ownership or classification rationale: {name}")
        classification = definition.get("classification")
        if not isinstance(classification, Mapping) or not isinstance(classification.get("required_true"), list) or not isinstance(classification.get("required_false"), list):
            failures.append(f"work-item type lacks machine-readable classification: {name}"); continue
        fields = [*classification["required_true"], *classification["required_false"]]
        if not fields or any(not isinstance(field, str) or not re.fullmatch(r"(?:extension_classification\.)?[a-z][a-z0-9_]*", field) for field in fields) or len(fields) != len(set(fields)):
            failures.append(f"work-item type classification fields are invalid or contradictory: {name}")
        elif name not in BUILTIN_TYPES and any(not field.startswith("extension_classification.") and field not in {"product_increment","governance_contract_change","follow_up_blocking"} for field in fields):
            failures.append(f"extension work-item type classification must use the schema-governed namespace: {name}")
        lifecycles = definition.get("compatible_execution_lifecycles")
        if not isinstance(lifecycles, list) or not lifecycles:
            failures.append(f"work-item type lacks lifecycle compatibility: {name}")
        elif len(lifecycles) != len(set(lifecycles)) or any(not isinstance(row, str) or row not in TRANSITIONS for row in lifecycles): failures.append(f"work-item type lifecycle compatibility is invalid: {name}")
        try: re.compile(str(definition["identity_pattern"]))
        except re.error: failures.append(f"work-item type has invalid identity pattern: {name}")
    return tuple(failures)

def load_work_item_registry(path: str | Path) -> dict[str, dict[str, object]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8")); rows = payload.get("types", {})
    failures = registry_failures(rows)
    if failures: raise ValueError("; ".join(failures))
    return {str(name): dict(definition) for name, definition in rows.items()}

def load_work_item_types(path: str | Path) -> frozenset[str]:
    return frozenset(load_work_item_registry(path))

def _nonempty_list(order: Mapping[str, object], name: str) -> bool:
    value = order.get(name)
    return isinstance(value, list) and bool(value) and all(isinstance(row, str) and row.strip() for row in value)


def _revision_set_hash(revisions: object) -> str:
    if not isinstance(revisions, list):
        return ""
    values = []
    for index, row in enumerate(revisions, 1):
        if not isinstance(row, Mapping) or row.get("revision") != index or not re.fullmatch(r"[0-9A-F]{64}", str(row.get("sha256", ""))):
            return ""
        values.append(str(row["sha256"]))
    return hashlib.sha256(("\n".join(values) + "\n").encode()).hexdigest().upper() if values else ""


def validate_sealed(order: Mapping[str, object], *, registered_types: set[str] | frozenset[str] = frozenset(BUILTIN_TYPES),
                    type_registry: Mapping[str, Mapping[str, object]] | None = None) -> tuple[str, ...]:
    failures: list[str] = []
    if order.get("schema") == "dual-hat-sealed-work-order/1.0":
        legacy_required = {"work_item_id", "work_item_type", "title", "operating_mode", "active_role", "lifecycle_state", "approved_scope", "explicit_exclusions", "stop_gates", "authorized_repositories", "authorized_mutation", "required_validation", "publication_authority", "approval_state", "approval_timestamp", "work_order_hash"}
        if legacy_required - set(order): failures.append("legacy work order is incomplete")
        if order.get("work_item_type") not in registered_types: failures.append("unknown work-item type")
        if order.get("operating_mode") not in MODES: failures.append("unknown operating mode")
        if order.get("work_order_hash") != canonical_hash(order): failures.append("stale work-order hash")
        if order.get("approval_state") != "author_approved_for_execution": failures.append("work order is not author approved")
        return tuple(failures)
    required = {
        "schema", "work_item_id", "work_item_type", "title", "operating_mode", "active_role",
        "lifecycle_state", "approved_scope", "explicit_exclusions", "stop_gates",
        "authorized_repositories", "authorized_paths", "authorized_mutation",
        "destructive_permissions", "required_validation", "publication_authority",
        "dependency_permissions", "external_service_permissions", "approval_state",
        "approval_timestamp", "source_revisions", "revision_hash_set_sha256", "current_revision",
        "revision_hash_set_encoding", "sealed_state", "material_revision_rule", "work_order_hash",
    }
    if required - set(order): failures.append("work order is incomplete")
    if order.get("schema") != "dual-hat-sealed-work-order/1.1": failures.append("unknown work-order schema")
    if not str(order.get("work_item_id", "")).strip() or not str(order.get("title", "")).strip(): failures.append("work-item identity or title is invalid")
    kind = str(order.get("work_item_type", ""))
    registry = type_registry or BUILTIN_REGISTRY
    failures.extend(registry_failures(registry))
    definition = registry.get(kind) if isinstance(registry, Mapping) else None
    if kind not in registered_types or definition is None: failures.append("unknown work-item type or executable definition")
    elif not re.fullmatch(str(definition.get("identity_pattern", r"(?!)")), str(order.get("work_item_id", ""))): failures.append("work-item identity violates registered type pattern")
    if order.get("operating_mode") not in MODES: failures.append("unknown operating mode")
    if order.get("active_role") not in {"architecture", "engineering"}: failures.append("unknown active role")
    if order.get("lifecycle_state") != "author_approved_for_execution": failures.append("lifecycle does not authorize execution")
    for field in ("approved_scope", "stop_gates", "authorized_repositories", "authorized_paths", "destructive_permissions", "required_validation"):
        if not _nonempty_list(order, field): failures.append(f"work order lacks {field}")
    if not isinstance(order.get("explicit_exclusions"), list): failures.append("explicit exclusions are invalid")
    if not str(order.get("authorized_mutation", "")).strip(): failures.append("mutation authority is missing")
    publication = order.get("publication_authority")
    if not isinstance(publication, Mapping) or not all(isinstance(value, bool) for value in publication.values()) or not any("push" in str(key) for key in publication): failures.append("publication or push authority is incomplete")
    elif publication.get("force_push") is True and not any(value is True for key, value in publication.items() if "push" in str(key) and key != "force_push"): failures.append("force-push authority contradicts push authority")
    for field in ("dependency_permissions", "external_service_permissions"):
        value = order.get(field)
        if not isinstance(value, Mapping) or not value or not all(isinstance(row, bool) for row in value.values()): failures.append(f"{field.replace('_', ' ')} are incomplete")
    revisions = order.get("source_revisions")
    if not isinstance(order.get("current_revision"), int) or not isinstance(revisions, list) or order.get("current_revision") != len(revisions): failures.append("current revision is inconsistent")
    if order.get("revision_hash_set_sha256") != _revision_set_hash(revisions): failures.append("revision hash set is stale or invalid")
    if order.get("revision_hash_set_encoding") != "uppercase SHA-256 values in revision order, LF-terminated": failures.append("revision hash set encoding is invalid")
    if order.get("sealed_state") != "immutable_approved_contract" or not str(order.get("material_revision_rule", "")).strip(): failures.append("seal semantics are invalid")
    if order.get("work_order_hash") != canonical_hash(order): failures.append("stale work-order hash")
    if order.get("approval_state") != "author_approved_for_execution": failures.append("work order is not author approved")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", str(order.get("approval_timestamp", ""))): failures.append("approval timestamp is invalid")
    return tuple(failures)


def execution_contract_failures(
    order: Mapping[str, object], *, current_handover: Mapping[str, object] | None,
    platform_profile: Mapping[str, object] | None,
    platform_preflight: Mapping[str, object] | None = None,
    registered_types: set[str] | frozenset[str] = frozenset(BUILTIN_TYPES),
    type_registry: Mapping[str, Mapping[str, object]] | None = None,
    evidence_root: str | Path | None = None,
) -> tuple[str, ...]:
    failures = list(validate_sealed(order, registered_types=registered_types, type_registry=type_registry))
    failures.extend(classification_failures(order, type_registry=type_registry))
    if order.get("schema") == "dual-hat-sealed-work-order/1.0":
        failures.append("legacy work-order schema cannot authorize execution; migrate, reapprove, and reseal")
    active = current_handover.get("active_work_item") if isinstance(current_handover, Mapping) else None
    if not isinstance(active, Mapping):
        failures.append("current handover context is missing")
    else:
        expected = {
            "work_item_id": order.get("work_item_id"), "work_item_type": order.get("work_item_type"),
            "title": order.get("title"), "operating_mode": order.get("operating_mode"),
            "work_order_revision": order.get("current_revision"), "work_order_hash": order.get("work_order_hash"),
        }
        if any(active.get(key) != value for key, value in expected.items()): failures.append("current handover contradicts sealed work order")
        lifecycle, role = active.get("lifecycle_state"), active.get("active_role")
        valid_execution_contexts = {("author_approved_for_execution", "architecture"), ("engineering", "engineering"), ("remediation_required", "engineering")}
        if (lifecycle, role) not in valid_execution_contexts: failures.append("current handover role or lifecycle does not authorize engineering execution")
        registry = type_registry or BUILTIN_REGISTRY
        definition = registry.get(str(order.get("work_item_type"))) if isinstance(registry, Mapping) else None
        if not isinstance(definition, Mapping) or lifecycle not in definition.get("compatible_execution_lifecycles", ()): failures.append("current handover lifecycle is incompatible with registered work-item semantics")
    if not isinstance(platform_profile, Mapping):
        failures.append("platform-profile context is missing")
    else:
        failures.extend(validate_profile(platform_profile, DUAL_HAT_CORE_VERSION))
        capabilities = platform_profile.get("mandatory_capabilities")
        if not isinstance(capabilities, Mapping) or not capabilities or any(value is not True for value in capabilities.values()): failures.append("platform profile has a mandatory capability gap")
        if not isinstance(platform_preflight, Mapping): failures.append("platform capability preflight context is missing")
        else:
            from profile_conformance import capability_preflight
            receipts = platform_preflight.get("capability_test_receipts")
            expected_preflight_artifact = f"engineering/process/work-items/{order.get('work_item_id')}/PLATFORM_PREFLIGHT.json"
            verification_profile = dict(platform_profile)
            verification_profile["preflight_artifact"] = expected_preflight_artifact
            derived_preflight = capability_preflight(verification_profile, capabilities.keys() if isinstance(capabilities, Mapping) else (), DUAL_HAT_CORE_VERSION, evidence_root, receipts if isinstance(receipts, Mapping) else None)
            supported = platform_preflight.get("supported_mandatory_requirements", ())
            if (platform_preflight.get("preflight_artifact") != expected_preflight_artifact
                    or platform_preflight.get("work_item_id") != order.get("work_item_id")
                    or platform_preflight.get("work_order_revision") != order.get("current_revision")
                    or platform_preflight.get("work_order_hash") != order.get("work_order_hash")
                    or platform_preflight.get("platform_profile_id") != platform_profile.get("profile_id")
                    or platform_preflight.get("platform_profile_version") != platform_profile.get("profile_version")):
                failures.append("platform preflight contradicts work order or profile")
            if platform_preflight.get("result") != "pass" or platform_preflight.get("execution_authorized") is not True or platform_preflight.get("hard_stop") is not False:
                failures.append("platform preflight does not authorize execution")
            if not isinstance(supported, list) or set(supported) != set(capabilities): failures.append("platform preflight capability set is incomplete")
            if platform_preflight.get("capability_evidence_verified") is not True: failures.append("platform preflight lacks verified executable capability evidence")
            if platform_preflight.get("capability_evidence_sha256") != capability_evidence_digest(platform_profile): failures.append("platform preflight evidence binding is stale or forged")
            for field in ("result", "execution_authorized", "hard_stop", "supported_mandatory_requirements", "verified_capability_evidence", "capability_test_receipts", "capability_evidence_verified", "runtime_profile_verified", "capability_evidence_sha256", "verified_capability_evidence_sha256", "platform_profile_sha256"):
                if platform_preflight.get(field) != derived_preflight.get(field): failures.append("platform preflight is not reproducible from governed evidence"); break
    return tuple(dict.fromkeys(failures))

def classification_failures(order: Mapping[str, object], *, type_registry: Mapping[str, Mapping[str, object]] | None = None) -> tuple[str, ...]:
    registry = type_registry or BUILTIN_REGISTRY
    invalid = registry_failures(registry)
    if invalid: return invalid
    kind = str(order.get("work_item_type", "")); definition = registry.get(kind)
    if not isinstance(definition, Mapping): return ("work-item type lacks executable classification semantics",)
    classification = definition.get("classification")
    if not isinstance(classification, Mapping): return ("work-item type lacks executable classification semantics",)
    def value(field: object):
        name = str(field)
        if name.startswith("extension_classification."):
            extension = order.get("extension_classification", {})
            return extension.get(name.split(".", 1)[1]) if isinstance(extension, Mapping) else None
        return order.get(name)
    failures = [f"{kind} classification requires {field}=true" for field in classification.get("required_true", ()) if value(field) is not True]
    failures.extend(f"{kind} classification requires {field}=false" for field in classification.get("required_false", ()) if value(field) is not False)
    extension = order.get("extension_classification")
    coupled = extension.get("coupled_governance_change") if isinstance(extension, Mapping) else None
    if coupled is not None and not isinstance(coupled, bool): failures.append("coupled governance classification must be boolean")
    if coupled is True and kind != "capability": failures.append("coupled governance classification is valid only for a capability")
    compatible = definition.get("compatible_execution_lifecycles", ())
    if order.get("lifecycle_state") not in compatible:
        failures.append(f"{kind} lifecycle is incompatible with registered execution semantics")
    return tuple(failures)

def transition_allowed(current: str, target: str) -> bool: return target in TRANSITIONS.get(current, set())

def mode_switch_failures(package: Mapping[str, object]) -> tuple[str, ...]:
    failures: list[str] = []
    if package.get("lifecycle_state") not in SAFE_MODE_BOUNDARIES: failures.append("mode switch is not at a safe boundary")
    repo = package.get("repository", {})
    if not isinstance(repo, Mapping) or repo.get("dirty_worktree"): failures.append("dirty worktree blocks mode switch")
    for field in ("approved_work_order_hash", "completed_steps", "pending_steps", "unresolved_decisions", "required_local_artifacts", "permitted_next_action", "continuation_phrase"):
        if field not in package: failures.append(f"mode-transition package lacks {field}")
    if package.get("schema") == "dual-hat-mode-transition/1.1":
        for field in ("model_tier_binding", "rollback_point", "current_handover"):
            if not package.get(field): failures.append(f"mode-transition package lacks {field}")
    return tuple(failures)

def execution_authorized(order: Mapping[str, object], user_text: str, *, current_handover: Mapping[str, object] | None = None,
                         platform_profile: Mapping[str, object] | None = None,
                         platform_preflight: Mapping[str, object] | None = None,
                         type_registry: Mapping[str, Mapping[str, object]] | None = None,
                         evidence_root: str | Path | None = None) -> bool:
    registered = frozenset(type_registry) if type_registry is not None else frozenset(BUILTIN_TYPES)
    return not execution_contract_failures(order, current_handover=current_handover, platform_profile=platform_profile, platform_preflight=platform_preflight,
                                           registered_types=registered, type_registry=type_registry, evidence_root=evidence_root) and user_text.strip().casefold().rstrip(".") in EXECUTION_PHRASES

def architecture_direct_mutation_allowed(impact: Mapping[str, object]) -> bool:
    return impact.get("exclusive_architecture_owner") is True and all(impact.get(key) is False for key in ("external_consumer", "shared_schema", "engineering_behavior", "validator_or_generator", "publication_or_repository", "synchronized_propagation", "uncertain_reach"))

def archival_allowed(state: str, *, follow_up_blocking: bool = False, actor: str = "architecture") -> bool:
    return actor == "architecture" and (state == "accepted" or (state == "accepted_with_follow_up" and not follow_up_blocking))

def boundary_review_failures(review: Mapping[str, object]) -> tuple[str, ...]:
    failures: list[str] = []
    required = {"reviewer_role", "sealed_work_order_hash_verified", "primary_evidence_inspected", "engineering_self_report_only", "tests_only", "deviation_found", "material_violation_unresolved", "specific_remediation_obligation", "systemic_control_obligation", "analogous_gap_review", "architecture_disposition"}
    if required - set(review): failures.append("Architecture boundary review is incomplete")
    if review.get("reviewer_role") != "architecture": failures.append("only Architecture may issue the boundary disposition")
    if review.get("sealed_work_order_hash_verified") is not True: failures.append("Architecture did not verify the sealed work order")
    if not review.get("primary_evidence_inspected"): failures.append("Architecture lacks independent primary evidence")
    if review.get("engineering_self_report_only") is True: failures.append("Engineering self-report cannot satisfy boundary review")
    if review.get("tests_only") is True: failures.append("passing tests cannot satisfy boundary review")
    if review.get("deviation_found") is True:
        if not review.get("specific_remediation_obligation"): failures.append("boundary violation lacks specific remediation")
        if not review.get("systemic_control_obligation"): failures.append("boundary violation lacks systemic control strengthening")
        if not review.get("analogous_gap_review"): failures.append("boundary violation lacks analogous-gap review")
    if review.get("material_violation_unresolved") is True and review.get("architecture_disposition") in {"accepted", "accepted_with_follow_up"}: failures.append("acceptance is blocked by unresolved material boundary violation")
    return tuple(failures)
