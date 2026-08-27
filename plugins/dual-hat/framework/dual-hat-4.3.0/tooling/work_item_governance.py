"""Work-item sealing, classification, transition, and archival controls.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Mapping

from dispatch_reconciliation import dispatch_inventory
from profile_conformance import capability_evidence_digest, validate_profile

MODES = {"integrated", "split"}
BUILTIN_TYPES = {"capability", "gov"}
# The active Dual Hat core version has exactly one authority, release/VERSION.json,
# and it is resolved from there at call time -- never bound at import, directly or
# indirectly. This module is imported by the sealing, classification, transition and
# archival controls and by call sites that never touch a platform profile; binding the
# resolution at import would turn missing, unreadable or ambiguous release evidence
# into an ImportError for every one of them, through a channel carrying none of the
# conformance vocabulary its callers are equipped to handle. Failure is surfaced as an
# entry in the returned failures tuple instead, exactly as every other conformance
# failure already is. The literal it replaces read 1.11.0 for seven minor releases
# while being the sole authority admitting an adopter's platform profile; a standing
# check in tests/test_framework.py fails the moment any such literal reappears.
VERSION_EVIDENCE_SCHEMA = "dual-hat-version/1.0"
# Closed structure: no field outside PERMITTED is tolerated and every field in REQUIRED
# must be present as a non-empty string. "$comment" carries the SPDX marker rather than
# release semantics, so it is permitted and not required.
VERSION_EVIDENCE_REQUIRED_FIELDS = {"maturity", "schema", "stability", "version"}
VERSION_EVIDENCE_PERMITTED_FIELDS = VERSION_EVIDENCE_REQUIRED_FIELDS | {"$comment"}
# The shape schemas/platform-profile.schema.json already pins for the profile side,
# matched rather than reinvented so the two ends of the comparison cannot diverge.
SEMANTIC_VERSION_PATTERN = r"[0-9]+\.[0-9]+\.[0-9]+"
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
TERMINATION_TRANSITION_CONDITIONS = {
    ("engineering", "engineering_complete"): ("planned_scope_completion", False),
    ("engineering", "engineering_blocked"): ("hard_stop", False),
    ("engineering", "engineering_aborted"): ("hard_stop", True),
    ("engineering_paused", "engineering_aborted"): ("hard_stop", True),
    ("engineering_blocked", "engineering_aborted"): ("hard_stop", True),
}
TERMINATION_RECEIPT_SCHEMA = "dual-hat-termination-preflight-receipt/1.0"
PLATFORM_AUTHORITY_SNAPSHOT_SCHEMA = "dual-hat-platform-authority-snapshot/1.0"
SAFE_MODE_BOUNDARIES = {"architecture", "work_order_ready", "author_approved_for_execution", "engineering_paused", "engineering_complete", "architecture_review", "accepted", "accepted_with_follow_up", "archived"}
EXECUTION_PHRASES = {"approve this work order and enter engineering mode", "execute the approved work order", "begin engineering execution"}

def core_version_failures(record: object) -> tuple[str, ...]:
    """Validate governed release evidence, reporting rather than raising.

    Reuses release_package.release_maturity for the maturity cross-check rather
    than deriving maturity a second time: release_package.py already enforces
    exactly this cross-check on the release path, so sharing the one derivation
    is what keeps the conformance path and the release gate from disagreeing.
    The import is local to the call for the reason stated at the top of this
    module -- release evidence must never be able to fail an import.
    """
    if not isinstance(record, Mapping): return ("governed release evidence is not a version record",)
    failures: list[str] = []
    unknown = sorted(str(field) for field in record if field not in VERSION_EVIDENCE_PERMITTED_FIELDS)
    if unknown: failures.append(f"governed release evidence carries an unknown field: {', '.join(unknown)}")
    missing = sorted(VERSION_EVIDENCE_REQUIRED_FIELDS - set(record))
    if missing: failures.append(f"governed release evidence lacks a required field: {', '.join(missing)}")
    for field in sorted(VERSION_EVIDENCE_PERMITTED_FIELDS & set(record)):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip(): failures.append(f"governed release evidence field is not a non-empty string: {field}")
    if record.get("schema") != VERSION_EVIDENCE_SCHEMA: failures.append("governed release evidence declares an unknown schema")
    declared = record.get("version")
    if not isinstance(declared, str) or not re.fullmatch(SEMANTIC_VERSION_PATTERN, declared):
        failures.append("governed release evidence version is not a semantic version")
    else:
        try:
            from release_package import release_maturity
            expected = release_maturity(declared)
        except Exception: failures.append("governed release maturity derivation is unavailable")
        else:
            if record.get("maturity") != expected: failures.append("governed release evidence maturity contradicts its semantic version")
    return tuple(dict.fromkeys(failures))


def active_core_version() -> tuple[str | None, tuple[str, ...]]:
    """Resolve the active core version from governed release evidence, at call time.

    Returns the version and an empty failures tuple, or None and the conformance
    failures that stopped it being resolved. Reuses release_package.version_record,
    the committed reader for this file, rather than opening it a second time.
    release_package.version() is deliberately not called in addition: it is the same
    read of the same file narrowed to one key, so calling it as well would read the
    evidence twice and could return a value the validated record never described.
    """
    try:
        from release_package import version_record
        record = version_record()
    except Exception: return None, ("governed release evidence is unreadable",)
    failures = core_version_failures(record)
    if failures: return None, failures
    return str(record["version"]), ()


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
        # Resolved here, inside the one branch that needs it, so a profile-free
        # caller never depends on release evidence being readable at all.
        core_version, core_version_resolution = active_core_version()
        failures.extend(core_version_resolution)
        if core_version is not None: failures.extend(validate_profile(platform_profile, core_version))
        capabilities = platform_profile.get("mandatory_capabilities")
        if not isinstance(capabilities, Mapping) or not capabilities or any(value is not True for value in capabilities.values()): failures.append("platform profile has a mandatory capability gap")
        if not isinstance(platform_preflight, Mapping): failures.append("platform capability preflight context is missing")
        else:
            from profile_conformance import capability_preflight
            receipts = platform_preflight.get("capability_test_receipts")
            expected_preflight_artifact = f"engineering/process/work-items/{order.get('work_item_id')}/PLATFORM_PREFLIGHT.json"
            verification_profile = dict(platform_profile)
            verification_profile["preflight_artifact"] = expected_preflight_artifact
            # An unresolvable core version already stands as a failure entry above, so
            # the run is refused either way; deriving a preflight against a version the
            # evidence never established would only fabricate a second, misleading one.
            derived_preflight = capability_preflight(verification_profile, capabilities.keys() if isinstance(capabilities, Mapping) else (), core_version, evidence_root, receipts if isinstance(receipts, Mapping) else None) if core_version is not None else None
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
            for field in ("result", "execution_authorized", "hard_stop", "supported_mandatory_requirements", "verified_capability_evidence", "capability_test_receipts", "capability_evidence_verified", "runtime_profile_verified", "capability_evidence_sha256", "verified_capability_evidence_sha256", "platform_profile_sha256") if derived_preflight is not None else ():
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

def _exact_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip()


def termination_preflight_failures(
    current: str,
    target: str,
    *,
    sealed_order: Mapping[str, object] | None,
    termination_receipt: Mapping[str, object] | None,
    platform_authority_snapshot: Mapping[str, object] | None,
    type_registry: Mapping[str, Mapping[str, object]] | None = None,
) -> tuple[str, ...]:
    """Validate Clause A evidence for a terminal engineering transition.

    The platform authority snapshot is caller-supplied trust-boundary evidence. The
    receipt must reproduce its complete process and worker inventories exactly. Worker
    semantics are deliberately not implemented here: ``dispatch_inventory`` remains the
    sole authority for registration, state, heartbeat, successor, consumed-result, and
    named-worker refusals.
    """
    condition = TERMINATION_TRANSITION_CONDITIONS.get((current, target))
    if condition is None:
        return ()
    expected_terminal_condition, abort_authority_required = condition
    failures: list[str] = []

    if not isinstance(sealed_order, Mapping):
        return ("termination preflight lacks a sealed work order",)
    registered_types = frozenset(type_registry) if type_registry is not None else frozenset(BUILTIN_TYPES)
    sealed_failures = validate_sealed(sealed_order, registered_types=registered_types, type_registry=type_registry)
    if sealed_failures:
        failures.append("termination preflight sealed work order is invalid: " + "; ".join(sealed_failures))
    approved_scope = sealed_order.get("approved_scope")
    stop_gates = sealed_order.get("stop_gates")
    if not isinstance(approved_scope, list) or not all(_exact_nonempty_string(row) for row in approved_scope):
        failures.append("termination preflight sealed approved scope is invalid")
        approved_scope = []
    if not isinstance(stop_gates, list) or not all(_exact_nonempty_string(row) for row in stop_gates):
        failures.append("termination preflight sealed stop gates are invalid")
        stop_gates = []

    if not isinstance(termination_receipt, Mapping):
        return tuple(dict.fromkeys([*failures, "terminal transition requires a termination-preflight receipt"]))
    receipt_fields = {
        "schema", "governing_identity", "terminal_condition", "planned_item_dispositions",
        "required_results", "processes", "workers",
    }
    if expected_terminal_condition == "hard_stop":
        receipt_fields.add("hard_stop")
    if set(termination_receipt) != receipt_fields:
        failures.append("termination-preflight receipt fields are incomplete or unknown")
    if termination_receipt.get("schema") != TERMINATION_RECEIPT_SCHEMA:
        failures.append("termination-preflight receipt schema is invalid")
    if termination_receipt.get("terminal_condition") != expected_terminal_condition:
        failures.append("termination-preflight receipt names the wrong terminal condition")

    identity = termination_receipt.get("governing_identity")
    if not isinstance(identity, Mapping) or set(identity) != {"work_item_id", "work_order_hash"}:
        failures.append("termination-preflight governing identity is incomplete or unknown")
    elif (identity.get("work_item_id") != sealed_order.get("work_item_id")
          or identity.get("work_order_hash") != sealed_order.get("work_order_hash")):
        failures.append("termination-preflight receipt is not bound to the sealed work order")

    dispositions = termination_receipt.get("planned_item_dispositions")
    disposition_scope: list[str] = []
    if not isinstance(dispositions, list):
        failures.append("planned-item dispositions are invalid")
    else:
        for row in dispositions:
            if not isinstance(row, Mapping) or set(row) != {"scope_item", "disposition", "evidence"}:
                failures.append("planned-item disposition fields are incomplete or unknown")
                continue
            scope_item = row.get("scope_item")
            disposition = row.get("disposition")
            if not _exact_nonempty_string(scope_item):
                failures.append("planned-item disposition lacks an exact scope identity")
            else:
                disposition_scope.append(scope_item)
            if not _exact_nonempty_string(disposition):
                failures.append("planned-item disposition is invalid")
            if not _exact_nonempty_string(row.get("evidence")):
                failures.append("planned-item disposition lacks evidence")
        if set(disposition_scope) != set(approved_scope) or len(disposition_scope) != len(set(disposition_scope)):
            failures.append("planned-item dispositions do not exactly cover sealed approved scope")
        if expected_terminal_condition == "planned_scope_completion" and any(
            isinstance(row, Mapping) and row.get("disposition") != "complete" for row in dispositions
        ):
            failures.append("planned-scope completion carries a non-complete disposition")

    results = termination_receipt.get("required_results")
    result_scope: list[str] = []
    if not isinstance(results, list):
        failures.append("required results are invalid")
    else:
        for row in results:
            if not isinstance(row, Mapping) or set(row) != {"scope_item", "evidence"}:
                failures.append("required-result fields are incomplete or unknown")
                continue
            scope_item = row.get("scope_item")
            if not _exact_nonempty_string(scope_item):
                failures.append("required result lacks an exact scope identity")
            else:
                result_scope.append(scope_item)
            if not _exact_nonempty_string(row.get("evidence")):
                failures.append("required result lacks non-empty evidence")
        if set(result_scope) != set(approved_scope) or len(result_scope) != len(set(result_scope)):
            failures.append("required results do not exactly cover sealed approved scope")

    processes = termination_receipt.get("processes")
    process_ids: list[str] = []
    if not isinstance(processes, list):
        failures.append("owned-process inventory is invalid")
    else:
        for process in processes:
            if not isinstance(process, Mapping) or set(process) != {"process_id", "state", "terminal_evidence"}:
                failures.append("owned-process fields are incomplete or unknown")
                continue
            process_id = process.get("process_id")
            if not _exact_nonempty_string(process_id):
                failures.append("owned process lacks an exact process identity")
            else:
                process_ids.append(process_id)
            if process.get("state") != "terminal":
                failures.append(f"owned process {process_id!r} is nonterminal")
            if not _exact_nonempty_string(process.get("terminal_evidence")):
                failures.append(f"owned process {process_id!r} lacks terminal evidence")
        if len(process_ids) != len(set(process_ids)):
            failures.append("owned-process inventory repeats a process identity")

    workers = termination_receipt.get("workers")
    if not isinstance(workers, list):
        failures.append("delegated-worker inventory is invalid")
    else:
        try:
            reconciled_workers = dispatch_inventory(workers=workers)
        except (TypeError, ValueError) as exc:
            failures.append(f"delegated-worker inventory is invalid: {exc}")
        else:
            failures.extend(f"delegated-worker reconciliation blocks closure: {row}" for row in reconciled_workers["blocking_workers"])

    snapshot = platform_authority_snapshot
    snapshot_fields = {"schema", "work_item_id", "work_order_hash", "processes", "workers"}
    if not isinstance(snapshot, Mapping):
        failures.append("termination preflight lacks a platform-authority snapshot")
    else:
        if set(snapshot) != snapshot_fields:
            failures.append("platform-authority snapshot fields are incomplete or unknown")
        if snapshot.get("schema") != PLATFORM_AUTHORITY_SNAPSHOT_SCHEMA:
            failures.append("platform-authority snapshot schema is invalid")
        if (snapshot.get("work_item_id") != sealed_order.get("work_item_id")
                or snapshot.get("work_order_hash") != sealed_order.get("work_order_hash")):
            failures.append("platform-authority snapshot is not bound to the sealed work order")
        if snapshot.get("processes") != processes or snapshot.get("workers") != workers:
            failures.append("termination-preflight inventories do not exactly reconcile platform authority")

    hard_stop = termination_receipt.get("hard_stop")
    if expected_terminal_condition == "hard_stop":
        hard_stop_fields = {"gate", "evidence", "preserved_state", "affected_work", "resumption_condition"}
        if abort_authority_required:
            hard_stop_fields.update({"abort_authority", "terminal_disposition"})
        if not isinstance(hard_stop, Mapping) or set(hard_stop) != hard_stop_fields:
            failures.append("hard-stop evidence fields are incomplete or unknown")
        else:
            for field in hard_stop_fields:
                if not _exact_nonempty_string(hard_stop.get(field)):
                    failures.append(f"hard-stop evidence lacks {field}")
            if hard_stop.get("gate") not in stop_gates:
                failures.append("hard-stop gate is not named in sealed stop_gates")
            if abort_authority_required and hard_stop.get("abort_authority") not in stop_gates:
                failures.append("abort authority is not named in sealed stop_gates")

    return tuple(dict.fromkeys(failures))


def transition_allowed(
    current: str,
    target: str,
    *,
    sealed_order: Mapping[str, object] | None = None,
    termination_receipt: Mapping[str, object] | None = None,
    platform_authority_snapshot: Mapping[str, object] | None = None,
    type_registry: Mapping[str, Mapping[str, object]] | None = None,
) -> bool:
    if target not in TRANSITIONS.get(current, set()):
        return False
    return not termination_preflight_failures(
        current,
        target,
        sealed_order=sealed_order,
        termination_receipt=termination_receipt,
        platform_authority_snapshot=platform_authority_snapshot,
        type_registry=type_registry,
    )

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
