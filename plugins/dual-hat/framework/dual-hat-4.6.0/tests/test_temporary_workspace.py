"""Temporary-workspace containment tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tooling.temporary_workspace import TemporaryWorkspaceError, TemporaryWorkspacePolicy


class TemporaryWorkspaceTests(unittest.TestCase):
    def test_default_is_isolated_and_cleanup_is_owner_scoped(self) -> None:
        with tempfile.TemporaryDirectory() as root_text:
            repository = Path(root_text) / "source"
            repository.mkdir()
            policy = TemporaryWorkspacePolicy(repository, namespace="test-dual-hat")
            with policy.owned_run("validation") as first:
                first_path = first.path
                with policy.owned_run("validation") as second:
                    second_path = second.path
                    self.assertNotEqual(first_path, second_path)
                    (second.path / "state.txt").write_text("retained while owned\n", encoding="utf-8")
                self.assertTrue(first_path.exists())
                self.assertFalse(second_path.exists())
            self.assertFalse(first_path.exists())

    def test_cleanup_runs_after_exception(self) -> None:
        with tempfile.TemporaryDirectory() as root_text:
            repository = Path(root_text) / "source"
            repository.mkdir()
            policy = TemporaryWorkspacePolicy(repository, namespace="test-dual-hat")
            run_path = None
            with self.assertRaisesRegex(RuntimeError, "expected"):
                with policy.owned_run("failure") as run:
                    run_path = run.path
                    raise RuntimeError("expected")
            self.assertIsNotNone(run_path)
            self.assertFalse(run_path.exists())

    def test_rejects_repository_workspace_sibling_and_relative_roots(self) -> None:
        with tempfile.TemporaryDirectory() as root_text:
            base = Path(root_text)
            repository = base / "source"
            repository.mkdir()
            sibling = base / "workspace"
            sibling.mkdir()
            policy = TemporaryWorkspacePolicy(repository, prohibited_roots=(sibling,))
            for unsafe in (repository / "workspace", sibling, Path("workspace/.validation")):
                with self.subTest(unsafe=str(unsafe)):
                    with self.assertRaises(TemporaryWorkspaceError):
                        policy.resolve_base(unsafe)


if __name__ == "__main__":
    unittest.main()
