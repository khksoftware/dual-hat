"""Command-line validation for a standalone Dual Hat tree.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from framework_completeness import validate_framework


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Dual Hat semantic completeness")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args()
    failures = validate_framework(args.root)
    if args.json:
        print(json.dumps({"passed": not failures, "failures": list(failures)}, indent=2))
    elif failures:
        print("\n".join(f"FAIL: {failure}" for failure in failures))
    else:
        print("Dual Hat semantic completeness passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
