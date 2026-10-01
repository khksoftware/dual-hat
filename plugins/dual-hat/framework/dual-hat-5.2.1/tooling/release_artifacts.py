"""Classify generated Dual Hat release products outside canonical source inputs.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import re


_RELEASE_PRODUCT = re.compile(
    r"^release/v(?P<version>\d+\.\d+\.\d+)/dual-hat-(?P=version)"
    r"(?:\.zip|\.release\.json|\.zip\.sha256)$"
)


def is_release_product(relative_path: str) -> bool:
    """Return whether a canonical-root-relative path is a governed release product."""

    return _RELEASE_PRODUCT.fullmatch(relative_path.replace("\\", "/")) is not None
