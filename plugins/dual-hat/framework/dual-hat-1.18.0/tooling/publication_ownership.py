# SPDX-License-Identifier: Apache-2.0
"""Disjoint ownership policy for composite standalone publications."""

from __future__ import annotations


STANDALONE_OWNED_PREFIXES = (
    ".agents/plugins/",
    ".claude-plugin/",
    "assets/",
    "plugins/",
)
STANDALONE_OWNED_PATHS = {
    "BINARY_PROVENANCE.json",
    "guides/DEPLOYMENT_FORMS.md",
    "release/RELEASE_NOTES_v1.16.0.md",
    "tests/test_agent_plugin_package.py",
}


def standalone_owned(path: str) -> bool:
    """Return whether ``path`` belongs to standalone deployment packaging."""

    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return (
        normalized in STANDALONE_OWNED_PATHS
        or any(normalized.startswith(prefix) for prefix in STANDALONE_OWNED_PREFIXES)
    )
