"""Release package contract tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

DUAL_HAT_CAPABILITY_PROOFS = {"governed_publication", "binary_secret_gate", "committed_tree_release_binding", "transactional_writes"}


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
sys.path.insert(0, str(ROOT / "tests"))
from test_framework import available_reparse_flavours, make_reparse, remove_reparse  # noqa: E402
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

    @classmethod
    def _publication_sandbox(cls, root: Path, name: str = "work") -> tuple[Path, Path]:
        """A throwaway repository on origin/main, and the bare repo it publishes to.

        Real git, real refs, no network: every endpoint is a bare repository
        inside the caller's temporary directory. The endpoint checks under test
        run against genuine ``remote.origin.*`` configuration rather than a
        stubbed ``_git``, because the defect these tests exist for is what git
        itself returns for a query -- a stub would encode the same wrong belief
        the shipped code holds and would agree with it.
        """
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
                        with self.assertRaisesRegex(RuntimeError, "containment"):
                            release_package.source_files()
                finally:
                    remove_reparse(link)

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
        # Ran as a permanent skip on any host without symlink privilege. Both
        # flavours are directory reparse points here, so the fixture bodies are
        # identical and only the way the link is made differs.
        with TemporaryDirectory() as probe:
            flavours = available_reparse_flavours(Path(probe))
        if not flavours:
            self.skipTest("host permits neither a symlink nor a junction fixture")
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

    def test_release_maturity_agrees_with_the_major_it_derives_from(self) -> None:
        # The invariant is that the label agrees with its own major, not that
        # any one version is special -- so the majors are enumerated and the
        # versions are BUILT from them. A per-version literal here would need
        # rewriting at every major and would prove nothing about 3.0.0, which
        # is the recurrence this exists to prevent: the 0.x-to-1.x boundary was
        # fixed by hand, nothing kept it synchronized, and the identical
        # contradiction returned at 1.x-to-2.x.
        #
        # The expectation is restated here from the major rather than read back
        # from release_maturity(). Comparing the function against itself is the
        # exact blindness this test exists to break.
        for major, rest in ((0, "9.0"), (1, "18.5"), (2, "0.0"), (3, "4.1"), (10, "0.0")):
            with self.subTest(major=major):
                version = f"{major}.{rest}"
                implied = f"stable_{major}_x" if major >= 1 else "functional_pre_1_0"
                self.assertEqual(
                    implied, release_package.release_maturity(version),
                    f"the maturity label derived for {version} contradicts its own major",
                )

    def test_no_superseded_endpoint_query_or_stray_maturity_literal_survives(self) -> None:
        # Rule 20's migration half, for both conventions this change supersedes.
        modules = {
            path.relative_to(ROOT).as_posix(): ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for path in sorted((ROOT / "tooling").glob("*.py"))
        }

        # (a) No consumer still resolves a remote endpoint with the
        # single-endpoint query. `git remote get-url` without --all returns one
        # url while git uses every configured one, so any surviving call site
        # is a second, weaker answer to a question this change settled.
        single_endpoint = [
            f"{path}:{node.lineno}"
            for path, tree in modules.items()
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            for arguments in ([a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)],)
            if "get-url" in arguments and "--all" not in arguments
        ]
        with self.subTest(convention="remote endpoint query"):
            self.assertEqual(
                [], single_endpoint,
                "a remote endpoint is still resolved with `git remote get-url` without --all, "
                "which reports only the first url while git uses every configured one",
            )

        # (b) No maturity literal survives outside the one derivation. A label
        # spelled out anywhere else is a second authority for a value
        # release_maturity() owns, and is how a hand-written boundary gets
        # reintroduced.
        derivation = [
            node for tree in modules.values() for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "release_maturity"
        ]
        self.assertEqual(1, len(derivation), "maturity is derived in more than one place, or in none")
        inside = {id(node) for node in ast.walk(derivation[0])}
        stray = [
            f"{path}:{node.lineno}: {node.value!r}"
            for path, tree in modules.items()
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and re.fullmatch(r"stable_[0-9]+_x|functional_pre_1_0", node.value)
            and id(node) not in inside
        ]
        with self.subTest(convention="maturity label"):
            self.assertEqual(
                [], stray,
                "a maturity label literal survives outside release_maturity(), the one "
                "authority for it",
            )

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
        # major the shipped version carries, so 3.0.0 must bring its own
        # section rather than inheriting this one.
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
