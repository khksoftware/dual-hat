"""Fail-closed binary classification and prohibited-content inspection.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import hashlib
import re
from pathlib import PurePosixPath
from typing import Mapping, Sequence


SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[opurs]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"\b(?:sk|rk|pk)_(?:live|test)_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{12,}", re.I),
)
REQUIRED_ATTESTATION_FIELDS = {
    "path", "content_type", "purpose", "provenance", "sha256", "size_bytes",
    "rights_basis", "review_evidence", "retention_rule", "distribution_rule",
}
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".py", ".js", ".html", ".css", ".txt", ".toml", ".yaml", ".yml", ".sha256"}
TEXT_BASENAMES = {"LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "README", ".gitignore", "SHA256SUMS"}


class ContentSecurityError(RuntimeError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def secret_hits(path: str, data: bytes) -> tuple[str, ...]:
    subject = PurePosixPath(path)
    if subject.suffix.casefold() not in TEXT_SUFFIXES and subject.name not in TEXT_BASENAMES:
        raise ContentSecurityError(f"unsupported binary requires explicit allowlist and attestation: {path}")
    if b"\x00" in data or any(byte < 9 or 13 < byte < 32 for byte in data):
        raise ContentSecurityError(f"unsupported binary requires explicit allowlist and attestation: {path}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise ContentSecurityError(f"unsupported binary requires explicit allowlist and attestation: {path}")
    return tuple(f"{path}:{pattern.pattern}" for pattern in SECRET_PATTERNS if pattern.search(text))


def validate_binary_attestation(path: str, data: bytes, attestation: Mapping[str, object]) -> None:
    missing = REQUIRED_ATTESTATION_FIELDS - set(attestation)
    if missing or any(attestation.get(field) in (None, "") for field in REQUIRED_ATTESTATION_FIELDS):
        raise ContentSecurityError(f"binary attestation is incomplete for {path}: {sorted(missing)}")
    if attestation.get("path") != PurePosixPath(path).as_posix():
        raise ContentSecurityError(f"binary attestation path mismatch: {path}")
    if attestation.get("sha256") != sha256(data) or attestation.get("size_bytes") != len(data):
        raise ContentSecurityError(f"binary attestation hash or size mismatch: {path}")
    if attestation.get("distribution_rule") != "include":
        raise ContentSecurityError(f"binary present in publication set must have distribution_rule include: {path}")


def inspect_content_set(
    files: Mapping[str, bytes], *, binary_attestations: Sequence[Mapping[str, object]] = ()
) -> dict[str, object]:
    attestations = {str(row.get("path", "")): row for row in binary_attestations}
    classifications: list[dict[str, object]] = []
    hits: list[str] = []
    for path, data in sorted(files.items()):
        try:
            found = secret_hits(path, data)
            hits.extend(found)
            classifications.append({"path": path, "state": "text_scanned", "secret_hits": len(found)})
        except ContentSecurityError:
            attestation = attestations.get(path)
            if attestation is None:
                raise
            validate_binary_attestation(path, data, attestation)
            classifications.append({"path": path, "state": "allowlisted_binary_attested", "secret_hits": "not_scanned"})
    unknown = sorted(set(attestations) - set(files))
    if unknown:
        raise ContentSecurityError(f"binary allowlist contains absent payloads: {unknown}")
    if hits:
        raise ContentSecurityError(f"possible secrets in governed content: {hits}")
    return {"status": "passed", "classifications": classifications, "binary_attestation_count": len(attestations)}
