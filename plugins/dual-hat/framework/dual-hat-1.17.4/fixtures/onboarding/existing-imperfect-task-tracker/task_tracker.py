# SPDX-License-Identifier: Apache-2.0
"""Synthetic imperfect task tracker; onboarding must inspect metadata, not execute it."""
import json
from pathlib import Path

STORE = Path("tasks.local.json")


def add(title: str) -> None:
    tasks = json.loads(STORE.read_text()) if STORE.exists() else []
    tasks.append({"title": title, "done": False})
    STORE.write_text(json.dumps(tasks))


def all_tasks():
    return json.loads(STORE.read_text()) if STORE.exists() else []
