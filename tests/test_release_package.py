"""Release package contract tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
sys.path.insert(0, str(ROOT / "tests"))
from test_framework import (  # noqa: E402
    assert_probed_flavours_all_ran, available_reparse_flavours, make_reparse, remove_reparse,
)
import release_package  # noqa: E402
from content_security import ContentSecurityError, inspect_content_set, sha256  # noqa: E402
from release_artifacts import is_release_product  # noqa: E402

DUAL_HAT_CAPABILITY_PROOFS = {"governed_publication", "binary_secret_gate", "committed_tree_release_binding", "transactional_writes"}


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

    @classmethod
    def _publication_sandbox(cls, root: Path, name: str = "work") -> tuple[Path, Path]:
        """A throwaway repository on origin/main, and the bare repo it publishes to."""
        approved = root / f"{name}-approved.git"
        work = root / name
        cls._git(root, "init", "--bare", "-b", "main", str(approved))
        cls._git(root, "init", "-b", "main", str(work))
        cls._git(work, "config", "user.name", "Dual Hat Release Test")
        cls._git(work, "config", "user.email", "dual-hat-release@example.invalid")
        (work / "README.md").write_text("sandbox\n", encoding="utf-8")
        cls._git(work, "add", "README.md")
        cls._git(work, "commit", "-m", "Sandbox publication commit")
        cls._git(work, "remote", "add", "origin", str(approved))
        cls._git(work, "push", "-u", "origin", "main")
        return work, approved

    def test_every_configured_push_endpoint_is_proven_not_only_the_first(self) -> None:
        # git pushes to EVERY configured remote.origin.pushurl, and
        # `git remote get-url --push` without --all reports only the first.
        # The Red for this is not that a flag is missing from a command string
        # -- that would pass against a fix that added the flag and ignored the
        # extra lines. The Red is that with a genuinely unapproved second push
        # endpoint configured, the shipped check returns a PASS record.
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, approved = self._publication_sandbox(root)
            unapproved = root / "unapproved.git"
            self._git(root, "init", "--bare", "-b", "main", str(unapproved))
            self._git(work, "remote", "set-url", "--push", "origin", str(approved))
            self._git(work, "remote", "set-url", "--add", "--push", "origin", str(unapproved))
            self.assertEqual(
                2, len(self._git(work, "remote", "get-url", "--all", "--push", "origin").splitlines()),
                "fixture did not configure a second push endpoint",
            )
            with patch.object(release_package, "ROOT", work):
                with self.assertRaisesRegex(RuntimeError, "endpoint"):
                    release_package.fresh_remote_repository_state(str(approved))

    def test_every_configured_fetch_endpoint_is_proven_not_only_the_first(self) -> None:
        # The defect is the query shape and it is present on both lines. The
        # push endpoint is left explicitly approved here so that only the
        # fetch side is unproven and the failure cannot be the push side's.
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, approved = self._publication_sandbox(root, "fetchwork")
            unapproved = root / "unapproved.git"
            self._git(root, "init", "--bare", "-b", "main", str(unapproved))
            self._git(work, "remote", "set-url", "--push", "origin", str(approved))
            self._git(work, "config", "--add", "remote.origin.url", str(unapproved))
            self.assertEqual(
                2, len(self._git(work, "remote", "get-url", "--all", "origin").splitlines()),
                "fixture did not configure a second fetch endpoint",
            )
            with patch.object(release_package, "ROOT", work):
                with self.assertRaisesRegex(RuntimeError, "endpoint"):
                    release_package.fresh_remote_repository_state(str(approved))

    def test_remote_state_record_cannot_assert_a_singular_verified_endpoint(self) -> None:
        # The evidence-integrity half, and a SEPARATE defect from the query.
        # Both endpoints here resolve to the approved identity, so the check
        # legitimately passes -- and the record it signs must then state what
        # it actually proved. A scalar "push_endpoint_identity" covering two
        # configured endpoints is a singular verified claim about a plural
        # fact: it is not merely incomplete, it reads as complete.
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, approved = self._publication_sandbox(root, "recordwork")
            same_endpoint_other_spelling = str(approved).replace("\\", "/")
            self._git(work, "remote", "set-url", "--push", "origin", str(approved))
            self._git(work, "remote", "set-url", "--add", "--push", "origin", same_endpoint_other_spelling)
            self._git(work, "config", "--add", "remote.origin.url", same_endpoint_other_spelling)
            identity = release_package._remote_identity(str(approved))
            with patch.object(release_package, "ROOT", work):
                state = release_package.fresh_remote_repository_state(str(approved))
            for side in ("fetch", "push"):
                with self.subTest(side=side):
                    self.assertNotIn(
                        f"{side}_endpoint_identity", state,
                        f"the record still carries a singular verified {side} endpoint while two are configured",
                    )
                    self.assertEqual(
                        [identity, identity], state[f"{side}_endpoint_identities"],
                        f"the record does not enumerate every verified {side} endpoint",
                    )

    def test_single_endpoint_passes_and_instead_of_rewriting_still_fails_closed(self) -> None:
        # Regression guard for two behaviours that must survive the repair.
        # The second is correct behaviour reached incidentally -- `get-url`
        # reports the REWRITTEN url, so the identity comparison fails closed --
        # and nothing else protects it. It is not to be "fixed".
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            work, approved = self._publication_sandbox(root, "singlework")
            with patch.object(release_package, "ROOT", work):
                state = release_package.fresh_remote_repository_state(str(approved))
            self.assertEqual("main", state["branch"])
            identity = release_package._remote_identity(str(approved))
            self.assertEqual([identity], state["push_endpoint_identities"])
            self.assertEqual([identity], state["fetch_endpoint_identities"])
            rewritten = (root / "rewritten.git").as_posix()
            self._git(work, "config", f"url.{rewritten}.insteadOf", str(approved))
            with patch.object(release_package, "ROOT", work):
                with self.assertRaisesRegex(RuntimeError, "endpoint"):
                    release_package.fresh_remote_repository_state(str(approved))

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
        # Ran as a permanent skip on any host without symlink privilege. See
        # tests/test_framework.py's reparse-fixture support: the junction is an
        # additional route to this guard, not a replacement for the symlink.
        with TemporaryDirectory() as probe:
            flavours = available_reparse_flavours(Path(probe))
        if not flavours:
            self.skipTest("host permits neither a symlink nor a junction fixture")
        ran = []
        for flavour in flavours:
            with self.subTest(reparse=flavour), TemporaryDirectory() as temporary, TemporaryDirectory() as outside:
                root = Path(temporary); (root / "export").mkdir()
                if flavour == "symlink":
                    target = Path(outside) / "payload.md"; target.write_text("outside", encoding="utf-8")
                    link = root / "payload.md"; declared = "payload.md"
                else:
                    # A junction points only at a directory, so the allowlisted
                    # path crosses the reparse point instead of being it. Either
                    # way the declared source resolves outside the release root,
                    # which is the escape the guard exists to refuse.
                    target = Path(outside) / "payload"; target.mkdir()
                    (target / "payload.md").write_text("outside", encoding="utf-8")
                    link = root / "payload"; declared = "payload/payload.md"
                self.assertTrue(make_reparse(link, target, flavour), f"{flavour} fixture failed after probing as available")
                try:
                    (root / "export/EXPORT_SOURCES.json").write_text(json.dumps({"included": [declared]}), encoding="utf-8")
                    with patch.object(release_package, "ROOT", root):
                        # `root` is a bare TemporaryDirectory, never a
                        # git repository -- this fixture tests the containment
                        # guard against a reparse-point escape, a property
                        # orthogonal to commit-binding, which the new
                        # git-cleanliness check cannot evaluate here at all.
                        with self.assertRaisesRegex(RuntimeError, "containment"):
                            release_package.source_files(require_clean=False)
                finally:
                    remove_reparse(link)
                ran.append(flavour)
        assert_probed_flavours_all_ran(self, flavours, ran)

    def test_private_key_and_embedded_token_are_rejected(self) -> None:
        for value in (
            b"-----BEGIN " + b"PRIVATE KEY-----\nfixture",
            b"access_" + b"token = '" + b"abcdefghijklmnopqrstuvwxyz123456'",
            b"xoxb" + b"-0123456789012-0123456789012-abcdefghijklmnopqrstuvwx",
            b"AIza" + b"SyD-fixturefixturefixturefixturefix",
            b"sk_liv" + b"e_fixture0123456789abcdefgh",
            b"eyJhbGciOiJIUzI1NiJ9" + b".eyJzdWIiOiJmaXh0dXJlIn0" + b".fixturefixturefixturefixture",
        ):
            with self.subTest(value=value[:20]):
                with self.assertRaisesRegex(ContentSecurityError, "possible secrets"):
                    inspect_content_set({"configuration.txt": value})

    @unittest.skipUnless(
        (ROOT / "export/EXPORT_SOURCES.json").is_file() or (ROOT / ".dual-hat/export-manifest.json").is_file(),
        "release construction requires canonical or publication controls",
    )
    def test_release_set_is_exact_and_a_foreign_file_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "release"
            result = release_package.build(output, production=False)
            self.assertEqual("nonpublishable_plan", result["release_mode"])
            (output / "unexpected.release.txt").write_text("unexpected", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "membership mismatch"):
                release_package.validate_release_set(output, require_publication_provenance=False)

    @unittest.skipUnless(
        (ROOT / "export/EXPORT_SOURCES.json").is_file() or (ROOT / ".dual-hat/export-manifest.json").is_file(),
        "release construction requires canonical or publication controls",
    )
    def test_build_failure_after_commit_leaves_output_untouched_and_journal_recoverable(self) -> None:
        """`fail_after_commit` fires right after the transaction commits and before `_txn.apply()` runs, so no release artifact under `output` (besides the journal directory, which is never itself a release..."""
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "release"
            with self.assertRaisesRegex(RuntimeError, "injected"):
                release_package.build(output, fail_after_commit=True, production=False)
            self.assertEqual([], [path.name for path in output.iterdir() if path.is_file()])
            self.assertEqual(len(release_package._txn.scan(output)), 1, "the committed journal survives")
            completed = release_package._txn.recover_pending(output)
            self.assertEqual(len(completed), 1)
            release_package.validate_release_set(output, require_publication_provenance=False)
            self.assertEqual(release_package._txn.scan(output), ())
            self.assertFalse((output / release_package._txn.JOURNAL_DIR).exists())


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
                # `root` is a bare TemporaryDirectory, never a git
                # repository -- this fixture tests the manifest-owned
                # classification match itself, a property orthogonal to
                # commit-binding, which `require_clean` cannot evaluate here.
                self.assertEqual({"README.md": portable}, release_package.source_files(require_clean=False))
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

    @staticmethod
    def _write_binding_publication(root: Path) -> None:
        """A composite-publication sandbox that also carries a valid `release/VERSION.json` as a canonical-source entry, so `build()` -- which `_write_composite_publication` above never needed to satisfy --..."""
        readme = b"# Portable framework\n"
        version_json = release_package.canonical_json({
            "$comment": "SPDX-License-Identifier: Apache-2.0",
            "maturity": "functional_pre_1_0",
            "schema": "dual-hat-version/1.0",
            "stability": "test fixture",
            "version": "0.1.0",
        })
        records = [
            {"path": "README.md", "sha256": sha256(readme), "bytes": len(readme),
             "mode": "100644", "license": "Apache-2.0", "origin": "canonical_source"},
            {"path": "release/VERSION.json", "sha256": sha256(version_json), "bytes": len(version_json),
             "mode": "100644", "license": "Apache-2.0", "origin": "canonical_source"},
        ]
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
        (root / "release").mkdir(parents=True)
        (root / "plugins/dual-hat").mkdir(parents=True)
        (root / "README.md").write_bytes(readme)
        (root / "release/VERSION.json").write_bytes(version_json)
        (root / ".dual-hat/export-manifest.json").write_bytes(manifest_bytes)
        (root / ".dual-hat/published-state.json").write_bytes(release_package.canonical_json(marker))
        (root / "plugins/dual-hat/plugin.json").write_bytes(b'{"name":"standalone-deployment"}\n')

    def test_dirty_collected_path_makes_a_nonproduction_build_refuse(self) -> None:
        """`source_files()` -- the collection path every non-production build (the framework's own `self_test()` included) reads from -- is now bound to the commit `build()` stamps: a collected path that..."""
        with TemporaryDirectory() as sandbox, TemporaryDirectory() as outputs:
            root = Path(sandbox)
            self._write_binding_publication(root)
            self._git(root, "init", "-b", "main")
            self._git(root, "config", "user.name", "Dual Hat Release Test")
            self._git(root, "config", "user.email", "dual-hat-release@example.invalid")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "Binding publication sandbox")
            head = self._git(root, "rev-parse", "HEAD")
            # Outputs live in a SEPARATE temporary directory, never under
            # `root`/`ROOT` -- a build's own output directory is otherwise
            # read back as unclassified content by the very next collection.
            def _canonical_source_commit(output: Path) -> str:
                manifest_path = output / f"dual-hat-{release_package.version()}.release.json"
                return json.loads(manifest_path.read_text(encoding="utf-8"))["canonical_source_commit"]

            def _propagate_uncommitted_readme_edit(new_bytes: bytes) -> None:
                """Mirror what a release orchestrator's propagation step actually does: rewrite README.md AND its export-manifest declaration together, consistently, then leave both uncommitted."""
                manifest_path = root / ".dual-hat/export-manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                for row in manifest["content_files"]:
                    if row["path"] == "README.md":
                        row["sha256"] = sha256(new_bytes)
                        row["bytes"] = len(new_bytes)
                manifest["tree_sha256"] = sha256(release_package.canonical_json(manifest["content_files"]))
                manifest_path.write_bytes(release_package.canonical_json(manifest))
                (root / "README.md").write_bytes(new_bytes)

            with patch.object(release_package, "ROOT", root):
                clean_output = Path(outputs) / "out-clean"
                release_package.build(clean_output, production=False)
                self.assertEqual(head, _canonical_source_commit(clean_output))

                # Dirty exactly one collected path, without committing --
                # consistently with its own manifest declaration, exactly as
                # the real mid-propagation state is (manifest and content
                # agree; only the git commit lags behind).
                _propagate_uncommitted_readme_edit(b"uncommitted edit\n")
                dirty_output = Path(outputs) / "out-dirty"
                with self.assertRaisesRegex(RuntimeError, "dirty"):
                    release_package.build(dirty_output, production=False)

                # The one enumerated, disclosed caller with a real reason to
                # build from a dirty tree still can, by explicit request.
                allowed_output = Path(outputs) / "out-allowed"
                release_package.build(
                    allowed_output, production=False, allow_uncommitted_source=True,
                )
                self.assertEqual(head, _canonical_source_commit(allowed_output))

                # Refused outright for a production build: dirty tolerance
                # must never reach the path that stamps a real publication.
                with self.assertRaisesRegex(RuntimeError, "only valid for a non-production build"):
                    release_package.build(
                        Path(outputs) / "out-prod", production=True,
                        allow_uncommitted_source=True, expected_remote_identity="x",
                    )

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
            responses={("rev-parse","HEAD"):"b"*40,("status","--porcelain=v1","--","."):"",("branch","--show-current"):"main",("rev-parse","--abbrev-ref","--symbolic-full-name","@{upstream}"):"origin/main",("rev-parse","origin/main"):"b"*40,("remote","get-url","--all","origin"):"https://token@example.invalid/approved/dual-hat.git",("remote","get-url","--all","--push","origin"):"git@example.invalid:approved/dual-hat.git",("ls-remote","--heads","origin","refs/heads/main"):"%s\trefs/heads/main"%("b"*40),("rev-parse",("b"*40)+"^{tree}"):"c"*40}
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
                responses[("remote","get-url","--all","--push","origin")]="git@example.invalid:other/fork.git"
                with self.assertRaisesRegex(RuntimeError,"endpoint"): release_package.release_provenance_record("example.invalid/approved/dual-hat")
                responses[("remote","get-url","--all","--push","origin")]="git@example.invalid:approved/dual-hat.git"
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


    @unittest.skipIf(os.environ.get("DUAL_HAT_RELEASE_SELF_TEST_CHILD") == "1", "outer source-tree test owns remote-identity propagation")
    def test_expected_remote_identity_reaches_production_release_validation(self) -> None:
        with TemporaryDirectory() as temporary:
            output=Path(temporary)/"release"; release_package.build(output,production=False)
            manifest_path=output/f"dual-hat-{release_package.version()}.release.json"; manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
            # The schema string is read from the module's own constant rather
            # than typed as a literal here, so this fixture cannot go stale
            # against a future schema bump the way a hand-typed "/1.0" once
            # did -- inert either way, since `release_provenance_record` is
            # patched to return this exact record and the record is
            # therefore compared against itself, but at least the ONE fact
            # this fixture asserts (the identity is propagated) cannot rot.
            record={"schema":release_package.PUBLICATION_PROVENANCE_SCHEMA,"canonical_source_commit":manifest["canonical_source_commit"],"external_publication_commit":manifest["external_publication_commit"]}
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
    def test_validate_release_set_drives_the_unpatched_provenance_record_against_a_real_remote(self) -> None:
        """Every other production-path test above reaches the endpoint verification only through a patched `_git` or a patched `release_provenance_record` itself."""
        with TemporaryDirectory() as sandbox, TemporaryDirectory() as outputs:
            container = Path(sandbox)
            work = container / "work"
            work.mkdir()
            self._write_binding_publication(work)
            approved = container / "approved.git"
            self._git(container, "init", "--bare", "-b", "main", str(approved))
            self._git(work, "init", "-b", "main")
            self._git(work, "config", "user.name", "Dual Hat Release Test")
            self._git(work, "config", "user.email", "dual-hat-release@example.invalid")
            self._git(work, "add", ".")
            self._git(work, "commit", "-m", "Binding publication sandbox")
            self._git(work, "remote", "add", "origin", str(approved))
            self._git(work, "push", "-u", "origin", "main")
            output = Path(outputs) / "release"
            with patch.object(release_package, "ROOT", work):
                built = release_package.build(output, production=True, expected_remote_identity=str(approved))
                self.assertEqual("production_standalone", built["release_mode"])
                # Passes on the approved identity: a second, direct call
                # through the public validation entry point, unpatched,
                # exactly as the design for this seam asks for.
                release_package.validate_release_set(
                    output, require_publication_provenance=True, expected_remote_identity=str(approved),
                )
                # Refused when a second `pushurl` names another bare
                # repository -- the exact vector the identity contract
                # above exists to close, now proven at the level a real
                # release manifest is actually validated against.
                unapproved = container / "unapproved.git"
                self._git(container, "init", "--bare", "-b", "main", str(unapproved))
                self._git(work, "remote", "set-url", "--add", "--push", "origin", str(unapproved))
                with self.assertRaisesRegex(RuntimeError, "endpoint"):
                    release_package.validate_release_set(
                        output, require_publication_provenance=True, expected_remote_identity=str(approved),
                    )

    def test_remote_identity_keeps_a_non_default_port_and_collapses_the_scheme_default(self) -> None:
        approved = release_package._remote_identity("https://example.invalid/org/dual-hat.git")
        self.assertEqual(
            approved, release_package._remote_identity("https://example.invalid:443/org/dual-hat.git"),
            "the scheme's own default port must collapse to the same identity as omitting it",
        )
        self.assertEqual(
            approved, release_package._remote_identity("ssh://git@example.invalid:22/org/dual-hat.git"),
            "ssh's own default port must collapse to the same identity as omitting it",
        )
        self.assertNotEqual(
            approved, release_package._remote_identity("https://example.invalid:8443/org/dual-hat.git"),
            "a non-default port names a different repository identity",
        )

    def test_remote_identity_refuses_a_downgraded_push_transport_never_collapsing_it(self) -> None:
        approved = release_package._remote_identity("https://example.invalid/org/dual-hat.git")
        for scheme in ("http", "git"):
            with self.subTest(scheme=scheme):
                with self.assertRaisesRegex(RuntimeError, "refused transport"):
                    release_package._remote_identity(f"{scheme}://example.invalid/org/dual-hat.git", push=True)
        # A transport downgrade is refused only where `push` says this
        # value is being compared AS a push endpoint. Scheme was never part
        # of the identity string at all -- only host and a non-default port
        # are -- so the identical spelling remains an ordinary fetch
        # endpoint identity, equal to the approved one, on the non-push call
        # path; this function does not decide fetch endpoint policy, proven
        # here by executing that path rather than asserted from its
        # signature.
        self.assertEqual(approved, release_package._remote_identity("http://example.invalid/org/dual-hat.git"))

    def test_remote_identity_still_normalises_userinfo_scp_form_suffix_case_and_slashes(self) -> None:
        # Positive control for the deliberate collapses this repair leaves
        # alone: a refusal-shaped fix must not also refuse -- or stop
        # matching -- a spelling that was always meant to compare equal.
        approved = release_package._remote_identity("https://example.invalid/org/dual-hat.git")
        for spelling in (
            "https://token@example.invalid/org/dual-hat.git",
            "https://user:password@example.invalid/org/dual-hat.git",
            "ssh://git@example.invalid/org/dual-hat.git",
            "git@example.invalid:org/dual-hat.git",
            "https://example.invalid/org/dual-hat",
            "HTTPS://EXAMPLE.INVALID/ORG/DUAL-HAT.GIT",
            "https://example.invalid/org/dual-hat.git?ref=main",
            "https://example.invalid/org/dual-hat.git#fragment",
            "https://example.invalid//org/dual-hat.git",
        ):
            with self.subTest(spelling=spelling):
                self.assertEqual(approved, release_package._remote_identity(spelling))


    def test_fresh_remote_repository_state_refuses_a_diverted_push_default_naming_the_key_and_value(self) -> None:
        # The push-routing vector this endpoint check cannot otherwise see:
        # `origin`'s own configured endpoints stay entirely clean in both
        # cases, and a bare `git push` would still land somewhere else.
        for key, mutate in (
            ("remote.pushDefault", lambda work, diverted: self._git(work, "config", "remote.pushDefault", "diverted")),
            ("branch.main.pushRemote", lambda work, diverted: self._git(work, "config", "branch.main.pushRemote", "diverted")),
        ):
            with self.subTest(key=key):
                with TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    work, approved = self._publication_sandbox(root, f"divertwork-{key.replace('.', '-')}")
                    diverted = root / "diverted.git"
                    self._git(root, "init", "--bare", "-b", "main", str(diverted))
                    self._git(work, "remote", "add", "diverted", str(diverted))
                    mutate(work, diverted)
                    with patch.object(release_package, "ROOT", work):
                        with self.assertRaisesRegex(RuntimeError, re.escape(key) + r"='diverted'"):
                            release_package.fresh_remote_repository_state(str(approved))


    @unittest.skipUnless(
        (ROOT / "export/EXPORT_SOURCES.json").is_file() or (ROOT / ".dual-hat/export-manifest.json").is_file(),
        "release construction requires canonical or publication controls",
    )
    def test_release_output_reparse_point_is_rejected(self) -> None:
        # Ran as a permanent skip on any host without symlink privilege. Both
        # flavours are directory reparse points here, so the fixture bodies are
        # identical and only the way the link is made differs.
        with TemporaryDirectory() as probe:
            flavours = available_reparse_flavours(Path(probe))
        if not flavours:
            self.skipTest("host permits neither a symlink nor a junction fixture")
        ran = []
        for flavour in flavours:
            with self.subTest(reparse=flavour), TemporaryDirectory() as temporary:
                root = Path(temporary)
                target = root / "actual"; target.mkdir()
                link = root / "release"
                self.assertTrue(make_reparse(link, target, flavour), f"{flavour} fixture failed after probing as available")
                try:
                    with patch.object(release_package, "release_provenance", return_value=("a" * 40, "b" * 40)):
                        with self.assertRaisesRegex(RuntimeError, "reparse point"):
                            release_package.build(link, production=False)
                finally:
                    remove_reparse(link)
                ran.append(flavour)
        assert_probed_flavours_all_ran(self, flavours, ran)

    def test_version_refuses_malformed_governed_release_evidence(self) -> None:
        """`version()` is a second entry point to the same `release/VERSION.json` authority `active_core_version()` validates, and previously performed none of that validation itself."""
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "release").mkdir(parents=True)
            bad = {
                "$comment": "SPDX-License-Identifier: Apache-2.0",
                "maturity": "stable_1_x",  # contradicts the declared version below
                "schema": "dual-hat-version/1.0",
                "stability": "test fixture",
                "version": "2.0.0",
            }
            (root / "release/VERSION.json").write_text(json.dumps(bad), encoding="utf-8")
            with patch.object(release_package, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "maturity contradicts"):
                    release_package.version()

    def test_release_maturity_refuses_each_malformed_shape(self) -> None:
        """Measured against the shipped module: every shape below either parsed silently to a plausible-looking label, or raised a bare `ValueError` outside this module's `RuntimeError` convention -- so a..."""
        for malformed in (
            "007.1.1", "1_0.0.0", " 2.0.0", "+2.0.0", "2.0.0-rc1", "2.x", "2",
            "2.0.0\n", "٠2.0.0", "", "abc",
        ):
            with self.subTest(malformed=malformed):
                with self.assertRaises(RuntimeError):
                    release_package.release_maturity(malformed)


    def test_release_identity_carries_notes_a_changelog_head_and_a_governed_migration(self) -> None:
        # Replaces the weaker test_version_and_notes_agree, and is stronger on
        # both halves that test asserted: the release-notes existence check is
        # carried unchanged, and `version appears somewhere in the CHANGELOG`
        # becomes `the CHANGELOG's head entry IS this version`. A version
        # mentioned in a two-year-old entry satisfied the old form.
        version = json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))["version"]
        major = version.split(".", 1)[0]

        with self.subTest(half="release notes"):
            self.assertTrue(
                (ROOT / f"release/RELEASE_NOTES_v{version}.md").is_file(),
                "the shipped version has no release notes of its own",
            )

        with self.subTest(half="changelog head"):
            headings = re.findall(r"(?m)^## +(\S+)", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))
            self.assertEqual(
                version, headings[0] if headings else "",
                "the CHANGELOG's head entry is not the version being shipped",
            )

        # release/VERSION.json's own stability string is the authority here:
        # "breaking changes require a new major version and governed
        # migration". A major that ships without one leaves the framework's
        # stated stability contract unmet by its own release. Anchored on the
        # major the shipped version carries, so EACH new major must bring its
        # own section rather than inheriting an earlier one.
        with self.subTest(half="governed migration"):
            migration = ROOT / "release/UPGRADING.md"
            self.assertTrue(
                migration.is_file(),
                "no governed migration document exists, and VERSION.json's own stability "
                "string requires one for a major version",
            )
            self.assertRegex(
                migration.read_text(encoding="utf-8"),
                rf"(?m)^## .*(?<![0-9]){re.escape(major)}\.0\.0(?![0-9])",
                "the governed migration document carries no section for the shipped major",
            )


if __name__ == "__main__":
    unittest.main()
