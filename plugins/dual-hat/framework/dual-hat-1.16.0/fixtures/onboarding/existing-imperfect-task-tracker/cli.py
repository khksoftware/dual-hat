# SPDX-License-Identifier: Apache-2.0
import sys
from task_tracker import add, all_tasks

if sys.argv[1:2] == ["add"]:
    add(" ".join(sys.argv[2:]))
else:
    print(all_tasks())
