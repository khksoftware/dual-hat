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
import zipfile

from temporary_workspace import TemporaryWorkspacePolicy


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


def source_files() -> dict[str, bytes]:
    specification = json.loads((ROOT / "export/EXPORT_SOURCES.json").read_text(encoding="utf-8"))
    included = tuple(str(path) for path in specification["included"])
    actual = tuple(sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
        and path.relative_to(ROOT).as_posix() not in CONTROL_PATHS
    ))
    if tuple(sorted(included)) != actual:
        raise RuntimeError(
            f"release source classification mismatch; unclassified={sorted(set(actual) - set(included))}; "
            f"stale={sorted(set(included) - set(actual))}"
        )
    return {relative: normalized(ROOT / relative) for relative in sorted(included)}


def package_entries() -> dict[str, bytes]:
    release_version = version()
    prefix = f"dual-hat-{release_version}/"
    source = source_files()
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
    return {prefix + path: data for path, data in sorted({**source, **controls}.items())}


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


def build(output: Path, source_commit: str, external_publication_commit: str) -> dict[str, object]:
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
            "maturity": "functional_pre_1_0",
            "schema": "dual-hat-release-manifest/1.0",
            "version": release_version,
        }
        (staging / manifest_name).write_bytes(canonical_json(release_manifest))
        (staging / checksum_name).write_text(
            f"{validation['archive_sha256']}  {basename}\n", encoding="utf-8"
        )
        output.mkdir(parents=True, exist_ok=True)
        published: list[Path] = []
        try:
            for name in (basename, manifest_name, checksum_name):
                source = staging / name
                destination = output / name
                destination.write_bytes(source.read_bytes())
                published.append(destination)
                if sha256(destination.read_bytes()) != sha256(source.read_bytes()):
                    raise RuntimeError(f"published release artifact hash mismatch: {name}")
        except BaseException:
            for path in published:
                path.unlink(missing_ok=True)
            raise
    archive_path = output / basename
    manifest_path = output / manifest_name
    checksum_path = output / checksum_name
    return {
        **validation,
        "archive": archive_path.as_posix(),
        "checksum": checksum_path.as_posix(),
        "manifest": manifest_path.as_posix(),
        "version": release_version,
    }


def self_test(source_commit: str = "TEST-SOURCE", external_commit: str = "TEST-EXTERNAL") -> dict[str, object]:
    policy = TemporaryWorkspacePolicy(ROOT, namespace="dual-hat-release")
    with policy.owned_run("package-test") as run:
        first = run.subdirectory("first")
        second = run.subdirectory("second")
        one = build(first, source_commit, external_commit)
        two = build(second, source_commit, external_commit)
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
    parser.add_argument("action", choices=("build", "validate", "self-test"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--external-publication-commit")
    args = parser.parse_args()
    if args.action == "self-test":
        result = self_test()
    elif args.action == "validate":
        if args.archive is None:
            parser.error("validate requires --archive")
        result = validate_archive(args.archive)
    else:
        if args.output is None or not args.source_commit or not args.external_publication_commit:
            parser.error("build requires --output, --source-commit, and --external-publication-commit")
        result = build(args.output, args.source_commit, args.external_publication_commit)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
