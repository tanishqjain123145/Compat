"""
Worker server — runs inside the target venv.
by Tanishq Jain

Protocol (file-based IPC, no command-line length limits):
  argv[1]  path to payload file  (host writes, we read)
  argv[2]  path to result file   (we write, host reads)

Both files are raw pickle bytes — no base64, no encoding.

This script is intentionally self-contained: it imports nothing from the
compat package because the target venv won't have compat installed.
All helpers are inlined below.
"""

import importlib.util
import os
import pickle
import sys
import traceback
from pathlib import Path


# ---------------------------------------------------------------------------
# Inline IPC helpers (mirrors compat/serializer.py, no compat dependency)
# ---------------------------------------------------------------------------

def _read_payload(path: str) -> dict:
    return pickle.loads(Path(path).read_bytes())


def _write_result(path: str, value) -> None:
    try:
        envelope = {"ok": True, "value": value}
        Path(path).write_bytes(pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL))
    except Exception as exc:
        _write_error(path, TypeError(f"Return value is not serializable: {exc}"))


def _write_error(path: str, exc: Exception) -> None:
    envelope = {
        "ok":        False,
        "error_type": type(exc).__name__,
        "error_msg":  str(exc),
        "traceback":  traceback.format_exc(),
    }
    Path(path).write_bytes(pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL))


# ---------------------------------------------------------------------------
# Compat shim
# ---------------------------------------------------------------------------
# When the worker re-imports the user's source file it hits @runtime(...)
# decorators again. We inject a fake compat package that makes @runtime a
# transparent no-op, preventing infinite subprocess recursion.
#
# We handle every valid import style:
#
#   from compat import runtime          → compat_mod.runtime is the function
#   from compat.runtime import runtime  → compat_mod_runtime.runtime is fn
#   import compat; compat.runtime(...)  → compat_mod.runtime is the function

def _install_compat_shim():
    import types

    def _noop_runtime(requirements=None):
        def decorator(func):
            func._compat_original = func
            return func
        return decorator

    # compat.runtime module (for "from compat.runtime import runtime")
    runtime_mod = types.ModuleType("compat.runtime")
    runtime_mod.runtime = _noop_runtime

    # compat package (for "from compat import runtime")
    compat_mod = types.ModuleType("compat")
    compat_mod.runtime      = _noop_runtime   # the FUNCTION, not the module
    compat_mod.__version__  = "worker-shim"

    sys.modules["compat"]         = compat_mod
    sys.modules["compat.runtime"] = runtime_mod


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        sys.stderr.write(
            "worker_server.py: usage: worker_server.py <payload_path> <result_path>\n"
        )
        sys.exit(1)

    payload_path = sys.argv[1]
    result_path  = sys.argv[2]

    # --- Read payload ---
    try:
        payload = _read_payload(payload_path)
    except Exception as exc:
        _write_error(result_path, RuntimeError(f"Failed to read payload: {exc}"))
        sys.exit(1)

    func_name:   str  = payload["func_name"]
    module_name: str  = payload["module"]
    source_file: str  = payload["source_file"]
    args:        tuple = payload["args"]
    kwargs:      dict  = payload["kwargs"]

    # --- Load user module + call function ---
    try:
        _install_compat_shim()

        # Ensure the source file's directory is on sys.path so that
        # relative imports inside the module resolve correctly.
        # We insert at position 0 to mirror normal script execution.
        src_dir = str(Path(source_file).parent.resolve())
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        # When the module was run as __main__, we can't import it by name.
        # Use the file stem instead — the behaviour is identical.
        load_name = (
            Path(source_file).stem
            if module_name == "__main__"
            else module_name
        )

        spec = importlib.util.spec_from_file_location(load_name, source_file)
        if spec is None:
            raise ImportError(
                f"Cannot build module spec for '{load_name}' "
                f"from '{source_file}'"
            )

        mod = importlib.util.module_from_spec(spec)
        sys.modules[load_name] = mod

        # Execute the module (runs top-level code, defines functions, etc.)
        # The compat shim is already installed so @runtime is a no-op here.
        spec.loader.exec_module(mod)

        func = getattr(mod, func_name, None)
        if func is None:
            raise AttributeError(
                f"Function '{func_name}' not found in '{source_file}'. "
                "It must be defined at module level."
            )

        # Unwrap the @runtime decorator if the shim left _compat_original
        if hasattr(func, "_compat_original"):
            func = func._compat_original

        result = func(*args, **kwargs)
        _write_result(result_path, result)

    except SystemExit as exc:
        _write_error(result_path, RuntimeError(
            f"Worker function called sys.exit({exc.code})"
        ))
        sys.exit(1)

    except Exception as exc:
        _write_error(result_path, exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
