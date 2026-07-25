# SPDX-License-Identifier: Apache-2.0
"""Platform-neutral contained-path semantics for Dual Hat tooling."""
from __future__ import annotations

import os
import stat
from pathlib import Path


class ContainmentError(ValueError):
    pass


_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_component(value: object) -> str:
    component = str(value)
    if not component or component in {".", ".."} or component != component.strip(): raise ContainmentError("unsafe empty or dot path component")
    if any(token in component for token in ("/", "\\", ":")) or any(ord(char) < 32 for char in component): raise ContainmentError("unsafe separator, device, ADS, or control syntax")
    if component.endswith((".", " ")) or component.split(".", 1)[0].upper() in _RESERVED: raise ContainmentError("unsafe reserved or aliased component")
    return component


def is_reparse(path: Path) -> bool:
    try: attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except FileNotFoundError: return False
    return path.is_symlink() or bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def contained(root: str | Path, relative: str | Path, *, must_exist: bool = False,
              kind: str | None = None, reject_reparse: bool = True) -> Path:
    authority = Path(root).resolve(strict=True); candidate = Path(relative)
    if candidate.is_absolute() or candidate.drive or candidate.root or not candidate.parts: raise ContainmentError("path must be nonempty and relative")
    current = authority
    for part in candidate.parts:
        safe_component(part); current /= part
        if reject_reparse and current.exists() and is_reparse(current): raise ContainmentError("path crosses a symlink or reparse point")
    result = current.resolve(strict=must_exist)
    try: result.relative_to(authority)
    except ValueError as exc: raise ContainmentError("path escapes authorized root") from exc
    if must_exist and kind == "file" and not result.is_file(): raise ContainmentError("path is not a regular file")
    if must_exist and kind == "directory" and not result.is_dir(): raise ContainmentError("path is not a directory")
    return result


def contained_roots(target: str | Path, roots: dict[str, str]) -> dict[str, Path]:
    authority = Path(target).resolve(); resolved: dict[str, Path] = {}
    for name, relative in roots.items():
        candidate = Path(relative)
        if candidate.is_absolute() or candidate.drive or candidate.root or not candidate.parts: raise ContainmentError("profile root must be nonempty and relative")
        for part in candidate.parts: safe_component(part)
        path = (authority / candidate).resolve()
        try: path.relative_to(authority)
        except ValueError as exc: raise ContainmentError("profile root escapes product target") from exc
        if path == authority: raise ContainmentError("profile root cannot equal product target")
        resolved[name] = path
    folded = [str(path).casefold() for path in resolved.values()]
    if len(set(folded)) != len(folded): raise ContainmentError("profile roots collide")
    for left_name, left in resolved.items():
        for right_name, right in resolved.items():
            if left_name != right_name and (left in right.parents or right in left.parents):
                raise ContainmentError("profile roots cannot overlap or nest")
    return resolved
