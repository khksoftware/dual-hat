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

from repository_hygiene import (  # noqa: E402
    MARKDOWN_LINE_ANCHOR_CITATION,
    WINDOWS_DRIVE_ABSOLUTE_PATH,
    validate_no_embedded_absolute_local_paths,
)


class AbsoluteLocalPathTests(unittest.TestCase):
    @staticmethod
    def _git_init(root: Path) -> None:
        subprocess.run(("git", "init", "-q"), cwd=root, check=True)

    # Every absolute-path fixture in this file is SYNTHETIC by construction.
    # This module ships publicly through the export allowlist, so a fixture
    # spelling out a real machine's drive, username or directory layout
    # discloses it to every adopter. That is a publication-disclosure concern
    # and NOT a rule 35 compliance defect: the lines are already exempt by file
    # shape and the check is not failing on them.
    #
    # The binding constraint on every replacement is that it must still trip
    # the detector it exists to exercise. A fixture that quietly stopped
    # matching would leave its test green while testing nothing -- a silently
    # deleted test rather than a passing one -- so each is asserted against the
    # pattern here rather than assumed to still match.
    def _assert_detectable(self, value: str) -> str:
        self.assertRegex(
            value, WINDOWS_DRIVE_ABSOLUTE_PATH,
            "fixture no longer matches WINDOWS_DRIVE_ABSOLUTE_PATH, so its test would pass "
            "because the value stopped matching the detector rather than because the "
            "behaviour under test still holds",
        )
        return value

    def test_scan_catches_a_hardcoded_default_used_as_a_live_pointer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._git_init(root)
            script = root / "tooling/example_tool.py"
            script.parent.mkdir(parents=True)
            pointer = self._assert_detectable("Z:\\\\Example\\\\Operator\\\\projects\\\\dual-hat")
            script.write_text(f'DEFAULT_ROOT = Path("{pointer}")\n', encoding="utf-8")
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
            # The registry match is on `line_contains: "alpha.txt"`, so the two
            # leaf filenames are load-bearing and stay; only the disclosive
            # prefix is replaced.
            registered = self._assert_detectable("Z:\\Example\\Operator\\alpha.txt")
            unregistered = self._assert_detectable("Z:\\Example\\Operator\\beta.txt")
            doc.write_text(
                f"Reviewed at `{registered}`.\n"
                f"Separately, also found at `{unregistered}`.\n",
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
            # Synthetic by construction. This file ships publicly through the
            # export allowlist, so a fixture spelling out a real machine's
            # directory layout discloses that layout to every adopter -- a
            # publication-disclosure concern, not a rule 35 compliance defect:
            # the line is already exempt by file shape and the check is not
            # failing on it.
            #
            # The replacement must still be drive-letter-rooted AND still carry
            # a #Lnn anchor inside the matched span, because those are the two
            # structural facts the exemption under test turns on. Asserted here
            # rather than assumed: a fixture that quietly stopped matching the
            # detector would leave this test green while testing nothing, which
            # is a silently deleted test rather than a passing one.
            citation_line = "Inspected `Z:/example-project/tooling/x.py#L38)`.\n"
            matched = WINDOWS_DRIVE_ABSOLUTE_PATH.search(citation_line)
            self.assertIsNotNone(
                matched, "the citation fixture no longer matches WINDOWS_DRIVE_ABSOLUTE_PATH",
            )
            self.assertRegex(
                matched.group(0), MARKDOWN_LINE_ANCHOR_CITATION,
                "the citation fixture no longer fires MARKDOWN_LINE_ANCHOR_CITATION",
            )
            citation_style.write_text(citation_line, encoding="utf-8")
            subprocess.run(("git", "add", "-A"), cwd=root, check=True)
            self.assertEqual((), validate_no_embedded_absolute_local_paths(root))

    def test_live_repository_has_no_unexempted_absolute_local_path_embeddings(self):
        self.assertEqual((), validate_no_embedded_absolute_local_paths(ROOT))


if __name__ == "__main__":
    unittest.main()
