"""Validate semantic ownership for the standalone Dual Hat framework.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import NamedTuple

from release_artifacts import is_release_product
from publication_ownership import standalone_owned


GITIGNORE_FILENAME = ".gitignore"
REPOSITORY_METADATA_NAME = ".git"


class _IgnoreRule(NamedTuple):
    """One parsed ignore pattern, bound to the tree region it governs.

    ``scope`` is the root-relative directory prefix the rule applies to (empty
    for a rule that governs the whole tree). ``offset`` is prepended to the
    root-relative path to re-express it relative to the directory the ignore
    file itself sits in, which is how an ignore file ABOVE ``root`` -- the one
    that ignores, say, ``*.egg-info/`` for the whole repository -- still reaches
    content inside ``root``.
    """

    matcher: re.Pattern[str]
    directory_only: bool
    negated: bool
    scope: str
    offset: str


def _translate(pattern: str) -> str:
    """Translate one gitignore glob into a regular-expression fragment."""
    index = 0
    length = len(pattern)
    parts: list[str] = []
    while index < length:
        char = pattern[index]
        if pattern.startswith("**/", index):
            parts.append("(?:[^/]+/)*")
            index += 3
        elif pattern.startswith("**", index):
            parts.append(".*")
            index += 2
        elif char == "*":
            parts.append("[^/]*")
            index += 1
        elif char == "?":
            parts.append("[^/]")
            index += 1
        elif char == "[":
            close = index + 1
            if close < length and pattern[close] in "!^":
                close += 1
            if close < length and pattern[close] == "]":
                close += 1
            while close < length and pattern[close] != "]":
                close += 1
            if close >= length:
                parts.append(re.escape(char))
                index += 1
            else:
                body = pattern[index + 1:close]
                parts.append("[" + ("^" + body[1:] if body.startswith("!") else body) + "]")
                index = close + 1
        else:
            parts.append(re.escape(char))
            index += 1
    return "".join(parts)


def _parse_ignore_file(path: Path, *, scope: str, offset: str) -> list[_IgnoreRule]:
    rules: list[_IgnoreRule] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return rules
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        negated = line.startswith("!")
        if negated:
            line = line[1:]
        if line.startswith("\\"):
            line = line[1:]
        directory_only = line.endswith("/")
        if directory_only:
            line = line[:-1]
        if not line:
            continue
        anchored = "/" in line
        if line.startswith("/"):
            line = line[1:]
        body = _translate(line)
        expression = "^" + (body if anchored else "(?:[^/]+/)*" + body) + "$"
        rules.append(_IgnoreRule(re.compile(expression), directory_only, negated, scope, offset))
    return rules


def _ignore_rules(root: Path) -> list[_IgnoreRule]:
    """Every ignore rule that governs content under ``root``.

    Read out of the repository's own ignore files rather than restated here, so
    this cannot drift from what the repository actually ignores. Ancestor ignore
    files are consulted up to and including the work-tree root, because a
    subdirectory of a larger repository (Dual Hat vendored inside a product
    tree) inherits that repository's ignores; a ``root`` that is itself a
    work-tree root inherits nothing. A tree with no ignore file anywhere -- an
    unpacked release package, for instance -- simply yields no rules.
    """
    rules: list[_IgnoreRule] = []
    ancestors: list[Path] = []
    if not (root / REPOSITORY_METADATA_NAME).exists():
        current = root.parent
        while True:
            ancestors.append(current)
            if (current / REPOSITORY_METADATA_NAME).exists() or current.parent == current:
                break
            current = current.parent
        if not (ancestors and (ancestors[-1] / REPOSITORY_METADATA_NAME).exists()):
            ancestors = []
    for ancestor in reversed(ancestors):
        rules.extend(_parse_ignore_file(
            ancestor / GITIGNORE_FILENAME,
            scope="",
            offset=root.relative_to(ancestor).as_posix() + "/",
        ))
    rules.extend(_parse_ignore_file(root / GITIGNORE_FILENAME, scope="", offset=""))
    return rules


def _is_ignored(relative: str, directory: bool, rules: list[_IgnoreRule]) -> bool:
    ignored = False
    for rule in rules:
        if rule.scope and not relative.startswith(rule.scope):
            continue
        if rule.directory_only and not directory:
            continue
        if rule.matcher.match(rule.offset + relative[len(rule.scope):]):
            ignored = not rule.negated
    return ignored


def repository_content_files(root: Path) -> tuple[Path, ...]:
    """Every file under ``root`` that the repository's own ignore state keeps.

    Both walks below share this one function. They used to carry a literal
    exclusion list each and had ALREADY drifted apart from one another -- the
    export-classification walk excluded only ``__pycache__``, the leakage walk
    excluded ``__pycache__`` and ``.git`` -- so any other ignored residue inside
    the tree (a ``.pytest_cache``, a virtualenv, an egg-info, the generated
    agent-skill copies) was reported as unowned content under an error naming
    the export allowlist rather than the artifact that caused it. A third
    literal list would be the same defect a third time, so the exclusion is
    derived from the ignore files instead of restated in this module.

    ``.git`` itself is skipped by name rather than by rule because it is the
    repository's own metadata: git never reports it as either ignored or
    content, so no ignore file mentions it.
    """
    root = root.resolve()
    rules = _ignore_rules(root)
    collected: list[Path] = []
    for directory, names, files in os.walk(root):
        here = Path(directory)
        relative = here.relative_to(root).as_posix()
        prefix = "" if relative in {"", "."} else relative + "/"
        if prefix and (here / GITIGNORE_FILENAME).is_file():
            rules.extend(_parse_ignore_file(here / GITIGNORE_FILENAME, scope=prefix, offset=""))
        names[:] = sorted(
            name for name in names
            if name != REPOSITORY_METADATA_NAME and not _is_ignored(prefix + name, True, rules)
        )
        collected.extend(
            here / name for name in sorted(files)
            if name != REPOSITORY_METADATA_NAME and not _is_ignored(prefix + name, False, rules)
        )
    return tuple(collected)


REQUIRED_DOMAIN_FIELDS = {
    "id", "responsibilities", "owner", "implementation_nature", "support",
    "documentation", "validation", "profile_relationship",
}
REQUIRED_DOMAIN_IDS = {
    "architecture", "engineering_execution", "planning", "validation",
    "repository_governance", "sessions_and_continuity",
    "publication_and_closure", "repository_and_product_onboarding",
    "model_tiers_and_runtime_binding", "documentation_and_help",
}
REQUIRED_GUIDES = {
    "architecture/OPERATING_MODES.md",
    "governance/ARCHITECTURE_OFFICE_GUIDE.md",
    "governance/ENGINEERING_AGENT_GUIDE.md",
    "governance/PLATFORM_PROFILE_CONTRACT.md",
    "governance/ROLE_TRANSITIONS.md",
    "guides/OPERATING_MODES.md",
    "process/WORK_ITEM_LIFECYCLE.md",
    "sessions/TASK_CONTEXT_RETRIEVAL.md",
    "guides/COMMAND_REFERENCE.md",
}
REQUIRED_PLANNING_SUPPORT = {
    "schemas/planning-backlog.schema.json",
    "schemas/future-work.schema.json",
    "schemas/planning-history-event.schema.json",
    "templates/PLANNING_BACKLOG.json",
    "templates/FUTURE_WORK_REGISTRY.json",
    "templates/PLANNING_HISTORY.jsonl",
    "tooling/planning_reconciliation.py",
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
    # Generalized rather than pinned to one incident's exact numbers or
    # names, so the denylist itself carries no fingerprint of a particular
    # past leak or private source tree. A bare "Capability N" is deliberately
    # not added: it is one of Dual Hat's own generic work-item-type examples
    # (see tests/test_operating_modes.py), not a leak signature.
    re.compile(r"\bPhase" + r"\s+\d+\b"),
    # Two path segments after "workspace/" (identity, then a category like
    # projects/global) is what a real leaked data path looks like; a bare
    # single-segment "workspace/" is common, legitimate scaffold boilerplate
    # (see scripts/bootstrap_product.py's generated .gitignore) and must not
    # trip this.
    re.compile("workspace" + r"/[^/\s]+/[^/\s]+/", re.IGNORECASE),
)
# Kept separate from FORBIDDEN_PRODUCT_PATTERNS above (rather than folded
# back into that tuple) because this one pattern, alone among the three, has
# a real exemption below -- test files -- that the other two do not and
# must not gain; a real "Phase N" or leaked workspace/ path is a real leak
# regardless of which file carries it.
FORBIDDEN_ABSOLUTE_PATH_PATTERN = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]")
# Narrow, path-shape-only test-file recognition -- deliberately the same
# shape tooling/repository_hygiene.py's own TEST_FILE_PATH_COMPONENT/
# TEST_FILENAME carve-out already uses for the identical judgment call
# (a synthetic absolute-path-shaped fixture proving a detector's own
# rejection/exemption behavior is not a live path anything resolves), so
# every leakage-adjacent check in this repository agrees on what counts as
# a test file rather than each inventing its own definition. Confirmed
# necessary by a real incident: a real, human-authored export of content
# already live in this repository failed here because this check had no
# way to distinguish tests/test_repository_hygiene.py's own synthetic
# drive-letter-rooted fixture values (proving the sibling detector's own
# rejection behavior) from a genuine leak.
TEST_FILE_PATH_COMPONENT = re.compile(r"(?:^|/)tests?/")
TEST_FILENAME_PATTERN = re.compile(r"(?i)(?:^|/)(?:test_[^/]+|[^/]+_test)\.py$")


def _is_test_file_path(relative_path: str) -> bool:
    return bool(TEST_FILE_PATH_COMPONENT.search(relative_path) or TEST_FILENAME_PATTERN.search(relative_path))


FORBIDDEN_PLATFORM_PATTERNS = (
    re.compile(r"\b(?:Codex|OpenAI|ChatGPT|Windows|PowerShell|GitHub|Gemini)\b", re.IGNORECASE),
    re.compile(r"\bVisual Studio Code\b", re.IGNORECASE),
)
# REPOSITORY_BOUNDARIES.md's dependency-direction invariant: "Dual Hat never
# imports product, engineering, archive, or workspace state." That invariant
# had no mechanical check anywhere in tooling/ or tests/ before this pattern
# was added; it is a real Python import statement (a leading-dots relative
# import counts), not a bare mention of the word, so file-open/path-string
# references to those directories (legitimate when Dual Hat tooling validates
# an external product's own engineering/ layout) do not trip it.
FORBIDDEN_DEPENDENCY_IMPORT_PATTERNS = (
    re.compile(r"^\s*(?:from\s+\.*|import\s+)(?:product|engineering|archive|workspace)\b", re.MULTILINE),
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
            if domain_id == "planning":
                missing_planning = REQUIRED_PLANNING_SUPPORT - set(support)
                if missing_planning:
                    failures.append(f"planning domain lacks lifecycle support: {sorted(missing_planning)}")

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

    content = repository_content_files(root)

    source_map = root / "export/EXPORT_SOURCES.json"
    if source_map.is_file():
        payload = json.loads(source_map.read_text(encoding="utf-8"))
        controls = {"export/EXPORT_READINESS.json", "export/EXPORT_SOURCES.json"}
        actual = {
            path.relative_to(root).as_posix()
            for path in content
            if path.relative_to(root).as_posix() not in controls | RELEASE_CONTROL_PATHS
            and not is_release_product(path.relative_to(root).as_posix())
        }
        declared = set(payload.get("included", ()))
        if actual != declared:
            failures.append(
                "framework export classification mismatch; "
                f"unclassified={sorted(actual - declared)}; stale={sorted(declared - actual)}"
            )

    for path in content:
        relative = path.relative_to(root).as_posix()
        if is_release_product(relative):
            continue
        if path.suffix.lower() not in {".md", ".py", ".json", ".jsonl"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if relative in RELEASE_CONTROL_PATHS:
            continue
        for pattern in FORBIDDEN_PRODUCT_PATTERNS:
            if pattern.search(text):
                failures.append(f"product-specific leakage in {relative}: {pattern.pattern}")
        if FORBIDDEN_ABSOLUTE_PATH_PATTERN.search(text) and not _is_test_file_path(relative):
            failures.append(f"product-specific leakage in {relative}: {FORBIDDEN_ABSOLUTE_PATH_PATTERN.pattern}")
        if path.suffix.lower() == ".py" and relative != "tooling/framework_completeness.py":
            for pattern in FORBIDDEN_DEPENDENCY_IMPORT_PATTERNS:
                if pattern.search(text):
                    failures.append(
                        f"dependency-direction violation in {relative}: Dual Hat imports "
                        f"product/engineering/archive/workspace state ({pattern.pattern})"
                    )
        if relative != "tooling/framework_completeness.py" and not standalone_owned(relative):
            for pattern in FORBIDDEN_PLATFORM_PATTERNS:
                if pattern.search(text):
                    failures.append(f"platform-specific leakage in normative core {relative}: {pattern.pattern}")
    return tuple(sorted(set(failures)))
