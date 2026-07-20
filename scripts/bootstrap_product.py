# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a neutral Dual Hat product repository.")
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    required = {"product", "dual_hat", "engineering", "workspace"}
    if profile.get("schema") != "dual-hat-product-profile/1.0" or set(profile.get("roots", {})) != required:
        raise SystemExit("profile does not satisfy the Dual Hat product-profile contract")
    target = args.target.resolve()
    actions = [target / profile["roots"][name] for name in sorted(required)]
    profile_path = target / profile["roots"]["engineering"] / "product-profile.json"
    payload = json.dumps(profile, indent=2, sort_keys=True) + "\n"
    if profile_path.exists() and profile_path.read_text(encoding="utf-8") != payload:
        raise SystemExit(f"refusing to overwrite conflicting file: {profile_path}")
    if args.dry_run:
        print(json.dumps({"directories": [str(path) for path in actions], "profile": str(profile_path)}, indent=2))
        return 0
    for path in actions:
        path.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(payload, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "applied", "profile": str(profile_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
