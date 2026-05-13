"""
platform.py - All platform-specific logic lives here, nowhere else.
by Tanishq Jain

Every other module imports from here instead of branching on sys.platform.
This makes the cross-platform surface explicit and testable.

Supported platforms:
  - Linux   (sys.platform == "linux")
  - macOS   (sys.platform == "darwin")
  - Windows (sys.platform == "win32") includes 64-bit Windows
"""

import os
import sys
import tempfile
from pathlib import Path


IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform == "linux"
IS_POSIX = os.name == "posix"


def venv_python(venv_dir: Path) -> Path:
    """Return the Python interpreter path inside a venv."""
    if IS_WINDOWS:
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_pip(venv_dir: Path) -> Path:
    """Return the pip path inside a venv."""
    if IS_WINDOWS:
        return venv_dir / "Scripts" / "pip.exe"
    return venv_dir / "bin" / "pip"


def default_cache_dir() -> Path:
    """Return the platform-appropriate cache directory for compat."""
    if IS_WINDOWS:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "compat_runtime" / "envs"
        return Path.home() / "compat_runtime" / "envs"

    if IS_MACOS:
        return Path.home() / "Library" / "Caches" / "compat_runtime" / "envs"

    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "compat_runtime" / "envs"
    return Path.home() / ".compat_runtime" / "envs"


def make_ipc_files() -> tuple[str, str]:
    """
    Create two temp files for IPC:
      - payload file: host writes, worker reads
      - result file: worker writes, host reads
    """
    tmpdir = tempfile.mkdtemp(prefix="compat_ipc_")
    payload_path = os.path.join(tmpdir, "payload.bin")
    result_path = os.path.join(tmpdir, "result.bin")
    open(payload_path, "wb").close()
    open(result_path, "wb").close()
    return payload_path, result_path


def cleanup_ipc_files(payload_path: str, result_path: str):
    """Remove IPC temp files and their parent directory."""
    import shutil

    parent = Path(payload_path).parent
    try:
        shutil.rmtree(parent, ignore_errors=True)
    except Exception:
        pass


def subprocess_flags() -> int:
    """Return platform-appropriate subprocess creation flags."""
    if IS_WINDOWS:
        return 0x08000000
    return 0


def safe_path_str(path: Path) -> str:
    """
    Return a path as a string, safe for use in subprocess args.

    We do not call .resolve() here. Venv executables can be symlinks to the
    base interpreter, and resolving them can lose the venv context.
    """
    return str(path)


IPC_TEXT_ENCODING = "utf-8"
