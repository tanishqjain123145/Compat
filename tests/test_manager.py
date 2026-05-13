import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from compat.exceptions import EnvironmentBuildError, RuntimeNotFoundError
from compat.manager import RuntimeManager


class EncodedStdout:
    def __init__(self, encoding="cp1252"):
        self.buffer = io.BytesIO()
        self.encoding = encoding

    def write(self, text):
        self.buffer.write(text.encode(self.encoding))

    def flush(self):
        pass


def successful_run(*args, **kwargs):
    return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")


def failing_run(*args, **kwargs):
    return SimpleNamespace(returncode=1, stdout=b"stdout", stderr=b"stderr")


def test_create_runtime_logs_are_safe_for_windows_console(
    tmp_path, monkeypatch
):
    req = tmp_path / "requirements.txt"
    req.write_text("", encoding="utf-8")
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    manager = RuntimeManager(cache_dir=tmp_path / "cache")
    monkeypatch.setattr("compat.manager.subprocess.run", successful_run)
    monkeypatch.setattr("sys.stdout", EncodedStdout("cp1252"))

    manager._create_runtime(runtime_dir, req)

    assert (runtime_dir / ".compat_ready").read_text(encoding="utf-8") == "ok"


def test_create_runtime_raises_clear_error_when_venv_creation_fails(
    tmp_path, monkeypatch
):
    req = tmp_path / "requirements.txt"
    req.write_text("", encoding="utf-8")
    manager = RuntimeManager(cache_dir=tmp_path / "cache")
    monkeypatch.setattr("compat.manager.subprocess.run", failing_run)

    with pytest.raises(EnvironmentBuildError, match="venv creation failed"):
        manager._create_runtime(tmp_path / "runtime", req)


def test_invalidate_rejects_missing_requirements(tmp_path):
    manager = RuntimeManager(cache_dir=tmp_path / "cache")

    with pytest.raises(RuntimeNotFoundError, match="Requirements file not found"):
        manager.invalidate(tmp_path / "missing.txt")


def test_list_runtimes_reports_ready_state_and_size(tmp_path):
    runtime = tmp_path / "cache" / "req_123"
    runtime.mkdir(parents=True)
    (runtime / ".compat_ready").write_text("ok", encoding="utf-8")
    (runtime / "file.bin").write_bytes(b"12345")
    manager = RuntimeManager(cache_dir=tmp_path / "cache")

    assert manager.list_runtimes() == [
        {
            "name": "req_123",
            "path": str(runtime),
            "ready": True,
            "size_mb": 0.0,
        }
    ]
