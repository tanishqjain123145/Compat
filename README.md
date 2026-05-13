# compat-runtime

`compat-runtime` is a Python helper library for executing functions inside isolated virtual environments with different dependency sets. It is useful for compatibility testing, dependency isolation, and reproducing behavior across multiple versions of the same library.

## Key features

- `@runtime("runtimes/old_requirements.txt")` decorator runs the wrapped function in a fresh venv.
- Automatically caches created runtimes by requirements hash.
- Supports Windows, macOS, and Linux.
- Provides CLI helpers to list, invalidate, and clear cached runtimes.

## Usage

```python
from compat import runtime

@runtime("runtimes/old_requirements.txt")
def get_version():
    import pydantic
    return pydantic.__version__

print(get_version())
```

Requirements paths are resolved relative to the decorated function's source file, so the package works regardless of the current working directory.

## Install

```bash
python -m pip install .
```

## Run tests

```bash
python -m pytest
```

## Build and publish

```bash
python -m build
python -m twine upload dist/*
```

## GitHub / repository setup

```bash
git init
git add .
git commit -m "Initial compat-runtime package"
# add your remote and push:
git remote add origin https://github.com/<your-user>/compat-runtime.git
git branch -M main
git push -u origin main
```

## License

MIT
