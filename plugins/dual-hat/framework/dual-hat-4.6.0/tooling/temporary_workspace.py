"""Owned, isolated temporary workspaces for framework operations.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tempfile
import uuid


class TemporaryWorkspaceError(ValueError):
    """Raised when a temporary workspace would cross a governed boundary."""


def _resolved(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _within(path: Path, boundary: Path) -> bool:
    try:
        path.relative_to(boundary)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class TemporaryWorkspacePolicy:
    """Resolve temporary roots while excluding repositories and mutable workspaces."""

    repository_root: Path
    prohibited_roots: tuple[Path, ...] = ()
    namespace: str = "dual-hat"

    def __post_init__(self) -> None:
        repository = _resolved(self.repository_root)
        prohibited = tuple(dict.fromkeys(
            _resolved(path) for path in (
                repository,
                repository / "workspace",
                *self.prohibited_roots,
            )
        ))
        if not self.namespace or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in self.namespace):
            raise TemporaryWorkspaceError("temporary-workspace namespace must be a safe path component")
        object.__setattr__(self, "repository_root", repository)
        object.__setattr__(self, "prohibited_roots", prohibited)

    def resolve_base(self, requested: str | Path | None = None) -> Path:
        if requested is None:
            base = _resolved(Path(tempfile.gettempdir()) / f"{self.namespace}-runs")
        else:
            raw = Path(requested).expanduser()
            if not raw.is_absolute():
                raise TemporaryWorkspaceError("custom temporary root must be absolute")
            base = _resolved(raw)
        for boundary in self.prohibited_roots:
            if _within(base, boundary):
                raise TemporaryWorkspaceError(
                    f"temporary root overlaps prohibited boundary: {boundary.name or boundary.anchor}"
                )
        return base

    def owned_run(self, purpose: str, requested_root: str | Path | None = None) -> "OwnedTemporaryRun":
        return OwnedTemporaryRun(self, purpose, self.resolve_base(requested_root))


class OwnedTemporaryRun(AbstractContextManager["OwnedTemporaryRun"]):
    """Own one unique run directory and remove only that directory at exit."""

    def __init__(self, policy: TemporaryWorkspacePolicy, purpose: str, base: Path):
        if not purpose or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in purpose):
            raise TemporaryWorkspaceError("temporary-workspace purpose must be a safe path component")
        self.policy = policy
        self.purpose = purpose
        self.base = base
        self.run_id = uuid.uuid4().hex
        self.path = base / f"{purpose}-{self.run_id}"
        if any(_within(self.path, boundary) for boundary in policy.prohibited_roots):
            raise TemporaryWorkspaceError("owned temporary run would enter a prohibited boundary")
        self._entered = False

    def __enter__(self) -> "OwnedTemporaryRun":
        if self._entered or self.path.exists():
            raise TemporaryWorkspaceError("temporary run is not fresh")
        self.base.mkdir(parents=True, exist_ok=True)
        self.path.mkdir()
        marker = {
            "schema": "dual-hat-temporary-run/1.0",
            "run_id": self.run_id,
            "purpose": self.purpose,
            "owner_scoped_cleanup": True,
        }
        (self.path / ".temporary-run-owner.json").write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        self._entered = True
        return self

    def subdirectory(self, role: str) -> Path:
        if not self._entered:
            raise TemporaryWorkspaceError("temporary run has not started")
        if not role or Path(role).name != role or role in {".", ".."}:
            raise TemporaryWorkspaceError("temporary subdirectory role must be one safe component")
        destination = self.path / role
        destination.mkdir(exist_ok=False)
        return destination

    def cleanup(self) -> None:
        if self.path.exists():
            shutil.rmtree(self.path)
        if self.path.exists():
            raise TemporaryWorkspaceError("temporary run cleanup postcondition failed")
        if self.base.exists() and not any(self.base.iterdir()):
            self.base.rmdir()

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.cleanup()
        return False
