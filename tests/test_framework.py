# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations


import ast
import builtins
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))

from framework_completeness import (  # noqa: E402
    FORBIDDEN_DEPENDENCY_IMPORT_PATTERNS,
    repository_content_files,
    validate_framework,
)
from path_containment import is_reparse  # noqa: E402
from staged_publication import (  # noqa: E402
    BUNDLE_PAYLOAD,
    BUNDLE_ROOT,
    CORE_VERSION_KEY,
    PublicationValidationError,
    VERSION_AUTHORITY,
    declared_core_versions,
    main as staged_publication_main,
    stage_manifest_owned,
    validate_bundle_version_currency,
    validate_staged,
    verify_commit_tree,
)
from publication_ownership import standalone_owned  # noqa: E402

DUAL_HAT_CAPABILITY_PROOFS = {"canonical_path_containment", "network_policy_validation", "rights_readiness_validation"}


# --- reparse-point fixture support -------------------------------------------
#
# Single home for the reparse fixtures the path-containment guards need, shared
# by tests/test_quality_review.py and tests/test_release_package.py rather than
# reimplemented there. The junction half started life inline in
# test_staging_rejects_junction_without_touching_external_cache below; it is
# lifted here unchanged in behaviour so the five guards that used to skip can
# reach it instead of a second junction mechanism being written beside it.
#
# The two flavours are not interchangeable and neither replaces the other:
#
#   * a symlink is the stronger fixture, because it can point at a file as well
#     as a directory; but on some hosts creating one requires a privilege the
#     test process does not hold, which is why every guard below used to skip
#     permanently rather than run;
#   * a junction is directory-only and exists only on hosts that provide that
#     kind of reparse point, but it needs no such privilege. It is a real
#     reparse point, so it exercises the same guard by the same mechanism -- an
#     ADDITIONAL route to the assertion, not a substitute.
#
# A host that permits neither still skips, honestly and for a real reason.


def make_reparse(link: Path, target: Path, flavour: str) -> bool:
    """Point ``link`` at ``target``; return False if the host refuses that flavour."""
    if flavour == "symlink":
        try:
            link.symlink_to(target, target_is_directory=target.is_dir())
        except OSError:
            return False
        return True
    if flavour != "junction":
        raise ValueError(f"unknown reparse flavour: {flavour}")
    if os.name != "nt":
        return False
    created = subprocess.run(
        ("cmd", "/c", "mklink", "/J", str(link), str(target)),
        capture_output=True,
        text=True,
    )
    return not created.returncode and is_reparse(link)


def remove_reparse(link: Path) -> None:
    if not is_reparse(link):
        return
    try:
        link.rmdir()
    except OSError:
        link.unlink(missing_ok=True)


def available_reparse_flavours(base: Path) -> tuple[str, ...]:
    """Which reparse flavours this host actually permits, probed once per fixture."""
    probe_target = base / "reparse-probe-target"
    probe_target.mkdir(exist_ok=True)
    flavours = []
    for flavour in ("symlink", "junction"):
        probe = base / f"reparse-probe-{flavour}"
        if make_reparse(probe, probe_target, flavour):
            flavours.append(flavour)
            remove_reparse(probe)
    return tuple(flavours)


def assert_probed_flavours_all_ran(testcase, probed: "tuple[str, ...]", ran: list) -> None:
    """Fail when a reparse flavour the host permits did not run to completion."""
    testcase.assertEqual(
        list(probed), ran,
        f"host permits {list(probed)!r} but only {ran!r} ran to completion -- "
        "a flavour the host permits was skipped",
    )


# --- README "Framework areas" completeness (README completeness) ------------------------
#
# The list is a completeness claim about this repository's own top-level
# structure and nothing kept it synchronized: it drifted by seven of twenty-one
# directories before a review noticed. The two assertions that use these
# helpers check the two directions SEPARATELY, and both are required. A single
# listed-implies-exists check would have passed silently through the whole of
# that drift, because every directory that WAS listed did exist -- the seven the
# list omitted are invisible to it. The converse direction is not hypothetical
# either: a hand-maintained traversal list elsewhere in this project named a
# guide file that does not exist and had been sending every reader after it.
#
# What counts as a framework area is derived rather than enumerated. A
# leading-dot directory is tooling or repository metadata (.git, .dual-hat,
# .pytest_cache), never a framework area; and anything the repository's own
# ignore state excludes never reaches the comparison at all, because
# repository_content_files() has already pruned it.

FRAMEWORK_AREA_ABSENCE_EXEMPTIONS = {
    "export": (
        "Canonical-source-only distribution control. export/EXPORT_SOURCES.json and "
        "export/EXPORT_READINESS.json are the release packager's own control files and "
        "are deliberately excluded from the release set, so the directory is absent "
        "from an unpacked package while remaining a real area of the canonical "
        "repository. The exemption is inert wherever the canonical allowlist is "
        "present, so it cannot excuse the directory going missing here."
    ),
}


def readme_framework_areas() -> set[str]:
    """Every top-level directory README.md's "Framework areas" section claims exists."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    heading = "## Framework areas"
    if heading not in text:
        return set()
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    return {
        token[:-1]
        for line in section.splitlines()
        if line.lstrip().startswith("- ")
        for token in re.findall(r"`([^`]+)`", line)
        if token.endswith("/") and "/" not in token[:-1]
    }


def existing_framework_areas() -> set[str]:
    """Every real top-level directory of this tree that holds unignored content."""
    areas = {
        relative.split("/", 1)[0]
        for path in repository_content_files(ROOT)
        for relative in (path.relative_to(ROOT).as_posix(),)
        if "/" in relative and not relative.startswith(".")
    }
    return {area for area in areas if not standalone_owned(area + "/")}


MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)\s]+)")


def _normalized(relative: str, *, lower: bool = False) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    return " ".join((text.lower() if lower else text).split())


def _is_absent(requirement, text: str) -> bool:
    """A requirement is a phrase, or a tuple of interchangeable alternatives."""
    if isinstance(requirement, tuple):
        return not any(option in text for option in requirement)
    return requirement not in text


def _reference_resolves(source_relative: str, canonical_relative: str) -> bool:
    """True when source carries a reference resolving to exactly canonical.

    Both a markdown link and a bare repository-relative path mention count; a
    link to any other file does not, and a link to a path that does not exist
    does not.
    """
    canonical_path = (ROOT / canonical_relative).resolve()
    if not canonical_path.is_file():
        return False
    source_path = ROOT / source_relative
    text = source_path.read_text(encoding="utf-8")
    for target in MARKDOWN_LINK_PATTERN.findall(text):
        target = target.split("#", 1)[0].strip()
        if not target or "://" in target:
            continue
        try:
            resolved = (source_path.parent / target).resolve()
        except (OSError, ValueError):
            continue
        if resolved == canonical_path:
            return True
    return canonical_relative in " ".join(text.split())


def _reference_sentences(source_relative: str, canonical_relative: str,
                         *, lower: bool = False) -> list[str]:
    """Sentences of `source` that carry a reference resolving to `canonical`.

    Used to enforce that a pointer is a pointer. See
    `assert_single_canonical_home` for why this is not optional.
    """
    source_path = ROOT / source_relative
    canonical_path = (ROOT / canonical_relative).resolve()
    raw = source_path.read_text(encoding="utf-8")
    text = " ".join((raw.lower() if lower else raw).split())
    needles = [canonical_relative.lower() if lower else canonical_relative]
    for target in MARKDOWN_LINK_PATTERN.findall(raw):
        cleaned = target.split("#", 1)[0].strip()
        if not cleaned or "://" in cleaned:
            continue
        try:
            resolved = (source_path.parent / cleaned).resolve()
        except (OSError, ValueError):
            continue
        if resolved == canonical_path:
            needles.append(cleaned.lower() if lower else cleaned)
    return [sentence for sentence in re.split(r"(?<=[.!?])\s+", text)
            if any(needle in sentence for needle in needles)]


class CanonicalHomeAssertions:
    """Shared single-canonical-home predicate.

    Deliberately a plain mixin rather than a `TestCase` subclass: it is imported
    by `test_operating_modes.py`, and importing a `TestCase` into another test
    module makes the loader collect that module's tests a second time.
    """

    def assert_single_canonical_home(self, *, canonical, canonical_substance,
                                     secondaries, lower=False):
        """Assert one obligation is reachable from every file that owns a stake.

        `canonical_substance` is asserted unconditionally against `canonical`.
        `secondaries` maps each other file to the substance it must carry unless
        it defers to `canonical` by an explicit resolving reference.
        """
        canonical_text = _normalized(canonical, lower=lower)
        for requirement in canonical_substance:
            self.assertFalse(
                _is_absent(requirement, canonical_text),
                f"canonical home {canonical} no longer states {requirement!r}; "
                "the obligation has no home left",
            )
        for secondary, substance in secondaries.items():
            # A pointer that quotes the obligation it points at is not a
            # pointer. It satisfies the SUBSTANCE branch of this very predicate,
            # so the deferral passes for the wrong reason and the duplication
            # survives while the record says it was consolidated. This defect is
            # invisible to a check gated on `missing`, because the quoted text is
            # exactly what stops the phrase from being missing -- so the guard
            # runs unconditionally, before `missing` is consulted.
            #
            # Caught in drafting on the re-pointing pass, in that pass's
            # own work, which is why it is mechanised rather than remembered:
            # every re-point creates a fresh opportunity to write that sentence.
            for sentence in _reference_sentences(secondary, canonical, lower=lower):
                for requirement in substance:
                    self.assertTrue(
                        _is_absent(requirement, sentence),
                        f"{secondary} points at its canonical home {canonical} in "
                        f"a sentence that itself restates {requirement!r}: "
                        f"{sentence!r}. A reference must refer to the obligation, "
                        "not reproduce it -- otherwise the deferral is satisfied "
                        "by the duplicate it was written to remove.",
                    )
            text = _normalized(secondary, lower=lower)
            missing = [item for item in substance if _is_absent(item, text)]
            if not missing:
                continue
            self.assertTrue(
                _reference_resolves(secondary, canonical),
                f"{secondary} no longer states {missing!r} and carries no "
                f"reference resolving to its canonical home {canonical}; a "
                "reader of this file cannot reach the obligation",
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

    def test_readme_framework_areas_names_no_directory_that_is_absent(self):
        """Direction 1 of 2: listed implies exists."""
        listed = readme_framework_areas()
        self.assertTrue(listed, "README.md carries no parsable '## Framework areas' list")
        missing = listed - existing_framework_areas()
        if not (ROOT / "export/EXPORT_SOURCES.json").is_file():
            missing -= set(FRAMEWORK_AREA_ABSENCE_EXEMPTIONS)
        self.assertEqual(
            set(),
            missing,
            "README.md's 'Framework areas' list names directories that do not exist "
            f"in this tree: {sorted(missing)}. Direction checked: listed implies exists.",
        )

    def test_readme_framework_areas_omits_no_directory_that_exists(self):
        """Direction 2 of 2: exists implies listed."""
        unlisted = existing_framework_areas() - readme_framework_areas()
        self.assertEqual(
            set(),
            unlisted,
            "top-level framework areas exist that README.md's 'Framework areas' list "
            f"does not name: {sorted(unlisted)}. Direction checked: exists implies listed.",
        )

    def test_existing_framework_areas_excludes_standalone_owned_prefixes(self):
        """Direction 2 must not fire on a standalone-owned top-level directory."""
        global ROOT
        original_root = ROOT
        with tempfile.TemporaryDirectory() as raw_root:
            synthetic_root = Path(raw_root)
            (synthetic_root / "governance").mkdir()
            (synthetic_root / "governance" / "kept.md").write_text("kept\n", encoding="utf-8")
            (synthetic_root / "assets").mkdir()
            (synthetic_root / "assets" / "logo.png").write_bytes(b"not-a-real-image")
            (synthetic_root / "README.md").write_text(
                "# Synthetic\n\n## Framework areas\n\n- `governance/` kept area.\n",
                encoding="utf-8",
            )
            ROOT = synthetic_root
            try:
                unlisted = existing_framework_areas() - readme_framework_areas()
            finally:
                ROOT = original_root
        self.assertEqual(
            set(),
            unlisted,
            "a standalone-owned top-level directory was reported as an unlisted "
            f"framework area: {sorted(unlisted)}",
        )

    def test_completeness_walk_excludes_repository_ignored_content(self):
        """Ignored residue is not unowned content and must not be reported as it."""
        probe = ROOT / f"framework-completeness-ignored-probe-{uuid.uuid4().hex[:8]}.pyc"
        self.assertFalse(probe.exists(), "probe path is already in use")
        probe.write_bytes(b"ignored residue")
        try:
            kept = {path.relative_to(ROOT).as_posix() for path in repository_content_files(ROOT)}
            self.assertNotIn(probe.name, kept)
            self.assertEqual((), validate_framework(ROOT))
        finally:
            probe.unlink(missing_ok=True)

    def test_ignore_derivation_reads_ancestor_nested_and_negated_rules(self):
        """The exclusion is derived from real ignore files, not restated as a list."""
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base / ".git").mkdir()
            (base / ".gitignore").write_text("*.egg-info/\n", encoding="utf-8")
            root = base / "dual-hat"
            (root / "tooling/local").mkdir(parents=True)
            (root / "probe.egg-info").mkdir()
            (root / "tooling/__pycache__").mkdir()
            (root / ".gitignore").write_text("__pycache__/\n*.pyc\n!keep.pyc\n", encoding="utf-8")
            (root / "tooling/.gitignore").write_text("local/\n", encoding="utf-8")
            (root / "probe.egg-info/PKG-INFO").write_text("x", encoding="utf-8")
            (root / "tooling/__pycache__/module.pyc").write_bytes(b"x")
            (root / "tooling/local/scratch.txt").write_text("x", encoding="utf-8")
            (root / "tooling/module.py").write_text("x", encoding="utf-8")
            (root / "drop.pyc").write_bytes(b"x")
            (root / "keep.pyc").write_bytes(b"x")
            kept = {path.relative_to(root).as_posix() for path in repository_content_files(root)}
            self.assertEqual(
                {".gitignore", "keep.pyc", "tooling/.gitignore", "tooling/module.py"},
                kept,
            )

    def test_repository_boundaries_dependency_direction_invariant_is_mechanically_checked(self):
        # REPOSITORY_BOUNDARIES.md's "Dual Hat never imports product,
        # engineering, archive, or workspace state" had no automated check
        # anywhere in tooling/ or tests/: a review confirmed the search came up
        # empty. validate_framework() now flags any real Python import
        # statement in the repo that targets those forbidden top-level
        # packages; this test pins the governing sentence and proves the
        # mechanism actually discriminates a real violation from legitimate
        # local module names and path-string references (which must not
        # false-positive, since Dual Hat's own tooling legitimately builds
        # path strings like "engineering/process/work-items/..." when
        # validating an external product's own layout).
        boundaries = (ROOT / "governance/REPOSITORY_BOUNDARIES.md").read_text(encoding="utf-8")
        normalized = " ".join(boundaries.split())
        self.assertIn(
            "Dual Hat never imports product, engineering, archive, or workspace state.",
            normalized,
        )

        violating_samples = (
            "import product\n",
            "from engineering import work_item_governance\n",
            "from ..archive import ledger\n",
            "from ...workspace.state import cursor\n",
            "  from workspace import active_session\n",
        )
        for sample in violating_samples:
            self.assertTrue(
                any(pattern.search(sample) for pattern in FORBIDDEN_DEPENDENCY_IMPORT_PATTERNS),
                f"expected a dependency-direction violation to be detected in: {sample!r}",
            )

        benign_samples = (
            "from temporary_workspace import TemporaryWorkspaceError\n",
            "import argparse\n",
            "from publication_ownership import standalone_owned\n",
            'expected_preflight_artifact = f"engineering/process/work-items/{wid}/PLATFORM_PREFLIGHT.json"\n',
            '"workspace/" in relative\n',
        )
        for sample in benign_samples:
            self.assertFalse(
                any(pattern.search(sample) for pattern in FORBIDDEN_DEPENDENCY_IMPORT_PATTERNS),
                f"did not expect a dependency-direction violation to be detected in: {sample!r}",
            )

    def test_json_and_schema_files_parse(self):
        for path in [*ROOT.rglob("*.json"), *ROOT.rglob("*.schema.json")]:
            json.loads(path.read_text(encoding="utf-8"))


    def test_plugin_bundle_tracks_canonical_version(self):
        """Currency of the LIVE shipped bundle, asserted through its one owner."""
        payload_path = ROOT / "plugins/dual-hat/framework-payload.json"
        if not payload_path.is_file():
            self.skipTest("no plugin bundle present in this checkout")
        paths = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(ROOT).parts
        }
        result = validate_bundle_version_currency(
            paths, lambda path: (ROOT / path).read_bytes()
        )
        self.assertEqual("passed", result["bundle_version_currency"])
        self.assertEqual(
            json.loads((ROOT / VERSION_AUTHORITY).read_text(encoding="utf-8"))["version"],
            result["bundle_framework_version"],
        )
        # Not a gate predicate: the gate checks the bundled tree by repository
        # path, while this confirms the payload's own relative reference
        # resolves from the payload file's directory rather than the root.
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        self.assertTrue((payload_path.parent / payload["framework_root"]).resolve().is_dir())


    # --- the plugin bundle must be current to publish at all -----------------
    #
    # `test_plugin_bundle_tracks_canonical_version` already asserts the
    # predicate and is deliberately NOT duplicated here. It detected the stale
    # 1.18.5 bundle correctly and was red at a published HEAD, which is the
    # whole problem: a red test is advisory and a human can ship past it. What
    # follows exercises the *blocking* half -- that the governed publication
    # path refuses -- and a gate never observed refusing is exactly the failure
    # being repaired, so each stale granularity gets its own negative control
    # alongside a positive one proving a current bundle still publishes.
    #
    # Versions here are synthetic and unrelated to the shipped one: the suite
    # must never pin the live version as a literal.
    CURRENT_FIXTURE_VERSION = "9.9.9"
    STALE_FIXTURE_VERSION = "8.8.8"
    AHEAD_FIXTURE_VERSION = "10.0.0"

    @classmethod
    def _bundle_fixture(
        cls,
        *,
        payload_overrides: dict | None = None,
        core_version: str | None = None,
        manifest_version: str | None = None,
        extra_snapshot: bool = False,
        bundled_tree_version: str | None = None,
        omit_bundled_tree: bool = False,
    ) -> tuple[set[str], object]:
        """A synthetic published tree carrying a plugin bundle."""
        current = cls.CURRENT_FIXTURE_VERSION
        snapshot = f"{BUNDLE_ROOT}/framework/dual-hat-{current}"
        payload = {
            "$comment": "SPDX-License-Identifier: Apache-2.0",
            "content_manifest": f"./framework/dual-hat-{current}/.dual-hat-release/content-manifest.json",
            "framework_root": f"./framework/dual-hat-{current}",
            "framework_version": current,
            "generation": (
                f"Exact extraction of the checksum-bound Dual Hat {current} "
                "standalone package; do not hand-edit the payload."
            ),
            "schema": "dual-hat-plugin-framework-payload/1.0",
            "source_release_archive": f"dual-hat-{current}.zip",
            "source_release_sha256": "A1" * 32,
        }
        payload.update(payload_overrides or {})
        example = {"schema": "example", CORE_VERSION_KEY: core_version or current}
        content = {
            VERSION_AUTHORITY: {"version": current},
            BUNDLE_PAYLOAD: payload,
            f"{snapshot}/{VERSION_AUTHORITY}": {"version": bundled_tree_version or current},
            f"{snapshot}/examples/platform-profile.example.json": example,
            f"{BUNDLE_ROOT}/.example-plugin/plugin.json": {
                "name": "dual-hat", "version": manifest_version or current,
            },
        }
        if omit_bundled_tree:
            for path in [key for key in content if key.startswith(f"{snapshot}/")]:
                del content[path]
        if extra_snapshot:
            content[f"{BUNDLE_ROOT}/framework/dual-hat-{cls.STALE_FIXTURE_VERSION}/README.md"] = None
        encoded = {
            path: (b"stale snapshot" if body is None
                   else json.dumps(body, sort_keys=True).encode("utf-8"))
            for path, body in content.items()
        }
        return set(encoded), encoded.__getitem__

    @staticmethod
    def _refusal_rows(exception: PublicationValidationError) -> list[str]:
        """Exactly the failure rows, recovered the way a caller would."""
        _, separator, joined = str(exception).partition("publication refused: ")
        return joined.split("; ") if separator else [str(exception)]

    def test_publication_gate_passes_a_current_plugin_bundle(self):
        paths, read = self._bundle_fixture()
        result = validate_bundle_version_currency(paths, read)
        self.assertEqual("passed", result["bundle_version_currency"])
        self.assertEqual(self.CURRENT_FIXTURE_VERSION, result["bundle_framework_version"])

    def test_publication_gate_refuses_every_stale_bundle_granularity(self):
        """Each control names the EXACT rows its own condition produces."""
        stale = self.STALE_FIXTURE_VERSION
        current = self.CURRENT_FIXTURE_VERSION
        snapshot = f"{BUNDLE_ROOT}/framework/dual-hat-{current}"
        manifest = f"{BUNDLE_ROOT}/.example-plugin/plugin.json"
        cases = {
            # (1) The bundled snapshot's own declared version. Only that one
            # field is disturbed: a stale bare version carries no
            # framework-naming token, so granularity 1 is the only thing that
            # can produce this row and the control cannot be carried by
            # another granularity.
            "declared bundle version": (
                dict(payload_overrides={"framework_version": stale}),
                [f"{BUNDLE_PAYLOAD}: framework_version is {stale!r}, "
                 f"not the shipped {current!r}"],
            ),
            # (1b) Equality, not "not behind". A bundle AHEAD of the shipped
            # version is refused on the same terms -- legitimate during a
            # version bump performed in the wrong order, and named in this
            # change's adopter-visible classification.
            "bundle ahead of the shipped version": (
                dict(payload_overrides={"framework_version": self.AHEAD_FIXTURE_VERSION}),
                [f"{BUNDLE_PAYLOAD}: framework_version is "
                 f"{self.AHEAD_FIXTURE_VERSION!r}, not the shipped {current!r}"],
            ),
            # (1c) The tree the payload points at. Two rows by construction:
            # the stale root value also names the framework, so granularity 3
            # sees it too. Declared rather than concealed.
            "framework root the payload points at": (
                dict(payload_overrides={"framework_root": f"./framework/dual-hat-{stale}"}),
                [f"{BUNDLE_PAYLOAD}: framework_root is "
                 f"'./framework/dual-hat-{stale}', not './framework/dual-hat-{current}'",
                 f"{BUNDLE_PAYLOAD}: framework_root names framework version "
                 f"{stale!r}, which is not the shipped {current!r}"],
            ),
            # (1d) The archive the payload binds. Two rows for the same reason.
            "source release archive": (
                dict(payload_overrides={"source_release_archive": f"dual-hat-{stale}.zip"}),
                [f"{BUNDLE_PAYLOAD}: source_release_archive is "
                 f"'dual-hat-{stale}.zip', not the shipped version's archive",
                 f"{BUNDLE_PAYLOAD}: source_release_archive names framework "
                 f"version {stale!r}, which is not the shipped {current!r}"],
            ),
            # (1e) The bundled tree's OWN release/VERSION.json disagreeing.
            # Enumerated by the gate, probed and working, and until now
            # untested -- the fixture derived that file from the current
            # version in every case, so it could never disagree.
            "bundled tree declares another version": (
                dict(bundled_tree_version=stale),
                [f"{snapshot}/{VERSION_AUTHORITY}: bundled tree declares "
                 f"{stale!r}, not the shipped {current!r}"],
            ),
            # (1f) No bundled tree for the shipped version at all. The second
            # of the two enumerated conditions that had no control.
            "bundled tree absent": (
                dict(omit_bundled_tree=True),
                [f"no bundled framework tree for the shipped version at "
                 f"{snapshot}/{VERSION_AUTHORITY}"],
            ),
            # (2) Vendored content declaring a stale core version -- the same
            # rule one level down, where a shipped example trained adopters
            # onto a version the framework had already left behind.
            "vendored declared core version": (
                dict(core_version=stale),
                [f"{snapshot}/examples/platform-profile.example.json: "
                 f"{CORE_VERSION_KEY} = {stale!r} but the shipped core version "
                 f"is {current!r}"],
            ),
            # (3) The generator rebinding every machine-readable field and
            # leaving a narrative one stale. Every bound field is CORRECT; only
            # the prose disagrees, so exactly one row and it is granularity 3's.
            # A gate that trusted the generator's own fields would pass this.
            "narrative generation string": (
                dict(payload_overrides={
                    "generation": f"Exact extraction of the checksum-bound Dual "
                                  f"Hat {stale} standalone package.",
                }),
                [f"{BUNDLE_PAYLOAD}: generation names framework version "
                 f"{stale!r}, which is not the shipped {current!r}"],
            ),
            # (4) The manifest adopters actually resolve the plugin through.
            "plugin manifest version": (
                dict(manifest_version=stale),
                [f"{manifest}: version is {stale!r}, not the shipped {current!r}"],
            ),
            # (5) A superseded snapshot left beside the current one, so the
            # install path can still resolve the old tree.
            "superseded snapshot retained": (
                dict(extra_snapshot=True),
                [f"superseded framework snapshots still present alongside the "
                 f"shipped {current!r}: ['dual-hat-{stale}']"],
            ),
        }
        for label, (keywords, expected_rows) in cases.items():
            with self.subTest(granularity=label):
                paths, read = self._bundle_fixture(**keywords)
                with self.assertRaises(PublicationValidationError) as refusal:
                    validate_bundle_version_currency(paths, read)
                message = str(refusal.exception)
                self.assertIn("publication refused", message)
                self.assertEqual(expected_rows, self._refusal_rows(refusal.exception))
                # The row separator must appear exactly as many times as there
                # are rows to separate. No row and no prefix may contain it, or
                # a caller counting failures on it silently miscounts -- which
                # the superseded-snapshot row and this message's own prefix
                # both used to do.
                self.assertEqual(len(expected_rows), len(message.split("; ")))

    def test_publication_gate_refuses_a_bundle_it_has_no_authority_to_check(self):
        """A publication carrying a bundle but no version authority is refused."""
        paths, read = self._bundle_fixture()
        paths.discard(VERSION_AUTHORITY)
        with self.assertRaises(PublicationValidationError) as refusal:
            validate_bundle_version_currency(paths, read)
        self.assertEqual(
            f"publication carries a plugin bundle but no {VERSION_AUTHORITY} "
            "to check it against",
            str(refusal.exception),
        )

    def test_declared_core_versions_has_one_authority_shared_with_the_gate(self):
        """The walker the gate owns is the walker the shipped-data check calls."""
        document = {"a": {CORE_VERSION_KEY: "1.2.3"}, "b": [{CORE_VERSION_KEY: "4.5.6"}]}
        self.assertEqual(
            [f"p: {CORE_VERSION_KEY} = '1.2.3'", f"p: {CORE_VERSION_KEY} = '4.5.6'"],
            sorted(declared_core_versions(document, "p")),
        )
        self.assertEqual([], list(declared_core_versions({CORE_VERSION_KEY: "not-a-version"}, "p")))

        # (a) The name this suite imports is defined by the gate module itself,
        # so a local `def declared_core_versions` shadowing the import is red.
        gate = sys.modules[declared_core_versions.__module__]
        self.assertEqual(
            (ROOT / "tooling/staged_publication.py").resolve(),
            Path(gate.__file__).resolve(),
            "declared_core_versions is no longer defined by the publication "
            "gate; this suite is exercising a second implementation of the rule",
        )

        # (b) And the shipped-data check calls THAT symbol rather than a copy.
        # Its own call site is read, so the check cannot be quietly re-pointed:
        # every plain-name call it makes must resolve to a builtin or to the
        # gate module, which turns a reintroduced local walker red under
        # whatever name it is given.
        checked = "test_no_hardcoded_core_version_survives_the_release_evidence_authority"
        body = next(
            (
                node
                for node in ast.walk(ast.parse(Path(__file__).read_text(encoding="utf-8")))
                if isinstance(node, ast.FunctionDef) and node.name == checked
            ),
            None,
        )
        # Renaming the checked function must say so, not surface as a bare
        # StopIteration from the search that failed to find it.
        self.assertIsNotNone(
            body,
            f"{checked} no longer exists under that name, so the shipped-data "
            "check's call site cannot be located; re-point this guard at it",
        )
        called = sorted({
            node.func.id for node in ast.walk(body)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        })
        self.assertIn(
            declared_core_versions.__name__, called,
            f"{checked} no longer walks the shipped data through the gate's own "
            "authority; it has been re-pointed at something else",
        )
        foreign = [
            f"{name} is defined in "
            f"{getattr(globals().get(name), '__module__', None)!r}"
            for name in called
            if not hasattr(builtins, name)
            and getattr(globals().get(name), "__module__", None) != gate.__name__
        ]
        self.assertEqual(
            [], foreign,
            f"{checked} calls a walker this test module defines instead of the "
            f"one {gate.__name__} owns; that is a second implementation of one "
            "rule, free to drift from it",
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

    def test_staging_a_publication_that_removes_a_previously_owned_file(self):
        """A file the prior manifest owned, dropped by the new manifest and deleted from the worktree, is a removal to stage, not an unknown file."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._git(root, "init", "-b", "main")
            self._git(root, "config", "user.name", "Dual Hat Test")
            self._git(root, "config", "user.email", "dual-hat-test@example.invalid")

            def publish(files: dict[str, bytes]) -> None:
                manifest = {
                    "schema": "dual-hat-export-manifest/3.0",
                    "tree_sha256": "TEST-TREE",
                    "content_files": [
                        {"path": path, "sha256": hashlib.sha256(data).hexdigest().upper()}
                        for path, data in sorted(files.items())
                    ],
                }
                manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
                marker = {
                    "schema": "dual-hat-published-state/1.0",
                    "tree_sha256": "TEST-TREE",
                    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest().upper(),
                }
                (root / ".dual-hat").mkdir(exist_ok=True)
                for path, data in files.items():
                    (root / path).parent.mkdir(parents=True, exist_ok=True)
                    (root / path).write_bytes(data)
                (root / ".dual-hat/export-manifest.json").write_bytes(manifest_bytes)
                (root / ".dual-hat/published-state.json").write_text(
                    json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )

            publish({"README.md": b"initial\n", "templates/ORPHAN.md": b"orphan\n"})
            self._git(root, "add", "--", "README.md", "templates/ORPHAN.md",
                      ".dual-hat/export-manifest.json", ".dual-hat/published-state.json")
            self._git(root, "commit", "-m", "Initial governed publication")

            (root / "templates/ORPHAN.md").unlink()
            publish({"README.md": b"updated\n"})
            staged = stage_manifest_owned(root)
            self.assertEqual("passed", staged["status"])
            self._git(root, "commit", "-m", "Forward publication removing the orphan")
            verified = verify_commit_tree(root)
            self.assertEqual("passed", verified["status"])
            tree = subprocess.run(("git", "ls-tree", "-r", "--name-only", "HEAD"), cwd=root,
                                  check=True, capture_output=True, text=True).stdout.splitlines()
            self.assertNotIn("templates/ORPHAN.md", tree)
            self.assertIn("README.md", tree)

    def test_staging_cleans_python_cache_but_rejects_unknown_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            cache = root / "tooling/__pycache__"
            cache.mkdir(parents=True)
            (cache / "unsafe.pyc").write_bytes(b"compiled")
            loose_cache = root / "generated.pyo"
            loose_cache.write_bytes(b"compiled")
            staged = stage_manifest_owned(root)
            self.assertEqual(
                [
                    "generated.pyo",
                    "tooling/__pycache__/",
                    "tooling/__pycache__/unsafe.pyc",
                ],
                staged["cleaned_python_cache_paths"],
            )
            self.assertEqual(3, staged["cleaned_python_cache_count"])
            self.assertFalse(cache.exists())
            self.assertFalse(loose_cache.exists())
            self._git(root, "reset")
            cache.mkdir(parents=True)
            retained = cache / "retain.txt"
            retained.write_text("not generated bytecode\n", encoding="utf-8")
            (cache / "generated.pyc").write_bytes(b"compiled")
            with self.assertRaisesRegex(PublicationValidationError, "unknown"):
                stage_manifest_owned(root)
            self.assertTrue(retained.exists())
            self.assertFalse((cache / "generated.pyc").exists())
            retained.unlink()
            cache.rmdir()
            (root / "manual.txt").write_text("unowned", encoding="utf-8")
            with self.assertRaisesRegex(PublicationValidationError, "unknown"):
                stage_manifest_owned(root)

    def test_staging_ignores_gitignored_generated_content_but_still_rejects_real_unknown_files(self):
        """The worktree scan is derived from ``git ls-files``."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            # A repository-level ignore rule, not a tracked .gitignore file --
            # keeping the fixture from introducing an untracked-but-not-ignored
            # file of its own that would otherwise need accounting for.
            (root / ".git/info/exclude").write_text(
                "generated_skills/\n", encoding="utf-8"
            )
            generated = root / "generated_skills"
            generated.mkdir()
            (generated / "skill_one.md").write_text("generated\n", encoding="utf-8")
            (generated / "skill two with space.md").write_text(
                "generated\n", encoding="utf-8"
            )

            # Gitignored, generated, untracked content -- including the
            # space-in-filename case -- must stage cleanly. It must never
            # read as unknown.
            staged = stage_manifest_owned(root)
            self.assertEqual("passed", staged["status"])

            self._git(root, "reset")
            # A genuinely unaccounted file -- untracked and NOT ignored --
            # must still be refused. The fix narrows what counts as present;
            # it does not disable the unknown-content check.
            (root / "manual_real_unknown.md").write_text(
                "not owned\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(PublicationValidationError, "unknown"):
                stage_manifest_owned(root)

    def _reparse_flavours(self) -> tuple[str, ...]:
        """Every reparse flavour this host permits, or an honest skip if none does."""
        with tempfile.TemporaryDirectory() as probe:
            flavours = available_reparse_flavours(Path(probe))
        if not flavours:
            self.skipTest("host permits neither a symlink nor a junction fixture")
        return flavours

    def test_staging_rejects_directory_symlink_without_touching_external_cache(self):
        probed = self._reparse_flavours()
        ran = []
        for flavour in probed:
            with self.subTest(reparse=flavour), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                root = base / "publication"
                external = base / "external"
                root.mkdir()
                external.mkdir()
                self._publication_repo(root)
                external_cache = external / "outside.pyc"
                external_cache.write_bytes(b"external-bytecode")
                local_cache = root / "tooling/__pycache__"
                local_cache.mkdir(parents=True)
                local_artifact = local_cache / "local.pyc"
                local_artifact.write_bytes(b"local-bytecode")
                link = root / "linked-cache"
                self.assertTrue(
                    make_reparse(link, external, flavour),
                    f"{flavour} fixture failed after probing as available",
                )
                try:
                    with self.assertRaisesRegex(
                        PublicationValidationError,
                        "symlink or reparse entries.*linked-cache",
                    ):
                        stage_manifest_owned(root)
                    self.assertEqual(b"external-bytecode", external_cache.read_bytes())
                    self.assertEqual(b"local-bytecode", local_artifact.read_bytes())
                    self.assertTrue(is_reparse(link))
                finally:
                    remove_reparse(link)
                ran.append(flavour)
        assert_probed_flavours_all_ran(self, probed, ran)

    def test_staging_rejects_file_symlink_without_touching_external_cache(self):
        probed = self._reparse_flavours()
        ran = []
        for flavour in probed:
            with self.subTest(reparse=flavour), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                root = base / "publication"
                root.mkdir()
                self._publication_repo(root)
                if flavour == "symlink":
                    target = base / "external.pyc"
                    target.write_bytes(b"external-bytecode")
                    witness = target
                else:
                    # A junction points only at a directory, so the reparse point
                    # keeps its position -- a cache-named entry inside the
                    # publication root, which is what the guard is about -- while
                    # the bytecode it must not reach sits inside the target.
                    target = base / "external"
                    target.mkdir()
                    witness = target / "outside.pyc"
                    witness.write_bytes(b"external-bytecode")
                link = root / "linked.pyc"
                self.assertTrue(
                    make_reparse(link, target, flavour),
                    f"{flavour} fixture failed after probing as available",
                )
                try:
                    with self.assertRaisesRegex(
                        PublicationValidationError,
                        "symlink or reparse entries.*linked.pyc",
                    ):
                        stage_manifest_owned(root)
                    self.assertEqual(b"external-bytecode", witness.read_bytes())
                    self.assertTrue(is_reparse(link))
                finally:
                    remove_reparse(link)
                ran.append(flavour)
        assert_probed_flavours_all_ran(self, probed, ran)

    def test_actual_test_runner_discovers_nonpackage_tests_from_any_cwd(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp)
            tests = fixture / "copied-tests"
            caller = fixture / "caller"
            tests.mkdir()
            caller.mkdir()
            (tests / "test_probe.py").write_text(
                "import unittest\n\n"
                "class ProbeTests(unittest.TestCase):\n"
                "    def test_probe(self):\n"
                "        self.assertTrue(True)\n",
                encoding="utf-8",
            )
            environment = dict(os.environ)
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            documented = subprocess.run(
                (
                    sys.executable,
                    "tooling/run_tests.py",
                    "--start-directory",
                    str(tests),
                ),
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            framework_path = subprocess.run(
                (
                    sys.executable,
                    str(ROOT / "tooling/run_tests.py"),
                    "--start-directory",
                    str(tests),
                ),
                cwd=caller,
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertIn("OK", documented.stderr)
            self.assertIn("OK", framework_path.stderr)
            self.assertFalse(any(fixture.rglob("*.pyc")))
            self.assertFalse(
                any(path.name == "__pycache__" for path in fixture.rglob("*"))
            )

    def test_committed_release_products_coexist_with_source_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            release = root / "release/v0.1.0"
            release.mkdir(parents=True)
            for name in (
                "dual-hat-0.1.0.zip",
                "dual-hat-0.1.0.release.json",
                "dual-hat-0.1.0.zip.sha256",
            ):
                (release / name).write_bytes(b"release product")
            self._git(root, "add", "release/v0.1.0")
            self._git(root, "commit", "-m", "Publish release")
            verified = verify_commit_tree(root)
            self.assertEqual("passed", verified["status"])
            self.assertEqual(3, verified["tree_file_count"])

    def test_staging_scans_manifest_owned_content_for_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            credential_fixture = "api_" + "key = 'abcdefghijklmnopqrstuvwx'\n"
            self._write_publication(root, credential_fixture)
            with self.assertRaisesRegex(PublicationValidationError, "possible secrets"):
                stage_manifest_owned(root)

    # --- preserved_path reaches every arm, and the documented CLI can supply
    # one -------------------------------------------------------------------
    #
    # `validate_staged`'s `unknown_staged` arm computed `staged - owned` with
    # no `preserved_path` filter while `unknown` two lines above applies one.
    # This module's own history shows the asymmetry is an oversight: the
    # commit that added `preserved_path` applied the identical guard to
    # `unknown` in all three functions and to the `prior_owned - owned`
    # removal loop, and simply did not reach this fifth, textually
    # identical, occurrence. Separately, the documented CLI (`main`) never
    # passed a `preserved_path` to any of the three functions it dispatches
    # to, so the exact command sequence the guide documents could not
    # succeed against any repository carrying the standalone deployment
    # content (`plugins/`, `.agents/plugins/`, ...) a derived publication
    # repository legitimately has alongside the portable core.

    def test_unknown_staged_respects_a_supplied_preserved_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            preserved = root / "assets/dual-hat/icon.png"
            preserved.parent.mkdir(parents=True)
            preserved.write_bytes(b"not-a-real-icon")
            self._git(root, "add", "--", "assets/dual-hat/icon.png")
            result = validate_staged(root, preserved_path=standalone_owned)
            self.assertEqual("passed", result["status"])

    def test_unknown_staged_still_refuses_a_non_preserved_staged_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            (root / "manual.txt").write_text("unowned", encoding="utf-8")
            self._git(root, "add", "--", "manual.txt")
            with self.assertRaisesRegex(PublicationValidationError, r"unknown_staged=\['manual\.txt'\]"):
                validate_staged(root, preserved_path=standalone_owned)

    def test_documented_cli_stage_action_succeeds_against_standalone_deployment_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            plugin = root / "plugins/dual-hat/some-form/plugin.json"
            plugin.parent.mkdir(parents=True)
            plugin.write_text('{"name":"standalone-plugin"}\n', encoding="utf-8")
            previous_argv = sys.argv
            sys.argv = ["staged_publication.py", "stage", "--root", str(root)]
            try:
                self.assertEqual(0, staged_publication_main())
            finally:
                sys.argv = previous_argv
            staged = subprocess.run(
                ("git", "diff", "--cached", "--name-only"), cwd=root,
                check=True, capture_output=True, text=True,
            ).stdout
            self.assertNotIn("plugins/dual-hat/some-form/plugin.json", staged)

    def test_documented_cli_still_refuses_a_genuinely_unknown_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._publication_repo(root)
            (root / "manual.txt").write_text("unowned", encoding="utf-8")
            previous_argv = sys.argv
            sys.argv = ["staged_publication.py", "stage", "--root", str(root)]
            try:
                with self.assertRaisesRegex(PublicationValidationError, "manual.txt"):
                    staged_publication_main()
            finally:
                sys.argv = previous_argv

    # --- the core version has exactly one authority ---------------------------
    #
    # Principle 15's second half, for the core-version convention. The instance fix
    # -- resolving the active core version from release/VERSION.json instead of
    # a constant -- closes the first half only. Without a standing check, a
    # contributor who does not know the convention ever changed reintroduces a
    # literal and nothing signals the drift; that is precisely how
    # DUAL_HAT_CORE_VERSION sat at 1.11.0 through seven minor releases while
    # being the sole authority admitting an adopter's platform profile.
    #
    # Every half below is anchored on a DIRECT read of release/VERSION.json,
    # never on the resolver under test, so the shipped data and the resolver
    # cannot satisfy this check by being wrong in the same direction.

    @staticmethod
    def _shipped_version() -> str:
        return str(json.loads(
            (ROOT / "release/VERSION.json").read_text(encoding="utf-8")
        )["version"])

    # `declared_core_versions` is imported from the publication gate rather
    # than reimplemented here. This check and the gate must agree on what
    # counts as a declared core version; two copies would be two rules free to
    # drift, and drift between duplicated authorities is the defect this whole
    # repair exists to close.

    # A fourteen-case mutation battery against the three halves below, built
    # by an independent review, caught six reintroduction shapes and let
    # eight past. Every name below is disclosed rather than silently carved
    # out, per this check's own reason for existing: `CORE_VERSION_KEY` (imported above from
    # the publication gate) is the shared authority naming WHICH json key
    # carries a declared core version. It holds a key NAME string, never a
    # version value, and is itself part of the mechanism this check hardens --
    # flagging it would refuse the fix in the name of the defect.
    _CORE_VERSION_ASSIGNED_NAME_EXEMPTIONS = frozenset({"CORE_VERSION_KEY"})

    @classmethod
    def _core_version_named_assignment_targets(cls, module: Path) -> list[str]:
        """Every assignment to a name containing CORE_VERSION, any value shape."""
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        hits: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
                targets = [node.target]
            else:
                continue
            for target in targets:
                for name_node in ast.walk(target):
                    if (
                        isinstance(name_node, ast.Name)
                        and "CORE_VERSION" in name_node.id
                        and name_node.id not in cls._CORE_VERSION_ASSIGNED_NAME_EXEMPTIONS
                    ):
                        hits.append(f"{module.relative_to(ROOT).as_posix()}:{node.lineno}: {name_node.id}")
        return hits

    @staticmethod
    def _non_json_core_version_declarations(shipped: str) -> list[str]:
        """D5: half (b) below scans only `*.json`, so a stale core version in a Markdown/YAML/TOML/text adopter-facing artifact is invisible -- precisely the "trains adopters into the defect" mechanism the..."""
        pattern = re.compile(r'dual_hat_core_version"?\s*[:=]\s*"?([0-9]+\.[0-9]+\.[0-9]+)')
        hits: list[str] = []
        for path in sorted(ROOT.rglob("*")):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix.lower() not in {".md", ".yaml", ".yml", ".toml", ".txt"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                match = pattern.search(line)
                if match and match.group(1) != shipped:
                    hits.append(
                        f"{path.relative_to(ROOT).as_posix()}:{number}: "
                        f"dual_hat_core_version = {match.group(1)!r}"
                    )
        return hits

    @staticmethod
    def _inline_core_version_dict_literals(shipped: str) -> list[str]:
        """D6: a core-version key hardcoded inside an inline dict LITERAL in a test module -- never loaded from any shipped JSON file -- is invisible to half (b) below (not a `.json` file) and to half (c)..."""
        hits: list[str] = []
        for module in sorted((ROOT / "tests").glob("*.py")):
            tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Dict):
                    continue
                for key_node, value_node in zip(node.keys, node.values):
                    if (
                        isinstance(key_node, ast.Constant) and isinstance(key_node.value, str)
                        and "core_version" in key_node.value
                        and isinstance(value_node, ast.Constant) and isinstance(value_node.value, str)
                        and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value_node.value)
                        and value_node.value != shipped
                    ):
                        hits.append(
                            f"{module.relative_to(ROOT).as_posix()}:{node.lineno}: "
                            f"{key_node.value} = {value_node.value!r}"
                        )
        return hits

    @staticmethod
    def _other_keyed_core_version_declarations(shipped: str) -> list[str]:
        """D8: half (b) below keys on the exact name `dual_hat_core_version`, so a second core-version pin under any OTHER key containing `core_version` in shipped JSON passed silently."""
        def other_keyed(payload, key=None):
            if isinstance(payload, dict):
                for name, value in payload.items():
                    yield from other_keyed(value, str(name))
            elif isinstance(payload, list):
                for value in payload:
                    yield from other_keyed(value, key)
            elif (
                key is not None and key != CORE_VERSION_KEY and "core_version" in key
                and isinstance(payload, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", payload)
            ):
                yield f"{key} = {payload!r}"

        hits: list[str] = []
        for path in sorted(ROOT.rglob("*.json")):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            payload = FrameworkTests._loaded_json(path)
            if payload is None:
                continue
            relative = path.relative_to(ROOT).as_posix()
            for row in other_keyed(payload):
                if not row.endswith(f"{shipped!r}"):
                    hits.append(f"{relative}: {row}")
        return hits

    def test_no_hardcoded_core_version_survives_the_release_evidence_authority(self):
        shipped = self._shipped_version()

        # (a) Code half. Any version-shaped string literal anywhere in the
        # tooling surface is a second authority for a value release/VERSION.json
        # already owns. AST constants are scanned rather than source text, so
        # the check sees an indirect binding -- a default argument, a dataclass
        # field, a decorator argument -- exactly as it sees a plain assignment.
        # D3, D4: `rglob` rather than `glob`, and `scripts/` is in the surface
        # -- it holds Python today and sat outside all three original halves.
        literals = [
            f"{module.relative_to(ROOT).as_posix()}:{node.lineno}: {node.value!r}"
            for base in (ROOT / "tooling", ROOT / "scripts")
            for module in sorted(base.rglob("*.py"))
            for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"), filename=str(module)))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", node.value)
        ]
        with self.subTest(half="tooling literal"):
            self.assertEqual(
                [], literals,
                "a hardcoded version literal was reintroduced into the tooling "
                "surface; the active core version has exactly one authority, "
                "release/VERSION.json, and must be resolved from it at call time",
            )

        # D1, D2, D7: any assignment to a CORE_VERSION-shaped name, however
        # the value is built, over the same widened tooling/scripts surface.
        named = [
            hit
            for base in (ROOT / "tooling", ROOT / "scripts")
            for module in sorted(base.rglob("*.py"))
            for hit in self._core_version_named_assignment_targets(module)
        ]
        with self.subTest(half="tooling assigned name"):
            self.assertEqual(
                [], named,
                "a name matching CORE_VERSION was (re)bound in the tooling "
                "surface, however its value was constructed; the active core "
                "version has exactly one authority, release/VERSION.json, and "
                "must be resolved from it at call time",
            )

        # (b) Data half. Principle 15 names already-produced artifacts, not only code
        # call sites: the shipped example declaring 1.11.0 is what trained
        # adopters into the defect and concealed it for seven minor releases.
        disagreements = [
            row
            for path in sorted(ROOT.rglob("*.json"))
            if ".git" not in path.parts and "__pycache__" not in path.parts
            for payload in (self._loaded_json(path),)
            if payload is not None
            for row in declared_core_versions(payload, path.relative_to(ROOT).as_posix())
            if not row.endswith(f"{shipped!r}")
        ]
        with self.subTest(half="shipped data"):
            self.assertEqual(
                [], disagreements,
                f"shipped data declares a core version other than {shipped!r}, "
                "the version release/VERSION.json actually ships",
            )

        # D8: the same shipped JSON, under any OTHER core-version-shaped key.
        with self.subTest(half="shipped data, other keys"):
            self.assertEqual([], self._other_keyed_core_version_declarations(shipped))

        # D5: shipped Markdown/YAML/TOML/text declarations outside JSON.
        with self.subTest(half="shipped non-json artifact"):
            self.assertEqual([], self._non_json_core_version_declarations(shipped))

        # D6: an inline dict literal in a test module, never loaded from JSON.
        with self.subTest(half="test fixture dict literal"):
            self.assertEqual([], self._inline_core_version_dict_literals(shipped))

        # (c) Test half. A test that pins the current version as a literal
        # reintroduces the same drift one release later; the suite must read it
        # from the same authority everything else does.
        pinned = [
            f"{module.relative_to(ROOT).as_posix()}:{number}"
            for module in sorted((ROOT / "tests").glob("*.py"))
            for number, line in enumerate(module.read_text(encoding="utf-8").splitlines(), 1)
            if shipped in line
        ]
        with self.subTest(half="test literal"):
            self.assertEqual(
                [], pinned,
                f"a test pins the shipped version {shipped!r} as a literal "
                "instead of reading release/VERSION.json",
            )

    # --- the core version is never bound at import scope ----------------------
    #
    # A design constraint protected until now by review and evidence only:
    # `work_item_governance.py` is imported by the sealing, classification,
    # transition and archival controls and by call sites that never touch a
    # platform profile. An import-scope binding would turn unreadable or
    # malformed release evidence into an `ImportError` for all of them,
    # through a channel carrying none of the conformance vocabulary its
    # callers are equipped to handle -- exactly the shape proved destructively
    # (a scratch copy with the release evidence file deleted outright still
    # imports cleanly) rather than merely designed against. Adopts that
    # destructive proof, and an AST scan for the same property, as standing
    # tests, since nothing had run either one before.

    _CORE_VERSION_RESOLVER_CALL_NAMES = frozenset({
        "active_core_version", "core_version_failures", "version_record", "release_maturity", "version",
    })

    @classmethod
    def _resolver_call_expressions(cls, node: ast.AST) -> bool:
        """True if `node`'s own immediately-evaluated expressions call a
        resolver name, without descending into a nested def/class/lambda's
        body -- each of those is visited separately, on its own timing."""
        stack = [node]
        while stack:
            current = stack.pop()
            if current is not node and isinstance(
                current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
            ):
                continue
            if isinstance(current, ast.Call):
                func = current.func
                if (isinstance(func, ast.Name) and func.id in cls._CORE_VERSION_RESOLVER_CALL_NAMES) or (
                    isinstance(func, ast.Attribute) and func.attr in cls._CORE_VERSION_RESOLVER_CALL_NAMES
                ):
                    return True
            stack.extend(ast.iter_child_nodes(current))
        return False

    @classmethod
    def _import_scope_binding_sites(cls, module_path: Path) -> list[str]:
        """`path:line` for every module-level statement, function/method default argument, decorator expression, or class-body statement where a resolver call could execute at import time."""
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
        relative = module_path.relative_to(ROOT).as_posix()
        hits: list[str] = []

        def visit(node: ast.stmt, immediate: bool) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if immediate:
                    for decorator in node.decorator_list:
                        if cls._resolver_call_expressions(decorator):
                            hits.append(f"{relative}:{decorator.lineno}: decorator on {node.name}")
                    for default in (*node.args.defaults, *node.args.kw_defaults):
                        if default is not None and cls._resolver_call_expressions(default):
                            hits.append(f"{relative}:{default.lineno}: default argument on {node.name}")
                for statement in node.body:
                    visit(statement, False)
            elif isinstance(node, ast.ClassDef):
                if immediate:
                    for decorator in node.decorator_list:
                        if cls._resolver_call_expressions(decorator):
                            hits.append(f"{relative}:{decorator.lineno}: decorator on {node.name}")
                    for base in (*node.bases, *(keyword.value for keyword in node.keywords)):
                        if cls._resolver_call_expressions(base):
                            hits.append(f"{relative}:{base.lineno}: base of {node.name}")
                for statement in node.body:
                    visit(statement, immediate)
            elif immediate and cls._resolver_call_expressions(node):
                hits.append(f"{relative}:{node.lineno}: module or class body statement")

        for statement in tree.body:
            visit(statement, True)
        return hits

    @staticmethod
    def _core_version_resolution_modules() -> list[Path]:
        """`work_item_governance.py`'s resolution path, and any module that imports it or `release_package` at module scope -- test_operating_ modes.py's own `core_version()` names the risk this closes: "A..."""
        resolver_source = [ROOT / "tooling/release_package.py", ROOT / "tooling/work_item_governance.py"]
        importers: list[Path] = []
        for base in (ROOT / "tooling", ROOT / "tests"):
            for module in sorted(base.rglob("*.py")):
                if module in resolver_source:
                    continue
                tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import) and any(
                        alias.name in ("work_item_governance", "release_package") for alias in node.names
                    ):
                        importers.append(module)
                        break
                    if isinstance(node, ast.ImportFrom) and node.module in (
                        "work_item_governance", "release_package",
                    ):
                        importers.append(module)
                        break
        return resolver_source + importers

    def test_core_version_resolution_has_no_import_scope_binding(self):
        hits = [
            hit
            for module in self._core_version_resolution_modules()
            for hit in self._import_scope_binding_sites(module)
        ]
        self.assertEqual(
            [], hits,
            "a core-version resolver call executes at import time rather than at "
            "call time; a profile-free caller of work_item_governance must never "
            "depend on release evidence being readable at all",
        )

    def test_core_version_resolution_survives_release_evidence_deleted_outright(self):
        """The destructive proof this design constraint was originally verified by, adopted as the second assertion: the module imports cleanly and reports an unreadable-evidence failure entry, never an..."""
        with tempfile.TemporaryDirectory() as scratch:
            scratch_root = Path(scratch)
            scratch_tooling = scratch_root / "dual-hat" / "tooling"
            shutil.copytree(ROOT / "tooling", scratch_tooling)
            probe = textwrap.dedent(
                f"""
                import sys
                sys.path.insert(0, {str(scratch_tooling)!r})
                import work_item_governance
                version, failures = work_item_governance.active_core_version()
                assert version is None, version
                assert failures == ("governed release evidence is unreadable",), failures
                import dispatch_reconciliation, profile_conformance  # unrelated controls
                print("IMPORT_AND_RESOLUTION_OK")
                """
            )
            result = subprocess.run(
                [sys.executable, "-c", probe], capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("IMPORT_AND_RESOLUTION_OK", result.stdout)

    # --- a maturity label agrees with its own version -------------------------
    #
    # Principle 15's second half, for the maturity convention. Correcting the
    # derivation closes the first half only. The previous boundary was written
    # by hand for 0.x-to-1.x with nothing keeping it synchronized, and the
    # identical contradiction returned at 1.x-to-2.x: every major from 2 upward
    # was stamped stable_1_x and no test anywhere could notice. Without a
    # standing check this repair is a second one-time boundary fix on the same
    # unsynchronized convention, and the NEXT major is the predicted third
    # recurrence. Named as a condition rather than as a version literal: a
    # literal here is true of one release and stale at the following one, and
    # the detector below cannot tell a comment discussing a version from a test
    # pinning one, so a literal in this comment disarms it.
    #
    # Anchored on the major the version itself carries, NEVER on
    # release_maturity(). A check asserting only that the declared label equals
    # the function's output reproduces release_package.py's own cross-check and
    # is blind in the identical way: at the first major past 1.x both sides read
    # the 1.x label, they agree, and they are both wrong. The fixture agreeing
    # with the defect is what let it survive, so agreement is exactly the wrong
    # thing to assert.
    #
    # The version is described rather than spelled out here for a reason worth
    # keeping: an earlier draft of this comment named it as a literal and the
    # anti-reintroduction check below caught the line the moment that version
    # shipped. The check is right and the comment was wrong. A prose example is
    # still a pin -- it goes stale exactly like a code one, and it is fixed by
    # removing the literal, never by narrowing the check to forgive comments.

    MATURITY_LABEL = r"stable_[0-9]+_x|functional_pre_1_0"

    @staticmethod
    def _maturity_disagreements(record) -> tuple[str, ...]:
        version = str(record["version"])
        declared = str(record["maturity"])
        major = int(version.split(".", 1)[0])
        implied = f"stable_{major}_x" if major >= 1 else "functional_pre_1_0"
        if declared == implied:
            return ()
        return (f"{version} declares maturity {declared!r}; its major implies {implied!r}",)

    @classmethod
    def _declared_maturities(cls, payload, path):
        """Yield every (path, record) carrying both a version and a maturity."""
        if isinstance(payload, dict):
            if (isinstance(payload.get("version"), str) and isinstance(payload.get("maturity"), str)
                    and re.fullmatch(cls.MATURITY_LABEL, payload["maturity"])
                    and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", payload["version"])):
                yield path, payload
            for value in payload.values():
                yield from cls._declared_maturities(value, path)
        elif isinstance(payload, list):
            for value in payload:
                yield from cls._declared_maturities(value, path)

    def test_declared_maturity_agrees_with_the_version_it_is_declared_for(self):
        # (a) The shipped release evidence, read directly from the file.
        shipped = json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))
        with self.subTest(half="shipped record"):
            self.assertEqual(
                (), self._maturity_disagreements(shipped),
                "release/VERSION.json declares a maturity its own version contradicts",
            )

        # (b) Principle 15's data half. Fixing a derivation does nothing to
        # artifacts already written under it, so every committed record that
        # carries both a version and a maturity is re-checked against the
        # corrected derivation rather than assumed to have followed the code.
        # Reported repository-relative, never absolute: this failure message is
        # durable output and an absolute path in it discloses the machine that
        # produced it. The relative form is already derived below for exactly
        # this reason.
        disagreements = [
            f"{path_name}: {row}"
            for path in sorted(ROOT.rglob("*.json"))
            if ".git" not in path.parts and "__pycache__" not in path.parts
            for payload in (self._loaded_json(path),)
            if payload is not None
            for path_name, record in self._declared_maturities(payload, path.relative_to(ROOT).as_posix())
            for row in self._maturity_disagreements(record)
        ]
        with self.subTest(half="committed records"):
            self.assertEqual(
                [], disagreements,
                "a committed record carries a maturity label its own version contradicts",
            )

        # (c) The check must FIRE on a contradiction, so that (a) and (b)
        # passing is a fact about the data rather than about the check. Versions
        # are built from the major so this covers every major, which is the
        # recurrence the standing half exists for -- not just the boundary that
        # happens to be current.
        for major in (1, 2, 3, 11):
            with self.subTest(half="fires on a contradiction", major=major):
                self.assertNotEqual(
                    (), self._maturity_disagreements(
                        {"version": f"{major}.0.0", "maturity": f"stable_{major - 1}_x"}),
                    "a version carrying the previous major's label was not reported",
                )

        # (d) and must NOT fire on an agreeing pair, so (c) is not vacuous.
        for major in (0, 1, 2, 3, 10):
            with self.subTest(half="silent when they agree", major=major):
                label = f"stable_{major}_x" if major >= 1 else "functional_pre_1_0"
                self.assertEqual(
                    (), self._maturity_disagreements({"version": f"{major}.4.1", "maturity": label}))

    @staticmethod
    def _loaded_json(path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None


if __name__ == "__main__":
    unittest.main()
