"""
Worker server - runs inside the target venv.
by Tanishq Jain

Protocol (file-based IPC, no command-line length limits):
  argv[1]  path to payload file  (host writes, we read)
  argv[2]  path to result file   (we write, host reads)

Both files are raw pickle bytes; no base64, no encoding.

This script is intentionally self-contained: it imports nothing from the
compat package because the target venv will not have compat installed.
All helpers are inlined below.
"""

import importlib.util
import pickle
import sys
import traceback
from pathlib import Path


def _read_payload(path: str) -> dict:
    return pickle.loads(Path(path).read_bytes())


def _write_result(path: str, value) -> None:
    try:
        envelope = {"ok": True, "value": value}
        Path(path).write_bytes(
            pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL)
        )
    except Exception as exc:
        _write_error(path, TypeError(f"Return value is not serializable: {exc}"))


def _write_error(path: str, exc: Exception) -> None:
    envelope = {
        "ok": False,
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
        "traceback": traceback.format_exc(),
    }
    Path(path).write_bytes(pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL))


def _install_compat_shim():
    import types

    def _noop_runtime(requirements=None):
        def decorator(func):
            func._compat_original = func
            return func

        return decorator

    runtime_mod = types.ModuleType("compat.runtime")
    runtime_mod.runtime = _noop_runtime

    compat_mod = types.ModuleType("compat")
    compat_mod.runtime = _noop_runtime
    compat_mod.__version__ = "worker-shim"

    sys.modules["compat"] = compat_mod
    sys.modules["compat.runtime"] = runtime_mod


def main():
    if len(sys.argv) < 3:
        sys.stderr.write(
            "_worker_server.py: usage: _worker_server.py <payload_path> "
            "<result_path>\n"
        )
        sys.exit(1)

    payload_path = sys.argv[1]
    result_path = sys.argv[2]

    try:
        payload = _read_payload(payload_path)
    except Exception as exc:
        _write_error(result_path, RuntimeError(f"Failed to read payload: {exc}"))
        sys.exit(1)

    func_name: str = payload["func_name"]
    module_name: str = payload["module"]
    source_file: str = payload["source_file"]
    args: tuple = payload["args"]
    kwargs: dict = payload["kwargs"]

    try:
        _install_compat_shim()

        src_dir = str(Path(source_file).parent.resolve())
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

        load_name = Path(source_file).stem if module_name == "__main__" else module_name

        spec = importlib.util.spec_from_file_location(load_name, source_file)
        if spec is None:
            raise ImportError(
                f"Cannot build module spec for '{load_name}' from '{source_file}'"
            )

        mod = importlib.util.module_from_spec(spec)
        sys.modules[load_name] = mod
        spec.loader.exec_module(mod)

        func = getattr(mod, func_name, None)
        if func is None:
            raise AttributeError(
                f"Function '{func_name}' not found in '{source_file}'. "
                "It must be defined at module level."
            )

        if hasattr(func, "_compat_original"):
            func = func._compat_original

        result = func(*args, **kwargs)
        _write_result(result_path, result)

    except SystemExit as exc:
        _write_error(
            result_path,
            RuntimeError(f"Worker function called sys.exit({exc.code})"),
        )
        sys.exit(1)

    except Exception as exc:
        _write_error(result_path, exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
