"""
RuntimeManager: venv lifecycle + function dispatch.
by Tanishq Jain
"""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from compat.exceptions import EnvironmentBuildError, RuntimeNotFoundError
from compat.platform import (
    cleanup_ipc_files,
    default_cache_dir,
    make_ipc_files,
    safe_path_str,
    subprocess_flags,
    venv_pip,
    venv_python,
    IPC_TEXT_ENCODING,
)
from compat.serializer import decode_result, encode_payload
from compat.utils import safe_env_name

_WORKER_SCRIPT = (
    Path(__file__).parent.parent / "workers" / "worker_server.py"
).resolve()


class RuntimeManager:
    """
    Central coordinator. Thread-safe for reads (env lookup); not safe for
    concurrent writes to the same env (first-run creation). Fine for typical
    single-threaded script use.
    """

    def __init__(self, cache_dir: Path | None = None):
        self.base_dir = cache_dir or default_cache_dir()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Environment management
    # ------------------------------------------------------------------

    def _hash_requirements(self, req: Path) -> str:
        digest = hashlib.sha256(req.read_bytes()).hexdigest()[:16]
        return safe_env_name(req.stem, digest)

    def _ensure_runtime(self, req: Path) -> Path:
        key = self._hash_requirements(req)
        runtime_dir = self.base_dir / key
        if not (runtime_dir / ".compat_ready").exists():
            if runtime_dir.exists():
                shutil.rmtree(runtime_dir)
            self._create_runtime(runtime_dir, req)
        return runtime_dir

    def _create_runtime(self, runtime_dir: Path, req: Path):
        print(f"[compat] Creating runtime: {runtime_dir.name}", flush=True)

        # --- Create venv ---
        result = subprocess.run(
            [sys.executable, "-m", "venv", safe_path_str(runtime_dir)],
            capture_output=True,
            creationflags=subprocess_flags(),
        )
        if result.returncode != 0:
            raise EnvironmentBuildError(
                f"venv creation failed:\n"
                + result.stderr.decode(errors="replace")
            )

        # --- Install deps ---
        print(f"[compat] Installing from {req.name} …", flush=True)
        result = subprocess.run(
            [
                safe_path_str(venv_pip(runtime_dir)),
                "install",
                "--no-color",
                "--quiet",
                "-r",
                safe_path_str(req),
            ],
            capture_output=True,
            creationflags=subprocess_flags(),
        )
        if result.returncode != 0:
            raise EnvironmentBuildError(
                f"pip install failed:\n"
                + result.stderr.decode(errors="replace")
                + result.stdout.decode(errors="replace")
            )

        # Stamp only after full success (partial installs never get reused)
        (runtime_dir / ".compat_ready").write_text(
            "ok", encoding=IPC_TEXT_ENCODING
        )
        print("[compat] Runtime ready ✓", flush=True)

    def invalidate(self, requirements_path: str | Path):
        rp = Path(requirements_path)
        if not rp.exists():
            raise RuntimeNotFoundError(f"Requirements file not found: {rp}")
        key = self._hash_requirements(rp)
        runtime_dir = self.base_dir / key
        if runtime_dir.exists():
            shutil.rmtree(runtime_dir)
            print(f"[compat] Invalidated: {key}", flush=True)
        else:
            print(f"[compat] No cached runtime for: {key}", flush=True)

    def list_runtimes(self) -> list[dict]:
        runtimes = []
        for d in sorted(self.base_dir.iterdir()):
            if d.is_dir():
                ready = (d / ".compat_ready").exists()
                size_mb = sum(
                    f.stat().st_size for f in d.rglob("*") if f.is_file()
                ) / 1e6
                runtimes.append({
                    "name": d.name,
                    "path": str(d),
                    "ready": ready,
                    "size_mb": round(size_mb, 1),
                })
        return runtimes

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(
        self,
        func_name: str,
        module: str,
        source_file: str,
        requirements: Path,
        args: tuple,
        kwargs: dict,
    ):
        if not requirements.exists():
            raise RuntimeNotFoundError(
                f"Requirements file not found: {requirements}\n"
                "Relative paths are resolved from the decorated function's "
                "source file."
            )

        runtime_dir = self._ensure_runtime(requirements)
        python_exe  = venv_python(runtime_dir)

        payload = {
            "func_name":   func_name,
            "module":      module,
            "source_file": source_file,
            "args":        args,
            "kwargs":      kwargs,
        }

        # Write payload + result to temp files (no command-line length limits,
        # no encoding issues, works identically on all platforms).
        payload_path, result_path = make_ipc_files()

        try:
            Path(payload_path).write_bytes(encode_payload(payload))

            proc = subprocess.run(
                [
                    safe_path_str(python_exe),
                    safe_path_str(_WORKER_SCRIPT),
                    payload_path,   # worker reads from here
                    result_path,    # worker writes to here
                ],
                capture_output=True,
                creationflags=subprocess_flags(),
            )

            result_bytes = Path(result_path).read_bytes()

            if result_bytes:
                # Result envelope written — decode it regardless of exit code.
                # decode_result() raises WorkerError for error envelopes.
                return decode_result(result_bytes)

            # Empty result = hard crash before the worker could write anything
            if proc.returncode != 0:
                stderr = proc.stderr.decode(errors="replace").strip()
                stdout = proc.stdout.decode(errors="replace").strip()
                detail = stderr or stdout or "(no output)"
                raise RuntimeError(
                    f"Worker crashed (exit {proc.returncode}):\n{detail}"
                )

            raise RuntimeError(
                "Worker produced no result — this is a compat_runtime bug."
            )

        finally:
            cleanup_ipc_files(payload_path, result_path)
