# SPDX-License-Identifier: Apache-2.0
import unittest
import task_tracker


class TaskTrackerTests(unittest.TestCase):
    def test_empty_store(self):
        self.assertIsInstance(task_tracker.all_tasks(), list)
