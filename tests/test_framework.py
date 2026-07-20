# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from framework_completeness import validate_framework  # noqa: E402


class FrameworkTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
