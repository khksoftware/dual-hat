"""Validate a platform profile without making the core depend on it.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import ast
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Mapping

GUARANTEES = {"monitoring_not_weakened", "recovery_not_weakened", "security_not_weakened", "validation_not_weakened", "evidence_not_weakened"}
GAP_KINDS = {"unsupported_capability", "unavailable_capability", "misconfigured_capability", "temporarily_degraded_capability", "permission_or_access_failure", "security_or_rights_restriction", "tool_defect", "profile_defect", "core_contract_ambiguity"}
CORE_MANDATORY_CAPABILITIES = {"sealed_work_order", "repository_state_preservation", "explicit_user_and_architecture_reporting", "resumable_handoff", "detached_validation", "governed_publication", "quality_rule_discovery", "independent_deep_review", "canonical_path_containment", "network_policy_validation", "rights_readiness_validation", "binary_secret_gate", "committed_tree_release_binding", "transactional_writes", "post_run_residue_inspection"}
CAPABILITY_PROOF_MARKER = "DUAL_HAT_CAPABILITY_PROOFS"
KNOWN_ENVIRONMENT_LIMITATION_REQUIRED_FIELDS = {"id", "trap", "presents_as", "detect", "safe_alternative", "established"}

def known_environment_limitation_failures(entries: object) -> tuple[str, ...]:
    """Enforce the per-entry contract schemas/platform-profile.schema.json declares
    for known_environment_limitations: an object naming a stable id, the trap,
    how it presents, how to detect it, the safe alternative, and when it was
    established, plus an optional remedy. A bare string, or an object missing
    one of the six, carries none of what the next reader needs to act on the
    trap without re-discovering it themselves."""
    if not isinstance(entries, list): return ("known_environment_limitations is not a list",)
    failures: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            failures.append(f"known_environment_limitations[{index}] is not an object"); continue
        missing = KNOWN_ENVIRONMENT_LIMITATION_REQUIRED_FIELDS - set(entry)
        if missing: failures.append(f"known_environment_limitations[{index}] is missing required field(s): {sorted(missing)}")
        for field in KNOWN_ENVIRONMENT_LIMITATION_REQUIRED_FIELDS & set(entry):
            if not isinstance(entry[field], str) or not entry[field].strip():
                failures.append(f"known_environment_limitations[{index}].{field} must be a non-empty string")
        if "remedy" in entry and (not isinstance(entry["remedy"], str) or not entry["remedy"].strip()):
            failures.append(f"known_environment_limitations[{index}].remedy must be a non-empty string when present")
    return tuple(failures)

def capability_evidence_digest(profile: Mapping[str, object]) -> str:
    payload = profile.get("capability_evidence", {})
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()

def platform_profile_digest(profile: Mapping[str, object]) -> str:
    encoded = (json.dumps(profile, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()

def evidence_content_sha256(path: Path) -> str:
    """Hash text evidence canonically across governed Git checkout EOL policies."""
    data = path.read_bytes()
    try: canonical = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    except UnicodeDecodeError: canonical = data
    return hashlib.sha256(canonical).hexdigest().upper()

def canonical_test_output(output: str) -> str:
    normalized = output.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"(?m)^(Ran\s+\d+\s+tests?\s+in\s+)[0-9.]+s\s*$", r"\1<duration>s", normalized)

def unittest_output_counts(output: str) -> dict[str, int]:
    ran = re.findall(r"(?m)^Ran\s+(\d+)\s+tests?\s+in\s+(?:[0-9.]+|<duration>)s\s*$", output)
    if len(ran) != 1: raise ValueError("unittest output lacks exactly one execution summary")
    def count(name: str) -> int:
        match = re.search(rf"{name}=(\d+)", output)
        return int(match.group(1)) if match else 0
    executed=int(ran[0]); failed=count("failures"); errored=count("errors"); skipped=count("skipped")
    return {"discovered":executed,"executed":executed,"passed":executed-failed-errored-skipped,"failed":failed,"errored":errored,"skipped":skipped}

def _inside_git_work_tree(root: Path) -> bool:
    """Whether `root` sits inside a git work tree, decided STRUCTURALLY.

    Deliberately not decided by matching git's error text: that is localized and has
    changed wording between versions, so a text match would fail open on some machines
    and closed on others. Walking for `.git` answers the same question and cannot drift.
    `.git` is a directory in an ordinary clone and a FILE in a linked worktree, so this
    tests existence rather than directory-ness.
    """
    for candidate in (root, *root.parents):
        if (candidate / ".git").exists():
            return True
    return False

def governed_repository_digest(root: Path, excluded_relative: str) -> str:
    excluded=Path(excluded_relative).as_posix(); records=[]
    # A release package extracted into a plain directory is NOT a broken repository. The
    # rule below -- fail rather than substitute when git cannot answer -- was written for a
    # genuinely broken repository, and it is UNCHANGED for that case: a root that IS inside
    # a work tree still raises on any git failure. Only the no-repository context is
    # separated out here, because conflating the two made the release self-test raise on
    # four operating-mode cases in exactly the context that self-test exists to exercise.
    # It returns the digest of an empty inventory -- the honest answer to "what governed
    # evidence is tracked here", which is none -- and never a walk over whatever files
    # happen to be on disk, which is the substitution the rule below exists to prevent.
    if not _inside_git_work_tree(root):
        encoded=(json.dumps([],sort_keys=True,separators=(",",":"))+"\n").encode("utf-8")
        return hashlib.sha256(encoded).hexdigest().upper()
    result=subprocess.run(("git","ls-files","--cached","--others","--exclude-standard","-z"),cwd=root,capture_output=True)
    if result.returncode:
        stderr=result.stderr.decode("utf-8",errors="replace").strip()
        raise ValueError(f"governed evidence inventory is unavailable: git ls-files failed (exit {result.returncode}): {stderr}")
    relative_paths=[raw.decode("utf-8").replace("\\","/") for raw in result.stdout.split(b"\0") if raw]
    for relative in relative_paths:
        if relative == excluded: continue
        raw_path=root/relative
        if raw_path.exists() and (raw_path.is_symlink() or bool(getattr(raw_path.lstat(),"st_file_attributes",0)&getattr(stat,"FILE_ATTRIBUTE_REPARSE_POINT",0x400))): raise ValueError("governed evidence inventory contains linked content")
        path=raw_path.resolve()
        try: path.relative_to(root)
        except ValueError as exc: raise ValueError("governed evidence inventory escapes root") from exc
        if not path.exists(): continue  # A tracked deletion is part of the candidate by absence.
        if path.is_symlink() or not path.is_file(): raise ValueError("governed evidence inventory contains unavailable or linked content")
        records.append({"path":relative,"sha256":evidence_content_sha256(path)})
    encoded=(json.dumps(sorted(records,key=lambda row:row["path"]),sort_keys=True,separators=(",",":"))+"\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()

def verified_capability_evidence_digest(verified: Mapping[str, list[Mapping[str, object]]]) -> str:
    canonical = {requirement: sorted(rows, key=lambda row: str(row["locator"])) for requirement, rows in sorted(verified.items())}
    encoded = (json.dumps(canonical, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()

def declared_capability_proofs(path: Path) -> frozenset[str]:
    """Read explicit proof ownership without importing or executing a test module."""
    try: tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError): return frozenset()
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)): continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == CAPABILITY_PROOF_MARKER for target in targets): continue
        try: value = ast.literal_eval(node.value)
        except (ValueError, TypeError): return frozenset()
        if isinstance(value, (set, frozenset, list, tuple)) and all(isinstance(row, str) for row in value): return frozenset(value)
        return frozenset()
    return frozenset()

def validate_profile(profile: Mapping[str, object], core_version: str) -> tuple[str, ...]:
    failures: list[str] = []
    if profile.get("dual_hat_core_version") != core_version: failures.append("platform profile is incompatible with active Dual Hat core")
    if profile.get("precedence") != "dual_hat_core_governs_profile_specializes": failures.append("platform profile precedence is invalid")
    guarantees = profile.get("guarantees", {})
    if not isinstance(guarantees, Mapping) or any(guarantees.get(key) is not True for key in GUARANTEES): failures.append("platform profile weakens or omits a core guarantee")
    for field in ("profile_id", "profile_version", "supported_configuration", "applicability", "mandatory_capabilities", "capability_evidence", "capability_evidence_rationale", "preflight_artifact", "monitoring", "temporary_workspace", "detached_validation", "authentication", "recovery", "architecture_boundary_review", "validation"):
        if not profile.get(field): failures.append(f"platform profile lacks {field}")
    capabilities = profile.get("mandatory_capabilities", {})
    if isinstance(capabilities, Mapping):
        if CORE_MANDATORY_CAPABILITIES - set(capabilities): failures.append("platform profile omits mandatory Dual Hat core capabilities")
        if any(value is not True for value in capabilities.values()): failures.append("platform profile marks a mandatory core capability unsupported")
    evidence = profile.get("capability_evidence", {})
    if not isinstance(evidence, Mapping) or not isinstance(capabilities, Mapping) or set(evidence) != set(capabilities):
        failures.append("platform capability evidence does not cover every mandatory capability")
    elif any(not isinstance(rows, list) or not rows or any(not isinstance(row, str) or not re.fullmatch(r"(?:test|evidence):[^\s].*", row) for row in rows) for rows in evidence.values()):
        failures.append("platform capability evidence is empty or invalid")
    rationale = profile.get("capability_evidence_rationale", {})
    if (not isinstance(rationale, Mapping) or not isinstance(capabilities, Mapping) or set(rationale) != set(capabilities)
            or any(not isinstance(value, str) or not value.strip() for value in rationale.values())):
        failures.append("platform capability evidence lacks explicit semantic ownership rationale")
    failures.extend(known_environment_limitation_failures(profile.get("known_environment_limitations", [])))
    return tuple(failures)


def runtime_profile_failures(profile: Mapping[str, object]) -> tuple[str, ...]:
    """Attest stable host properties available to the active adapter."""
    configuration=profile.get("supported_configuration",{})
    if not isinstance(configuration,Mapping): return ("platform supported configuration is invalid",)
    declared_os=configuration.get("operating_system")
    if declared_os is not None and (not isinstance(declared_os,str) or declared_os.casefold()!=platform.system().casefold()):
        return ("active runtime operating system does not match the selected platform profile",)
    declared_python=configuration.get("python_implementation")
    if declared_python is not None and (not isinstance(declared_python,str) or declared_python.casefold()!=platform.python_implementation().casefold()):
        return ("active Python runtime does not match the selected platform profile",)
    return ()

def _verify_evidence(profile: Mapping[str, object], required: Iterable[str], evidence_root: str | Path | None,
                     test_receipts: Mapping[str, object] | None) -> tuple[dict[str, list[dict[str, object]]], list[str]]:
    verified: dict[str, list[dict[str, object]]] = {}
    failures: list[str] = []
    root = Path(evidence_root).resolve(strict=True) if evidence_root is not None else None
    evidence = profile.get("capability_evidence", {})
    for requirement in required:
        rows = evidence.get(requirement, ()) if isinstance(evidence, Mapping) else ()
        records = []
        for locator in rows if isinstance(rows, list) else ():
            kind, _, relative = str(locator).partition(":")
            if kind not in {"test", "evidence"} or not relative or root is None:
                failures.append(f"mandatory capability evidence cannot be verified: {requirement}:{locator}"); continue
            raw = root / relative
            current = root
            linked = False
            for part in Path(relative).parts:
                current = current / part
                if current.exists() and (
                    current.is_symlink()
                    or bool(
                        getattr(current.lstat(), "st_file_attributes", 0)
                        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
                    )
                ):
                    linked = True
                    break
            candidate = raw.resolve()
            try: candidate.relative_to(root)
            except ValueError: failures.append(f"mandatory capability evidence escapes root: {requirement}:{locator}"); continue
            if linked or not candidate.is_file():
                failures.append(f"mandatory capability evidence is unavailable: {requirement}:{locator}"); continue
            evidence_sha = evidence_content_sha256(candidate)
            if kind == "test":
                if requirement not in declared_capability_proofs(candidate):
                    failures.append(f"mandatory test evidence is semantically misbound: {requirement}:{locator}"); continue
                receipt = test_receipts.get(str(locator)) if isinstance(test_receipts, Mapping) else None
                receipt_fields = {"schema","locator","command","interpreter_path","interpreter_sha256","evidence_sha256","governed_repository_sha256","returncode","discovered","executed","passed","failed","errored","skipped","output_normalization","output","output_sha256"}
                counts = tuple(receipt.get(key) for key in ("discovered","executed","passed","failed","errored","skipped")) if isinstance(receipt, Mapping) else ()
                try:
                    expected_repository_sha=governed_repository_digest(root,str(profile.get("preflight_artifact","")))
                    output_counts=unittest_output_counts(str(receipt.get("output",""))) if isinstance(receipt,Mapping) else {}
                except ValueError: expected_repository_sha=""; output_counts={}
                if (not isinstance(receipt, Mapping) or set(receipt) != receipt_fields or receipt.get("schema") != "dual-hat-capability-test-receipt/1.2"
                        or receipt.get("locator") != locator or receipt.get("evidence_sha256") != evidence_sha
                        or receipt.get("governed_repository_sha256") != expected_repository_sha
                        or receipt.get("returncode") != 0 or len(counts) != 6
                        or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in counts)
                        or receipt["discovered"] < 1 or receipt["executed"] != receipt["discovered"]
                        or receipt["passed"] + receipt["failed"] + receipt["errored"] + receipt["skipped"] != receipt["executed"]
                        or receipt["failed"] != 0 or receipt["errored"] != 0
                        or receipt.get("output_normalization") != "unittest_duration_redacted_v1"
                        or not isinstance(receipt.get("output"),str) or canonical_test_output(receipt["output"]) != receipt["output"]
                        or any(receipt.get(key) != value for key,value in output_counts.items())
                        or hashlib.sha256(str(receipt.get("output","")).encode("utf-8")).hexdigest().upper() != receipt.get("output_sha256")
                        or not re.fullmatch(r"[A-F0-9]{64}", str(receipt.get("output_sha256", "")))):
                    failures.append(f"mandatory test evidence lacks a typed passing receipt: {requirement}:{locator}"); continue
                interpreter = Path(str(receipt.get("interpreter_path", "")))
                try: interpreter = interpreter.resolve(strict=True)
                except OSError: failures.append(f"mandatory test receipt interpreter is unavailable: {requirement}:{locator}"); continue
                if (not os.path.samefile(interpreter, Path(sys.executable).resolve())
                        or hashlib.sha256(interpreter.read_bytes()).hexdigest().upper() != receipt.get("interpreter_sha256")
                        or receipt.get("command") != [interpreter.as_posix(), "-B", "-m", "unittest", "discover", "-s", Path(relative).parent.as_posix(), "-p", Path(relative).name]):
                    failures.append(f"mandatory test receipt interpreter or command is not approved: {requirement}:{locator}"); continue
                records.append({"locator":str(locator),"sha256":evidence_sha,"receipt":dict(receipt)})
            else:
                try: semantic = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError): failures.append(f"mandatory semantic evidence is not typed JSON: {requirement}:{locator}"); continue
                fields={"schema","capability","result","source_locator","source_sha256"}
                if not isinstance(semantic,Mapping) or set(semantic)!=fields or semantic.get("schema")!="dual-hat-capability-evidence/1.0" or semantic.get("capability")!=requirement or semantic.get("result")!="recorded":
                    failures.append(f"mandatory semantic evidence contract is invalid: {requirement}:{locator}"); continue
                source=root/str(semantic.get("source_locator","")); source=source.resolve()
                try: source.relative_to(root)
                except ValueError: failures.append(f"mandatory semantic evidence source escapes root: {requirement}:{locator}"); continue
                if not source.is_file() or evidence_content_sha256(source)!=semantic.get("source_sha256"):
                    failures.append(f"mandatory semantic evidence source binding is invalid: {requirement}:{locator}"); continue
                records.append({"locator":str(locator),"sha256":evidence_sha,"semantic_evidence":dict(semantic)})
        if records: verified[requirement] = records
    return verified, failures

def capability_preflight(profile: Mapping[str, object] | None, required: Iterable[str], core_version: str,
                         evidence_root: str | Path | None = None,
                         test_receipts: Mapping[str, object] | None = None) -> dict[str, object]:
    required_set = tuple(dict.fromkeys(required))
    failures = ["no conformant platform profile selected"] if profile is None else [*validate_profile(profile, core_version),*runtime_profile_failures(profile)]
    capabilities = {} if profile is None else profile.get("mandatory_capabilities", {})
    if not isinstance(capabilities, Mapping): failures.append("mandatory capability declaration is invalid"); capabilities = {}
    evidence = {} if profile is None else profile.get("capability_evidence", {})
    for requirement in required_set:
        if capabilities.get(requirement) is not True: failures.append(f"mandatory capability unavailable: {requirement}")
        if not isinstance(evidence, Mapping) or not evidence.get(requirement): failures.append(f"mandatory capability lacks executable evidence: {requirement}")
    uncertainties = [] if profile is None else profile.get("uncertainties_requiring_architecture_review", [])
    degraded = [] if profile is None else profile.get("degraded_features", [])
    unavailable = [] if profile is None else profile.get("unavailable_external_services", [])
    if uncertainties: failures.append("platform capability uncertainty requires Architecture review")
    if any(item in required_set for item in degraded): failures.append("a mandatory capability is degraded")
    if any(item in required_set for item in unavailable): failures.append("a mandatory external service is unavailable")
    verified, evidence_failures = _verify_evidence(profile, required_set, evidence_root, test_receipts) if profile is not None else ({}, [])
    failures.extend(evidence_failures)
    if set(verified) != set(required_set): failures.append("verified capability evidence does not cover every required capability")
    unique = tuple(dict.fromkeys(failures))
    return {"execution_authorized": not unique, "hard_stop": bool(unique), "required": list(required_set),
            "supported_mandatory_requirements": list(required_set) if not unique else [],
            "verified_capability_evidence": verified,
            "capability_test_receipts": dict(test_receipts or {}),
            "capability_evidence_verified": not evidence_failures and set(verified) == set(required_set),
            "runtime_profile_verified": profile is not None and not runtime_profile_failures(profile),
            "result": "pass" if not unique else "hard_stop",
            "capability_evidence_sha256": capability_evidence_digest(profile) if profile is not None else "",
            "verified_capability_evidence_sha256": verified_capability_evidence_digest(verified),
            "platform_profile_sha256": platform_profile_digest(profile) if profile is not None else "",
            "failures": unique}

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
