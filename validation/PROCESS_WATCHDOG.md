<!-- SPDX-License-Identifier: Apache-2.0 -->

# Process and I/O Watchdog

For sustained scans, validation, migrations, exports, ingestion, retrieval, or multi-agent work, inspect attributable processes about every five minutes and immediately on disk churn, slowdown, erratic tests, unexpected process growth, interruption, or a task that appears to outlive its owner.

Inspect PID, parent/children, command line, start time, duration, CPU, memory, disk read/write rate, active repository/path, task owner, duplicate work, and continued purpose. Bound recursive roots; exclude archives, generated output, caches, ignored workspace, and irrelevant trees by default; use explicit audit profiles for exceptions. Prefer Git indexes/manifests to broad walks and prohibit duplicate concurrent search processes.

Terminate only clearly owned orphaned, duplicated, runaway, stale, or detached work after verifying it is not writing repository state, a database, package, export, snapshot, migration, or critical result. Prefer graceful termination. Never terminate ambiguous user or editor processes; ask when attribution is uncertain.

Child launchers use guaranteed cleanup. Delegated workers report and clean children. Closure verifies no orphaned scanner, test, retrieval, or export process remains. Significant interventions record identity, ownership, observed use, reason, action, and result.
