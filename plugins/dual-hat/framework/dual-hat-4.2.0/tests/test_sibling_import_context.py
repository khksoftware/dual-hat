"""Scoped sibling-import context-manager tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tooling.sibling_import_context import (
    _load_module_by_path_with_sibling_context,
    sibling_directory_on_path,
)


class SiblingDirectoryOnPathTests(unittest.TestCase):
    def test_inserts_for_the_block_and_removes_afterward(self) -> None:
        directory = str(ROOT / "tooling" / "onboarding")  # need not exist; only membership is tested
        self.assertNotIn(directory, sys.path)
        with sibling_directory_on_path(directory):
            self.assertIn(directory, sys.path)
            self.assertEqual(sys.path[0], directory)
        self.assertNotIn(directory, sys.path)

    def test_removes_even_when_the_block_raises(self) -> None:
        directory = str(ROOT / "tooling" / "validate_framework")
        with self.assertRaisesRegex(RuntimeError, "expected"):
            with sibling_directory_on_path(directory):
                self.assertIn(directory, sys.path)
                raise RuntimeError("expected")
        self.assertNotIn(directory, sys.path)

    def test_a_directory_another_caller_already_inserted_is_left_alone(self) -> None:
        """Only the call that inserted an entry may remove it -- a directory
        another loader put on sys.path first must survive this call's exit."""
        directory = str(ROOT / "tooling" / "quality_review")
        sys.path.insert(0, directory)
        try:
            with sibling_directory_on_path(directory):
                self.assertIn(directory, sys.path)
            # Still present: this call did not insert it, so it must not remove it.
            self.assertIn(directory, sys.path)
        finally:
            sys.path.remove(directory)

    def test_nested_calls_on_the_same_directory_do_not_remove_it_early(self) -> None:
        directory = str(ROOT / "tooling" / "release_artifacts")
        with sibling_directory_on_path(directory):
            self.assertIn(directory, sys.path)
            with sibling_directory_on_path(directory):
                self.assertIn(directory, sys.path)
            # Inner exit must not remove what the outer call still needs.
            self.assertIn(directory, sys.path)
        self.assertNotIn(directory, sys.path)


class LoadModuleByPathWithSiblingContextTests(unittest.TestCase):
    def test_loaded_module_resolves_a_bare_sibling_import(self) -> None:
        """A module loaded by file path outside any package context can still
        do `from sibling import x` against the file next to it, and the load
        leaves sys.path's membership for that directory unchanged net of
        whatever this process's ambient state already was. Deliberately not
        asserted as an absolute absent-before/absent-after pair: another test
        module elsewhere in this suite may already have put the framework's
        own tooling directory on sys.path permanently (a fact about that
        module's own top-of-file bootstrap, not about this one), and this
        test must hold regardless of run order or which other modules ran
        first in the same process."""
        directory = str(ROOT / "tooling")
        was_present = directory in sys.path
        module = _load_module_by_path_with_sibling_context(
            "probe_sibling_import_context_target",
            ROOT / "tooling" / "path_containment.py",
        )
        self.assertTrue(hasattr(module, "contained_roots"))
        self.assertEqual(directory in sys.path, was_present)

    def test_register_in_sys_modules_makes_the_module_resolvable_by_name(self) -> None:
        name = "probe_sibling_import_context_registered_target"
        self.assertNotIn(name, sys.modules)
        try:
            module = _load_module_by_path_with_sibling_context(
                name,
                ROOT / "tooling" / "path_containment.py",
                register_in_sys_modules=True,
            )
            self.assertIs(sys.modules[name], module)
        finally:
            sys.modules.pop(name, None)


class BootstrapProductConsumerRegressionTests(unittest.TestCase):
    """`scripts/bootstrap_product.py` carried the exact defect this module
    exists to prevent: a permanent, unscoped `sys.path.insert` of its tooling
    directory, executed at import time and never removed. This proves the
    repaired script no longer leaves that directory on sys.path once it has
    been imported, in a fresh interpreter isolated from whatever this test
    process's own sys.path already carries."""

    def test_importing_bootstrap_product_leaves_no_permanent_sys_path_entry(self) -> None:
        probe = textwrap.dedent(
            f"""
            import sys
            from pathlib import Path
            root = Path(r"{ROOT}")
            scripts_dir = str(root / "scripts")
            tooling_dir = str(root / "tooling")
            sys.path.insert(0, scripts_dir)
            assert tooling_dir not in sys.path, "precondition: tooling dir must start absent"
            import bootstrap_product  # noqa
            print("TOOLING_DIR_LEFT_ON_PATH=" + str(tooling_dir in sys.path))
            """
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TOOLING_DIR_LEFT_ON_PATH=False", result.stdout)


if __name__ == "__main__":
    unittest.main()
