"""Plan-first repository and product onboarding for Dual Hat.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import fnmatch
import json
import os
import re
import stat
from pathlib import Path
from typing import Mapping, Sequence

from path_containment import ContainmentError, contained, is_reparse


SCENARIOS = frozenset({"no_repository", "nearly_empty", "existing_project"})
DEPTHS = frozenset({"quick", "standard", "deep"})
BINDING_MODELS = frozenset({"external", "pinned_project_local"})
DISCOVERY_FIELDS = (
    "product_purpose", "intended_users", "problem", "vision", "desired_outcomes",
    "success_measures", "pain_points", "commitments", "technical_constraints",
    "business_constraints", "non_negotiable_behavior", "security", "privacy",
    "rights_and_licensing", "compliance", "deployment", "supported_environments",
    "external_services", "dependencies", "team_and_ownership", "roadmap", "known_risks",
    "cost_latency_and_operational_limits",
)
PRIVATE_NAMES = frozenset({".env", ".env.local", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"})
PRIVATE_NAME_TOKENS = frozenset({"credential", "secret", "password", "passwd", "token", "private-key", "private_key", "api-key", "api_key"})
EXECUTABLE_NAMES = frozenset({"package.json", "pyproject.toml", "setup.py", "Makefile", "Dockerfile"})
DEPENDENCY_NAMES = frozenset({"requirements.txt", "poetry.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock", "go.mod"})
TEXT_INSPECTION_SUFFIXES = frozenset({".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".py", ".js", ".html", ".css", ".sh", ".ps1", ".bat", ".cmd"})


class OnboardingError(RuntimeError):
    pass


def canonical_hash(value: Mapping[str, object], *, omit: Sequence[str] = ("package_hash",)) -> str:
    payload = {key: item for key, item in value.items() if key not in omit}
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    return hashlib.sha256(encoded).hexdigest().upper()


def framework_tree_checksum(root: str | Path) -> str:
    authority = Path(root).resolve(strict=True)
    if not authority.is_dir() or _linked(authority):
        raise OnboardingError("framework checksum requires a regular unlinked directory")
    rows = []
    for current, directories, names in os.walk(authority,topdown=True,followlinks=False):
        base=Path(current)
        for name in sorted(directories):
            if _linked(base/name): raise OnboardingError("framework checksum refuses linked directories")
        for name in sorted(names):
            path=base/name
            if _linked(path) or not path.is_file(): raise OnboardingError("framework checksum refuses linked or non-regular files")
            relative = path.relative_to(authority).as_posix()
            rows.append({"path":relative, "sha256":hashlib.sha256(path.read_bytes()).hexdigest().upper()})
    return hashlib.sha256((json.dumps(rows,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest().upper()


def _linked(path: Path) -> bool:
    try:
        return path.is_symlink() or bool(getattr(os.lstat(path), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        return False


def _authorized_target(authorized_root: str | Path, target: str | Path, *, must_exist: bool) -> Path:
    authority = Path(authorized_root).resolve(strict=True)
    candidate = Path(target)
    resolved = candidate.resolve(strict=must_exist)
    try:
        relative = resolved.relative_to(authority)
    except ValueError as exc:
        raise OnboardingError("target escapes the explicit authorized root") from exc
    current = authority
    for part in relative.parts:
        current /= part
        if current.exists() and _linked(current):
            raise OnboardingError("target crosses a symlink or reparse point")
    return resolved


def _ignore_patterns(root: Path) -> tuple[str, ...]:
    path = root / ".gitignore"
    if not path.is_file() or _linked(path):
        return ()
    return tuple(line.strip().lstrip("/") for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip() and not line.lstrip().startswith(("#", "!")))


def _ignored(relative: str, patterns: Sequence[str]) -> bool:
    normalized = relative.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(Path(normalized).name, pattern) or (pattern.endswith("/") and normalized.startswith(pattern)) for pattern in patterns)


def _safe_text(path: Path, *, maximum: int = 131072) -> str | None:
    if path.suffix.casefold() not in TEXT_INSPECTION_SUFFIXES or path.stat().st_size > maximum:
        return None
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _private_candidate(path: Path, relative: str, patterns: Sequence[str]) -> bool:
    name = path.name.casefold()
    if name in PRIVATE_NAMES or path.suffix.casefold() in {".key", ".pem", ".pfx"} or any(token in name for token in PRIVATE_NAME_TOKENS) or _ignored(relative, patterns):
        return True
    if path.suffix.casefold() in TEXT_INSPECTION_SUFFIXES | {".ini", ".cfg"} and path.stat().st_size <= 131072:
        data = path.read_bytes().lower()
        return bool(re.search(rb"(?:password|passwd|secret|api[_-]?key|(?:access|auth|bearer)[_-]?token|token|private[_-]?key)\s*[\"']?\s*[:=]", data))
    return False


def _safe_repository_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, directories, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        safe_directories: list[str] = []
        for name in sorted(directories):
            candidate = current_path / name
            if name in {".git", "node_modules", "vendor", "__pycache__"}:
                continue
            if _linked(candidate):
                raise OnboardingError(f"repository inspection refused linked directory: {candidate.relative_to(root).as_posix()}")
            safe_directories.append(name)
        directories[:] = safe_directories
        for name in sorted(names):
            candidate = current_path / name
            if _linked(candidate):
                raise OnboardingError(f"repository inspection refused linked file: {candidate.relative_to(root).as_posix()}")
            if candidate.is_file():
                files.append(candidate)
    return files


def classify_repository(target: str | Path, *, authorized_root: str | Path) -> str:
    root = _authorized_target(authorized_root, target, must_exist=False)
    if not root.exists():
        return "no_repository"
    if not root.is_dir():
        raise OnboardingError("onboarding target must be a directory or an absent intended directory")
    files = _safe_repository_files(root.resolve(strict=True))
    meaningful = [path for path in files if path.name not in {".gitignore", "README", "README.md", "LICENSE"}]
    return "nearly_empty" if len(meaningful) <= 2 else "existing_project"


def inspect_repository(target: str | Path, *, authorized_root: str | Path, depth: str = "standard") -> dict[str, object]:
    if depth not in DEPTHS:
        raise OnboardingError(f"unknown onboarding depth: {depth}")
    root = _authorized_target(authorized_root, target, must_exist=False)
    scenario = classify_repository(root, authorized_root=authorized_root)
    if scenario == "no_repository":
        return {"scenario": scenario, "inspection_mode": "no_files", "files": [], "excluded_private": [], "trust_review_required": False}
    authority = root.resolve(strict=True)
    files = _safe_repository_files(authority)
    relative = [path.relative_to(authority).as_posix() for path in files]
    patterns = _ignore_patterns(authority)
    private = sorted(item for item, source in zip(relative, files) if _private_candidate(source, item, patterns))
    visible = [path for path in relative if path not in private]
    limit = {"quick": 50, "standard": 500, "deep": 5000}[depth]
    selected = visible[:limit]
    texts: dict[str, str] = {}
    if depth in {"standard", "deep"}:
        candidates = selected if depth == "deep" else [path for path in selected if Path(path).name in EXECUTABLE_NAMES | DEPENDENCY_NAMES or Path(path).suffix.casefold() == ".md"]
        for relative_path in candidates:
            text = _safe_text(authority / relative_path)
            if text is not None:
                texts[relative_path] = text
    lowered = {path: text.casefold() for path, text in texts.items()}
    purpose_clues = sorted(path for path in texts if Path(path).name.casefold().startswith("readme"))
    script_risk = sorted(path for path, text in lowered.items() if re.search(r"\b(?:preinstall|postinstall|curl|wget|invoke-webrequest|eval\s*\(|exec\s*\(|subprocess\.)", text))
    suspicious = sorted(path for path, text in lowered.items() if re.search(r"(?:base64|fromcharcode|[a-z]+shell\s+-enc|chmod\s+777)", text))
    debt = sorted(path for path, text in lowered.items() if "todo" in text or "fixme" in text or "innerhtml" in text)
    deployment = sorted(path for path in selected if Path(path).name in {"Dockerfile", "docker-compose.yml", "Procfile"} or "/workflows/" in f"/{path}" or path.startswith(("deploy/", "infra/")))
    persistence = sorted(path for path in selected if any(token in path.casefold() for token in ("store", "database", "sqlite", "persist", "migration", "tasks.local")))
    migrations = sorted(path for path in selected if "migration" in path.casefold())
    planning = sorted(path for path in selected if Path(path).name.casefold() in {"roadmap.md", "backlog.md", "active_session.md", "current_handover.md"})
    rights = sorted(path for path in selected if Path(path).name.casefold().startswith(("license", "notice", "copying")))
    compliance = sorted(path for path in selected if any(token in path.casefold() for token in ("compliance", "privacy", "security", "threat")))
    subsystems = sorted({path.split("/",1)[0] for path in selected if "/" in path})
    result = {
        "scenario": scenario,
        "inspection_mode": "read_only_metadata",
        "files": selected,
        "files_truncated": len(visible) > limit,
        "excluded_private": private,
        "entrypoint_candidates": [path for path in selected if Path(path).name in EXECUTABLE_NAMES or path.endswith(("/__main__.py", "/main.py", "/app.py", "/index.html"))],
        "dependency_manifests": [path for path in selected if Path(path).name in DEPENDENCY_NAMES],
        "tests": [path for path in selected if "test" in Path(path).name.casefold()],
        "documentation": [path for path in selected if Path(path).suffix.casefold() == ".md"],
        "executable_hooks_and_scripts": [path for path in selected if "/hooks/" in f"/{path}" or Path(path).suffix.casefold() in {".ps1", ".sh", ".bat", ".cmd"}],
        "executed_repository_code": False,
        "installed_dependencies": False,
        "uploaded_content": False,
        "trust_review_required": scenario == "existing_project",
        "purpose_clues": purpose_clues,
        "deployment_surfaces": deployment,
        "persistence_surfaces": persistence,
        "incomplete_migration_candidates": migrations,
        "roadmap_and_work_item_surfaces": planning,
        "subsystem_candidates": subsystems,
        "rights_and_licensing_surfaces": rights,
        "privacy_security_compliance_surfaces": compliance,
        "dependency_risk_candidates": sorted(set(script_risk) | {path for path in selected if Path(path).name in DEPENDENCY_NAMES}),
        "implementation_vision_mismatch": scenario == "existing_project" and (not purpose_clues or not any(path for path in selected if Path(path).name in EXECUTABLE_NAMES)),
        "script_and_dependency_risks": script_risk,
        "suspicious_content_candidates": suspicious,
        "technical_debt_candidates": debt,
        "duplicate_authority_candidates": sorted(path for path in selected if Path(path).name.casefold() in {"roadmap-old.md", "architecture-old.md", "current_handover_old.md"}),
        "material_uncertainty": bool(suspicious or script_risk),
        "content_files_safely_inspected": sorted(texts),
    }
    if depth == "quick":
        result["depth_contract"] = "minimal metadata and next-step recommendation"
    elif depth == "standard":
        result["depth_contract"] = "metadata plus documentation and manifest assessment"
    else:
        result["depth_contract"] = "bounded content-aware subsystem, trust, dependency, migration, operations, and debt assessment"
    return result


def build_onboarding_package(
    *, target: str | Path, authorized_root: str | Path, discovery: Mapping[str, object], depth: str = "standard",
    binding_model: str = "external", operating_mode: str = "integrated",
    quality_rule_set_hash: str, effective_plan_hash: str,
) -> dict[str, object]:
    if depth not in DEPTHS or binding_model not in BINDING_MODELS or operating_mode not in {"integrated", "split"}:
        raise OnboardingError("unknown depth, binding model, or operating mode")
    evidence = inspect_repository(target, authorized_root=authorized_root, depth=depth)
    missing = [field for field in DISCOVERY_FIELDS if not discovery.get(field)]
    scenario = str(evidence["scenario"])
    mutation = {
        "requires_approval": True,
        "repository_creation": scenario == "no_repository",
        "material_scaffold_decision": scenario == "nearly_empty",
        "implementation_mutation": False,
        "binding_path": ".dual-hat/binding.json",
        "binding_model": binding_model,
    }
    scaffold = []
    if scenario == "nearly_empty":
        scaffold = [
            {"option": "retain", "when": "initial files align with the approved product model"},
            {"option": "replace", "when": "initial files are disposable or conflict with approved boundaries"},
            {"option": "migrate", "when": "useful initial work needs an explicit bounded transition"},
        ]
    package: dict[str, object] = {
        "schema": "dual-hat-onboarding-package/1.0",
        "state": "awaiting_user_approval",
        "repository_scenario": scenario,
        "depth": depth,
        "product_model": {field: discovery.get(field) for field in DISCOVERY_FIELDS},
        "user_and_stakeholder_model": {"intended_users": discovery.get("intended_users"), "team_and_ownership": discovery.get("team_and_ownership")},
        "protected_characteristics_and_non_negotiables": {"security": discovery.get("security"), "privacy": discovery.get("privacy"), "rights": discovery.get("rights_and_licensing"), "compliance": discovery.get("compliance"), "behavior": discovery.get("non_negotiable_behavior")},
        "operating_mode_recommendation": operating_mode,
        "installation_and_binding_recommendation": binding_model,
        "architecture_summary": discovery.get("architecture_summary", "technology-neutral boundaries to be selected after approval"),
        "risks_and_constraints": {"known_risks": discovery.get("known_risks"), "technical": discovery.get("technical_constraints"), "business": discovery.get("business_constraints")},
        "quality_rule_discovery": {"rule_set_hash": quality_rule_set_hash, "effective_plan_hash": effective_plan_hash},
        "technical_debt_proposal": discovery.get("technical_debt_proposal", [{"source":"repository_inspection", "path":path, "status":"proposed_not_accepted"} for path in evidence.get("technical_debt_candidates", [])]),
        "phase_level_roadmap": discovery.get("phase_level_roadmap", ["discovery", "approved foundation", "minimal first milestone", "validation"]),
        "proposed_work_items": discovery.get("proposed_work_items", ["approve onboarding package", "establish bounded foundation", "deliver minimal first milestone"]),
        "future_triggers": discovery.get("future_triggers", []),
        "dependencies": discovery.get("dependencies"),
        "assumptions": discovery.get("assumptions", []),
        "unresolved_decisions": missing,
        "minimum_viable_questions": missing,
        "repository_evidence": evidence,
        "mutation_plan": mutation,
        "scaffold_disposition_options": scaffold,
        "rollback_strategy": "remove only manifest-owned binding files; abandon an uncommitted new repository or revert the bounded checkpoint",
        "approval": {"approved": False, "approved_package_hash": None},
    }
    package["package_hash"] = canonical_hash(package)
    return package


def _authority_receipt_valid(receipt: Mapping[str, object], decision_payload_hash: str) -> bool:
    evidence=receipt.get("authority_evidence")
    if not isinstance(evidence,Mapping): return False
    required=(evidence.get("source_type")=="user_interaction" and bool(evidence.get("authority_id")) and bool(evidence.get("event_id")) and bool(evidence.get("captured_by")) and evidence.get("decision_payload_hash")==decision_payload_hash)
    return bool(required and evidence.get("evidence_hash")==canonical_hash(evidence,omit=("evidence_hash",)))


def approve_package(package: Mapping[str, object], *, approval_receipt: Mapping[str, object]) -> dict[str, object]:
    if package.get("state") != "awaiting_user_approval" or package.get("package_hash") != canonical_hash(package):
        raise OnboardingError("onboarding package is stale or not approval-ready")
    evidence = package.get("repository_evidence", {})
    if isinstance(evidence, Mapping) and evidence.get("material_uncertainty") is True:
        raise OnboardingError("material repository uncertainty requires resolution before approval")
    required = {"schema":"dual-hat-user-approval/1.0", "decision":"approve_onboarding", "approved_package_hash":package["package_hash"]}
    if any(approval_receipt.get(key) != value for key,value in required.items()) or not _authority_receipt_valid(approval_receipt,package["package_hash"]):
        raise OnboardingError("exact authority-bound onboarding approval receipt is required")
    result = dict(package)
    result["state"] = "approved_for_binding"
    result["approval"] = {**dict(approval_receipt), "approved": True}
    result["package_hash"] = canonical_hash(result)
    return result


def binding_plan(package: Mapping[str, object], *, framework_path: str | Path, framework_authorized_root: str | Path, framework_version: str, framework_checksum: str) -> dict[str, object]:
    approval = package.get("approval", {})
    if package.get("state") != "approved_for_binding" or not isinstance(approval, Mapping) or approval.get("approved") is not True:
        raise OnboardingError("user approval is required before repository mutation")
    if package.get("package_hash") != canonical_hash(package):
        raise OnboardingError("approved onboarding package is stale")
    framework = _authorized_target(framework_authorized_root, framework_path, must_exist=True)
    computed_checksum = framework_tree_checksum(framework)
    if not framework.is_dir() or not framework_version or not re.fullmatch(r"[A-Fa-f0-9]{64}", framework_checksum) or computed_checksum != framework_checksum.upper():
        raise OnboardingError("existing authorized framework path and verified version checksum are required")
    model = str(package["installation_and_binding_recommendation"])
    result = {
        "schema": "dual-hat-project-binding/1.0", "binding_model": model,
        "operation": "apply", "framework": {"path": framework.as_posix(), "version": framework_version, "sha256": computed_checksum, "checksum_verified": True, "checksum_method":"canonical path-and-content tree SHA-256"},
        "onboarding_package_hash": package["package_hash"], "approved": True,
        "approval_evidence": dict(approval),
        "project_footprint": [".dual-hat/binding.json"],
        "vendored_framework": False, "migration_requires_governed_approval": True,
    }
    result["plan_hash"] = canonical_hash(result, omit=("plan_hash",))
    return result


def apply_binding(target: str | Path, plan: Mapping[str, object], *, approved_package: Mapping[str, object], authorized_root: str | Path) -> Path:
    root = _authorized_target(authorized_root, target, must_exist=True)
    if plan.get("schema") != "dual-hat-project-binding/1.0" or plan.get("approved") is not True or plan.get("vendored_framework") is not False:
        raise OnboardingError("binding plan is invalid or unapproved")
    if approved_package.get("state") != "approved_for_binding" or approved_package.get("package_hash") != canonical_hash(approved_package):
        raise OnboardingError("exact approved onboarding package is absent or stale")
    if plan.get("onboarding_package_hash") != approved_package.get("package_hash") or plan.get("approval_evidence") != approved_package.get("approval"):
        raise OnboardingError("binding plan is not bound to the exact approved package")
    if plan.get("plan_hash") != canonical_hash(plan, omit=("plan_hash",)):
        raise OnboardingError("binding plan hash is stale")
    destination = contained(root, ".dual-hat/binding.json")
    if destination.exists():
        raise OnboardingError("binding already exists; use governed update or migration")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return destination


def removal_plan(target: str | Path, *, approved_package: Mapping[str, object], authorized_root: str | Path, approval_receipt: Mapping[str, object]) -> dict[str, object]:
    root = _authorized_target(authorized_root, target, must_exist=True)
    destination = contained(root, ".dual-hat/binding.json", must_exist=True, kind="file")
    payload = destination.read_bytes()
    if approved_package.get("state") != "approved_for_binding" or approved_package.get("package_hash") != canonical_hash(approved_package):
        raise OnboardingError("exact approved onboarding package is absent or stale")
    binding_sha256=hashlib.sha256(payload).hexdigest().upper()
    expected={"schema":"dual-hat-user-approval/1.0", "decision":"remove_binding", "onboarding_package_hash":approved_package["package_hash"], "binding_sha256":binding_sha256}
    decision_hash=canonical_hash({"decision":"remove_binding","onboarding_package_hash":approved_package["package_hash"],"binding_sha256":binding_sha256})
    if any(approval_receipt.get(key) != value for key,value in expected.items()) or not _authority_receipt_valid(approval_receipt,decision_hash):
        raise OnboardingError("exact authority-bound removal approval receipt is required")
    result = {"schema":"dual-hat-binding-operation/1.0", "operation":"remove", "approved":True, "approval_evidence":dict(approval_receipt), "onboarding_package_hash":approved_package["package_hash"], "binding_sha256":binding_sha256, "owned_paths":[".dual-hat/binding.json"]}
    result["operation_hash"] = canonical_hash(result, omit=("operation_hash",))
    return result


def remove_binding(target: str | Path, operation: Mapping[str, object], *, approved_package: Mapping[str, object], authorized_root: str | Path) -> None:
    root = _authorized_target(authorized_root, target, must_exist=True)
    destination = contained(root, ".dual-hat/binding.json", must_exist=True, kind="file")
    if operation.get("schema") != "dual-hat-binding-operation/1.0" or operation.get("operation") != "remove" or operation.get("approved") is not True or operation.get("operation_hash") != canonical_hash(operation, omit=("operation_hash",)):
        raise OnboardingError("approved removal operation is absent or stale")
    if operation.get("onboarding_package_hash") != approved_package.get("package_hash") or operation.get("owned_paths") != [".dual-hat/binding.json"] or operation.get("binding_sha256") != hashlib.sha256(destination.read_bytes()).hexdigest().upper():
        raise OnboardingError("removal operation is not bound to the approved package and current binding")
    payload = json.loads(destination.read_text(encoding="utf-8"))
    if payload.get("schema") != "dual-hat-project-binding/1.0" or payload.get("project_footprint") != [".dual-hat/binding.json"]:
        raise OnboardingError("refusing removal without exact manifest ownership")
    destination.unlink()
    try:
        destination.parent.rmdir()
    except OSError:
        pass


def create_greenfield_repository(target: str | Path, *, approved_package: Mapping[str, object], authorized_root: str | Path) -> Path:
    destination = _authorized_target(authorized_root, target, must_exist=False)
    if destination.exists() or approved_package.get("state") != "approved_for_binding" or approved_package.get("repository_scenario") != "no_repository" or approved_package.get("package_hash") != canonical_hash(approved_package):
        raise OnboardingError("approved no-repository package is required for greenfield creation")
    destination.mkdir()
    return destination
