"""Temporary-workspace containment tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import shutil
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

    def test_cleanup_removes_the_shared_base_once_the_last_run_leaves(self) -> None:
        with tempfile.TemporaryDirectory() as root_text:
            repository = Path(root_text) / "source"
            repository.mkdir()
            # An explicit base per test, never the shared namespace default: the
            # two race tests below deliberately leave a sibling's directory
            # behind, and against the default base that residue outlives the
            # run and decides a later verdict.
            base = Path(root_text) / "runs"
            policy = TemporaryWorkspacePolicy(repository, namespace="test-dual-hat")
            with policy.owned_run("validation", base) as first:
                self.assertEqual(base, first.base)
                with policy.owned_run("validation", base):
                    self.assertTrue(base.exists())
                self.assertTrue(base.exists(), "a sibling still owns a run under this base")
            self.assertFalse(base.exists())

    def test_cleanup_tolerates_the_shared_base_vanishing_while_it_is_listed(self) -> None:
        """A sibling's own cleanup can remove the shared base in the window
        between this run asking for its contents and the listing happening.
        The run is finished by then; it must not fail on housekeeping."""
        with tempfile.TemporaryDirectory() as root_text:
            repository = Path(root_text) / "source"
            repository.mkdir()
            base = Path(root_text) / "runs"
            policy = TemporaryWorkspacePolicy(repository, namespace="test-dual-hat")
            run = policy.owned_run("validation", base)
            run.__enter__()
            real_iterdir = Path.iterdir

            def vanishing_iterdir(self_path: Path):
                if self_path == base and base.exists():
                    shutil.rmtree(base)
                return real_iterdir(self_path)

            Path.iterdir = vanishing_iterdir
            try:
                run.cleanup()
            finally:
                Path.iterdir = real_iterdir
            self.assertFalse(run.path.exists())

    def test_cleanup_tolerates_a_sibling_repopulating_the_shared_base(self) -> None:
        """The opposite window: the base is empty when listed, and a sibling
        creates its own run directory before this run removes it, so the
        removal fails as not empty. Tolerating only a missing directory would
        still crash a finished run here."""
        with tempfile.TemporaryDirectory() as root_text:
            repository = Path(root_text) / "source"
            repository.mkdir()
            base = Path(root_text) / "runs"
            policy = TemporaryWorkspacePolicy(repository, namespace="test-dual-hat")
            run = policy.owned_run("validation", base)
            run.__enter__()
            real_rmdir = Path.rmdir

            def repopulating_rmdir(self_path: Path, *args, **kwargs):
                if self_path == base:
                    (base / "validation-sibling").mkdir(exist_ok=True)
                return real_rmdir(self_path, *args, **kwargs)

            Path.rmdir = repopulating_rmdir
            try:
                run.cleanup()
            finally:
                Path.rmdir = real_rmdir
            self.assertFalse(run.path.exists())
            self.assertTrue((base / "validation-sibling").exists(), "the sibling's own directory survives")

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
