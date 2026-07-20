# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from framework_completeness import validate_framework  # noqa: E402
from staged_publication import (  # noqa: E402
    PublicationValidationError,
    stage_manifest_owned,
    verify_commit_tree,
)


class FrameworkTests(unittest.TestCase):
    @staticmethod
    def _git(root: Path, *args: str) -> None:
        subprocess.run(("git", *args), cwd=root, check=True, capture_output=True, text=True)

    @staticmethod
    def _write_publication(root: Path, readme: str) -> None:
        readme_bytes = readme.encode("utf-8")
        manifest = {
            "schema": "dual-hat-export-manifest/3.0",
            "tree_sha256": "TEST-TREE",
            "content_files": [{
                "path": "README.md",
                "sha256": hashlib.sha256(readme_bytes).hexdigest().upper(),
            }],
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        marker = {
            "schema": "dual-hat-published-state/1.0",
            "tree_sha256": "TEST-TREE",
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest().upper(),
        }
        (root / ".dual-hat").mkdir(exist_ok=True)
        (root / "README.md").write_bytes(readme_bytes)
        (root / ".dual-hat/export-manifest.json").write_bytes(manifest_bytes)
        (root / ".dual-hat/published-state.json").write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def _publication_repo(self, root: Path) -> None:
        self._git(root, "init", "-b", "main")
        self._git(root, "config", "user.name", "Dual Hat Test")
        self._git(root, "config", "user.email", "dual-hat-test@example.invalid")
        self._write_publication(root, "initial\n")
        self._git(root, "add", "--", "README.md", ".dual-hat/export-manifest.json", ".dual-hat/published-state.json")
        self._git(root, "commit", "-m", "Initial governed publication")

    def test_semantic_completeness(self):
        self.assertEqual((), validate_framework(ROOT))

    def test_json_and_schema_files_parse(self):
        for path in [*ROOT.rglob("*.json"), *ROOT.rglob("*.schema.json")]:
            json.loads(path.read_text(encoding="utf-8"))

    def test_examples_cover_operating_workflows(self):
        expected = {
            "bounded-task.example.json", "context-pack.example.json",
            "current-handover.example.json", "technical-debt.example.json",
            "validation-run.example.json", "roadmap-and-phase.example.md",
        }
        self.assertTrue(expected.issubset({path.name for path in (ROOT / "examples").iterdir()}))

    def test_templates_cover_bootstrap_domains(self):
        expected = {
            "WORK_ORDER.md", "CURRENT_HANDOVER.md", "CURRENT_HANDOVER.json",
            "ACTIVE_SESSION.md", "CONTEXT_PACK.md", "ROADMAP.md",
            "TECHNICAL_DEBT_BACKLOG.json", "CANONICAL_ENTRYPOINTS.md",
            "CANONICAL_DOMAIN_INDEX.md", "PRODUCT_REPOSITORY.md",
        }
        self.assertTrue(expected.issubset({path.name for path in (ROOT / "templates").iterdir()}))

    def test_role_and_retrieval_help_is_first_class(self):
        expected = {
            "ARCHITECTURE_OFFICE_GUIDE.md", "ENGINEERING_AGENT_GUIDE.md",
            "TASK_CONTEXT_RETRIEVAL.md", "COMMAND_REFERENCE.md",
        }
        self.assertTrue(expected.issubset({path.name for path in (ROOT / "docs").iterdir()}))

    def test_inventory_separates_required_domains(self):
        payload = json.loads((ROOT / "repository/FRAMEWORK_CAPABILITY_INVENTORY.json").read_text(encoding="utf-8"))
        ids = {domain["id"] for domain in payload["domains"]}
        self.assertEqual(
            {"architecture", "engineering_execution", "planning", "validation",
             "repository_governance", "sessions_and_continuity",
             "publication_and_closure", "documentation_and_help"},
            ids,
        )

    def test_manifest_owned_staging_and_committed_tree_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            self._write_publication(root, "updated\n")
            staged = stage_manifest_owned(root)
            self.assertEqual(
                [".dual-hat/export-manifest.json", ".dual-hat/published-state.json", "README.md"],
                staged["staged_paths"],
            )
            self._git(root, "commit", "-m", "Forward publication")
            verified = verify_commit_tree(root)
            self.assertEqual("passed", verified["status"])
            self.assertEqual(3, verified["tree_file_count"])

    def test_staging_rejects_ignored_cache_and_unknown_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            cache = root / "tooling/__pycache__"
            cache.mkdir(parents=True)
            (cache / "unsafe.pyc").write_bytes(b"compiled")
            with self.assertRaisesRegex(PublicationValidationError, "forbidden"):
                stage_manifest_owned(root)
            (cache / "unsafe.pyc").unlink()
            cache.rmdir()
            (root / "manual.txt").write_text("unowned", encoding="utf-8")
            with self.assertRaisesRegex(PublicationValidationError, "unknown"):
                stage_manifest_owned(root)

    def test_staging_scans_manifest_owned_content_for_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            credential_fixture = "api_" + "key = 'abcdefghijklmnopqrstuvwx'\n"
            self._write_publication(root, credential_fixture)
            with self.assertRaisesRegex(PublicationValidationError, "possible secrets"):
                stage_manifest_owned(root)


if __name__ == "__main__":
    unittest.main()
