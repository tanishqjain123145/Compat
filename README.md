# compat-runtime

`compat-runtime` helps solve Python dependency conflicts by running functions inside
isolated virtual environments created from separate requirements files. It is
useful for compatibility testing, dependency isolation, and reproducing
behavior across multiple dependency versions.

## Features

- Decorate a function with `@runtime("requirements.txt")`.
- Resolve relative requirements paths from the decorated function's source file.
- Cache virtual environments by requirements-file hash.
- Execute worker code through file-based IPC, avoiding command-line length limits.
- Manage cached runtimes with the `compat` CLI.

## Install

```bash
python -m pip install compat-runtime
```

For local development from a checkout:

```bash
python -m pip install -e .[test,release]
```

## Usage

Create an app-specific requirements file:

```text
pydantic==2.5.3
```

Use it from Python:

```python
from compat import runtime


@runtime("requirements.txt")
def get_pydantic_version():
    import pydantic

    return pydantic.__version__


print(get_pydantic_version())
```

Arguments and return values must be picklable. Exceptions raised in the worker
process are surfaced as `compat.exceptions.WorkerError` with the worker
traceback attached.

## Cache Management

```bash
compat list
compat invalidate requirements.txt
compat clear
```

Cache locations follow the host platform:

- Windows: `%LOCALAPPDATA%\compat_runtime\envs`
- macOS: `~/Library/Caches/compat_runtime/envs`
- Linux: `$XDG_CACHE_HOME/compat_runtime/envs` or `~/.compat_runtime/envs`

## Test

```bash
python -m pytest -q
python -m compileall -q compat
```

## Build and Release

```bash
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ compat-runtime==0.1.0
python -m twine upload dist/*
```

Publishing uses standard Twine credentials. Set `TWINE_USERNAME=__token__` and
`TWINE_PASSWORD=<token>` for the target package index before uploading.

## Repository

Source code is published at:

```text
https://github.com/tanishqjain123145/Compat
```

## License

MIT
