"""Repository-hygiene checks for the standalone Dual Hat framework that are
not specific to framework-content leakage (see framework_completeness.py for
that concern) -- currently just GOVERNING_PRINCIPLES.md principle 14's standing
check.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence
import json
import re
import subprocess


def _active_tracked_files(root: Path) -> tuple[Path, ...]:
    """Git-tracked and untracked-but-present files, excluding archive/ trees.

    Mirrors the equivalent helper a consuming product's own repository-
    hygiene tooling may define, so a consuming product's own principle-14
    standing check and this framework's own check agree on what "active
    surface" means.
    """
    git_backed = subprocess.run(
        ("git", "rev-parse", "--is-inside-work-tree"), cwd=root,
        capture_output=True, text=True,
    ).returncode == 0
    if not git_backed:
        return tuple(
            path for path in root.rglob("*")
            if path.is_file() and "archive" not in path.relative_to(root).parts
            and ".git" not in path.relative_to(root).parts
        )
    rows: list[str] = []
    for command in (
        ("git", "ls-files"),
        ("git", "ls-files", "--others", "--exclude-standard"),
    ):
        rows.extend(subprocess.run(command, cwd=root, capture_output=True, text=True, check=True).stdout.splitlines())
    return tuple(
        root / relative for relative in sorted(set(row.replace("\\", "/") for row in rows if row))
        if "archive" not in Path(relative).parts
    )


# GOVERNING_PRINCIPLES.md principle 14: a durable file must never embed an
# absolute local filesystem path used as a live structural pointer or
# self-reference. Scoped to the two concrete shapes principle 14's own incident
# names -- a drive-letter-rooted path and a Unix/WSL home-directory path --
# not every string that merely looks like a path. See a consuming product's
# own repository-hygiene tooling (typically the primary place this
# convention gets enforced day to day) for the fuller design rationale this
# module intentionally mirrors, including why a keyword-based citation
# heuristic was rejected in favor of structural exemptions plus an explicit,
# human-reviewed registry.
WINDOWS_DRIVE_ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/](?!/)[^\s\"'`]*")
UNIX_HOME_ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9_/])/(?:home|Users)/[^\s\"'`]+")
WSL_MOUNTED_DRIVE_ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9_])/mnt/[A-Za-z](?:/[^\s\"'`]*)?")
ABSOLUTE_LOCAL_PATH_PATTERNS = (
    WINDOWS_DRIVE_ABSOLUTE_PATH, UNIX_HOME_ABSOLUTE_PATH, WSL_MOUNTED_DRIVE_ABSOLUTE_PATH,
)

# Same structural, non-live-pointer genres a consuming product's own check
# recognizes: test/fixture files (a deliberately synthetic value proving
# rejection behavior is not a live path anything resolves), JSON Schema
# example/default values (illustrative by genre), a markdown #Lnn
# review-evidence citation (a version-control-hosted permalink convention), and a
# regex pattern definition line (which can legitimately contain these
# substrings as regex source, not a path).
TEST_FILE_PATH_COMPONENT = re.compile(r"(?:^|/)tests?/")
TEST_FILENAME = re.compile(r"(?i)(?:^|/)(?:test_[^/]+|[^/]+_test)\.py$")
SCHEMA_FILENAME = re.compile(r"(?i)\.schema\.json$")
MARKDOWN_LINE_ANCHOR_CITATION = re.compile(r"#L\d+")
REGEX_PATTERN_DEFINITION_LINE = re.compile(r"re\.(?:compile|search|match|fullmatch|findall|finditer|sub|subn)\(")


def _is_exempt_by_file_shape(relative_path: str) -> bool:
    return bool(
        TEST_FILE_PATH_COMPONENT.search(relative_path) or TEST_FILENAME.search(relative_path)
        or SCHEMA_FILENAME.search(relative_path)
    )


def _is_exempt_by_line_shape(relative_path: str, line: str, matched: str) -> bool:
    if Path(relative_path).suffix == ".py" and REGEX_PATTERN_DEFINITION_LINE.search(line):
        return True
    if Path(relative_path).suffix == ".md" and MARKDOWN_LINE_ANCHOR_CITATION.search(matched):
        return True
    return False


ABSOLUTE_LOCAL_PATH_CITATIONS_REGISTRY = "repository/ABSOLUTE_LOCAL_PATH_CITATIONS.json"
ABSOLUTE_LOCAL_PATH_DEFERRED_SCOPE_REGISTRY = "repository/ABSOLUTE_LOCAL_PATH_DEFERRED_SCOPE.json"


def _load_registry_entries(root: Path, registry_relative_path: str) -> tuple[Mapping[str, object], ...]:
    registry_path = root / registry_relative_path
    if not registry_path.is_file():
        return ()
    document = json.loads(registry_path.read_text(encoding="utf-8"))
    return tuple(document.get("entries", ()))


def load_absolute_local_path_citations(repository_root: str | Path) -> tuple[Mapping[str, object], ...]:
    return _load_registry_entries(Path(repository_root).resolve(), ABSOLUTE_LOCAL_PATH_CITATIONS_REGISTRY)


def load_absolute_local_path_deferred_scope(repository_root: str | Path) -> tuple[Mapping[str, object], ...]:
    return _load_registry_entries(Path(repository_root).resolve(), ABSOLUTE_LOCAL_PATH_DEFERRED_SCOPE_REGISTRY)


def validate_no_embedded_absolute_local_paths(
    repository_root: str | Path, *, citations: Sequence[Mapping[str, object]] | None = None,
    deferred_scope: Sequence[Mapping[str, object]] | None = None,
) -> tuple[str, ...]:
    """Fail if active, non-archived tracked content embeds an absolute local
    filesystem path used as a live structural pointer or self-reference
    (GOVERNING_PRINCIPLES.md principle 14), rather than legitimate illustrative/
    historical citation or a factual provenance record.

    A real match either (a) sits in a structurally recognized non-live-
    pointer genre (test/fixture, JSON Schema example, markdown #Lnn evidence
    citation, regex pattern source -- see `_is_exempt_by_file_shape`/
    `_is_exempt_by_line_shape`), (b) is explicitly registered in
    ABSOLUTE_LOCAL_PATH_CITATIONS.json with a human-reviewed rationale
    confirming it IS legitimate, or (c) sits under a path registered in
    ABSOLUTE_LOCAL_PATH_DEFERRED_SCOPE.json, which makes no compliance claim
    and instead records that this check declines to adjudicate that area
    right now -- or, failing all three, it fails closed and is reported for
    human judgment.
    """
    root = Path(repository_root).resolve()
    registry_entries = citations if citations is not None else load_absolute_local_path_citations(root)
    citation_lookup: dict[str, tuple[str, ...]] = {}
    for entry in registry_entries:
        key = str(entry["path"])
        citation_lookup[key] = citation_lookup.get(key, ()) + (str(entry["line_contains"]),)
    deferred_entries = (
        deferred_scope if deferred_scope is not None else load_absolute_local_path_deferred_scope(root)
    )
    deferred_prefixes = tuple(str(entry["path_prefix"]) for entry in deferred_entries)
    active_files = _active_tracked_files(root)
    failures: list[str] = []
    for path in active_files:
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in {ABSOLUTE_LOCAL_PATH_CITATIONS_REGISTRY, ABSOLUTE_LOCAL_PATH_DEFERRED_SCOPE_REGISTRY}:
            continue
        if any(relative.startswith(prefix) for prefix in deferred_prefixes):
            continue
        if _is_exempt_by_file_shape(relative):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        needles = citation_lookup.get(relative, ())
        for line_number, line in enumerate(content.splitlines(), start=1):
            matches = [
                match.group(0) for pattern in ABSOLUTE_LOCAL_PATH_PATTERNS for match in pattern.finditer(line)
            ]
            if not matches:
                continue
            if any(needle in line for needle in needles):
                continue
            for matched in matches:
                if _is_exempt_by_line_shape(relative, line, matched):
                    continue
                failures.append(
                    f"{relative}:{line_number}: embeds an absolute local filesystem path "
                    f"outside principle 14's citation/provenance exemption: {matched!r}"
                )
    return tuple(dict.fromkeys(failures))
