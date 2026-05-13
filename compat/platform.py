"""
platform.py — All platform-specific logic lives here, nowhere else.
by Tanishq Jain

Every other module imports from here instead of branching on sys.platform.
This makes the cross-platform surface explicit and testable.

Supported platforms:
  - Linux   (sys.platform == "linux")
  - macOS   (sys.platform == "darwin")
  - Windows (sys.platform == "win32")  ← includes 64-bit Windows
"""

import os
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# OS detection
# ---------------------------------------------------------------------------

IS_WINDOWS = sys.platform == "win32"
IS_MACOS   = sys.platform == "darwin"
IS_LINUX   = sys.platform == "linux"
IS_POSIX   = os.name == "posix"   # Linux + macOS


# ---------------------------------------------------------------------------
# Venv executable paths
# ---------------------------------------------------------------------------
# Inside a venv, executables live in different places per platform:
#
#   POSIX (Linux/macOS):   <venv>/bin/python   <venv>/bin/pip
#   Windows:               <venv>\Scripts\python.exe
#                          <venv>\Scripts\pip.exe
#
# pathlib.Path handles the slash direction automatically, so we only need
# to branch on the directory name and the .exe suffix.

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


# ---------------------------------------------------------------------------
# Default cache directory
# ---------------------------------------------------------------------------
# Where compat_runtime stores its cached venvs.
#
#   Linux:    ~/.compat_runtime/envs/
#   macOS:    ~/Library/Caches/compat_runtime/envs/
#   Windows:  %LOCALAPPDATA%\compat_runtime\envs\
#             (falls back to ~/.compat_runtime/envs/ if LOCALAPPDATA unset)
#
# We follow platform conventions so we're a good citizen:
#   - macOS: ~/Library/Caches is the right place for app caches
#   - Windows: %LOCALAPPDATA% is the right place (not home dir)
#   - Linux: ~/.compat_runtime (XDG_CACHE_HOME would be ideal but adds complexity)

def default_cache_dir() -> Path:
    """Return the platform-appropriate cache directory for compat_runtime."""
    if IS_WINDOWS:
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "compat_runtime" / "envs"
        return Path.home() / "compat_runtime" / "envs"

    if IS_MACOS:
        return Path.home() / "Library" / "Caches" / "compat_runtime" / "envs"

    # Linux and everything else
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        return Path(xdg_cache) / "compat_runtime" / "envs"
    return Path.home() / ".compat_runtime" / "envs"


# ---------------------------------------------------------------------------
# Payload transport
# ---------------------------------------------------------------------------
# Windows has a hard command-line length limit of 8191 characters (CMD) or
# 32767 (CreateProcess directly). Large payloads — big arrays, DataFrames,
# etc. — can easily exceed this.
#
# Solution: always write the payload to a temp file and pass the FILE PATH
# as the argument, not the payload itself. File paths are short. This works
# identically on all platforms and removes the size limit entirely.
#
# We keep both files (payload + result) in the same temp directory so the
# worker only needs one directory path, making cleanup straightforward.

def make_ipc_files() -> tuple[str, str]:
    """
    Create two temp files for IPC:
      - payload file: host writes, worker reads
      - result file:  worker writes, host reads

    Returns (payload_path, result_path) as strings.
    Both files are created empty; caller is responsible for deletion.

    Why temp files instead of argv?
      - No command-line length limit (critical on Windows)
      - Works with binary data without encoding concerns
      - Cleaner than pipes for synchronous one-shot calls
    """
    # Use the same directory for both so one cleanup covers both
    tmpdir = tempfile.mkdtemp(prefix="compat_ipc_")
    payload_path = os.path.join(tmpdir, "payload.bin")
    result_path  = os.path.join(tmpdir, "result.bin")
    # Touch both files so they exist
    open(payload_path, "wb").close()
    open(result_path,  "wb").close()
    return payload_path, result_path


def cleanup_ipc_files(payload_path: str, result_path: str):
    """Remove IPC temp files and their parent directory."""
    import shutil
    parent = Path(payload_path).parent
    try:
        shutil.rmtree(parent, ignore_errors=True)
    except Exception:
        pass  # best-effort cleanup


# ---------------------------------------------------------------------------
# Subprocess creation flags
# ---------------------------------------------------------------------------
# On Windows, by default new processes inherit the parent's console window
# and can produce annoying flashes. CREATE_NO_WINDOW suppresses this.
# On POSIX this flag doesn't exist, so we use 0 (no flags).

def subprocess_flags() -> int:
    """Return platform-appropriate subprocess creation flags."""
    if IS_WINDOWS:
        # 0x08000000 = CREATE_NO_WINDOW
        # Prevents a console window from appearing for each worker process
        return 0x08000000
    return 0


# ---------------------------------------------------------------------------
# Path encoding safety
# ---------------------------------------------------------------------------
# Windows paths can contain spaces and non-ASCII characters (e.g. usernames
# with accents). pathlib handles this correctly as long as we always use
# Path objects or str(path) and never manually concatenate strings.
# The functions below are no-ops but serve as explicit documentation that
# we've thought about this.

def safe_path_str(p: Path) -> str:
    """
    Return a path as a string, safe for use in subprocess args.

    IMPORTANT: we do NOT call .resolve() here. venv executables are symlinks
    to the base Python interpreter, and resolving them loses the venv context
    (site-packages, etc.). We keep the original path as-is so the OS sees the
    symlink and correctly activates the venv.
    """
    return str(p)


# ---------------------------------------------------------------------------
# Text encoding for IPC files
# ---------------------------------------------------------------------------
# We use raw bytes (pickle) for the payload and result, so encoding is not
# an issue there. For any text files (like the .compat_ready sentinel),
# we explicitly use UTF-8 to avoid Windows cp1252 surprises.

IPC_TEXT_ENCODING = "utf-8"
