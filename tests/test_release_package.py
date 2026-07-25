"""Release package contract tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

DUAL_HAT_CAPABILITY_PROOFS = {"governed_publication", "binary_secret_gate", "committed_tree_release_binding", "transactional_writes"}


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
import release_package  # noqa: E402
from content_security import ContentSecurityError, inspect_content_set, sha256  # noqa: E402
from release_artifacts import is_release_product  # noqa: E402


class ReleasePackageTests(unittest.TestCase):
    @staticmethod
    def _git(root: Path, *arguments: str) -> str:
        return subprocess.run(
            ("git", *arguments),
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    @staticmethod
    def _write_composite_publication(root: Path) -> tuple[bytes, bytes]:
        portable = b"# Portable framework\n"
        plugin = b'{"name":"standalone-deployment"}\n'
        record = {
            "path": "README.md",
            "sha256": sha256(portable),
            "bytes": len(portable),
            "mode": "100644",
            "license": "Apache-2.0",
            "origin": "canonical_source",
        }
        records = [record]
        manifest = {
            "source_commit": "a" * 40,
            "tree_sha256": sha256(release_package.canonical_json(records)),
            "content_files": records,
        }
        manifest_bytes = release_package.canonical_json(manifest)
        marker = {
            "schema": "dual-hat-published-state/1.0",
            "license_expression": "Apache-2.0",
            "source_commit": "a" * 40,
            "tree_sha256": manifest["tree_sha256"],
            "manifest_sha256": sha256(manifest_bytes),
            "previous_export_identity": None,
            "canonical_branch": "main",
        }
        (root / ".dual-hat").mkdir(parents=True)
        (root / "plugins/dual-hat").mkdir(parents=True)
        (root / "README.md").write_bytes(portable)
        (root / ".dual-hat/export-manifest.json").write_bytes(manifest_bytes)
        (root / ".dual-hat/published-state.json").write_bytes(
            release_package.canonical_json(marker)
        )
        (root / "plugins/dual-hat/plugin.json").write_bytes(plugin)
        return portable, plugin

    def test_unknown_binary_fails_closed_and_attestation_is_distinct_from_scan(self) -> None:
        payload = b"\x89PNG\r\n\x1a\n\x00fixture"
        with self.assertRaisesRegex(ContentSecurityError, "explicit allowlist"):
            inspect_content_set({"assets/fixture.png": payload})
        attestation = {
            "path": "assets/fixture.png", "content_type": "image/png", "purpose": "test fixture",
            "provenance": "test-authored bytes", "sha256": sha256(payload), "size_bytes": len(payload),
            "rights_basis": "test fixture owned by project", "review_evidence": "unit test inspection",
            "retention_rule": "test scope only", "distribution_rule": "include",
        }
        result = inspect_content_set({"assets/fixture.png": payload}, binary_attestations=(attestation,))
        self.assertEqual("allowlisted_binary_attested", result["classifications"][0]["state"])
        self.assertEqual("not_scanned", result["classifications"][0]["secret_hits"])
        attestation["distribution_rule"] = "exclude"
        with self.assertRaisesRegex(ContentSecurityError, "must have distribution_rule include"):
            inspect_content_set({"assets/fixture.png": payload}, binary_attestations=(attestation,))
        with self.assertRaisesRegex(ContentSecurityError, "explicit allowlist"):
            inspect_content_set({"assets/fixture.bin": b"RIFF0000\x00payload"})

    def test_allowlisted_symlink_cannot_escape_release_source_root(self) -> None:
        with TemporaryDirectory() as temporary, TemporaryDirectory() as outside:
            root = Path(temporary); (root / "export").mkdir()
            source = Path(outside) / "payload.md"; source.write_text("outside", encoding="utf-8")
            link = root / "payload.md"
            try:
                link.symlink_to(source)
            except OSError:
                self.skipTest("host does not permit a symlink fixture")
            (root / "export/EXPORT_SOURCES.json").write_text(json.dumps({"included": ["payload.md"]}), encoding="utf-8")
            with patch.object(release_package, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "containment"):
                    release_package.source_files()

    def test_private_key_and_embedded_token_are_rejected(self) -> None:
        for value in (
            b"-----BEGIN " + b"PRIVATE KEY-----\nfixture",
            b"access_" + b"token = '" + b"abcdefghijklmnopqrstuvwxyz123456'",
        ):
            with self.subTest(value=value[:20]):
                with self.assertRaisesRegex(ContentSecurityError, "possible secrets"):
                    inspect_content_set({"configuration.txt": value})

    @unittest.skipUnless(
        (ROOT / "export/EXPORT_SOURCES.json").is_file() or (ROOT / ".dual-hat/export-manifest.json").is_file(),
        "release construction requires canonical or publication controls",
    )
    def test_release_set_is_exact_and_transaction_rolls_back_prior_bytes(self) -> None:
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "release"
            provenance = ("a" * 40, "b" * 40)
            with patch.object(release_package, "release_provenance", return_value=provenance):
                result = release_package.build(output, production=False)
                self.assertEqual("nonpublishable_plan", result["release_mode"])
                prior = {path.name: path.read_bytes() for path in output.iterdir()}
                for failure_point in (2, 4):
                    with self.assertRaisesRegex(RuntimeError, "injected"):
                        release_package.build(output, failure_after_publish=failure_point, production=False)
                    self.assertEqual(prior, {path.name: path.read_bytes() for path in output.iterdir()})
            (output / "unexpected.release.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "membership mismatch"):
                release_package.validate_release_set(output, require_publication_provenance=False)

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

    def test_composite_source_files_package_only_manifest_owned_portable_subset(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            portable, plugin = self._write_composite_publication(root)
            plugin_path = root / "plugins/dual-hat/plugin.json"
            with patch.object(release_package, "ROOT", root):
                self.assertEqual({"README.md": portable}, release_package.source_files())
                self.assertEqual(plugin, plugin_path.read_bytes())
                (root / "manual.txt").write_text("unknown", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "unclassified=.*manual.txt"):
                    release_package.source_files()

    def test_composite_commit_verifies_portable_subset_and_fails_on_drift(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            portable, plugin = self._write_composite_publication(root)
            plugin_path = root / "plugins/dual-hat/plugin.json"
            self._git(root, "init", "-b", "main")
            self._git(root, "config", "user.name", "Dual Hat Release Test")
            self._git(root, "config", "user.email", "dual-hat-release@example.invalid")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "Composite publication")
            verified = release_package.verify_portable_publication_commit(root, "HEAD")
            self.assertEqual("passed", verified["status"])
            self.assertEqual(plugin, plugin_path.read_bytes())

            (root / "README.md").write_text("altered portable bytes\n", encoding="utf-8")
            self._git(root, "add", "README.md")
            self._git(root, "commit", "-m", "Alter portable bytes")
            with self.assertRaisesRegex(
                RuntimeError,
                "content hash mismatch: README.md",
            ):
                release_package.verify_portable_publication_commit(root, "HEAD")

            (root / "README.md").unlink()
            self._git(root, "add", "-u", "README.md")
            self._git(root, "commit", "-m", "Remove portable file")
            with self.assertRaisesRegex(RuntimeError, "missing=.*README.md"):
                release_package.verify_portable_publication_commit(root, "HEAD")
            self.assertEqual(plugin, plugin_path.read_bytes())

    def test_canonical_source_tree_cannot_issue_a_production_release(self) -> None:
        if not (ROOT / "export/EXPORT_SOURCES.json").is_file(): self.skipTest("test applies to canonical source tree")
        with TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(RuntimeError,"explicit external repository identity"):
                release_package.build(Path(temporary)/"release")

    def test_production_provenance_requires_exact_marker_branch_upstream_and_remote(self) -> None:
        records=[{"path":"README.md","sha256":"A"*64,"bytes":1,"mode":"100644","license":"Apache-2.0","origin":"canonical_source"}]
        manifest={"source_commit":"a"*40,"tree_sha256":release_package.sha256(release_package.canonical_json(records)),"content_files":records}
        with TemporaryDirectory() as temporary:
            root=Path(temporary); (root/".dual-hat").mkdir(); manifest_bytes=release_package.canonical_json(manifest); (root/".dual-hat/export-manifest.json").write_bytes(manifest_bytes)
            marker={"schema":"dual-hat-published-state/1.0","license_expression":"Apache-2.0","source_commit":"a"*40,"tree_sha256":manifest["tree_sha256"],"manifest_sha256":sha256(manifest_bytes),"previous_export_identity":None,"canonical_branch":"main"}; (root/".dual-hat/published-state.json").write_text(json.dumps(marker),encoding="utf-8")
            responses={("rev-parse","HEAD"):"b"*40,("status","--porcelain=v1","--","."):"",("branch","--show-current"):"main",("rev-parse","--abbrev-ref","--symbolic-full-name","@{upstream}"):"origin/main",("rev-parse","origin/main"):"b"*40,("remote","get-url","origin"):"https://token@example.invalid/approved/dual-hat.git",("remote","get-url","--push","origin"):"git@example.invalid:approved/dual-hat.git",("ls-remote","--heads","origin","refs/heads/main"):"%s\trefs/heads/main"%("b"*40),("rev-parse",("b"*40)+"^{tree}"):"c"*40}
            committed={"commit":"b"*40,"manifest_sha256":marker["manifest_sha256"]}
            with patch.object(release_package,"ROOT",root), patch.object(release_package,"_git",side_effect=lambda *args:responses[args]), patch.object(release_package,"_is_ancestor",return_value=True), patch.object(release_package,"verify_commit_tree",return_value=committed):
                record=release_package.release_provenance_record("https://example.invalid/approved/dual-hat.git")
                self.assertEqual(("a"*40,"b"*40),release_package.release_provenance("git@example.invalid:approved/dual-hat.git")); self.assertNotIn("token",json.dumps(record))
                responses[("rev-parse","origin/main")]="c"*40
                with self.assertRaisesRegex(RuntimeError,"not aligned"): release_package.release_provenance_record("example.invalid/approved/dual-hat")
                responses[("rev-parse","origin/main")]="b"*40
                responses[("ls-remote","--heads","origin","refs/heads/main")]="%s\trefs/heads/main"%("d"*40)
                with self.assertRaisesRegex(RuntimeError,"not aligned"): release_package.release_provenance_record("example.invalid/approved/dual-hat")
                responses[("ls-remote","--heads","origin","refs/heads/main")]="%s\trefs/heads/main"%("b"*40)
                responses[("remote","get-url","--push","origin")]="git@example.invalid:other/fork.git"
                with self.assertRaisesRegex(RuntimeError,"endpoint"): release_package.release_provenance_record("example.invalid/approved/dual-hat")
                responses[("remote","get-url","--push","origin")]="git@example.invalid:approved/dual-hat.git"
                marker["canonical_branch"]="dev"; (root/".dual-hat/published-state.json").write_text(json.dumps(marker),encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError,"marker contract"): release_package.release_provenance_record("example.invalid/approved/dual-hat")

    @unittest.skipIf(
        os.environ.get("DUAL_HAT_RELEASE_SELF_TEST_CHILD") == "1",
        "outer release self-test already proves deterministic packaging",
    )
    def test_release_self_test(self) -> None:
        with patch.object(release_package, "release_provenance", return_value=("a" * 40, "b" * 40)):
            result = release_package.self_test()
        self.assertTrue(result["deterministic"])
        self.assertEqual(result["archive_sha256"], result["second_archive_sha256"])
        self.assertEqual("passed", result["extracted_framework_validation"])

    @unittest.skipUnless(
        (ROOT / "export/EXPORT_SOURCES.json").is_file() or (ROOT / ".dual-hat/export-manifest.json").is_file(),
        "release construction requires canonical or publication controls",
    )
    def test_release_manifest_record_forgery_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary, patch.object(
                release_package, "release_provenance", return_value=("a" * 40, "b" * 40)):
            output = Path(temporary) / "release"
            release_package.build(output, production=False)
            manifest_path = output / f"dual-hat-{release_package.version()}.release.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"][0]["sha256"] = "F" * 64
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "entry count is inconsistent"):
                release_package.validate_release_set(output, require_publication_provenance=False)

    @unittest.skipUnless(
        (ROOT / "export/EXPORT_SOURCES.json").is_file() or (ROOT / ".dual-hat/export-manifest.json").is_file(),
        "release construction requires canonical or publication controls",
    )
    def test_nonproduction_package_cannot_claim_production_provenance(self) -> None:
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "release"
            release_package.build(output, production=False)
            with self.assertRaisesRegex(RuntimeError, "nonpublishable release plan"):
                release_package.validate_release_set(output, require_publication_provenance=True)

    @unittest.skipIf(os.environ.get("DUAL_HAT_RELEASE_SELF_TEST_CHILD") == "1", "outer source-tree test owns remote-identity propagation")
    def test_expected_remote_identity_reaches_production_release_validation(self) -> None:
        with TemporaryDirectory() as temporary:
            output=Path(temporary)/"release"; release_package.build(output,production=False)
            manifest_path=output/f"dual-hat-{release_package.version()}.release.json"; manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
            record={"schema":"dual-hat-remote-publication-provenance/1.0","canonical_source_commit":manifest["canonical_source_commit"],"external_publication_commit":manifest["external_publication_commit"]}
            manifest["release_mode"]="production_standalone"; manifest["publication_provenance"]=record; manifest_path.write_bytes(release_package.canonical_json(manifest))
            with patch.object(release_package,"release_provenance_record",return_value=record) as verified:
                release_package.validate_release_set(output,require_publication_provenance=True,expected_remote_identity="example.invalid/approved/dual-hat")
            verified.assert_called_once_with(
                "example.invalid/approved/dual-hat",
                publication_commit=manifest["external_publication_commit"],
            )

    @unittest.skipUnless(
        (ROOT / "export/EXPORT_SOURCES.json").is_file() or (ROOT / ".dual-hat/export-manifest.json").is_file(),
        "release construction requires canonical or publication controls",
    )
    def test_release_output_reparse_point_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "actual"; target.mkdir()
            link = root / "release"
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError:
                self.skipTest("host does not permit a directory symlink fixture")
            with patch.object(release_package, "release_provenance", return_value=("a" * 40, "b" * 40)):
                with self.assertRaisesRegex(RuntimeError, "reparse point"):
                    release_package.build(link, production=False)

    def test_version_and_notes_agree(self) -> None:
        version = json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))["version"]
        self.assertIn(version, (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / f"release/RELEASE_NOTES_v{version}.md").is_file())


if __name__ == "__main__":
    unittest.main()
