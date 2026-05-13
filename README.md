# compat-runtime

Run individual Python functions inside isolated virtual environments, each with
its own `requirements.txt`.

`compat-runtime` is built for real dependency-conflict situations: testing a
function against multiple library versions, isolating a risky dependency, or
reproducing behavior from an older dependency stack without changing your main
application environment.

Install the package as `compat-runtime`, then import it as `compat`.

```bash
python -m pip install compat-runtime
```

```python
from compat import runtime
```

## Quick Start

Create a requirements file next to your Python module:

```text
pydantic==2.5.3
```

Decorate the function that should run in that dependency environment:

```python
from compat import runtime


@runtime("requirements.txt")
def get_pydantic_version():
    import pydantic

    return pydantic.__version__


print(get_pydantic_version())
```

On first call, `compat-runtime` creates a cached virtual environment, installs
the requirements, runs the function in a worker process, and returns the result
to your main Python process. Later calls reuse the cached environment.

## Why Use It?

- Test one codebase against old and new dependency versions.
- Keep conflicting dependencies out of your main environment.
- Reproduce production or legacy behavior from a pinned requirements file.
- Run dependency-heavy code only where it is needed.
- Avoid command-line length limits by using file-based IPC internally.

## Path Resolution

Relative requirements paths are resolved from the decorated function's source
file first, then from the current working directory. This means code can be run
from another directory and still find the right requirements file.

```python
@runtime("runtimes/pydantic-v1.txt")
def parse_with_old_pydantic(data):
    import pydantic

    return pydantic.__version__
```

## Return Values and Errors

Arguments and return values must be picklable because calls cross a process
boundary.

If the worker function raises an exception, the host process receives
`compat.exceptions.WorkerError` with the original exception type and worker
traceback attached.

## CLI

Use the `compat` command to inspect and manage cached runtimes:

```bash
compat list
compat invalidate requirements.txt
compat clear
```

Cache locations follow the host platform:

- Windows: `%LOCALAPPDATA%\compat_runtime\envs`
- macOS: `~/Library/Caches/compat_runtime/envs`
- Linux: `$XDG_CACHE_HOME/compat_runtime/envs` or `~/.compat_runtime/envs`

## Development

```bash
python -m pip install -e .[test,release]
python -m pytest -q
python -m compileall -q compat
```

Build and validate release artifacts:

```bash
python -m build
python -m twine check dist/*
```

## Publishing

This project is published from GitHub Actions using PyPI Trusted Publishing.
Creating and pushing a version tag such as `v0.1.1` runs the release workflow.

Verify an uploaded release with:

```bash
python -m pip install compat-runtime==0.1.1
python -c "import compat; print(compat.__version__)"
```

## Repository

Source code is available at:

```text
https://github.com/tanishqjain123145/Compat
```

## License

MIT
