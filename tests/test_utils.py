from pathlib import Path

from compat.utils import resolve_requirements, safe_env_name


def test_resolve_requirements_prefers_caller_file_directory(tmp_path, monkeypatch):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    requirements = app_dir / "requirements.txt"
    requirements.write_text("", encoding="utf-8")

    other_dir = tmp_path / "other"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)

    resolved = resolve_requirements("requirements.txt", str(app_dir / "module.py"))

    assert resolved == requirements.resolve()


def test_resolve_requirements_falls_back_to_current_working_directory(
    tmp_path, monkeypatch
):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    resolved = resolve_requirements("requirements.txt", None)

    assert resolved == requirements.resolve()


def test_resolve_requirements_returns_caller_relative_missing_path(tmp_path):
    source = tmp_path / "pkg" / "module.py"
    source.parent.mkdir()

    resolved = resolve_requirements("missing.txt", str(source))

    assert resolved == (source.parent / "missing.txt").resolve()


def test_safe_env_name_preserves_safe_chars_and_replaces_unsafe_chars():
    assert safe_env_name("req file:old/new", "abc123") == "req_file_old_new_abc123"
