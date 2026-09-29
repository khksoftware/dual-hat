# SPDX-License-Identifier: Apache-2.0
"""Shared, scoped import-context helpers for loading a module out of a tree
it is not part of.

That shape recurs in two forms wherever a script or tool needs to reach code
that sits outside its own normal package context. The first is a by-path
load: ``importlib.util.spec_from_file_location`` + ``exec_module`` executes a
module outside any package context, so the loaded file's own directory is
never on ``sys.path`` -- a bare ``from sibling import x`` inside it raises
``ModuleNotFoundError`` even though ``sibling.py`` sits right next to it, and
the error names the sibling rather than the file that failed to load it. The
second is an ordinary ``from sibling import x`` against a directory that is
not normally on ``sys.path`` at all, where the directory must be present
only for the statements that need it.

Both shapes share one correct fix: insert the needed directory on
``sys.path`` only for as long as the sensitive operation runs, remove it
again in ``finally``, and remove it only if this call is the one that
inserted it -- so a directory another loader already put on ``sys.path``,
concurrently or earlier in the same process, is left alone rather than
pulled out from under it. The alternative -- a permanent, unscoped
``sys.path.insert`` that never comes back off -- pollutes every subsequent
import in the process for the rest of its life, silently changes which
module a later bare import resolves to if a same-named module exists
elsewhere on the path, and leaves no trace of who put the entry there or
why. ``sibling_directory_on_path`` is the scoped primitive.
``_load_module_by_path_with_sibling_context`` is the by-path-load form built
on top of it.
"""

from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator


@contextmanager
def sibling_directory_on_path(directory: Path | str) -> Iterator[None]:
    """Put ``directory`` on ``sys.path`` for the duration of the ``with`` block only.

    Inserted at position 0 only if not already present; removed again in
    ``finally``, and only if this call is what inserted it, so a directory
    another loader already put on ``sys.path`` is left alone rather than
    pulled out from under it.
    """
    directory = str(directory)
    inserted = directory not in sys.path
    if inserted:
        sys.path.insert(0, directory)
    try:
        yield
    finally:
        if inserted:
            sys.path.remove(directory)


def _load_module_by_path_with_sibling_context(
    module_name: str,
    path: Path,
    *,
    register_in_sys_modules: bool = False,
) -> ModuleType:
    """Load a module by file location, giving it its own directory on
    ``sys.path`` for the duration of the load.

    ``spec_from_file_location`` + ``exec_module`` executes a module outside
    any package context: the loaded file's own directory is never added to
    ``sys.path``, so a bare ``from sibling import x`` inside it raises
    ``ModuleNotFoundError`` even though ``sibling.py`` sits right next to
    it -- the error names the sibling, not the file that failed to load it.
    The directory is inserted only long enough to execute the module, and
    removed again in ``finally`` so the caller's ``sys.path`` is never left
    mutated; it is inserted at all only if it was not already present, and
    only that insertion is undone, so a directory another loader put on
    ``sys.path`` first is left alone rather than pulled out from under it.

    ``register_in_sys_modules`` puts the module in ``sys.modules`` under
    ``module_name`` before ``exec_module`` runs, matching what a normal
    package import does -- needed by a caller whose loaded module defines
    something (for example a dataclass) that later resolves its own
    ``__module__`` back through ``sys.modules``. Off by default, matching
    the primitive's original proven call sites, which never needed it.
    """
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module by path: {path}")
    module = importlib.util.module_from_spec(spec)
    if register_in_sys_modules:
        sys.modules[spec.name] = module
    with sibling_directory_on_path(path.parent):
        spec.loader.exec_module(module)
    return module
