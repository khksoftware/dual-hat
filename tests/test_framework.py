# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

DUAL_HAT_CAPABILITY_PROOFS = {"canonical_path_containment", "network_policy_validation", "rights_readiness_validation"}

import ast
import builtins
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
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
    stage_manifest_owned,
    validate_bundle_version_currency,
    verify_commit_tree,
)
from publication_ownership import standalone_owned  # noqa: E402


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


# --- README "Framework areas" completeness (ENG-00170) ------------------------
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
    """Every top-level directory README.md's "Framework areas" section claims exists.

    Every backtick-quoted trailing-slash token on a bullet is taken, not just the
    first: one bullet legitimately names several directories.
    """
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
    return {
        relative.split("/", 1)[0]
        for path in repository_content_files(ROOT)
        for relative in (path.relative_to(ROOT).as_posix(),)
        if "/" in relative and not relative.startswith(".")
    }


# --- single-canonical-home support -------------------------------------------
#
# A cluster of these tests used to assert the same obligation, phrase by phrase,
# against every file that restated it. That pins duplication in place: the words
# cannot be consolidated to one home without the assertion going red, so the
# tests mechanise preservation of the redundancy rather than detecting anything
# about it.
#
# The failure that actually matters is not "this file no longer contains this
# sentence". It is "a reader of this file can no longer reach this obligation".
# The helpers below express exactly that, and nothing weaker:
#
#   * the canonical home is asserted to carry the obligation IN FULL and
#     UNCONDITIONALLY -- no assertion is relaxed there; and
#   * every other file that formerly restated it must EITHER still carry the
#     full substance OR carry a reference that resolves to THAT SPECIFIC
#     canonical file, which must exist.
#
# The chain closes end to end: secondary -> named canonical path -> that file
# exists -> that file is separately asserted to carry the obligation. A
# well-formed link to some other existing file does not satisfy the predicate,
# because confirming that a pointer is syntactically valid while saying nothing
# about where it points is the exact vacuity this rework exists to remove.
#
# The predicate is deliberately satisfiable in BOTH tree states: before
# consolidation the secondary carries the substance, after consolidation it
# carries the pointer. So there is no window in which the obligation is
# unguarded, and no exposure if consolidation is never performed.
#
# Known limitation, pre-existing and neither introduced nor repaired here: a
# secondary that keeps a working pointer while drifting its own prose passes, as
# does -- today, before any of this -- a file that keeps the pinned phrase and
# adds a clause contradicting it. These are `assertIn` checks on positive
# substrings; neither form detects contradiction.

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


def _negated_near(text: str, anchor: str, targets, *, window: int = 240) -> bool:
    """True when `anchor` is followed, within `window` characters, by a negation
    and one of `targets`.

    This exists because an unscoped `assertIn("accept", ...)` is satisfied by any
    "acceptance" anywhere in the document -- proven inert by mutation. Scoping the
    two halves of the obligation to one another is what makes the assertion
    capable of failing on the edit it is meant to catch.
    """
    negations = ("cannot", "never", "not ", "no ")
    start = 0
    while True:
        index = text.find(anchor, start)
        if index < 0:
            return False
        span = text[index + len(anchor):index + len(anchor) + window]
        if any(word in span for word in negations) and any(t in span for t in targets):
            return True
        start = index + 1


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
            # Caught in drafting on GOV-0011 deliverable 2, in this deliverable's
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


class FrameworkTests(CanonicalHomeAssertions, unittest.TestCase):
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
        """Direction 1 of 2: listed implies exists.

        Catches a dangling pointer -- an area named in README.md that no longer
        exists. On its own this direction is NOT sufficient and must never be
        the only check; see direction 2 below, which is the one the real drift
        needed.
        """
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
        """Direction 2 of 2: exists implies listed.

        This is the direction the actual drift needed and the reason a one-way
        check is refused: all seven of the twenty-one directories that went
        unlisted did exist, so a listed-implies-exists check would have passed
        throughout without a murmur.
        """
        unlisted = existing_framework_areas() - readme_framework_areas()
        self.assertEqual(
            set(),
            unlisted,
            "top-level framework areas exist that README.md's 'Framework areas' list "
            f"does not name: {sorted(unlisted)}. Direction checked: exists implies listed.",
        )

    def test_completeness_walk_excludes_repository_ignored_content(self):
        """Ignored residue is not unowned content and must not be reported as it.

        Before both walks consulted the repository's ignore state, any ignored
        artifact other than __pycache__ -- a .pytest_cache, a virtualenv, an
        egg-info, the generated agent-skill copies -- was reported as an
        unclassified file, under an error naming the EXPORT ALLOWLIST rather
        than the artifact that caused it:

            framework export classification mismatch;
            unclassified=['.ruff_cache/probe.txt', 'probe.egg-info/PKG-INFO']; stale=[]

        So a contributor who ran a linter or a test run inside the tree turned
        the framework's own completeness validator red and was then sent to the
        wrong file. The probe below is ignored by this tree's own .gitignore.
        """
        probe = ROOT / "framework-completeness-ignored-probe.pyc"
        self.assertFalse(probe.exists(), "probe path is already in use")
        probe.write_bytes(b"ignored residue")
        try:
            kept = {path.relative_to(ROOT).as_posix() for path in repository_content_files(ROOT)}
            self.assertNotIn(probe.name, kept)
            self.assertEqual((), validate_framework(ROOT))
        finally:
            probe.unlink(missing_ok=True)

    def test_ignore_derivation_reads_ancestor_nested_and_negated_rules(self):
        """The exclusion is derived from real ignore files, not restated as a list.

        Supplementary to the assertion above: it pins the derivation's semantics
        against a synthetic tree, including the ancestor case a Dual Hat tree
        vendored inside a larger repository actually depends on.
        """
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

    def test_examples_cover_operating_workflows(self):
        expected = {
            "bounded-task.example.json", "context-pack.example.json",
            "current-handover.example.json", "technical-debt.example.json",
            "validation-run.example.json", "roadmap-and-phase.example.md",
            "planning-backlog.example.json", "future-work.example.json",
            "planning-history.example.jsonl", "planning-lifecycle.example.md",
        }
        self.assertTrue(expected.issubset({path.name for path in (ROOT / "examples").iterdir()}))

    def test_templates_cover_bootstrap_domains(self):
        expected = {
            "WORK_ORDER.md", "CURRENT_HANDOVER.md", "CURRENT_HANDOVER.json",
            "ACTIVE_SESSION.md", "CONTEXT_PACK.md", "ROADMAP.md",
            "TECHNICAL_DEBT_BACKLOG.json", "CANONICAL_ENTRYPOINTS.md",
            "CANONICAL_DOMAIN_INDEX.md", "PRODUCT_REPOSITORY.md",
            "PLANNING_BACKLOG.json", "FUTURE_WORK_REGISTRY.json",
            "PLANNING_HISTORY.jsonl",
        }
        self.assertTrue(expected.issubset({path.name for path in (ROOT / "templates").iterdir()}))

    def test_role_and_retrieval_help_is_first_class(self):
        expected = {
            "governance/ARCHITECTURE_OFFICE_GUIDE.md",
            "governance/ENGINEERING_AGENT_GUIDE.md",
            "sessions/TASK_CONTEXT_RETRIEVAL.md",
            "guides/COMMAND_REFERENCE.md",
        }
        self.assertTrue(all((ROOT / path).is_file() for path in expected))
        self.assertFalse((ROOT / "docs").exists())

    def test_research_iterations_do_not_require_capability_churn(self):
        proportionality = (ROOT / "governance/GOVERNING_PRINCIPLES.md").read_text(encoding="utf-8")
        lifecycle = (ROOT / "process/CAPABILITY_LIFECYCLE.md").read_text(encoding="utf-8")
        self.assertIn("prefer explicit iterations within the same capability", proportionality)
        self.assertIn("does not require a separate capability identity", lifecycle)

    def test_specialist_review_and_long_run_reporting_contracts(self):
        review = (ROOT / "governance/CODE_REVIEW_CONTRACT.md").read_text(encoding="utf-8")
        engineering = (ROOT / "prompts/ENGINEERING_AGENT_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("Architecture/Design, UX, and QA", review)
        self.assertIn("bounded falsification-oriented posture", review)
        self.assertIn("one-to-five-minute user-update cadence", engineering)
        self.assertIn("Never invent percentage completion for an opaque worker", engineering)

    def test_routes_by_intended_end_without_mandatory_pipeline(self):
        # Re-pointed to one canonical home. Mutation evidence (deleting the
        # routing-lens statement from all four files) showed 14 of the original
        # 24 assertions survived that deletion, i.e. detected nothing:
        # `"not"` in all four files (11/32/33/39 occurrences -- it cannot fail
        # against any English document), `"single-role"` in all four (satisfied
        # by the unrelated self-acceptance sentence), and `deliver`/`discover`/
        # `decide` firing on "delivery"/"discovered"/"decides". Those bare
        # tokens are replaced here by phrases that name the obligation, so they
        # can be falsified by the edit they exist to catch.
        self.assert_single_canonical_home(
            lower=True,
            canonical="architecture/OPERATING_MODEL.md",
            canonical_substance=(
                "route a bounded activity by its intended end",
                "optional routing lenses",
                ("mandatory pipeline", "mandatory stages"),
            ),
            secondaries={
                "framework/DUAL_HAT_FRAMEWORK.md": (
                    "route an activity by its intended end",
                    ("mandatory pipeline", "mandatory stages"),
                ),
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": (
                    "single-role-pass routing only when it clarifies",
                    ("mandatory pipeline", "mandatory stages"),
                ),
                "prompts/ENGINEERING_AGENT_PROMPT.md": (
                    "single-role-pass labels only when they clarify",
                    ("mandatory pipeline", "mandatory stages"),
                ),
            },
        )

    def test_composes_distinct_value_roster_and_diagnoses_assignment(self):
        # This test carries TWO obligations over two disjoint file sets, so it
        # gets two canonical homes. 8 of its original 18 assertions detected
        # deletion. Dropped as proven inert: "smallest" and "distinct" (both
        # roster files) and "capability" and ("ownership","authority") (all
        # three assignment files) -- generic tokens satisfied elsewhere.
        self.assert_single_canonical_home(
            lower=True,
            canonical="governance/CODE_REVIEW_CONTRACT.md",
            canonical_substance=("failure axes",),
            secondaries={"prompts/ARCHITECTURE_OFFICE_PROMPT.md": ("failure axes",)},
        )
        self.assert_single_canonical_home(
            lower=True,
            canonical="governance/MODEL_TIER_AND_RUNTIME_BINDING.md",
            canonical_substance=("re-tier", "re-role"),
            secondaries={
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": ("re-tier", "re-role"),
                "prompts/ENGINEERING_AGENT_PROMPT.md": ("re-tier", "re-role"),
            },
        )

    def test_shared_artifact_lanes_are_single_writer(self):
        # The strongest of the duplication-pinning cluster: 21 of its 32
        # assertions detected deletion of the single-writer paragraph. The four
        # retained phrases each fired in all four files. Dropped as proven inert
        # against this obligation: "shared", "read-only", "checkpoint" (3 of 4
        # files each) and "writer" (2 of 4) -- generic tokens recurring
        # elsewhere in their own documents.
        substance = ("artifact lane", "active writer at a time",
                     "trivial serial", "quiescent")
        self.assert_single_canonical_home(
            lower=True,
            canonical="governance/VALIDATION_AND_PARALLELISM.md",
            canonical_substance=substance,
            secondaries={
                "governance/CODE_REVIEW_CONTRACT.md": substance,
                "framework/DUAL_HAT_FRAMEWORK.md": substance,
                # already carries a resolving link to the canonical home today
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
            },
        )

    def test_deliver_or_declare_is_only_for_governed_blockage(self):
        # 8 of the original 18 assertions detected deletion of the
        # deliver-or-declare paragraph. Retained are the two that fired in all
        # three files. Dropped as proven inert: "deliver" and "recoverable" (all
        # three files), "declare" and "preserved state" (two of three) -- each
        # satisfied by unrelated prose elsewhere in the same document.
        substance = ("blocked boundary", "exact obstacle")
        self.assert_single_canonical_home(
            lower=True,
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": substance,
                "prompts/ENGINEERING_AGENT_PROMPT.md": substance,
            },
        )

    def test_durable_learning_avoids_per_run_ledger(self):
        # 13 of the original 15 assertions detected deletion of the rule 17
        # statement. The two that did not -- "contradiction" and "staleness" in
        # GOVERNING_PRINCIPLES.md -- survive because that file discusses both
        # concepts under other rules, so they are dropped from the canonical
        # home's list while remaining load-bearing in the two secondaries.
        secondary_substance = ("accumulated framework release",
                               "governed phase progression",
                               "contradiction", "staleness", "per-run")
        self.assert_single_canonical_home(
            lower=True,
            canonical="governance/GOVERNING_PRINCIPLES.md",
            canonical_substance=("accumulated framework release",
                                 "governed phase progression", "per-run"),
            secondaries={
                "process/PHASE_RUN_PROTOCOL.md": secondary_substance,
                "framework/DUAL_HAT_FRAMEWORK.md": secondary_substance,
            },
        )

    def test_role_guides_apply_turn_exit_audit(self):
        # Re-pointed (GOV-0011 deliverable 2). The two role guides restated the
        # same turn-exit audit; asserting all six phrases against both files
        # unconditionally is what made the restatement un-removable.
        #
        # RELOCATED (GOV-0011 deliverable 2, Architecture ruling). The earlier
        # canonical home was governance/ENGINEERING_AGENT_GUIDE.md, chosen when
        # the two guides were peers -- both carried the full substance and
        # neither linked to the other. That choice could not survive the
        # consolidation: pointing either guide at the other hands its reader the
        # OTHER role's item 0, i.e. an instruction to emit a label that role may
        # never emit. The role-neutral body of the audit therefore moved to
        # framework/DUAL_HAT_FRAMEWORK.md -- the framework-wide invariant
        # contract, and the same home the continuity obligation was ruled into,
        # of which this audit is part of the same termination family. Each guide
        # retains only its own item 0 plus a pure reference. This test's earlier
        # comment anticipated exactly this move in writing; the `canonical=`
        # constant moved with it, as one visible reviewed line.
        substance = (
            "mandatory turn-exit audit",
            "before every response boundary",
            "do not emit a terminal response",
            "execute it in the same turn",
            "resumable next-action receipt",
            "accidental turn termination",
        )
        self.assert_single_canonical_home(
            lower=True,
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={
                "governance/ENGINEERING_AGENT_GUIDE.md": substance,
                "governance/ARCHITECTURE_OFFICE_GUIDE.md": substance,
            },
        )

    def test_role_label_check_is_item_zero_of_the_turn_exit_audit_with_named_resumption_points(self):
        # The role-label convention lived only in prompts/*_PROMPT.md with no tie-in
        # to the turn-exit audit next to it in these guides, so it silently lapsed
        # for consecutive responses with nothing catching it. The fix folded it in
        # as an explicit item 0 and named concrete resumption points where the full
        # audit must explicitly re-run; this guards that fix from the same
        # prose-only, untested drift it was written to prevent.
        # Re-pointed, then RELOCATED (GOV-0011 deliverable 2) to the same
        # canonical home as test_role_guides_apply_turn_exit_audit above, for
        # the same reason: this is item 0 of that audit and cannot sensibly live
        # in a different file from the audit it is item 0 of.
        #
        # Why relocating this one is safe even though item 0 is the ROLE-SPECIFIC
        # item: the two phrases below that come from item 0 are role-neutral as
        # strings. Neither names a role. The framework states them once in a
        # role-parameterised formulation ("the correct role label for the role
        # currently held"), and each guide independently keeps its own concrete
        # instance naming its own label. So the canonical home is genuinely
        # asserted in full, and no guide is made to carry another role's label.
        substance = (
            "0. in integrated mode, confirm this response begins with the correct role label",
            "role-boundary violation, not a formatting detail",
            "self-applied conventions",
            "no external code-level enforcement",
            "returning from a background-agent task notification",
            "returning from an unrelated tangent or side investigation",
            "context compaction summary is the active source of continuity",
        )
        self.assert_single_canonical_home(
            lower=True,
            canonical="framework/DUAL_HAT_FRAMEWORK.md",
            canonical_substance=substance,
            secondaries={
                "governance/ENGINEERING_AGENT_GUIDE.md": substance,
                "governance/ARCHITECTURE_OFFICE_GUIDE.md": substance,
            },
        )

    def test_hypothesis_blind_execution_and_three_arbiter_protocol_is_pinned_and_consistent(self):
        # REASONING_AND_DECISION_REVIEW.md defines sealed hypothesis-blind
        # execution, three-arbiter 3:0/2:1 voting, and the sealed-review gate on
        # narrowing external-source discovery/ingestion. Both prompts restated it
        # with independently drifted wording and no test tied any of the three
        # files together, so the restatements could diverge from each other or
        # from the canonical doc without anything catching it. Two concrete
        # drifts are fixed here (self-approval sentence unified across prompts;
        # Engineering's override list realigned from "evidence, mandatory
        # safeguards" to match the canonical/Architecture "primary evidence,
        # mandatory safety") and this test pins the shared substance so it
        # cannot silently re-diverge.
        # Re-pointed. The canonical home was already declared in this test's own
        # comment; it is now also the structural anchor.
        #
        # GUARD, and it is deliberate: the three assertions in the loop below --
        # "sealed independent reviewer", "population, rule, evidence, blind
        # spots", and the self-approval sentence -- are NOT part of the
        # hypothesis-blind obligation. Mutation proved they survive its deletion
        # in both prompts because they guard a DIFFERENT obligation living in the
        # adjacent paragraph: the external-source discovery/ingestion
        # restriction. They are mis-named, not inert. They are therefore kept
        # UNCONDITIONAL here rather than folded into the canonical-home
        # disjunction, because waiving them when a prompt defers on
        # hypothesis-blind would strand a real obligation with no check at all.
        # See PER_TEST_LEDGER.md T7 and the backlog candidate recorded there.
        canonical = "architecture/REASONING_AND_DECISION_REVIEW.md"
        normalized_canonical = _normalized(canonical)
        self.assertIn("convene exactly three sealed independent arbiters", normalized_canonical)
        self.assertIn("`3:0` or `2:1` decides within the authority", normalized_canonical)
        self.assertIn(
            "does not override primary evidence, mandatory safety, law, rights, privacy, "
            "explicit governance, a stop gate, or a decision reserved to the stakeholder or "
            "another authority",
            normalized_canonical,
        )
        self.assertIn("The proposing role cannot review its own restriction.", normalized_canonical)

        # The three preserved-in-place assertions for the adjacent obligation.
        for relative in ("prompts/ARCHITECTURE_OFFICE_PROMPT.md",
                         "prompts/ENGINEERING_AGENT_PROMPT.md"):
            normalized = _normalized(relative)
            self.assertIn("sealed independent reviewer", normalized)
            self.assertIn("population, rule, evidence, blind spots", normalized)
            self.assertIn("Neither Architecture nor Engineering may approve its own restriction.", normalized)

        self.assert_single_canonical_home(
            canonical=canonical,
            canonical_substance=("convene exactly three sealed independent arbiters",),
            secondaries={
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": (
                    "`3:0` or `2:1`",
                    "override primary evidence, mandatory safety, rights, privacy, governance, or a stop gate",
                    "For a material hypothesis choice or go/no-go question that can be tested, "
                    "preregister measures and thresholds and use sealed hypothesis-blind execution",
                    "commission exactly three isolated arbiters who research the same neutral "
                    "question from scratch without seeing one another's work",
                    "Treat the vote as advisory when the decision belongs to the user or another authority",
                ),
                "prompts/ENGINEERING_AGENT_PROMPT.md": (
                    "`3:0` or `2:1`",
                    "override primary evidence, mandatory safety, rights, privacy, governance, or a stop gate",
                    "keep the executor blind to sponsor preference, expected outcome, hypothesis "
                    "labels, and other parties' conclusions",
                    "provide the same neutral question and primary-evidence boundary to three "
                    "isolated agents, prevent cross-agent leakage, validate one locked vote per "
                    "report, and return the `3:0` or `2:1` result to Architecture",
                ),
            },
        )

    def test_universal_completion_claim_rule_is_pinned_and_consistent_across_governance_and_prompts(self):
        # The "complete"/"all"/"none remaining" scope-qualification rule was
        # independently restated in CONFORMANCE_POLICY.md and both prompts with
        # materially different prose, and CONFORMANCE_POLICY.md was never
        # referenced by filename in any test. Architecture's restatement was
        # also thinner than the other two: it never used the term "subset
        # completion" and never told the reader to reuse an existing manifest or
        # ledger instead of inventing new reporting ceremony, so it has been
        # brought into line with Conformance/Engineering here. This test pins
        # the shared substance across all three files.
        # EXEMPLAR. This is the only one of the nine in which every assertion
        # detects deletion of its own obligation -- 15 of 15, zero inert. That is
        # not luck. It is the consequence of one design choice, and it is the
        # rule applied when rebuilding T2 and tightening T1:
        #
        #   Assert LONG VERBATIM SPANS THAT NAME THE OBLIGATION, never generic
        #   tokens that merely co-occur with it.
        #
        # A span like "Reuse an existing manifest or ledger for this check"
        # cannot be satisfied by accident. A token like "accept" or "not" is
        # satisfied by any prose anywhere in the file, which is why the other
        # tests in this cluster carried roughly a hundred inert assertions
        # between them. Author replacements this way.
        shared = (
            "`complete`, `all`, `none remaining`, or",
            "authoritative inventory",
            "subset completion",
            "parent objective",
            "Reuse an existing manifest or ledger for this check",
        )
        self.assert_single_canonical_home(
            canonical="governance/CONFORMANCE_POLICY.md",
            canonical_substance=shared + (
                "Completion of a sample, batch, wave, medium, or other bounded subset must be "
                "reported as subset completion, never as completion of its parent objective.",
                "If the parent inventory is unknown or not yet reconciled, report the status as "
                "partial or unknown rather than inferring completion.",
            ),
            secondaries={
                "prompts/ARCHITECTURE_OFFICE_PROMPT.md": shared + (
                    "name the scope being closed and reconcile it against the authoritative "
                    "inventory by count and disposition.",
                    "Independently distinguish a completed sample, batch, wave, medium, or other "
                    "subset as subset completion, not completion of the parent objective",
                    "If the parent universe is unknown, say so; do not convert bounded evidence "
                    "into a universal completion claim.",
                ),
                "prompts/ENGINEERING_AGENT_PROMPT.md": shared + (
                    "Qualify every completion claim against the declared scope and authoritative inventory.",
                    "Report a completed sample, batch, wave, medium, or other subset as subset "
                    "completion rather than completion of the parent objective.",
                    "If the parent universe is unknown or has not been reconciled, report partial "
                    "or unknown status.",
                ),
            },
        )

    def test_version_and_plugin_ownership_boundary(self):
        version = json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))
        publication = (ROOT / "release/PUBLICATION.md").read_text(encoding="utf-8")
        # This milestone test protects invariants introduced at 1.17.0 and
        # still binding for every subsequent minor/patch release; the exact
        # published version is expected to advance without requiring a
        # change here, so this checks the numeric floor directly rather
        # than pinning one minor-line prefix that would need editing again
        # at the next minor bump.
        version_parts = tuple(int(part) for part in version["version"].split("."))
        self.assertGreaterEqual(version_parts, (1, 17, 0))
        current_release_notes = f"release/RELEASE_NOTES_v{version['version']}.md"
        self.assertTrue((ROOT / current_release_notes).is_file())
        source_map_path = ROOT / "export/EXPORT_SOURCES.json"
        if source_map_path.is_file():
            source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
            self.assertIn(current_release_notes, source_map["included"])
        # First-use readers land on this link before anything else; it must
        # always name the currently published release, not whichever one was
        # current when the paragraph was last edited.
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(current_release_notes, readme)
        self.assertIn("canonical source owns only the portable Dual Hat core", publication)
        self.assertIn("standalone", publication)
        self.assertIn("must not carry a", publication)
        self.assertNotIn("E" + "OS", publication)
        # Standalone-only plugin distribution legitimately exists under
        # plugins/ since 1.16.0; the portable-core boundary this test
        # protects is that none of it is ever classified as canonical
        # portable-core source, not that the directory itself is absent.
        plugins_root = ROOT / "plugins"
        if plugins_root.is_dir():
            for path in plugins_root.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(ROOT).as_posix()
                self.assertTrue(
                    standalone_owned(relative),
                    f"{relative} exists under plugins/ but is not "
                    "classified as standalone-owned",
                )

    def test_plugin_bundle_tracks_canonical_version(self):
        """Currency of the LIVE shipped bundle, asserted through its one owner.

        The plugin marketplace is a documented, officially supported install
        path; a stale bundle silently ships whatever governance or continuation
        defects the canonical framework has already fixed.

        The predicates belong to `validate_bundle_version_currency`, and this
        test calls it rather than restating them. Its distinct and still
        necessary job is asserting over *live shipped data*, which the gate's
        synthetic controls deliberately do not.

        It previously hand-implemented three of those predicates -- including a
        substring `framework_root` check where the gate uses equality, so the
        two already disagreed and a `dual-hat-<v>-old` root passed here while
        the gate refused it -- and discovered manifests through a hardcoded
        vendor list, the approach the gate's own rationale rejects for skipping
        whatever deployment form is added next.

        The plugin manifests' own "version" field previously tracked an
        independent packaging sequence (0.1.0, 0.2.0, ...) bumped in lockstep
        with every framework refresh but carrying no distinct meaning of its
        own. It now equals the framework version directly, removing that
        redundant parallel sequence -- a semantic this rule imposes on
        standalone-owned content, recorded in the change's classification.
        """
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

    def test_distinguishes_reassignment_from_authority_transition(self):
        transitions = (ROOT / "governance/ROLE_TRANSITIONS.md").read_text(encoding="utf-8")
        normalized = " ".join(transitions.lower().split())
        for required in (
            "re-tiering",
            "primary-hat transition",
            "specialist reassignment",
            "atomic safe boundary",
            "checkpointed",
            "architecture's acceptance authority",
        ):
            self.assertIn(required, normalized)
        self.assertIn("single-role pass", normalized)
        self.assertIn("sole authority to accept and archive", normalized)

    def test_single_role_pass_cannot_self_accept(self):
        # REPLACED, not re-pointed. Mutation evidence: deleting the
        # self-acceptance prohibition from all three files left 8 of the
        # original 9 assertions still passing. The whole test rested on the
        # literal string "single-role pass" surviving in one file; `"accept"`
        # was satisfied by "acceptance"/"accepted" elsewhere in every file, and
        # `("architecture", "self-acceptance")` by "architecture" appearing
        # 4/11/16 times per file. A rename or style pass touching that one token
        # would have retired the entire check silently.
        #
        # The obligation is core authority -- Engineering cannot accept its own
        # work -- so the check is rebuilt rather than dropped. It is still prose
        # matching; the property that changed is can-fail versus cannot-fail.
        # Scoping the anchor to the negation and the acceptance term means a
        # stray "acceptance" two hundred lines away no longer satisfies it.
        for relative in (
            "framework/DUAL_HAT_FRAMEWORK.md",
            "architecture/OPERATING_MODEL.md",
            "prompts/ENGINEERING_AGENT_PROMPT.md",
        ):
            normalized = _normalized(relative, lower=True)
            self.assertTrue(
                _negated_near(normalized, "single-role pass",
                              ("accept", "acceptance", "archiv")),
                f"{relative} no longer denies self-acceptance to a single-role "
                "pass within one statement; the prohibition may have been "
                "deleted while the words remained scattered in the file",
            )

    def test_blocked_state_has_entry_and_reentry_semantics(self):
        lifecycle = (ROOT / "process/WORK_ITEM_LIFECYCLE.md").read_text(encoding="utf-8")
        normalized = " ".join(lifecycle.lower().split())
        for required in (
            "governed lifecycle state",
            "no safe in-scope action remains",
            "exact obstacle",
            "re-entry condition",
            "neither accepted nor archived",
            "recorded checkpoint",
        ):
            self.assertIn(required, normalized)

    def test_durable_learning_has_nonplanning_owner(self):
        inventory = json.loads(
            (ROOT / "repository/FRAMEWORK_CAPABILITY_INVENTORY.json").read_text(encoding="utf-8")
        )
        domains = {row["id"]: row for row in inventory["domains"]}
        self.assertIn("durable-learning governance", domains["architecture"]["responsibilities"])
        self.assertNotIn(
            "accumulated durable-learning review",
            domains["planning"]["responsibilities"],
        )

    def test_plan_optimization_is_proportionate_and_retests_assumptions(self):
        # The heaviest test in the file: 23 phrases looped over 3 files = 69
        # assertions. 49 detected deletion of the rule 18 statement; 20 did not
        # and are dropped per file. Note the dropped set differs by file -- the
        # same token is load-bearing in one document and inert in another,
        # because the inert case merely has the word elsewhere. That is why the
        # disposition is per-token-per-file and not one list applied to N files;
        # the cheaper design is what produced the inert mass in the first place.
        self.assert_single_canonical_home(
            lower=True,
            canonical="governance/GOVERNING_PRINCIPLES.md",
            canonical_substance=(
                "brute force", "parallelism", "cheaper equivalent control",
                "sealed independent architecture optimization review", "straightforward",
                "bottleneck", "throughput", "value yield", "batching", "revise",
                "unchallenged", "consequence", "healthy work",
            ),
            secondaries={
                "planning/PLANNING_MODEL.md": (
                    "brute force", "value", "sequence", "parallelism", "checkpoint",
                    "evidence reuse", "cheaper equivalent control",
                    "sealed independent architecture optimization review", "straightforward",
                    "bottleneck", "throughput", "value yield", "batching", "wall time",
                    "revise", "unchallenged", "supported", "consequence", "uncertainty",
                    "healthy work",
                ),
                "prompts/ENGINEERING_AGENT_PROMPT.md": (
                    "brute force", "value", "sequence", "evidence reuse",
                    "cheaper equivalent control",
                    "sealed independent architecture optimization review", "straightforward",
                    "bottleneck", "throughput", "value yield", "batching", "wall time",
                    "revise", "unchallenged", "consequence", "healthy work",
                ),
            },
        )

    def test_concurrency_controls_require_executable_adverse_timing_validation(self):
        guidance = " ".join(
            (
                ROOT / "governance/VALIDATION_AND_PARALLELISM.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "competing actors",
            "adverse timing",
            "simultaneous acquisition",
            "token replacement",
            "stale-owner finalization",
            "process-identity reuse",
            "delayed child appearance",
            "cannot substantiate race-safety",
            "ordinary serial logic",
        ):
            self.assertIn(required, guidance)
        for required in (
            "inactivity-based",
            "stdout/stderr churn does not",
            "near two minutes",
            "near five minutes",
            "extend to ten minutes",
            "actively productive work has no ordinary wall-clock kill",
            "emergency ceiling is a last-resort invariant",
        ):
            self.assertIn(required, guidance)

    def test_hash_gates_declare_byte_policy_and_guard_worktree_drift(self):
        validation = " ".join(
            (
                ROOT / "validation/VALIDATION_PROTOCOL.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "every hash binding declares its byte policy",
            "repository-byte identity",
            "utf-8 without bom",
            "canonical lf newlines",
            "rejects invalid encoding, bom, and bare cr",
            "normalizes crlf to lf",
            "binary outputs, archives, databases, and release products always use",
            "never validate a mutable worktree input by hashing",
        ):
            self.assertIn(required, validation)

    def test_defect_closure_repairs_and_independently_reviews_the_failed_defense(self):
        proportionality = " ".join(
            (
                ROOT / "governance/GOVERNING_PRINCIPLES.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        review = " ".join(
            (
                ROOT / "governance/CODE_REVIEW_CONTRACT.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "concrete behavior",
            "owning root cause",
            "failed or missing prevention/detection defense",
            "reason it let the defect escape",
            "proportional executable regression evidence",
            "fail against the defective state",
            "directly analogous instances",
            "narrowest appropriate authority",
            "independent adversarial review",
            "attempts falsification",
            "new failure modes",
            "disproportionate runtime or maintenance cost",
            "independence is mandatory",
        ):
            self.assertIn(required, proportionality)
        self.assertIn("cannot approve its own prevention or detection repair", review)

    def test_systemic_mechanism_gap_recognition_is_pinned_and_cross_referenced_with_defect_closure(self):
        # Capability 234's closure surfaced two real defects that each looked
        # like an isolated slip but were not: a handover artifact went 11
        # commits stale because nothing mechanically checked its freshness,
        # and three consecutive phase closures in a row each failed to update
        # the same navigation pointers and archive the same superseded
        # document, because no documented closure step and no mechanical
        # check ever required it. Neither was fixed by correcting the one
        # instance in front of the agent; both required recognizing that the
        # apparent one-off was actually caused by one missing systemic
        # mechanism (an undocumented process step, or a synchronization check
        # that was never made mechanical) and repairing that mechanism. This
        # test pins the generalized rule (GOVERNING_PRINCIPLES.md rule 19)
        # and its cross-reference back to rule 15's correction-to-control
        # loop, so the two related rules stay linked rather than existing as
        # disconnected prose.
        proportionality = " ".join(
            (ROOT / "governance/GOVERNING_PRINCIPLES.md").read_text(encoding="utf-8").split()
        )
        for required in (
            "a missing systemic mechanism",
            "a process step that was never documented as mandatory",
            "a check that was never made mechanical, so correctness depended only on an agent remembering to do it",
            'a pointer, cross-reference, or "current state" marker that must track changing state but has no enforcement keeping it synchronized',
            "evidence of one shared systemic cause, not as independent bad luck",
            "do not close the investigation after explaining away each occurrence separately",
            "document the missing step, or add the missing mechanical enforcement",
            "the defect class becomes structurally hard to ship",
            "an instance-only fix leaves the same defect free to recur at the next occasion the pattern applies",
            "This complements rule 15's correction-to-control loop",
            "a precondition for generalizing that root cause correctly, not a substitute for it",
            "See rule 19 when the failure to prevent or detect this defect is itself evidence of a missing systemic mechanism",
        ):
            self.assertIn(required, proportionality)

    def test_convention_migration_requires_zero_stale_references_and_a_standing_literal_check(self):
        # A path-scoping convention changed once, and two of its consumer
        # scripts kept a hardcoded reference to the retired convention instead
        # of moving with it. Neither broke loudly -- each kept silently
        # resolving the superseded location -- and the drift was found only by
        # accident, months later, during an unrelated investigation. That is
        # exactly rule 19's "pointer or convention that must track changing
        # state but has no enforcement keeping it synchronized" shape, and it
        # is common enough across path schemes, identity/naming models, and
        # schema versions to warrant its own standing rule rather than relying
        # on rule 19's general recognition step to be applied fresh each time.
        # This test pins rule 20 and its cross-reference back to rule 19, so
        # the general gap-recognition rule and this specific standing defense
        # stay linked rather than existing as disconnected prose.
        proportionality = " ".join(
            (ROOT / "governance/GOVERNING_PRINCIPLES.md").read_text(encoding="utf-8").split()
        )
        for required in (
            "a path scheme, an identity or naming model, a schema version, or any other shared contract",
            "the change is not complete merely because its owning module or record was updated and its own tests pass",
            "prove with a mechanical check, not manual review, that every consumer moved with the convention",
            "a closure-blocking failure of the migration itself, not a follow-up item",
            "add a standing mechanical check that catches any new hardcoded reference to the superseded convention",
            "cannot silently reintroduce it later",
            "the standing defense for one especially common shape of rule 19's systemic mechanism gap",
            "applied specifically to convention migrations",
            "nothing to signal the drift until an unrelated investigation finds it by accident",
        ):
            self.assertIn(required, proportionality)

    def test_chat_switchover_uses_fresh_state_without_stopping_healthy_work(self):
        protocol = " ".join(
            (
                ROOT / "sessions/SESSION_AND_HANDOVER_PROTOCOL.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "ready to switch chats.",
            "nearest safe, low-ambiguity boundary",
            "without pausing healthy background work",
            "classify and reconcile every in-flight task",
            "delegated agent",
            "owned process",
            "fresh authoritative snapshot",
            "never construct the handoff from stale or assumed state",
            "compact current-project handoff artifact",
            "copyable bootstrap instruction",
            "full active goal",
            "exact current counters or state",
            "authoritative repository paths",
            "worktree ownership",
            "pending gates",
            "standing interaction",
            "safe to switch",
            "clean boundary cannot be reached promptly",
            "safest available handoff",
        ):
            self.assertIn(required, protocol)

    def test_consequential_parallel_work_has_one_nonopaque_orchestrator(self):
        guidance = " ".join(
            (
                ROOT / "governance/VALIDATION_AND_PARALLELISM.md"
            ).read_text(encoding="utf-8").lower().split()
        )
        for required in (
            "consequential delegated execution must not be opaque",
            "authoritative repository/workspace identity",
            "prohibited stale locations",
            "exactly one orchestrator",
            "parallel workers are pure bounded executors",
            "immutable leases",
            "structured terminal result",
            "never allocate follow-on work",
            "relaunch/reset a failed operation",
            "maximal contiguous checkpoint prefix",
            "retains later valid ranges behind gaps",
            "deduplicates exact identities",
            "residual immutable lease after quiescence",
            "complete recoverable unit payload",
            "hash-only receipt cannot",
            "cursor advancement occur atomically",
        ):
            self.assertIn(required, guidance)

    def test_inventory_separates_required_domains(self):
        payload = json.loads((ROOT / "repository/FRAMEWORK_CAPABILITY_INVENTORY.json").read_text(encoding="utf-8"))
        ids = {domain["id"] for domain in payload["domains"]}
        self.assertEqual(
            {"architecture", "engineering_execution", "planning", "validation",
             "repository_governance", "sessions_and_continuity",
             "publication_and_closure", "repository_and_product_onboarding",
             "model_tiers_and_runtime_binding", "documentation_and_help"},
            ids,
        )

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
        """A synthetic published tree carrying a plugin bundle.

        The payload carries the REAL shipped key set rather than a reduced one.
        That is not tidiness: the fixture previously omitted `schema`, and
        `schema` was precisely the field whose value tripped a false refusal
        under the original bare-digit token match. Five negative controls and a
        positive one all passed while a current bundle was one routine schema
        bump away from being refused, because no control ever put the real key
        set in front of the gate. A positive control that does not represent
        the artifact it certifies cannot certify it.
        """
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
        """Each control names the EXACT rows its own condition produces.

        The assertions were previously generic -- that the message mentioned
        the stale and the current version -- which cannot distinguish which
        condition fired. Control 1 was consequently over-determined and nobody
        could see it from the output: it set three payload fields stale at
        once, two of whose stale values also carry a framework-naming token, so
        it still refused with granularity 1 deleted outright. Asserting the
        exact row set is what makes a control self-isolate. Where a condition
        genuinely produces two rows, both are named here rather than hidden
        behind a substring match, so the redundancy is declared and a change to
        either granularity turns this red.
        """
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
        """A publication carrying a bundle but no version authority is refused.

        A hard obligation the gate has always enforced and the rule text did
        not state until this correction. Stating an obligation in a governed
        file that nothing compares against the code is how the two drift; this
        is the comparison.
        """
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
        """The walker the gate owns is the walker the shipped-data check calls.

        Two implementations of "what is a declared core version" would be two
        rules free to drift, which is the defect this whole repair is about.

        The behavioural half below pins the shared semantics, and on its own it
        CANNOT see the property this test is named for. It exercises the
        imported function directly, so reintroducing a local copy under any
        other name and re-pointing the shipped-data check at it left every
        assertion here green while the single authority was silently gone --
        measured, not supposed. A name asserting a structural property its body
        cannot detect is the same shape as a fixture that has stopped matching
        its detector: green because it stopped testing, not because the
        property holds.

        So the structural half asserts the property instead of the symptom, in
        the only two places it can fail: the defining module of the name this
        suite imports, and the defining module of every callable the
        shipped-data check actually names at its own call site.
        """
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

    def _reparse_flavours(self) -> tuple[str, ...]:
        """Every reparse flavour this host permits, or an honest skip if none does.

        These guards used to try a symlink and skip when the host refused one.
        On a host without symlink privilege that is not weak coverage, it is
        ABSENT coverage reporting as a skip: the guard never executed and never
        would. Probing both flavours converts them into tests that actually run
        wherever either kind of reparse point can be created.
        """
        with tempfile.TemporaryDirectory() as probe:
            flavours = available_reparse_flavours(Path(probe))
        if not flavours:
            self.skipTest("host permits neither a symlink nor a junction fixture")
        return flavours

    def test_staging_rejects_directory_symlink_without_touching_external_cache(self):
        for flavour in self._reparse_flavours():
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

    def test_staging_rejects_file_symlink_without_touching_external_cache(self):
        for flavour in self._reparse_flavours():
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
            eos_path = subprocess.run(
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
            self.assertIn("OK", eos_path.stderr)
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

    # --- the core version has exactly one authority ---------------------------
    #
    # Rule 20's second half, for the core-version convention. The instance fix
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

    def test_no_hardcoded_core_version_survives_the_release_evidence_authority(self):
        shipped = self._shipped_version()

        # (a) Code half. Any version-shaped string literal anywhere in the
        # tooling surface is a second authority for a value release/VERSION.json
        # already owns. AST constants are scanned rather than source text, so
        # the check sees an indirect binding -- a default argument, a dataclass
        # field, a decorator argument -- exactly as it sees a plain assignment.
        literals = [
            f"{module.relative_to(ROOT).as_posix()}:{node.lineno}: {node.value!r}"
            for module in sorted((ROOT / "tooling").glob("*.py"))
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

        # (b) Data half. Rule 20 names already-produced artifacts, not only code
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

    # --- a maturity label agrees with its own version -------------------------
    #
    # Rule 20's second half, for the maturity convention. Correcting the
    # derivation closes the first half only. The previous boundary was written
    # by hand for 0.x-to-1.x with nothing keeping it synchronized, and the
    # identical contradiction returned at 1.x-to-2.x: every major from 2 upward
    # was stamped stable_1_x and no test anywhere could notice. Without a
    # standing check this repair is a second one-time boundary fix on the same
    # unsynchronized convention, and 3.0.0 is the predicted third recurrence.
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

        # (b) Rule 20's data half. Fixing a derivation does nothing to
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
        # are built from the major so this covers 3.0.0 and beyond, which is the
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
