"""Release package contract tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
import release_package  # noqa: E402
from release_artifacts import is_release_product  # noqa: E402


class ReleasePackageTests(unittest.TestCase):
    def test_versioned_products_are_not_source_inputs(self) -> None:
        self.assertTrue(is_release_product("release/v0.1.0/dual-hat-0.1.0.zip"))
        self.assertTrue(is_release_product("release/v0.1.0/dual-hat-0.1.0.release.json"))
        self.assertTrue(is_release_product("release/v0.1.0/dual-hat-0.1.0.zip.sha256"))
        self.assertFalse(is_release_product("release/RELEASE_POLICY.md"))
        self.assertFalse(is_release_product("release/v0.1.0/unrelated.json"))
        if (ROOT / "export/EXPORT_SOURCES.json").is_file():
            self.assertNotIn(
                "release/v0.1.0/dual-hat-0.1.0.release.json",
                release_package.source_files(),
            )

    @unittest.skipIf(
        os.environ.get("DUAL_HAT_RELEASE_SELF_TEST_CHILD") == "1",
        "outer release self-test already proves deterministic packaging",
    )
    def test_release_self_test(self) -> None:
        result = release_package.self_test()
        self.assertTrue(result["deterministic"])
        self.assertEqual(result["archive_sha256"], result["second_archive_sha256"])
        self.assertEqual("passed", result["extracted_framework_validation"])

    def test_version_and_notes_agree(self) -> None:
        version = json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))["version"]
        self.assertIn(version, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / f"release/RELEASE_NOTES_v{version}.md").is_file())


if __name__ == "__main__":
    unittest.main()
