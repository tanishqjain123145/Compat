"""
Public API surface: the @runtime decorator.
by Tanishq Jain

Usage:

    from compat import runtime

    @runtime("runtimes/old_requirements.txt")
    def my_func(x):
        import some_library
        return some_library.process(x)

The requirements path is resolved relative to the decorated function's source
file, so it works correctly regardless of the working directory you run from.
"""

import inspect
from functools import wraps
from pathlib import Path

from compat.manager import RuntimeManager
from compat.utils import resolve_requirements

_manager = RuntimeManager()


def runtime(requirements: str | Path):
    """
    Decorator factory. Executes the decorated function in an isolated venv.

    Args:
        requirements: Path to a requirements.txt file. Relative paths are
            resolved relative to the decorated function's source file.

    The decorated function accepts and returns picklable values. Worker-side
    exceptions are reported as WorkerError with the original traceback.
    """

    def decorator(func):
        source_file = inspect.getfile(func)
        resolved_requirements = resolve_requirements(requirements, source_file)
        module = func.__module__

        @wraps(func)
        def wrapper(*args, **kwargs):
            return _manager.execute(
                func_name=func.__name__,
                module=module,
                source_file=source_file,
                requirements=resolved_requirements,
                args=args,
                kwargs=kwargs,
            )

        wrapper._compat_requirements = str(resolved_requirements)
        wrapper._compat_original = func
        wrapper._compat_source_file = source_file
        return wrapper

    return decorator
