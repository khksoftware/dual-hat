"""Build and verify deterministic Dual Hat ZIP releases.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit
import zipfile

from temporary_workspace import TemporaryWorkspacePolicy
from release_artifacts import is_release_product
from content_security import inspect_content_set
from path_containment import ContainmentError, contained
from staged_publication import verify_commit_tree


ROOT = Path(__file__).resolve().parents[1]
CONTROL_PATHS = {"export/EXPORT_READINESS.json", "export/EXPORT_SOURCES.json"}
ARCHIVE_DATE = (1980, 1, 1, 0, 0, 0)


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def normalized(path: Path) -> bytes:
    data = path.read_bytes()
    if b"\x00" in data:
        return data
    text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if path.suffix.lower() == ".json":
        return canonical_json(json.loads(text))
    return text.encode("utf-8")


def version() -> str:
    return str(json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))["version"])


def version_record() -> dict[str, object]:
    return json.loads((ROOT / "release/VERSION.json").read_text(encoding="utf-8"))


def release_maturity(release_version: str) -> str:
    return "stable_1_x" if int(release_version.split(".", 1)[0]) >= 1 else "functional_pre_1_0"


def source_files() -> dict[str, bytes]:
    canonical_specification = ROOT / "export/EXPORT_SOURCES.json"
    publication_manifest = ROOT / ".dual-hat/export-manifest.json"
    if canonical_specification.is_file():
        specification = json.loads(canonical_specification.read_text(encoding="utf-8"))
        included = tuple(str(path) for path in specification["included"])
        expected_publication: set[str] | None = None
    elif publication_manifest.is_file():
        manifest = json.loads(publication_manifest.read_text(encoding="utf-8"))
        records = manifest.get("content_files")
        if not isinstance(records, list):
            raise RuntimeError("published source manifest lacks content records")
        included = tuple(
            str(row["path"]) for row in records
            if isinstance(row, dict) and row.get("origin") == "canonical_source"
        )
        expected_publication = {str(row["path"]) for row in records if isinstance(row, dict)} | {
            ".dual-hat/export-manifest.json", ".dual-hat/published-state.json",
        }
    else:
        raise RuntimeError("release packaging requires a canonical allowlist or published export manifest")
    actual = tuple(sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
        and path.relative_to(ROOT).as_posix() not in CONTROL_PATHS
        and not is_release_product(path.relative_to(ROOT).as_posix())
    ))
    expected = tuple(sorted(expected_publication)) if expected_publication is not None else tuple(sorted(included))
    if expected != actual:
        raise RuntimeError(
            f"release source classification mismatch; unclassified={sorted(set(actual) - set(expected))}; "
            f"stale={sorted(set(expected) - set(actual))}"
        )
    missing_inputs = sorted(set(included) - set(actual))
    if missing_inputs:
        raise RuntimeError(f"release source inputs are missing: {missing_inputs}")
    try:
        result = {relative: normalized(contained(ROOT, relative, must_exist=True, kind="file")) for relative in sorted(included)}
    except ContainmentError as exc:
        raise RuntimeError(f"release source containment failed: {exc}") from exc
    if publication_manifest.is_file():
        declared = {
            str(row["path"]): (row.get("sha256"), row.get("bytes"))
            for row in records if isinstance(row, dict) and row.get("origin") == "canonical_source"
        }
        mismatches = sorted(path for path, data in result.items()
                            if declared.get(path) != (sha256(data), len(data)))
        if mismatches:
            raise RuntimeError(f"published source bytes contradict export provenance: {mismatches}")
    return result


def _git(*arguments: str) -> str:
    result = subprocess.run(("git", *arguments), cwd=ROOT, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Git provenance query failed")
    return result.stdout.strip()


def _remote_identity(value: str) -> str:
    raw=value.strip().replace("\\","/")
    if not raw: return ""
    if "://" in raw:
        parsed=urlsplit(raw); host=(parsed.hostname or "").casefold(); path=parsed.path
    else:
        scp=raw.split("@",1)[-1]
        if ":" in scp: host,path=scp.split(":",1)
        else:
            parts=scp.split("/",1); host=parts[0]; path=parts[1] if len(parts)>1 else ""
        host=host.casefold()
    path=path.removesuffix(".git").strip("/").casefold()
    return f"{host}/{path}" if host and path else ""


def _fresh_remote_ref(remote: str = "origin", branch: str = "main") -> str:
    output=_git("ls-remote","--heads",remote,f"refs/heads/{branch}")
    rows=[line.split() for line in output.splitlines() if line.strip()]
    if len(rows)!=1 or len(rows[0])!=2 or rows[0][1]!=f"refs/heads/{branch}" or not __import__("re").fullmatch(r"[0-9a-f]{40}",rows[0][0]):
        raise RuntimeError("fresh remote query did not return one canonical branch identity")
    return rows[0][0]


def fresh_remote_repository_state(expected_remote_identity: str, *, expected_remote_commit: str | None = None) -> dict[str, object]:
    """Query the authorized remote and prove canonical local/upstream alignment."""
    approved=_remote_identity(expected_remote_identity)
    if not approved: raise RuntimeError("approved remote identity is invalid")
    head=_git("rev-parse","HEAD"); branch=_git("branch","--show-current"); upstream=_git("rev-parse","--abbrev-ref","--symbolic-full-name","@{upstream}")
    if branch!="main" or upstream!="origin/main": raise RuntimeError("standalone publication is not on canonical main and origin/main")
    fetch_identity=_remote_identity(_git("remote","get-url","origin")); push_identity=_remote_identity(_git("remote","get-url","--push","origin"))
    if fetch_identity!=approved or push_identity!=approved: raise RuntimeError("standalone publication fetch or push endpoint is not the explicitly approved repository identity")
    remote_head=_fresh_remote_ref(); cached_head=_git("rev-parse",upstream)
    if expected_remote_commit is not None and remote_head!=expected_remote_commit: raise RuntimeError("fresh remote main differs from the authorized expected starting or publication commit")
    if remote_head!=head or cached_head!=remote_head: raise RuntimeError("fresh remote main, cached upstream, and local publication HEAD are not aligned")
    return {"schema":"dual-hat-fresh-remote-state/1.0","remote":"origin","branch":"main","remote_ref":"refs/heads/main",
            "local_commit":head,"cached_upstream_commit":cached_head,"fresh_remote_commit":remote_head,
            "fetch_endpoint_identity":fetch_identity,"push_endpoint_identity":push_identity}


def release_provenance_record(expected_remote_identity: str) -> dict[str, object]:
    if not expected_remote_identity.strip(): raise RuntimeError("production release requires an explicit external repository identity")
    remote_state=fresh_remote_repository_state(expected_remote_identity)
    head=str(remote_state["local_commit"])
    if not __import__("re").fullmatch(r"[0-9a-f]{40}",head): raise RuntimeError("publication repository HEAD is not a commit identity")
    if _git("status","--porcelain=v1","--","."): raise RuntimeError("release inputs are not committed in the active repository")
    publication_manifest=ROOT/".dual-hat/export-manifest.json"; marker_path=ROOT/".dual-hat/published-state.json"
    if not publication_manifest.is_file() or not marker_path.is_file(): raise RuntimeError("production release provenance requires standalone publication controls")
    manifest_bytes=publication_manifest.read_bytes(); manifest=json.loads(manifest_bytes); marker=json.loads(marker_path.read_text(encoding="utf-8"))
    marker_fields={"schema","license_expression","source_commit","tree_sha256","manifest_sha256","previous_export_identity","canonical_branch"}
    if set(marker)!=marker_fields or marker.get("schema")!="dual-hat-published-state/1.0" or marker.get("license_expression")!="Apache-2.0" or marker.get("canonical_branch")!="main": raise RuntimeError("standalone publication marker contract is invalid")
    records=manifest.get("content_files")
    if not isinstance(records,list) or not records or manifest.get("tree_sha256")!=sha256(canonical_json(records)):
        raise RuntimeError("standalone publication tree identity is not reproducible from manifest records")
    source=str(manifest.get("source_commit",""))
    if not __import__("re").fullmatch(r"[0-9a-f]{40}",source): raise RuntimeError("export manifest source commit is invalid")
    if marker.get("source_commit")!=source or marker.get("tree_sha256")!=manifest.get("tree_sha256") or marker.get("manifest_sha256")!=sha256(manifest_bytes):
        raise RuntimeError("standalone publication marker does not bind the exact export manifest bytes")
    committed=verify_commit_tree(ROOT,"HEAD")
    if committed.get("commit")!=head or committed.get("manifest_sha256")!=marker.get("manifest_sha256"):
        raise RuntimeError("committed publication tree does not match marker and manifest provenance")
    return {"schema":"dual-hat-remote-publication-provenance/1.0","canonical_source_commit":source,
            "external_publication_commit":head,"publication_tree":_git("rev-parse","HEAD^{tree}"),
            "manifest_tree_sha256":manifest["tree_sha256"],"manifest_sha256":marker["manifest_sha256"],
            "remote":"origin","branch":"main","remote_ref":"refs/heads/main","fresh_remote_commit":remote_state["fresh_remote_commit"],
            "fetch_endpoint_identity":remote_state["fetch_endpoint_identity"],"push_endpoint_identity":remote_state["push_endpoint_identity"]}


def release_provenance(expected_remote_identity: str) -> tuple[str, str]:
    record=release_provenance_record(expected_remote_identity)
    return str(record["canonical_source_commit"]),str(record["external_publication_commit"])


def package_entries() -> dict[str, bytes]:
    release_version = version()
    prefix = f"dual-hat-{release_version}/"
    source = source_files()
    inspect_content_set(source)
    records = [
        {"bytes": len(data), "path": path, "sha256": sha256(data)}
        for path, data in sorted(source.items())
    ]
    content_manifest = canonical_json({
        "archive_root": prefix.rstrip("/"),
        "file_count": len(records),
        "files": records,
        "license_expression": "Apache-2.0",
        "schema": "dual-hat-release-content-manifest/1.0",
        "version": release_version,
    })
    checksum_rows = [f"{row['sha256']}  {row['path']}" for row in records]
    checksum_rows.append(
        f"{sha256(content_manifest)}  .dual-hat-release/content-manifest.json"
    )
    controls = {
        ".dual-hat-release/content-manifest.json": content_manifest,
        ".dual-hat-release/SHA256SUMS": ("\n".join(checksum_rows) + "\n").encode("utf-8"),
    }
    complete = {**source, **controls}
    inspect_content_set(complete)
    return {prefix + path: data for path, data in sorted(complete.items())}


def _write_zip(destination: Path, entries: dict[str, bytes]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, data in sorted(entries.items()):
            info = zipfile.ZipInfo(path, ARCHIVE_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def validate_archive(archive_path: Path) -> dict[str, object]:
    expected = package_entries()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if names != sorted(expected):
            raise RuntimeError("release archive entries are not exact and deterministically ordered")
        actual = {name: archive.read(name) for name in names}
        if actual != expected:
            raise RuntimeError("release archive content differs from canonical package plan")
        if any(info.date_time != ARCHIVE_DATE for info in archive.infolist()):
            raise RuntimeError("release archive timestamp normalization failed")
    return {
        "archive_sha256": sha256(archive_path.read_bytes()),
        "entry_count": len(expected),
        "status": "passed",
    }


def _is_reparse(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


def _validate_output_boundary(output: Path, names: tuple[str, ...]) -> None:
    if output.exists() and _is_reparse(output):
        raise RuntimeError("release output directory is a reparse point")
    if output.exists():
        actual = {path.name for path in output.iterdir()}
        if actual and actual != set(names):
            raise RuntimeError(f"release-set membership mismatch before mutation; extra={sorted(actual-set(names))}; missing={sorted(set(names)-actual)}")
        for path in output.iterdir():
            if _is_reparse(path) or not path.is_file():
                raise RuntimeError(f"release output artifact is not a regular file: {path.name}")


def build(output: Path, source_commit: str | None = None, external_publication_commit: str | None = None, *,
          failure_after_publish: int | None = None, production: bool = True,
          expected_remote_identity: str = "") -> dict[str, object]:
    if production:
        provenance_record=release_provenance_record(expected_remote_identity)
        derived_source,derived_publication=str(provenance_record["canonical_source_commit"]),str(provenance_record["external_publication_commit"])
    else:
        head = _git("rev-parse", "HEAD")
        derived_source, derived_publication = head, head
        provenance_record={"schema":"dual-hat-remote-publication-provenance/1.0","verification":"not_applicable_nonpublishable_plan"}
    if source_commit is not None and source_commit != derived_source:
        raise RuntimeError("requested canonical source commit contradicts repository provenance")
    if external_publication_commit is not None and external_publication_commit != derived_publication:
        raise RuntimeError("requested external publication commit contradicts repository provenance")
    source_commit, external_publication_commit = derived_source, derived_publication
    release_version = version()
    basename = f"dual-hat-{release_version}.zip"
    manifest_name = f"dual-hat-{release_version}.release.json"
    checksum_name = f"dual-hat-{release_version}.zip.sha256"
    policy = TemporaryWorkspacePolicy(ROOT, namespace="dual-hat-release")
    with policy.owned_run("package-build") as run:
        staging = run.subdirectory("staging")
        staged_archive = staging / basename
        entries = package_entries()
        _write_zip(staged_archive, entries)
        validation = validate_archive(staged_archive)
        release_manifest = {
            "archive": basename,
            "archive_bytes": staged_archive.stat().st_size,
            "archive_entry_count": len(entries),
            "archive_sha256": validation["archive_sha256"],
            "archive_root": f"dual-hat-{release_version}/",
            "canonical_source_commit": source_commit,
            "external_publication_commit": external_publication_commit,
            "files": [
                {"bytes": len(data), "path": path, "sha256": sha256(data)}
                for path, data in sorted(entries.items())
            ],
            "format": "zip",
            "license_expression": "Apache-2.0",
            "maturity": release_maturity(release_version),
            "publication_provenance": provenance_record,
            "release_mode": "production_standalone" if production else "nonpublishable_plan",
            "schema": "dual-hat-release-manifest/1.0",
            "version": release_version,
        }
        (staging / manifest_name).write_bytes(canonical_json(release_manifest))
        (staging / checksum_name).write_text(
            f"{validation['archive_sha256']}  {basename}\n", encoding="utf-8"
        )
        validate_release_set(staging, source_commit=source_commit, external_publication_commit=external_publication_commit,
                             require_publication_provenance=production, expected_remote_identity=expected_remote_identity)
        names = (basename, manifest_name, checksum_name)
        _validate_output_boundary(output, names)
        output.mkdir(parents=True, exist_ok=True)
        prior = {name: (output / name).read_bytes() for name in names if (output / name).is_file()}
        try:
            for index, name in enumerate(names, 1):
                source = staging / name
                destination = output / name
                temporary = output / f".{name}.replace.tmp"
                temporary.write_bytes(source.read_bytes())
                os.replace(temporary, destination)
                if sha256(destination.read_bytes()) != sha256(source.read_bytes()):
                    raise RuntimeError(f"published release artifact hash mismatch: {name}")
                if failure_after_publish == index:
                    raise RuntimeError("injected release publication failure")
            release_set = validate_release_set(
                output, source_commit=source_commit,
                external_publication_commit=external_publication_commit,
                require_publication_provenance=production, expected_remote_identity=expected_remote_identity)
            if failure_after_publish == 4:
                raise RuntimeError("injected release final-validation failure")
        except BaseException:
            for name in names:
                destination = output / name
                (output / f".{name}.replace.tmp").unlink(missing_ok=True)
                if name in prior:
                    restore = output / f".{name}.rollback.tmp"
                    restore.write_bytes(prior[name])
                    os.replace(restore, destination)
                else:
                    destination.unlink(missing_ok=True)
            raise
    archive_path = output / basename
    manifest_path = output / manifest_name
    checksum_path = output / checksum_name
    return {
        **release_set,
        "archive": archive_path.as_posix(),
        "checksum": checksum_path.as_posix(),
        "manifest": manifest_path.as_posix(),
        "version": release_version,
        "rollback_state": "not_required",
    }


def validate_release_set(output: Path, *, source_commit: str | None = None,
                         external_publication_commit: str | None = None,
                         require_publication_provenance: bool = True,
                         expected_remote_identity: str = "") -> dict[str, object]:
    release_version = version()
    basename = f"dual-hat-{release_version}.zip"
    expected = {basename, f"dual-hat-{release_version}.release.json", f"dual-hat-{release_version}.zip.sha256"}
    if output.exists() and _is_reparse(output):
        raise RuntimeError("release output directory is a reparse point")
    actual = {path.name for path in output.iterdir()} if output.is_dir() else set()
    if actual != expected:
        raise RuntimeError(f"release-set membership mismatch; missing={sorted(expected-actual)}; extra={sorted(actual-expected)}")
    archive = output / basename
    validation = validate_archive(archive)
    manifest_path = output / f"dual-hat-{release_version}.release.json"
    checksum_path = output / f"dual-hat-{release_version}.zip.sha256"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checksum = checksum_path.read_text(encoding="utf-8").strip()
    expected_maturity = release_maturity(release_version)
    if version_record().get("maturity") != expected_maturity:
        raise RuntimeError("VERSION maturity contradicts semantic version maturity")
    if manifest.get("version") != release_version or manifest.get("maturity") != expected_maturity:
        raise RuntimeError("release manifest version or maturity contradicts framework version")
    if manifest.get("archive") != basename or manifest.get("archive_sha256") != validation["archive_sha256"]:
        raise RuntimeError("release manifest does not bind the archive")
    entries = package_entries()
    expected_files = [{"bytes": len(data), "path": path, "sha256": sha256(data)}
                      for path, data in sorted(entries.items())]
    if manifest.get("archive_entry_count") != validation["entry_count"] or manifest.get("files") != expected_files:
        raise RuntimeError("release manifest entry count is inconsistent")
    expected_manifest_fields = {
        "archive", "archive_bytes", "archive_entry_count", "archive_sha256", "archive_root",
        "canonical_source_commit", "external_publication_commit", "files", "format",
        "license_expression", "maturity", "publication_provenance", "release_mode", "schema", "version",
    }
    if set(manifest) != expected_manifest_fields:
        raise RuntimeError("release manifest fields are not exact")
    if manifest.get("archive_bytes") != archive.stat().st_size or manifest.get("archive_root") != f"dual-hat-{release_version}/":
        raise RuntimeError("release manifest archive metadata is inconsistent")
    if manifest.get("format") != "zip" or manifest.get("license_expression") != "Apache-2.0" or manifest.get("schema") != "dual-hat-release-manifest/1.0":
        raise RuntimeError("release manifest contract metadata is inconsistent")
    if manifest.get("release_mode") not in {"production_standalone", "nonpublishable_plan"}:
        raise RuntimeError("release manifest mode is invalid")
    if require_publication_provenance and manifest.get("release_mode") != "production_standalone":
        raise RuntimeError("nonpublishable release plan cannot satisfy production provenance")
    if checksum != f"{validation['archive_sha256']}  {basename}":
        raise RuntimeError("release checksum companion disagrees with the archive")
    if source_commit is not None and manifest.get("canonical_source_commit") != source_commit:
        raise RuntimeError("release manifest canonical commit mismatch")
    if external_publication_commit is not None and manifest.get("external_publication_commit") != external_publication_commit:
        raise RuntimeError("release manifest publication commit mismatch")
    for field in ("canonical_source_commit", "external_publication_commit"):
        if not __import__("re").fullmatch(r"[0-9a-f]{40}", str(manifest.get(field, ""))): raise RuntimeError("release manifest commit identity is invalid")
    if require_publication_provenance:
        derived=release_provenance_record(expected_remote_identity)
        if (manifest.get("canonical_source_commit") != derived["canonical_source_commit"]
                or manifest.get("external_publication_commit") != derived["external_publication_commit"]
                or manifest.get("publication_provenance") != derived):
            raise RuntimeError("release manifest does not match verified standalone publication provenance")
    elif manifest.get("publication_provenance")!={"schema":"dual-hat-remote-publication-provenance/1.0","verification":"not_applicable_nonpublishable_plan"}:
        raise RuntimeError("nonpublishable release plan contains invalid publication provenance")
    inspect_content_set({manifest_path.name: manifest_path.read_bytes(), checksum_path.name: checksum_path.read_bytes()})
    return {
        **validation,
        "release_mode": manifest["release_mode"],
        "release_set": "passed",
        "version": release_version,
    }


def self_test() -> dict[str, object]:
    policy = TemporaryWorkspacePolicy(ROOT, namespace="dual-hat-release")
    with policy.owned_run("package-test") as run:
        first = run.subdirectory("first")
        second = run.subdirectory("second")
        one = build(first, production=False)
        two = build(second, production=False)
        first_archive = first / f"dual-hat-{version()}.zip"
        second_archive = second / f"dual-hat-{version()}.zip"
        if first_archive.read_bytes() != second_archive.read_bytes():
            raise RuntimeError("release package rebuild is not deterministic")
        extract = run.subdirectory("extract")
        with zipfile.ZipFile(first_archive) as archive:
            archive.extractall(extract)
        package_root = extract / f"dual-hat-{version()}"
        completed = subprocess.run(
            (sys.executable, str(package_root / "tooling/validate_framework.py"), "--root", str(package_root)),
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise RuntimeError(completed.stdout + completed.stderr)
        tests = subprocess.run(
            (sys.executable, "-m", "unittest", "discover", "-s", "tests"),
            cwd=package_root,
            capture_output=True,
            text=True,
            env={**os.environ, "DUAL_HAT_RELEASE_SELF_TEST_CHILD": "1"},
        )
        if tests.returncode:
            raise RuntimeError(tests.stdout + tests.stderr)
        return {
            **one,
            "deterministic": True,
            "extracted_framework_validation": "passed",
            "extracted_tests": "passed",
            "second_archive_sha256": two["archive_sha256"],
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "validate", "self-test", "verify-remote"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--external-publication-commit")
    parser.add_argument("--expected-remote-identity")
    parser.add_argument("--expected-remote-commit")
    args = parser.parse_args()
    if args.action == "self-test":
        result = self_test()
    elif args.action == "verify-remote":
        if not args.expected_remote_identity: parser.error("verify-remote requires --expected-remote-identity")
        result=fresh_remote_repository_state(args.expected_remote_identity,expected_remote_commit=args.expected_remote_commit)
    elif args.action == "validate":
        if args.output is None:
            parser.error("validate requires --output for the exact release set")
        result = validate_release_set(args.output, source_commit=args.source_commit,
                                      external_publication_commit=args.external_publication_commit,
                                      expected_remote_identity=args.expected_remote_identity or "")
    else:
        if args.output is None:
            parser.error("build requires --output")
        result = build(args.output, args.source_commit, args.external_publication_commit,
                       expected_remote_identity=args.expected_remote_identity or "")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
