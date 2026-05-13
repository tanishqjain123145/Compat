"""
Public API surface: the @runtime decorator.
by Tanishq Jain

Usage:

    from compat import runtime          # or: from compat.runtime import runtime

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

# One shared manager per process — reuses cached venvs across all decorated fns.
_manager = RuntimeManager()


def runtime(requirements: str | Path):
    """
    Decorator factory. Executes the decorated function in an isolated venv.

    Args:
        requirements: Path to a requirements.txt file. Relative paths are
                      resolved relative to the decorated function's source file.

    The decorated function:
      - Accepts any picklable arguments.
      - Returns any picklable value.
      - May raise WorkerError if it throws inside the worker.
      - May raise SerializationError if args/return value can't be pickled.
      - May raise RuntimeNotFoundError if the requirements file is missing.
    """

    def decorator(func):
        source_file = inspect.getfile(func)

        # Resolve the requirements path now (at decoration time) so we get a
        # clear error immediately if the file doesn't exist, and so the path
        # is correct even when the decorated function is in a different
        # directory than the caller.
        resolved_requirements = resolve_requirements(requirements, source_file)

        # Handle the __main__ case: when a script is run directly, Python
        # sets __module__ to "__main__", which the worker can't re-import by
        # name.  We store the source file path and use spec_from_file_location
        # in the worker, so __main__ is handled transparently.
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
