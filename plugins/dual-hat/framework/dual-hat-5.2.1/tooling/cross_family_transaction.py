"""A redo journal with a single-rename commit point, for a set of files that must all
reach their new content together or not at all.

SPDX-License-Identifier: Apache-2.0

**Why this exists.** A caller that writes several related files one at a time --
replacing each with `os.replace` in turn -- can be interrupted between replacements.
Anything that looks afterward then sees some targets already at their new content and
others still at the old, with no way to tell whether that mix is the intended state or
a crash caught mid-flight. This module removes that observable state: every writer
using it leaves every target at its OLD content, or at its NEW content, or -- for the
one instant in between -- leaves a durable, self-describing record that lets the next
caller finish the job forward, deterministically, with no guesswork.

Four phases, three of which this module owns. Deciding WHAT the post-image should be
is entirely the caller's job; this module never inspects content for validity.

  `plan()`             -- PURE. Reads the current bytes of every target (the pre-image
                           digest) and hashes the caller-supplied post-image. Nothing
                           is written.
  `stage()`            -- Serialises every post-image into a private staging
                           directory, each blob through fsync-then-rename. Writes
                           `<txn_id>.prepared.json`. No target outside the private
                           journal directory is touched.
  `commit()`           -- THE commit point, and it is the whole of it: one
                           `os.replace` of `<txn_id>.prepared.json` onto
                           `<txn_id>.committed.json`. Before this call, undoing is a
                           no-op -- nothing real was written. After it, there is no
                           undo, only mandatory, idempotent redo.
  `apply()`            -- Idempotent, resumable redo. Per target, a three-way digest
                           check against its CURRENT bytes: already matches the
                           post-image -> skip; matches the pre-image -> replace;
                           matches neither -> refuse loudly, naming the path and both
                           digests, rather than clobbering content a third party wrote
                           after `plan()` ran. Deletes the journal, its staging, and
                           (once empty) the journal directory itself, once every
                           target matches its post-image.
  `recover_pending()`  -- `scan()` plus `apply()` to completion for every committed
                           journal present, plus discarding any staged-but-never-
                           committed leftover. Call this UNCONDITIONALLY before
                           anything else touches the same root: it is what converts
                           "recovery exists" into "recovery has already happened by
                           the time anything else runs".

The achievable property is about observable states, not about instantaneity: every
state reachable through the sanctioned route is the pre-state, the post-state, or a
state that `recover_pending()` converts to the post-state before any other writer or
reader proceeds.

**Bound the claim, do not overclaim it.** A single `os.replace` is atomic with respect
to the CALLING PROCESS dying -- the rename either happened or it did not, and the next
`recover_pending()` finishes or discards it deterministically. It is a redo mechanism
for process death (a kill, an uncaught exception, a lost connection), never a power-
loss or filesystem-crash guarantee: forcing a directory entry durable with a directory
fsync is refused on at least one supported platform, so no caller of this module may
claim survival of anything below the operating system's own crash-consistency
guarantees.

`binary_writes` is the byte-content counterpart of `writes`, for a target whose content
is not valid UTF-8 (a ZIP archive, for instance) -- `writes` reads and writes text and
cannot express one. A target may appear in at most one of the two; `plan()` refuses
rather than picking one silently.

This module intentionally does not support deleting a target or moving a directory: no
caller in this package needs either, and carrying unused generality is its own
maintenance cost. A future caller that needs one should add it here, once, rather than
inventing a second, divergent journal.

The journal directory (`JOURNAL_DIR`, nested under the caller-supplied root) is removed
once empty, by both `apply()` and `recover_pending()` -- a caller whose root has strict
membership expectations over its own top level (an exact set of expected file names,
checked before and after a write) never needs to special-case its presence.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

#: Nested under the caller-supplied root. Never a path anything else in this package
#: reads or writes, and never left behind once a transaction has fully applied.
JOURNAL_DIR = ".release-transaction"

SCHEMA = "dual-hat-cross-family-transaction/1"

#: `PermissionError` `winerror == 5` -- another process holding a target open, even
#: only for read -- is retried rather than refused; this bounds how long `apply()`
#: waits for a transient holder to release the target before surfacing the error.
_WINERROR_5_MAX_ATTEMPTS = 6
_WINERROR_5_BACKOFF_SECONDS = 0.05


class CrossFamilyTransactionError(RuntimeError):
    """A transaction cannot be planned, staged, committed, or applied as asked.

    Every message this carries names the exact path and the exact digests involved --
    never raised to paper over a conflict.
    """


@dataclass(frozen=True)
class PlannedEntry:
    target: str
    pre_present: bool
    pre_digest: str | None
    post_digest: str
    #: Whether this target's content is read/written as raw bytes (`binary_writes`)
    #: rather than UTF-8 text (`writes`).
    binary: bool = False


@dataclass(frozen=True)
class TransactionPlan:
    txn_id: str
    entries: tuple[PlannedEntry, ...]


@dataclass(frozen=True)
class ApplyResult:
    txn_id: str
    applied: tuple[str, ...]
    skipped: tuple[str, ...]
    completed: bool


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _normalise_target(target: str) -> str:
    return str(target).replace("\\", "/")


def transaction_id(targets: Iterable[str]) -> str:
    """Deterministic over the TARGET SET, not a fresh id per call, so a second `plan()`
    against the same targets recognises an already in-flight transaction rather than
    minting a second, colliding journal."""
    normalised = sorted(_normalise_target(target) for target in targets)
    payload = "\n".join(normalised)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _journal_directory(root: Path) -> Path:
    return root / JOURNAL_DIR


def _prepared_path(root: Path, txn_id: str) -> Path:
    return _journal_directory(root) / f"{txn_id}.prepared.json"


def _committed_path(root: Path, txn_id: str) -> Path:
    return _journal_directory(root) / f"{txn_id}.committed.json"


def _staging_dir(root: Path, txn_id: str) -> Path:
    return _journal_directory(root) / f"{txn_id}.staging"


def _replace_with_retry(source: Path, target: Path) -> None:
    """`os.replace`, retrying only `PermissionError` `winerror == 5` -- a transient
    refusal when another process holds the target open, unrelated to either file's
    content."""
    attempt = 0
    while True:
        try:
            os.replace(source, target)
            return
        except PermissionError as error:
            attempt += 1
            if getattr(error, "winerror", None) != 5 or attempt >= _WINERROR_5_MAX_ATTEMPTS:
                raise
            time.sleep(_WINERROR_5_BACKOFF_SECONDS * attempt)


def _fsync_then_replace_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".cfxtmp", dir=str(path.parent),
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        _replace_with_retry(Path(temporary), path)
        with path.open("r+b") as committed:
            os.fsync(committed.fileno())
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _fsync_then_replace_bytes(path: Path, data: bytes) -> None:
    """Byte-identical twin of `_fsync_then_replace_text`, for `binary_writes` content
    that is not valid UTF-8 and cannot go through the text path at all."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".cfxtmp", dir=str(path.parent),
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _replace_with_retry(Path(temporary), path)
        with path.open("r+b") as committed:
            os.fsync(committed.fileno())
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _cleanup_if_empty(directory: Path) -> None:
    """Best-effort: remove `directory` if (and only if) it is now empty. Never raises
    -- a non-empty directory (another transaction still in flight) or a directory that
    never existed are both fine outcomes, not errors."""
    try:
        directory.rmdir()
    except OSError:
        pass


def plan(
    root: str | Path, writes: Mapping[str, str], *,
    binary_writes: Mapping[str, bytes] = {},
) -> TransactionPlan:
    """PURE. Nothing is written. `writes` maps repository-relative target -> full
    post-image TEXT; `binary_writes` is the same idea for content that is not valid
    UTF-8. A target may appear in at most one of the two; `plan()` refuses rather than
    picking one silently. Reads the CURRENT bytes of every target for its pre-image
    digest; a target absent at plan time carries `pre_present=False, pre_digest=None`.
    """
    overlap = set(writes) & set(binary_writes)
    if overlap:
        raise CrossFamilyTransactionError(
            f"target(s) named in both writes and binary_writes: {sorted(overlap)} -- "
            f"a target's post-state is written text or written bytes, never both"
        )
    root = Path(root)
    entries: list[PlannedEntry] = []
    for target in sorted(set(writes) | set(binary_writes)):
        normalised = _normalise_target(target)
        path = root / normalised
        pre_present = path.is_file()
        binary = target in binary_writes
        post_digest = _sha256_bytes(binary_writes[target]) if binary else _sha256_text(writes[target])
        if not pre_present:
            pre_digest = None
        elif binary:
            pre_digest = _sha256_bytes(path.read_bytes())
        else:
            pre_digest = _sha256_text(path.read_text(encoding="utf-8"))
        entries.append(PlannedEntry(
            target=normalised, pre_present=pre_present, pre_digest=pre_digest,
            post_digest=post_digest, binary=binary,
        ))
    txn_id = transaction_id(entry.target for entry in entries)
    return TransactionPlan(txn_id=txn_id, entries=tuple(entries))


def stage(
    root: str | Path, txn_plan: TransactionPlan, writes: Mapping[str, str], *,
    binary_writes: Mapping[str, bytes] = {},
) -> Path:
    """Serialise every post-image into a private staging directory. No target outside
    the journal directory is touched. Returns the path to the written
    `.prepared.json`. Idempotent: re-staging the same plan overwrites the same staging
    blobs and the same prepared journal with byte-identical content."""
    root = Path(root)
    staging = _staging_dir(root, txn_plan.txn_id)
    staging.mkdir(parents=True, exist_ok=True)
    normalised_writes = {_normalise_target(target): text for target, text in writes.items()}
    normalised_binary_writes = {_normalise_target(target): data for target, data in binary_writes.items()}
    entry_documents = []
    for index, entry in enumerate(txn_plan.entries):
        staged_name = f"{index}.blob"
        if entry.binary:
            _fsync_then_replace_bytes(staging / staged_name, normalised_binary_writes[entry.target])
        else:
            _fsync_then_replace_text(staging / staged_name, normalised_writes[entry.target])
        entry_documents.append({
            "target": entry.target, "pre_present": entry.pre_present,
            "pre_digest": entry.pre_digest, "post_digest": entry.post_digest,
            "staged": staged_name, "binary": entry.binary,
        })
    document = {
        "schema": SCHEMA, "txn_id": txn_plan.txn_id, "created_utc": _utc_now_iso(),
        "entries": entry_documents,
    }
    prepared_path = _prepared_path(root, txn_plan.txn_id)
    _fsync_then_replace_text(prepared_path, json.dumps(document, sort_keys=True, indent=2) + "\n")
    return prepared_path


def commit(root: str | Path, txn_id: str) -> Path:
    """THE commit point: one `os.replace` of the prepared journal onto the committed
    one. Requires a completed `stage()` first. Idempotent: committing an already-
    committed transaction is a no-op (returns the existing committed path unchanged)."""
    root = Path(root)
    committed_path = _committed_path(root, txn_id)
    if committed_path.is_file():
        return committed_path
    prepared_path = _prepared_path(root, txn_id)
    if not prepared_path.is_file():
        raise CrossFamilyTransactionError(
            f"transaction {txn_id} has no prepared journal; commit() requires a "
            f"completed stage() first -- nothing has been committed"
        )
    _replace_with_retry(prepared_path, committed_path)
    return committed_path


def _apply_entry(root: Path, txn_id: str, entry: Mapping[str, object]) -> str:
    target = root / str(entry["target"])
    binary = bool(entry.get("binary", False))
    if target.is_file():
        current_digest = _sha256_bytes(target.read_bytes()) if binary else _sha256_text(target.read_text(encoding="utf-8"))
    else:
        current_digest = None
    if current_digest == entry["post_digest"]:
        return "skipped"
    if current_digest == entry["pre_digest"]:
        staged = _staging_dir(root, txn_id) / str(entry["staged"])
        if not staged.is_file():
            raise CrossFamilyTransactionError(
                f"transaction {txn_id}: staged blob for {entry['target']} is missing "
                f"({staged}) -- the journal is committed but its own staging was lost, "
                f"which this module cannot redo from. This state needs a human."
            )
        if binary:
            _fsync_then_replace_bytes(target, staged.read_bytes())
        else:
            _fsync_then_replace_text(target, staged.read_text(encoding="utf-8"))
        return "applied"
    raise CrossFamilyTransactionError(
        f"refuse to apply {entry['target']}: current content matches neither the "
        f"pre-image digest ({entry['pre_digest']}) recorded when transaction {txn_id} "
        f"was planned, nor the post-image digest ({entry['post_digest']}) it committed "
        f"to write. A third party wrote this file between plan and apply. Nothing was "
        f"overwritten. Current digest: {current_digest}."
    )


def _delete_journal(root: Path, txn_id: str) -> None:
    _committed_path(root, txn_id).unlink(missing_ok=True)
    _prepared_path(root, txn_id).unlink(missing_ok=True)
    staging = _staging_dir(root, txn_id)
    if staging.is_dir():
        shutil.rmtree(staging, ignore_errors=True)


def apply(root: str | Path, txn_id: str) -> ApplyResult:
    """Idempotent, resumable redo. Requires a COMMITTED journal -- before the commit
    point undo is a no-op and there is nothing here to redo. Raises
    `CrossFamilyTransactionError` and leaves the journal in place on ANY entry this
    cannot safely resolve (a third-party write, a missing staged blob), so a caller
    retrying later sees the same committed journal rather than a partially-cleaned
    one."""
    root = Path(root)
    committed_path = _committed_path(root, txn_id)
    if not committed_path.is_file():
        raise CrossFamilyTransactionError(
            f"transaction {txn_id} has no committed journal; apply() only redoes a "
            f"transaction that has passed its commit point"
        )
    document = json.loads(committed_path.read_text(encoding="utf-8"))
    applied: list[str] = []
    skipped: list[str] = []
    for entry in document["entries"]:
        outcome = _apply_entry(root, txn_id, entry)
        (applied if outcome == "applied" else skipped).append(str(entry["target"]))
    _delete_journal(root, txn_id)
    _cleanup_if_empty(_journal_directory(root))
    return ApplyResult(txn_id=txn_id, applied=tuple(applied), skipped=tuple(skipped), completed=True)


def scan(root: str | Path) -> tuple[str, ...]:
    """Read-only. The ids of every COMMITTED journal present -- durable, external
    proof that a write set was left unproven. A directory listing only."""
    directory = _journal_directory(Path(root))
    if not directory.is_dir():
        return ()
    suffix = ".committed.json"
    return tuple(sorted(path.name[: -len(suffix)] for path in directory.glob(f"*{suffix}")))


def orphaned_prepared(root: str | Path) -> tuple[str, ...]:
    """Prepared journals with no committed sibling: S-phase leftovers. Before the
    commit point undo is a no-op, so the correct disposition is discard, never redo."""
    root = Path(root)
    directory = _journal_directory(root)
    if not directory.is_dir():
        return ()
    committed = set(scan(root))
    suffix = ".prepared.json"
    ids = (path.name[: -len(suffix)] for path in directory.glob(f"*{suffix}"))
    return tuple(sorted(pid for pid in ids if pid not in committed))


def discard_prepared(root: str | Path, txn_id: str) -> None:
    """Discard an S-phase leftover. Safe unconditionally: nothing has been written to
    a real target by a transaction that never reached its commit point."""
    root = Path(root)
    _prepared_path(root, txn_id).unlink(missing_ok=True)
    staging = _staging_dir(root, txn_id)
    if staging.is_dir():
        shutil.rmtree(staging, ignore_errors=True)


def recover_pending(root: str | Path) -> tuple[str, ...]:
    """**The unskippable step.** Discards every orphaned prepared-only journal, then
    applies every committed journal to completion. Cheap: a directory listing plus, in
    the overwhelming majority of calls, nothing else. Call this UNCONDITIONALLY before
    doing anything else against the same root -- the placement that makes a half-
    applied state UNREACHABLE rather than merely detected. Returns the ids of every
    transaction this call completed (empty, ordinarily)."""
    root = Path(root)
    for txn_id in orphaned_prepared(root):
        discard_prepared(root, txn_id)
    completed: list[str] = []
    for txn_id in scan(root):
        apply(root, txn_id)
        completed.append(txn_id)
    _cleanup_if_empty(_journal_directory(root))
    return tuple(completed)
