"""Demo: Two Flask versions requiring different Werkzeug versions."""

from compat import runtime


def _package_version(name: str, module):
    version = getattr(module, "__version__", None)
    if version:
        return version

    try:
        import importlib.metadata as metadata
        return metadata.version(name)
    except Exception:
        return "unknown"


@runtime("runtimes/flask_old.txt")
def flask_1_info() -> dict:
    import flask
    import werkzeug

    return {
        "flask_version": flask.__version__,
        "werkzeug_version": _package_version("Werkzeug", werkzeug),
        "message": "Flask 1.x runtime uses older Werkzeug"
    }


@runtime("runtimes/flask_new.txt")
def flask_2_info() -> dict:
    import flask
    import werkzeug

    return {
        "flask_version": flask.__version__,
        "werkzeug_version": _package_version("Werkzeug", werkzeug),
        "message": "Flask 2.x runtime uses newer Werkzeug"
    }


def print_conflict_demo() -> None:
    old_info = flask_1_info()
    new_info = flask_2_info()

    print("\nDependency conflict demo: same lib used with two incompatible versions")
    print("-" * 72)
    print("Old Flask runtime:")
    print(f"  Flask:    {old_info['flask_version']}")
    print(f"  Werkzeug: {old_info['werkzeug_version']}")
    print("\nNew Flask runtime:")
    print(f"  Flask:    {new_info['flask_version']}")
    print(f"  Werkzeug: {new_info['werkzeug_version']}")
    print("\nThis shows the same dependency (werkzeug) can exist in two separate isolated runtimes.")


if __name__ == "__main__":
    print_conflict_demo()
