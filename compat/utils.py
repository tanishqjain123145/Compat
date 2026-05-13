"""
Utility helpers for compat.
by Tanishq Jain
"""

import sys
from pathlib import Path


def resolve_requirements(
    requirements: str | Path, caller_file: str | None = None
) -> Path:
    """
    Resolve a requirements path to an absolute Path.

    Resolution order:
      1. If already absolute, use as-is.
      2. If relative, try relative to the caller's source file first.
      3. Fall back to cwd.
    """
    path = Path(requirements)
    if path.is_absolute():
        return path

    if caller_file:
        candidate = Path(caller_file).parent / path
        if candidate.exists():
            return candidate.resolve()

    candidate = Path.cwd() / path
    if candidate.exists():
        return candidate.resolve()

    if caller_file:
        return (Path(caller_file).parent / path).resolve()
    return path.resolve()


def python_version_info() -> str:
    """Return a short human-readable Python version string."""
    version = sys.version_info
    return f"{version.major}.{version.minor}.{version.micro}"


def safe_env_name(stem: str, digest: str) -> str:
    """Build a filesystem-safe environment directory name."""
    safe = "".join(char if char.isalnum() or char in "-_." else "_" for char in stem)
    return f"{safe}_{digest}"
