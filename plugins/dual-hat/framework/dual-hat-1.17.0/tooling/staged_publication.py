# SPDX-License-Identifier: Apache-2.0
"""Fail-closed staging and committed-tree checks for governed publications."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

sys.dont_write_bytecode = True

from release_artifacts import is_release_product
from content_security import ContentSecurityError, inspect_content_set
from path_containment import ContainmentError, contained, is_reparse


MANIFEST = ".dual-hat/export-manifest.json"
MARKER = ".dual-hat/published-state.json"
CONTROLS = {MANIFEST, MARKER}
FORBIDDEN_DIRECTORIES = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".nox", "node_modules", "dist", "build", "target",
}
FORBIDDEN_FILES = {".coverage", ".DS_Store", "Thumbs.db"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".class"}
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[opurs]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{12,}", re.I),
)


class PublicationValidationError(RuntimeError):
    """Raised when publication input is not exactly governed and safe."""


def _git(root: Path, *args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ("git", *args), cwd=root, check=True, capture_output=True,
        text=not binary,
    )
    return result.stdout if not binary else result.stdout


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _json_bytes(data: bytes, label: str) -> dict:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicationValidationError(f"invalid UTF-8 JSON in {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise PublicationValidationError(f"{label} must contain a JSON object")
    return value


def _records(manifest: dict) -> list[dict]:
    records = manifest.get("content_files", manifest.get("files"))
    if not isinstance(records, list) or not records:
        raise PublicationValidationError("publication manifest has no content records")
    if any(not isinstance(row, dict) or not isinstance(row.get("path"), str) for row in records):
        raise PublicationValidationError("publication manifest has an invalid content record")
    return records


def _owned(manifest: dict) -> set[str]:
    return {str(row["path"]) for row in _records(manifest)} | CONTROLS


def _forbidden(path: str) -> bool:
    parts = Path(path).parts
    name = parts[-1] if parts else path
    return (
        any(part in FORBIDDEN_DIRECTORIES for part in parts)
        or name in FORBIDDEN_FILES
        or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES
        or re.search(r"\.py[cod]$", name, re.I) is not None
    )


def _validate_controls(manifest_bytes: bytes, marker_bytes: bytes) -> tuple[dict, set[str]]:
    manifest = _json_bytes(manifest_bytes, MANIFEST)
    marker = _json_bytes(marker_bytes, MARKER)
    if marker.get("manifest_sha256") != _sha(manifest_bytes):
        raise PublicationValidationError("published-state marker does not bind the manifest")
    if marker.get("tree_sha256") != manifest.get("tree_sha256"):
        raise PublicationValidationError("published-state marker and manifest tree identities differ")
    owned = _owned(manifest)
    forbidden = sorted(path for path in owned if _forbidden(path))
    if forbidden:
        raise PublicationValidationError(f"manifest owns forbidden generated artifacts: {forbidden}")
    return manifest, owned


def _filesystem_files(root: Path) -> set[str]:
    files: set[str] = set()
    for current, directories, names in os.walk(root):
        directories[:] = [name for name in directories if name != ".git"]
        base = Path(current)
        for name in names:
            relative = (base / name).relative_to(root).as_posix()
            if not is_release_product(relative):
                files.add(relative)
    return files


def clean_generated_python_caches(root: Path) -> list[str]:
    """Remove only generated Python cache artifacts contained by ``root``."""

    unresolved_root = root.absolute()
    if is_reparse(unresolved_root):
        raise PublicationValidationError(
            "publication root is a symlink or reparse point"
        )
    root = unresolved_root.resolve(strict=True)
    cleaned: list[str] = []
    cache_artifacts: list[Path] = []
    cache_directories: list[Path] = []
    linked_or_reparse: list[str] = []
    for current, directories, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        if is_reparse(current_path):
            linked_or_reparse.append(current_path.relative_to(root).as_posix())
            directories[:] = []
            continue
        current_path.resolve(strict=True).relative_to(root)
        traversable: list[str] = []
        for name in directories:
            if name == ".git":
                continue
            directory = current_path / name
            if is_reparse(directory):
                linked_or_reparse.append(directory.relative_to(root).as_posix())
                continue
            traversable.append(name)
            if name == "__pycache__":
                cache_directories.append(directory)
        directories[:] = traversable
        for name in names:
            artifact = current_path / name
            if is_reparse(artifact):
                linked_or_reparse.append(artifact.relative_to(root).as_posix())
                continue
            if artifact.suffix.casefold() not in {".pyc", ".pyo"}:
                continue
            cache_artifacts.append(artifact)
    if linked_or_reparse:
        raise PublicationValidationError(
            "publication worktree contains symlink or reparse entries: "
            f"{sorted(linked_or_reparse)}"
        )
    for artifact in cache_artifacts:
        relative = artifact.relative_to(root).as_posix()
        try:
            contained(root, relative, must_exist=True, kind="file").unlink()
        except ContainmentError as exc:
            raise PublicationValidationError(
                f"Python cache cleanup crossed a symlink or reparse point: {relative}"
            ) from exc
        else:
            cleaned.append(relative)
    for directory in sorted(
        cache_directories,
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        relative = directory.relative_to(root).as_posix()
        try:
            contained(root, relative, must_exist=True, kind="directory").rmdir()
        except ContainmentError as exc:
            raise PublicationValidationError(
                f"Python cache cleanup crossed a symlink or reparse point: {relative}"
            ) from exc
        except OSError:
            continue
        cleaned.append(relative + "/")
    return sorted(cleaned)


def _worktree_controls(root: Path) -> tuple[dict, set[str]]:
    manifest_path, marker_path = root / MANIFEST, root / MARKER
    if not manifest_path.is_file() or not marker_path.is_file():
        raise PublicationValidationError("publication controls are missing")
    return _validate_controls(manifest_path.read_bytes(), marker_path.read_bytes())


def _revision_bytes(root: Path, revision: str, path: str) -> bytes:
    return _git(root, "show", f"{revision}:{path}", binary=True)  # type: ignore[return-value]


def _index_bytes(root: Path, path: str) -> bytes:
    return _revision_bytes(root, "", path)


def _validate_payload(manifest: dict, read: Callable[[str], bytes]) -> list[str]:
    payload: dict[str, bytes] = {}
    for row in _records(manifest):
        path = str(row["path"])
        data = read(path)
        if _sha(data) != row.get("sha256"):
            raise PublicationValidationError(f"content hash mismatch: {path}")
        payload[path] = data
    attestations = manifest.get("binary_attestations", ())
    if not isinstance(attestations, (list, tuple)):
        raise PublicationValidationError("publication binary attestations are invalid")
    try:
        inspect_content_set(payload, binary_attestations=attestations)
    except ContentSecurityError as exc:
        raise PublicationValidationError(str(exc)) from exc
    return []


def validate_staged(
    root: Path,
    *,
    preserved_path: Callable[[str], bool] | None = None,
) -> dict:
    """Validate the exact staged index against the staged publication manifest."""
    root = root.resolve()
    preserved_path = preserved_path or (lambda path: False)
    manifest_bytes = _index_bytes(root, MANIFEST)
    marker_bytes = _index_bytes(root, MARKER)
    manifest, owned = _validate_controls(manifest_bytes, marker_bytes)
    index_paths = {
        path for path in str(_git(root, "ls-files")).splitlines()
        if not is_release_product(path)
    }
    staged = set(str(_git(root, "diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB")).splitlines())
    forbidden = sorted(path for path in index_paths | staged if _forbidden(path))
    unknown = sorted(path for path in index_paths - owned if not preserved_path(path))
    missing = sorted(owned - index_paths)
    unknown_staged = sorted(staged - owned)
    if forbidden or unknown or missing or unknown_staged:
        raise PublicationValidationError(
            f"staged publication mismatch; forbidden={forbidden}; unknown={unknown}; "
            f"missing={missing}; unknown_staged={unknown_staged}"
        )
    _validate_payload(manifest, lambda path: _index_bytes(root, path))
    return {
        "status": "passed", "owned_file_count": len(owned),
        "staged_file_count": len(staged), "staged_paths": sorted(staged),
        "manifest_sha256": _sha(manifest_bytes), "secret_scan": "passed",
    }


def stage_manifest_owned(
    root: Path,
    *,
    preserved_path: Callable[[str], bool] | None = None,
) -> dict:
    """Stage only manifest-owned paths and then validate the complete index."""
    root = root.resolve()
    preserved_path = preserved_path or (lambda path: False)
    cleaned_python_cache_paths = clean_generated_python_caches(root)
    manifest, owned = _worktree_controls(root)
    current = _filesystem_files(root)
    forbidden = sorted(path for path in current if _forbidden(path))
    unknown = sorted(path for path in current - owned if not preserved_path(path))
    missing = sorted(owned - current)
    if forbidden or unknown or missing:
        raise PublicationValidationError(
            f"publication worktree mismatch; forbidden={forbidden}; unknown={unknown}; missing={missing}"
        )
    if str(_git(root, "diff", "--cached", "--name-only")).strip():
        raise PublicationValidationError("staged index must be empty before governed staging")
    pre_stage_status = str(_git(root, "status", "--short", "--untracked-files=all")).splitlines()
    prior_owned: set[str] = set()
    try:
        prior_manifest = _json_bytes(_revision_bytes(root, "HEAD", MANIFEST), f"HEAD:{MANIFEST}")
        prior_owned = _owned(prior_manifest)
    except subprocess.CalledProcessError:
        pass
    subprocess.run(("git", "add", "--", *sorted(owned)), cwd=root, check=True)
    for removed in sorted(path for path in prior_owned - owned if not preserved_path(path)):
        subprocess.run(("git", "add", "-u", "--", removed), cwd=root, check=True)
    result = validate_staged(root, preserved_path=preserved_path)
    result["pre_stage_status"] = pre_stage_status
    result["staging_strategy"] = "manifest-owned paths only"
    result["cleaned_python_cache_count"] = len(cleaned_python_cache_paths)
    result["cleaned_python_cache_paths"] = cleaned_python_cache_paths
    return result


def verify_commit_tree(
    root: Path,
    revision: str = "HEAD",
    *,
    preserved_path: Callable[[str], bool] | None = None,
) -> dict:
    """Verify a committed publication tree before it is pushed."""
    root = root.resolve()
    preserved_path = preserved_path or (lambda path: False)
    manifest_bytes = _revision_bytes(root, revision, MANIFEST)
    marker_bytes = _revision_bytes(root, revision, MARKER)
    manifest, owned = _validate_controls(manifest_bytes, marker_bytes)
    tree_paths = {
        path for path in str(_git(root, "ls-tree", "-r", "--name-only", revision)).splitlines()
        if not is_release_product(path)
    }
    forbidden = sorted(path for path in tree_paths if _forbidden(path))
    unknown = sorted(path for path in tree_paths - owned if not preserved_path(path))
    missing = sorted(owned - tree_paths)
    if forbidden or unknown or missing:
        raise PublicationValidationError(
            f"committed publication mismatch; forbidden={forbidden}; unknown={unknown}; missing={missing}"
        )
    _validate_payload(manifest, lambda path: _revision_bytes(root, revision, path))
    commit = str(_git(root, "rev-parse", revision)).strip()
    return {
        "status": "passed", "revision": revision, "commit": commit,
        "tree_file_count": len(tree_paths), "manifest_sha256": _sha(manifest_bytes),
        "forbidden_artifact_scan": "passed", "secret_scan": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "validate-staged", "verify-commit"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    if args.action == "stage":
        result = stage_manifest_owned(args.root)
    elif args.action == "validate-staged":
        result = validate_staged(args.root)
    else:
        result = verify_commit_tree(args.root, args.revision)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
