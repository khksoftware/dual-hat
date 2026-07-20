"""Validate and reconcile canonical Dual Hat planning state.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


BACKLOG_STATUSES = {
    "candidate", "ready", "authorized", "in_progress", "blocked", "completed",
    "deferred", "cancelled", "superseded",
}
FUTURE_STATUSES = {"monitored", "triggered", "promoted", "retired", "superseded"}
BACKLOG_TRANSITIONS = {
    "candidate": {"ready", "deferred", "cancelled", "superseded"},
    "ready": {"authorized", "deferred", "cancelled", "superseded"},
    "authorized": {"in_progress", "cancelled", "superseded"},
    "in_progress": {"blocked", "completed", "cancelled", "superseded"},
    "blocked": {"in_progress", "deferred", "cancelled", "superseded"},
    "deferred": {"candidate", "cancelled", "superseded"},
    "completed": set(), "cancelled": set(), "superseded": set(),
}
FUTURE_TRANSITIONS = {
    "monitored": {"triggered", "retired", "superseded"},
    "triggered": {"monitored", "promoted", "retired", "superseded"},
    "promoted": {"retired", "superseded"},
    "retired": set(), "superseded": set(),
}
COMMON_FIELDS = {
    "id", "title", "objective", "owner", "dependencies", "status",
    "entry_criteria", "exit_criteria", "requirements", "validation", "risks",
    "superseded_by",
}


def _load_registry(path: Path, schema: str) -> tuple[list[dict[str, Any]], list[str]]:
    failures: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"{path}: cannot read registry: {exc}"]
    if not isinstance(payload, dict) or payload.get("schema") != schema:
        failures.append(f"{path}: expected schema {schema}")
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return [], [*failures, f"{path}: items must be an array"]
    return items, failures


def _load_history(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    failures: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"{path}: cannot read history: {exc}"]
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"{path}:{number}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(event, dict):
            failures.append(f"{path}:{number}: event must be an object")
            continue
        event["_line"] = number
        events.append(event)
    return events, failures


def reconcile_planning(backlog_path: Path, future_path: Path, history_path: Path) -> tuple[str, ...]:
    backlog, failures = _load_registry(backlog_path, "dual-hat-planning-backlog/1.0")
    future, more = _load_registry(future_path, "dual-hat-future-work/1.0")
    failures.extend(more)
    events, more = _load_history(history_path)
    failures.extend(more)

    current: dict[str, tuple[str, dict[str, Any]]] = {}
    for kind, items, statuses in (
        ("backlog", backlog, BACKLOG_STATUSES),
        ("future_work", future, FUTURE_STATUSES),
    ):
        for index, item in enumerate(items):
            label = f"{kind}[{index}]"
            if not isinstance(item, dict):
                failures.append(f"{label}: item must be an object")
                continue
            required = COMMON_FIELDS | ({"trigger"} if kind == "future_work" else set())
            missing = sorted(required - set(item))
            if missing:
                failures.append(f"{label}: missing fields {missing}")
            unknown = sorted(set(item) - required - {"$comment"})
            if unknown:
                failures.append(f"{label}: unknown fields {unknown}")
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                failures.append(f"{label}: id must be a non-empty string")
                continue
            if item_id in current:
                failures.append(f"duplicate planning id across current registries: {item_id}")
            current[item_id] = (kind, item)
            if item.get("status") not in statuses:
                failures.append(f"{item_id}: invalid {kind} status {item.get('status')!r}")
            for field in ("title", "objective", "owner"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    failures.append(f"{item_id}: {field} must be non-empty")
            for field in ("dependencies", "entry_criteria", "exit_criteria", "requirements", "validation", "risks"):
                if not isinstance(item.get(field), list) or any(not isinstance(value, str) or not value.strip() for value in item.get(field, [])):
                    failures.append(f"{item_id}: {field} must be an array of non-empty strings")
            if item.get("status") == "superseded" and not item.get("superseded_by"):
                failures.append(f"{item_id}: superseded item must identify superseded_by")
            if item.get("status") != "superseded" and item.get("superseded_by") is not None:
                failures.append(f"{item_id}: only a superseded item may identify superseded_by")
            if kind == "future_work":
                trigger = item.get("trigger")
                required_trigger = {"event", "selector", "invoker", "review_interval", "last_evaluated_at"}
                if not isinstance(trigger, dict) or required_trigger - set(trigger):
                    failures.append(f"{item_id}: future work requires a complete trigger")
                elif set(trigger) != required_trigger:
                    failures.append(f"{item_id}: future-work trigger has unknown fields")
                elif any(not isinstance(trigger[field], str) or not trigger[field].strip() for field in ("event", "selector", "invoker", "review_interval")):
                    failures.append(f"{item_id}: future-work trigger fields must be non-empty")

    seen_events: set[str] = set()
    prior: dict[str, tuple[str, str, datetime]] = {}
    for event in events:
        line = event.pop("_line")
        prefix = f"{history_path}:{line}"
        required = {"schema", "event_id", "item_id", "item_kind", "occurred_at", "from_status", "to_status", "reason", "actor", "source_authority"}
        missing = sorted(required - set(event))
        if missing:
            failures.append(f"{prefix}: missing fields {missing}")
            continue
        unknown = sorted(set(event) - required)
        if unknown:
            failures.append(f"{prefix}: unknown fields {unknown}")
        if event["schema"] != "dual-hat-planning-history-event/1.0":
            failures.append(f"{prefix}: unexpected history schema")
        event_id = event["event_id"]
        if event_id in seen_events:
            failures.append(f"duplicate history event id: {event_id}")
        seen_events.add(event_id)
        item_id = event["item_id"]
        kind = event["item_kind"]
        if item_id not in current:
            failures.append(f"{prefix}: history item is absent from current registries: {item_id}")
            continue
        if current[item_id][0] != kind:
            failures.append(f"{prefix}: item_kind contradicts current registry for {item_id}")
        statuses = BACKLOG_STATUSES if kind == "backlog" else FUTURE_STATUSES if kind == "future_work" else set()
        if event["to_status"] not in statuses:
            failures.append(f"{prefix}: invalid to_status {event['to_status']!r}")
        try:
            occurred = datetime.fromisoformat(str(event["occurred_at"]).replace("Z", "+00:00"))
        except ValueError:
            failures.append(f"{prefix}: occurred_at must be an ISO-8601 date-time")
            continue
        if item_id not in prior:
            if event["from_status"] is not None:
                failures.append(f"{prefix}: first item event must have null from_status")
            initial_status = "candidate" if kind == "backlog" else "monitored" if kind == "future_work" else None
            if event["to_status"] != initial_status:
                failures.append(f"{prefix}: first {kind} event must enter {initial_status!r}")
        else:
            prior_kind, prior_status, prior_time = prior[item_id]
            if kind != prior_kind or event["from_status"] != prior_status:
                failures.append(f"{prefix}: transition does not continue prior state for {item_id}")
            transitions = BACKLOG_TRANSITIONS if kind == "backlog" else FUTURE_TRANSITIONS if kind == "future_work" else {}
            if event["to_status"] not in transitions.get(prior_status, set()):
                failures.append(f"{prefix}: invalid {kind} transition {prior_status!r} -> {event['to_status']!r}")
            if occurred < prior_time:
                failures.append(f"{prefix}: event time moves backwards for {item_id}")
        prior[item_id] = (kind, event["to_status"], occurred)

    for item_id, (kind, item) in current.items():
        if item_id not in prior:
            failures.append(f"{item_id}: current item has no history")
        elif prior[item_id][1] != item.get("status"):
            failures.append(f"{item_id}: current status does not match latest history event")
    return tuple(sorted(set(failures)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile Dual Hat planning registries and history")
    parser.add_argument("--backlog", required=True, type=Path)
    parser.add_argument("--future-work", required=True, type=Path)
    parser.add_argument("--history", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    failures = reconcile_planning(args.backlog, args.future_work, args.history)
    if args.json:
        print(json.dumps({"passed": not failures, "failures": list(failures)}, indent=2))
    elif failures:
        print("\n".join(f"FAIL: {failure}" for failure in failures))
    else:
        print("Dual Hat planning reconciliation passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
