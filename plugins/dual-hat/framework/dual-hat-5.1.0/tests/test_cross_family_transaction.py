"""cross_family_transaction contract tests.

SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

DUAL_HAT_CAPABILITY_PROOFS = {"transactional_writes"}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tooling"))
import cross_family_transaction as cfx  # noqa: E402


_KILL_HELPER = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import cross_family_transaction as cfx

root = Path(sys.argv[2])
marker = Path(sys.argv[3])

writes = {"manifest.json": '{"ok": true}\n'}
binary_writes = {"archive.zip": b"\xff\xfe\x00\x01NOT-UTF8\x00\xfe\xff"}
planned = cfx.plan(root, writes, binary_writes=binary_writes)
cfx.stage(root, planned, writes, binary_writes=binary_writes)
cfx.commit(root, planned.txn_id)

marker.write_text("committed-not-yet-applied", encoding="utf-8")
import time
time.sleep(30)
"""


class CrossFamilyTransactionTests(unittest.TestCase):
    def test_a_text_and_a_binary_entry_both_reach_their_post_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            writes = {"manifest.json": '{"ok": true}\n'}
            binary_writes = {"archive.zip": b"\xff\xfe\x00\x01NOT-UTF8\x00\xfe\xff"}
            planned = cfx.plan(root, writes, binary_writes=binary_writes)
            cfx.stage(root, planned, writes, binary_writes=binary_writes)
            cfx.commit(root, planned.txn_id)
            result = cfx.apply(root, planned.txn_id)
            self.assertEqual(set(result.applied), {"manifest.json", "archive.zip"})
            self.assertEqual((root / "manifest.json").read_text(encoding="utf-8"), '{"ok": true}\n')
            self.assertEqual((root / "archive.zip").read_bytes(), binary_writes["archive.zip"])
            self.assertEqual(cfx.scan(root), ())
            # The journal directory is cleaned up once empty -- a caller with strict
            # membership expectations over `root`'s own top level must never see it.
            self.assertFalse((root / cfx.JOURNAL_DIR).exists())

    def test_plan_refuses_a_target_named_in_both_writes_and_binary_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(cfx.CrossFamilyTransactionError):
                cfx.plan(root, {"a": "text"}, binary_writes={"a": b"bytes"})

    def test_apply_of_an_already_applied_transaction_is_a_pure_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary_writes = {"archive.zip": b"CONTENT"}
            planned = cfx.plan(root, {}, binary_writes=binary_writes)
            cfx.stage(root, planned, {}, binary_writes=binary_writes)
            cfx.commit(root, planned.txn_id)
            cfx.apply(root, planned.txn_id)
            # Re-plan/stage/commit the identical transaction and apply again: every
            # entry already matches its post-image, so this is a pure skip.
            planned2 = cfx.plan(root, {}, binary_writes=binary_writes)
            self.assertEqual(planned.txn_id, planned2.txn_id)
            cfx.stage(root, planned2, {}, binary_writes=binary_writes)
            cfx.commit(root, planned2.txn_id)
            result = cfx.apply(root, planned2.txn_id)
            self.assertEqual(result.applied, ())
            self.assertEqual(result.skipped, ("archive.zip",))

    def test_a_third_party_write_between_plan_and_apply_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "archive.zip").write_bytes(b"OLD")
            planned = cfx.plan(root, {}, binary_writes={"archive.zip": b"NEW"})
            cfx.stage(root, planned, {}, binary_writes={"archive.zip": b"NEW"})
            cfx.commit(root, planned.txn_id)
            (root / "archive.zip").write_bytes(b"TAMPERED-BY-SOMETHING-ELSE")
            with self.assertRaises(cfx.CrossFamilyTransactionError):
                cfx.apply(root, planned.txn_id)
            self.assertEqual((root / "archive.zip").read_bytes(), b"TAMPERED-BY-SOMETHING-ELSE")

    def test_recover_pending_finishes_a_committed_but_unapplied_transaction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            writes = {"manifest.json": '{"ok": true}\n'}
            planned = cfx.plan(root, writes)
            cfx.stage(root, planned, writes)
            cfx.commit(root, planned.txn_id)
            # Nothing real has changed yet -- commit() only renamed the private
            # journal file, never touched `manifest.json` itself.
            self.assertFalse((root / "manifest.json").exists())
            self.assertEqual(len(cfx.scan(root)), 1)
            completed = cfx.recover_pending(root)
            self.assertEqual(completed, (planned.txn_id,))
            self.assertEqual((root / "manifest.json").read_text(encoding="utf-8"), '{"ok": true}\n')
            self.assertEqual(cfx.scan(root), ())
            self.assertFalse((root / cfx.JOURNAL_DIR).exists())

    def test_a_real_process_kill_between_commit_and_apply_is_recovered_forward(self):
        """A REAL subprocess is launched, allowed to reach "committed, nothing applied
        yet", and REALLY killed -- proving this holds for an actual process death, not
        only for an in-process exception a `try`/`except` could paper over."""
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as helper_dir:
            root = Path(temporary)
            helper = Path(helper_dir) / "_kill_helper.py"
            helper.write_text(_KILL_HELPER, encoding="utf-8")
            marker = Path(helper_dir) / "reached_marker.txt"

            process = subprocess.Popen(
                [sys.executable, str(helper), str(ROOT / "tooling"), str(root), str(marker)],
                cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            deadline = time.time() + 15
            while not marker.is_file() and time.time() < deadline and process.poll() is None:
                time.sleep(0.05)
            self.assertTrue(marker.is_file(), "the helper process never reached its marker")

            process.kill()
            process.wait(timeout=10)

            self.assertFalse((root / "manifest.json").exists())
            self.assertFalse((root / "archive.zip").exists())
            self.assertEqual(len(cfx.scan(root)), 1)

            completed = cfx.recover_pending(root)
            self.assertEqual(len(completed), 1)
            self.assertEqual((root / "manifest.json").read_text(encoding="utf-8"), '{"ok": true}\n')
            self.assertEqual((root / "archive.zip").read_bytes(), b"\xff\xfe\x00\x01NOT-UTF8\x00\xfe\xff")
            self.assertEqual(cfx.scan(root), ())
            self.assertFalse((root / cfx.JOURNAL_DIR).exists())


if __name__ == "__main__":
    unittest.main()
