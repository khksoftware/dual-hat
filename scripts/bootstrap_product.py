# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import argparse
import json
from pathlib import Path


FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]


def _text(name: str) -> str:
    return (FRAMEWORK_ROOT / "templates" / name).read_text(encoding="utf-8")


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
    roots = {name: target / profile["roots"][name] for name in required}
    profile_path = roots["engineering"] / "product-profile.json"
    payload = json.dumps(profile, indent=2, sort_keys=True) + "\n"
    files = {
        profile_path: payload,
        roots["product"] / "architecture/README.md": "# Product Architecture\n\nCurrent decisions, requirements, models, schemas, specifications, and workflows are indexed here.\n",
        roots["product"] / "governance/README.md": "# Product Governance\n\nProduct behavior, authority, rights, and conformance extensions are indexed here.\n",
        roots["product"] / "src/README.md": "# Product Source\n\nProduction code belongs here and cannot depend on engineering, framework administration, archives, or workspace.\n",
        roots["product"] / "tests/README.md": "# Product Tests\n\nAutomated product tests and their ownership are indexed here.\n",
        roots["engineering"] / "START_HERE.md": "# Start Here\n\nRead the active session, roadmap, current handover, bounded work order, and owning domain before mutation.\n",
        roots["engineering"] / "planning/ROADMAP.md": _text("ROADMAP.md"),
        roots["engineering"] / "planning/PLANNING_BACKLOG.json": _text("PLANNING_BACKLOG.json"),
        roots["engineering"] / "planning/FUTURE_WORK_REGISTRY.json": _text("FUTURE_WORK_REGISTRY.json"),
        roots["engineering"] / "planning/PLANNING_HISTORY.jsonl": "",
        roots["engineering"] / "sessions/ACTIVE_SESSION.md": _text("ACTIVE_SESSION.md"),
        roots["engineering"] / "handoffs/CURRENT_HANDOVER.md": _text("CURRENT_HANDOVER.md"),
        roots["engineering"] / "handoffs/CURRENT_HANDOVER.json": _text("CURRENT_HANDOVER.json"),
        roots["engineering"] / "repository/CANONICAL_ENTRYPOINTS.md": _text("CANONICAL_ENTRYPOINTS.md"),
        roots["engineering"] / "repository/CANONICAL_DOMAIN_INDEX.md": _text("CANONICAL_DOMAIN_INDEX.md"),
        target / ".gitignore": "/workspace/\n__pycache__/\n*.py[cod]\n",
    }
    conflicts = [str(path) for path, content in files.items() if path.exists() and path.read_text(encoding="utf-8") != content]
    if conflicts:
        raise SystemExit("refusing to overwrite conflicting files: " + ", ".join(conflicts))
    if args.dry_run:
        print(json.dumps({"files": [str(path) for path in sorted(files)], "workspace": str(roots["workspace"])}, indent=2))
        return 0
    roots["workspace"].mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "applied", "profile": str(profile_path), "files": len(files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
