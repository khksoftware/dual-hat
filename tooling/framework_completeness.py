"""Validate semantic ownership for the standalone Dual Hat framework.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from release_artifacts import is_release_product


REQUIRED_DOMAIN_FIELDS = {
    "id", "responsibilities", "owner", "implementation_nature", "support",
    "documentation", "validation", "profile_relationship",
}
REQUIRED_DOMAIN_IDS = {
    "architecture", "engineering_execution", "planning", "validation",
    "repository_governance", "sessions_and_continuity",
    "publication_and_closure", "documentation_and_help",
}
REQUIRED_GUIDES = {
    "governance/ARCHITECTURE_OFFICE_GUIDE.md",
    "governance/ENGINEERING_AGENT_GUIDE.md",
    "sessions/TASK_CONTEXT_RETRIEVAL.md",
    "reference/COMMAND_REFERENCE.md",
}
DOMAIN_OPERATIONAL_SUFFIXES = {
    "engineering_execution": (".schema.json", "templates/WORK_ORDER.md"),
    "planning": (".schema.json", "templates/ROADMAP.md"),
    "validation": (".schema.json", "templates/PHASE_HEALTH_REVIEW.md"),
    "repository_governance": ("templates/CANONICAL_DOMAIN_INDEX.md",),
    "sessions_and_continuity": (".schema.json", "templates/CURRENT_HANDOVER.json"),
    "publication_and_closure": ("templates/EXIT_REPORT.md",),
}
FORBIDDEN_PRODUCT_PATTERNS = (
    re.compile(r"Phase\s+15"),
    re.compile(r"workspace/(?:alex|user|author)[^/]*/", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]"),
)
RELEASE_CONTROL_PATHS = {
    ".dual-hat-release/content-manifest.json",
    ".dual-hat-release/SHA256SUMS",
}


def validate_framework(root: Path) -> tuple[str, ...]:
    root = root.resolve()
    failures: list[str] = []
    inventory_path = root / "repository/FRAMEWORK_CAPABILITY_INVENTORY.json"
    if not inventory_path.is_file():
        return ("framework capability inventory is missing",)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    domains = inventory.get("domains")
    if not isinstance(domains, list) or not domains:
        return ("framework capability inventory has no domains",)

    domain_ids: set[str] = set()
    responsibilities: set[str] = set()
    referenced: set[str] = {"repository/FRAMEWORK_CAPABILITY_INVENTORY.json"}
    for index, domain in enumerate(domains):
        if not isinstance(domain, dict):
            failures.append(f"domain {index} is not an object")
            continue
        missing = REQUIRED_DOMAIN_FIELDS - set(domain)
        if missing:
            failures.append(f"domain {index} missing fields: {sorted(missing)}")
            continue
        domain_id = str(domain["id"])
        if domain_id in domain_ids:
            failures.append(f"duplicate domain id: {domain_id}")
        domain_ids.add(domain_id)
        rows = domain["responsibilities"]
        if not isinstance(rows, list) or not rows:
            failures.append(f"domain {domain_id} has no responsibilities")
        else:
            for value in rows:
                key = str(value).casefold()
                if key in responsibilities:
                    failures.append(f"responsibility has multiple owners: {value}")
                responsibilities.add(key)
        for field in ("owner", "documentation", "validation"):
            referenced.add(str(domain[field]))
        if not isinstance(domain["support"], list):
            failures.append(f"domain {domain_id} support must be an array")
        else:
            support = [str(path) for path in domain["support"]]
            if not support:
                failures.append(f"domain {domain_id} has no operational support")
            referenced.update(support)
            for required in DOMAIN_OPERATIONAL_SUFFIXES.get(domain_id, ()):
                if required.startswith("."):
                    if not any(path.endswith(required) for path in support):
                        failures.append(f"domain {domain_id} lacks required support type: {required}")
                elif required not in support:
                    failures.append(f"domain {domain_id} lacks required support: {required}")

    missing_domains = REQUIRED_DOMAIN_IDS - domain_ids
    extra_domains = domain_ids - REQUIRED_DOMAIN_IDS
    if missing_domains or extra_domains:
        failures.append(
            f"framework domain set mismatch; missing={sorted(missing_domains)}; "
            f"unexpected={sorted(extra_domains)}"
        )
    if len(responsibilities) < 100:
        failures.append("framework responsibility inventory is materially incomplete")
    referenced.update(REQUIRED_GUIDES)

    for relative in sorted(referenced):
        path = root / relative
        if not path.is_file():
            failures.append(f"declared framework owner/support is missing: {relative}")
        elif path.suffix.lower() in {".md", ".py"} and path.stat().st_size < 160:
            failures.append(f"declared framework owner/support is not substantive: {relative}")

    source_map = root / "export/EXPORT_SOURCES.json"
    if source_map.is_file():
        payload = json.loads(source_map.read_text(encoding="utf-8"))
        controls = {"export/EXPORT_READINESS.json", "export/EXPORT_SOURCES.json"}
        actual = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
            and path.relative_to(root).as_posix() not in controls | RELEASE_CONTROL_PATHS
            and not is_release_product(path.relative_to(root).as_posix())
        }
        declared = set(payload.get("included", ()))
        if actual != declared:
            failures.append(
                "framework export classification mismatch; "
                f"unclassified={sorted(actual - declared)}; stale={sorted(declared - actual)}"
            )

    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {"__pycache__", ".git"} for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        if is_release_product(relative):
            continue
        if path.suffix.lower() not in {".md", ".py", ".json", ".jsonl"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if relative in RELEASE_CONTROL_PATHS or relative == "release/PUBLICATION_AND_DRIFT.md":
            # A derived publication may identify its current canonical source;
            # this generated receipt is not framework authority.
            continue
        for pattern in FORBIDDEN_PRODUCT_PATTERNS:
            if pattern.search(text):
                failures.append(f"product-specific leakage in {relative}: {pattern.pattern}")
    return tuple(sorted(set(failures)))
