"""Cross-platform agent plugin package contract tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "dual-hat"
sys.path.insert(0, str(ROOT / "tooling"))

from content_security import validate_binary_attestation  # noqa: E402


class AgentPluginPackageTests(unittest.TestCase):
    def payload(self) -> tuple[dict[str, object], Path]:
        descriptor = json.loads((PLUGIN / "framework-payload.json").read_text(encoding="utf-8"))
        framework_root = (PLUGIN / str(descriptor["framework_root"])).resolve()
        self.assertTrue(framework_root.is_relative_to(PLUGIN.resolve()))
        return descriptor, framework_root

    def test_codex_and_claude_resolve_the_same_bundled_framework(self) -> None:
        descriptor, framework_root = self.payload()
        version = json.loads((framework_root / "release" / "VERSION.json").read_text(encoding="utf-8"))
        self.assertEqual(descriptor["framework_version"], version["version"])
        required = (
            "README.md",
            "repository/CANONICAL_ENTRYPOINTS.md",
            "repository/CANONICAL_DOMAIN_INDEX.md",
            "process/ONBOARDING.md",
            "guides/INSTALLATION_AND_BINDING.md",
            "governance/CONFORMANCE_POLICY.md",
            "governance/CODE_REVIEW_CONTRACT.md",
            "validation/VALIDATION_PROTOCOL.md",
        )
        self.assertFalse([path for path in required if not (framework_root / path).is_file()])

        manifests = (
            PLUGIN / ".codex-plugin" / "plugin.json",
            PLUGIN / ".claude-plugin" / "plugin.json",
        )
        for manifest_path in manifests:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("dual-hat", manifest["name"])
            self.assertEqual("./skills/", manifest["skills"])
            self.assertTrue((PLUGIN / manifest["skills"] / "use-dual-hat" / "SKILL.md").is_file())
            self.assertTrue(framework_root.is_dir())

    def test_bundled_payload_matches_its_release_manifest_and_available_source_zip(self) -> None:
        descriptor, framework_root = self.payload()
        content_manifest_path = PLUGIN / str(descriptor["content_manifest"])
        content_manifest = json.loads(content_manifest_path.read_text(encoding="utf-8"))
        expected_paths = {str(row["path"]) for row in content_manifest["files"]}
        actual_paths = {
            path.relative_to(framework_root).as_posix()
            for path in framework_root.rglob("*")
            if path.is_file() and ".dual-hat-release" not in path.parts
        }
        self.assertEqual(expected_paths, actual_paths)
        for row in content_manifest["files"]:
            data = (framework_root / str(row["path"])).read_bytes()
            self.assertEqual(row["bytes"], len(data))
            self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest().upper())

        archive = (
            ROOT
            / "release"
            / f"v{descriptor['framework_version']}"
            / str(descriptor["source_release_archive"])
        )
        if archive.is_file():
            archive_bytes = archive.read_bytes()
            self.assertEqual(
                descriptor["source_release_sha256"],
                hashlib.sha256(archive_bytes).hexdigest().upper(),
            )
            with zipfile.ZipFile(archive) as source:
                prefix = f"dual-hat-{descriptor['framework_version']}/"
                archived_files = {name for name in source.namelist() if not name.endswith("/")}
                extracted_files = {
                    prefix + path.relative_to(framework_root).as_posix()
                    for path in framework_root.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(archived_files, extracted_files)
                for name in archived_files:
                    self.assertEqual(
                        source.read(name),
                        (framework_root / name.removeprefix(prefix)).read_bytes(),
                    )

    def test_binary_assets_have_complete_matching_attestations(self) -> None:
        provenance = json.loads((ROOT / "BINARY_PROVENANCE.json").read_text(encoding="utf-8"))
        attestations = provenance["binary_attestations"]
        self.assertEqual(
            {
                path.relative_to(ROOT).as_posix()
                for path in ROOT.rglob("*.png")
                if path.is_file()
            },
            {str(row["path"]) for row in attestations},
        )
        for attestation in attestations:
            path = str(attestation["path"])
            validate_binary_attestation(path, (ROOT / path).read_bytes(), attestation)

    def test_package_has_no_scaffold_placeholders_or_external_install_requirement(self) -> None:
        governed_text = (
            PLUGIN / ".codex-plugin" / "plugin.json",
            PLUGIN / ".claude-plugin" / "plugin.json",
            PLUGIN / "README.md",
            PLUGIN / "skills" / "use-dual-hat" / "SKILL.md",
            PLUGIN / "skills" / "use-dual-hat" / "references" / "framework-routing.md",
            ROOT / "guides" / "DEPLOYMENT_FORMS.md",
        )
        combined = "\n".join(path.read_text(encoding="utf-8") for path in governed_text)
        self.assertNotIn("[TODO:", combined)
        self.assertNotIn("separate verified framework installation", combined)
        self.assertNotIn("does not bundle the framework", combined)


if __name__ == "__main__":
    unittest.main()
