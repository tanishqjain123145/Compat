"""
Utility helpers for compat_runtime.
by Tanishq Jain
"""

import sys
from pathlib import Path


def resolve_requirements(requirements: str | Path, caller_file: str | None = None) -> Path:
    """
    Resolve a requirements path to an absolute Path.

    Resolution order:
      1. If already absolute → use as-is.
      2. If relative, try relative to the *caller's source file* first.
      3. Fall back to cwd.

    This means @runtime("runtimes/old.txt") works correctly regardless of
    what directory the user runs python from.
    """
    p = Path(requirements)
    if p.is_absolute():
        return p

    # Try relative to the decorated function's source file
    if caller_file:
        candidate = Path(caller_file).parent / p
        if candidate.exists():
            return candidate.resolve()

    # Fall back to cwd
    candidate = Path.cwd() / p
    if candidate.exists():
        return candidate.resolve()

    # Neither worked — return the resolved path so the caller can emit a
    # clear FileNotFoundError with the full path.
    return (Path(caller_file).parent / p).resolve() if caller_file else p.resolve()


def python_version_info() -> str:
    """Return a short human-readable Python version string."""
    v = sys.version_info
    return f"{v.major}.{v.minor}.{v.micro}"


def safe_env_name(stem: str, digest: str) -> str:
    """Build a filesystem-safe environment directory name."""
    # Replace characters that are problematic on Windows/macOS/Linux
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in stem)
    return f"{safe}_{digest}"
