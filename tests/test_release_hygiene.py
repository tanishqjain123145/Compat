from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_distribution_is_named_compat():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["name"] == "compat"


def test_source_and_readme_are_ascii_safe():
    paths = [
        *sorted((ROOT / "compat").glob("*.py")),
        ROOT / "README.md",
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.isascii(), f"{path.relative_to(ROOT)} contains non-ASCII text"


def test_release_clutter_is_not_tracked_in_root():
    assert not (ROOT / "ps.py").exists()
    assert not (ROOT / "runtimes").exists()
    assert not (ROOT / "workers").exists()
