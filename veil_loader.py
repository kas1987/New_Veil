"""Veil Town safe module loader.

Replaces the deprecated SourceFileLoader.load_module() pattern used
throughout the project. The old pattern has a critical bug: calling
``SourceFileLoader(name, path).load_module()`` on an already-loaded name
re-executes the module code, replacing class objects in the module
namespace. Any existing references (e.g. ``Message`` in a test) still
point to the old class, so ``isinstance()`` checks fail.

This loader uses the modern importlib API (spec_from_file_location +
module_from_spec + exec_module) and guards against double-loading by
checking ``sys.modules`` first.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_module(name: str, path: str | Path) -> object:
    """Load a Python module by file path, caching in sys.modules.

    Parameters
    ----------
    name : str
        The module name to register in ``sys.modules``.
    path : str | Path
        Filesystem path to the ``.py`` file.

    Returns
    -------
    module
        The loaded (or cached) module object.
    """
    path = Path(path).resolve()

    # Return cached module if already loaded with the same resolved path.
    if name in sys.modules:
        existing = sys.modules[name]
        if getattr(existing, "__file__", None) == str(path):
            return existing

    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create import spec for {name} from {path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # register BEFORE exec to handle circular refs
    spec.loader.exec_module(mod)
    return mod
