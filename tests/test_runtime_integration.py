import importlib.util
import importlib
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from compat.exceptions import RuntimeNotFoundError, WorkerError
from compat.manager import RuntimeManager

runtime_module = importlib.import_module("compat.runtime")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def isolated_runtime_manager(tmp_path, monkeypatch):
    manager = RuntimeManager(cache_dir=tmp_path / "cache")
    monkeypatch.setattr(runtime_module, "_manager", manager)
    return manager


def test_runtime_executes_from_source_relative_requirements_when_cwd_changes(
    tmp_path, monkeypatch, isolated_runtime_manager
):
    app = tmp_path / "app"
    app.mkdir()
    (app / "requirements.txt").write_text("", encoding="utf-8")
    module_path = app / "case_module.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from compat import runtime

            @runtime("requirements.txt")
            def add(a, b=0):
                import sys
                return {"value": a + b, "exe": sys.executable}
            """
        ),
        encoding="utf-8",
    )
    module = load_module(module_path)
    monkeypatch.chdir(tmp_path)

    result = module.add(2, b=5)

    assert result["value"] == 7
    assert str(isolated_runtime_manager.base_dir) in result["exe"]
    assert result["exe"] != sys.executable


def test_runtime_preserves_worker_exception_type(
    tmp_path, isolated_runtime_manager
):
    app = tmp_path / "app"
    app.mkdir()
    (app / "requirements.txt").write_text("", encoding="utf-8")
    module_path = app / "case_error.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from compat import runtime

            @runtime("requirements.txt")
            def fail():
                raise ValueError("boom")
            """
        ),
        encoding="utf-8",
    )
    module = load_module(module_path)

    with pytest.raises(WorkerError) as exc_info:
        module.fail()

    assert exc_info.value.original_type == "ValueError"
    assert "boom" in str(exc_info.value)


def test_runtime_rejects_missing_requirements_at_call_time(
    tmp_path, isolated_runtime_manager
):
    app = tmp_path / "app"
    app.mkdir()
    module_path = app / "case_missing.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from compat import runtime

            @runtime("missing.txt")
            def value():
                return 1
            """
        ),
        encoding="utf-8",
    )
    module = load_module(module_path)

    with pytest.raises(RuntimeNotFoundError):
        module.value()


def test_runtime_reports_bad_requirements_install(
    tmp_path, isolated_runtime_manager
):
    app = tmp_path / "app"
    app.mkdir()
    (app / "requirements.txt").write_text("invalid @ @ @\n", encoding="utf-8")
    module_path = app / "case_bad_requirements.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from compat import runtime

            @runtime("requirements.txt")
            def value():
                return 1
            """
        ),
        encoding="utf-8",
    )
    module = load_module(module_path)

    with pytest.raises(RuntimeError, match="pip install failed"):
        module.value()


def test_runtime_reports_unpicklable_return_value(
    tmp_path, isolated_runtime_manager
):
    app = tmp_path / "app"
    app.mkdir()
    (app / "requirements.txt").write_text("", encoding="utf-8")
    module_path = app / "case_unpicklable.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from compat import runtime

            @runtime("requirements.txt")
            def unpicklable():
                return lambda value: value
            """
        ),
        encoding="utf-8",
    )
    module = load_module(module_path)

    with pytest.raises(WorkerError) as exc_info:
        module.unpicklable()

    assert exc_info.value.original_type in {"TypeError", "AttributeError"}


def test_runtime_supports_main_source_files(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    (app / "requirements.txt").write_text("", encoding="utf-8")
    script = app / "script.py"
    script.write_text(
        textwrap.dedent(
            """
            from compat import runtime

            @runtime("requirements.txt")
            def value():
                return "main-ok"

            if __name__ == "__main__":
                print(value())
            """
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["LOCALAPPDATA"] = str(tmp_path / "localappdata")
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert "main-ok" in result.stdout
