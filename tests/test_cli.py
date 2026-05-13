from types import SimpleNamespace

import pytest

from compat import cli


class FakeManager:
    base_dir = None

    def __init__(self, runtimes=None):
        self._runtimes = runtimes or []
        self.invalidated = []

    def list_runtimes(self):
        return self._runtimes

    def invalidate(self, requirements):
        self.invalidated.append(requirements)


def test_cmd_list_prints_empty_message(monkeypatch, capsys):
    monkeypatch.setattr("compat.manager.RuntimeManager", lambda: FakeManager())

    cli._cmd_list()

    assert capsys.readouterr().out.strip() == "No cached runtimes."


def test_cmd_list_prints_runtime_summary(monkeypatch, capsys):
    runtimes = [
        {"name": "req_123", "ready": True, "size_mb": 1.2},
        {"name": "bad_456", "ready": False, "size_mb": 0.4},
    ]
    monkeypatch.setattr("compat.manager.RuntimeManager", lambda: FakeManager(runtimes))

    cli._cmd_list()
    output = capsys.readouterr().out

    assert "req_123" in output
    assert "bad_456" in output
    assert "BROKEN" in output
    assert "2 runtime(s), 1.6 MB total" in output


def test_main_rejects_missing_invalidate_argument(capsys):
    with pytest.raises(SystemExit) as exc_info:
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("sys.argv", ["compat", "invalidate"])
        try:
            cli.main()
        finally:
            monkeypatch.undo()

    assert exc_info.value.code == 1
    assert "Usage: compat invalidate" in capsys.readouterr().err


def test_cmd_clear_aborts_when_user_declines(monkeypatch, capsys):
    fake_base_dir = SimpleNamespace(mkdir=lambda **kwargs: None)
    manager = FakeManager([{"name": "req_123", "ready": True, "size_mb": 1.0}])
    manager.base_dir = fake_base_dir
    monkeypatch.setattr("compat.manager.RuntimeManager", lambda: manager)
    monkeypatch.setattr("builtins.input", lambda prompt: "n")

    cli._cmd_clear()

    assert "Aborted." in capsys.readouterr().out
