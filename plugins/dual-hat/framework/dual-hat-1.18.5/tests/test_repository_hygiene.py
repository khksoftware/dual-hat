# SPDX-License-Identifier: Apache-2.0
"""GOVERNING_PRINCIPLES.md rule 35's standing check: a durable file must
never embed an absolute local filesystem path used as a live structural
pointer or self-reference. Red-green-refactor coverage (rule 26): one test
reproduces the exact defect class rule 35 was written for and confirms it is
caught; the rest confirm every declared exemption genre -- test fixture,
schema example, markdown evidence citation, regex pattern source, an
explicit human-reviewed citation, and a deferred-scope prefix -- is spared,
so the check does not just flag everything path-shaped, and a final test
proves the live repository itself is currently clean.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from repository_hygiene import validate_no_embedded_absolute_local_paths  # noqa: E402


class AbsoluteLocalPathTests(unittest.TestCase):
    @staticmethod
    def _git_init(root: Path) -> None:
        subprocess.run(("git", "init", "-q"), cwd=root, check=True)

    def test_scan_catches_a_hardcoded_default_used_as_a_live_pointer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._git_init(root)
            script = root / "tooling/example_tool.py"
            script.parent.mkdir(parents=True)
            script.write_text('DEFAULT_ROOT = Path("Z:\\\\Example\\\\Operator\\\\projects\\\\dual-hat")\n', encoding="utf-8")
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            failures = validate_no_embedded_absolute_local_paths(root)
            self.assertEqual(1, len(failures))
            self.assertIn("tooling/example_tool.py:1", failures[0])
            self.assertIn("rule 35", failures[0])

    def test_scan_spares_a_registered_citation_but_still_catches_an_unregistered_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._git_init(root)
            doc = root / "NOTES.md"
            doc.write_text(
                "Reviewed at `Z:\\Example\\Operator\\alpha.txt`.\n"
                "Separately, also found at `Z:\\Example\\Operator\\beta.txt`.\n",
                encoding="utf-8",
            )
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            citations = ({"path": "NOTES.md", "line_contains": "alpha.txt"},)
            failures = validate_no_embedded_absolute_local_paths(root, citations=citations)
            self.assertEqual(1, len(failures))
            self.assertIn("beta.txt", failures[0])
            self.assertNotIn("alpha.txt", " ".join(failures))

    def test_scan_spares_a_registered_deferred_scope_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._git_init(root)
            doc = root / "process/work-items/example/NOTE.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("Backup lives at `C:\\Downloads\\Example`.\n", encoding="utf-8")
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            deferred = ({"path_prefix": "process/work-items/example/"},)
            self.assertEqual((), validate_no_embedded_absolute_local_paths(root, deferred_scope=deferred))
            self.assertEqual(1, len(validate_no_embedded_absolute_local_paths(root, deferred_scope=())))

    def test_scan_spares_test_schema_citation_and_regex_source_genres(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._git_init(root)
            test_file = root / "tests/test_example.py"
            test_file.parent.mkdir(parents=True)
            test_file.write_text('BAD = "C:\\\\Attacker\\\\payload.exe"\n', encoding="utf-8")
            schema_file = root / "schemas/example.schema.json"
            schema_file.parent.mkdir(parents=True)
            schema_file.write_text('{"example": "C:/Python/python.exe"}\n', encoding="utf-8")
            regex_line = root / "tooling/example_detector.py"
            regex_line.parent.mkdir(parents=True, exist_ok=True)
            regex_line.write_text(
                'PATTERN = re.compile(r"(?:[A-Za-z]:\\\\|/Users/|/home/)[^\\\\s]+")\n', encoding="utf-8",
            )
            citation_style = root / "process/REVIEW.md"
            citation_style.parent.mkdir(parents=True, exist_ok=True)
            citation_style.write_text(
                "Inspected `Z:/example-project/tooling/x.py#L38)`.\n", encoding="utf-8",
            )
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            self.assertEqual((), validate_no_embedded_absolute_local_paths(root))

    def test_live_repository_has_no_unexempted_absolute_local_path_embeddings(self):
        self.assertEqual((), validate_no_embedded_absolute_local_paths(ROOT))


if __name__ == "__main__":
    unittest.main()
