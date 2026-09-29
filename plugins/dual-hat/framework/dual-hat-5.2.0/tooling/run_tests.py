# SPDX-License-Identifier: Apache-2.0
"""Run Dual Hat tests without generating repository bytecode caches."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import unittest  # noqa: E402
from pathlib import Path  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tests", nargs="*", help="optional dotted unittest names")
    parser.add_argument("--start-directory", default="tests")
    parser.add_argument("--pattern", default="test*.py")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    loader = unittest.defaultTestLoader
    if args.tests:
        suite = loader.loadTestsFromNames(args.tests)
    else:
        start_directory = Path(args.start_directory)
        if not start_directory.is_absolute():
            start_directory = ROOT / start_directory
        suite = loader.discover(
            str(start_directory.resolve()),
            pattern=args.pattern,
        )
    result = unittest.TextTestRunner(verbosity=2 if args.verbose else 1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
