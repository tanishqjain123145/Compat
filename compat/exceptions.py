"""
Custom exceptions for compat_runtime.
by Tanishq Jain

Preserves original exception type and worker traceback for clean error reporting.
"""


class WorkerError(Exception):
    """
    Raised in the host process when the worker function raises an exception.

    Attributes:
        original_type   Name of the exception class raised in the worker.
        worker_traceback  Full traceback string from the worker process.
    """

    def __init__(self, error_type: str, error_msg: str, worker_traceback: str):
        self.original_type = error_type
        self.worker_traceback = worker_traceback
        super().__init__(
            f"{error_type}: {error_msg}\n\n"
            f"--- Worker traceback ---\n{worker_traceback.rstrip()}"
        )


class SerializationError(TypeError):
    """
    Raised when arguments or return values cannot be pickled.
    Gives a clear message instead of a cryptic pickle error.
    """


class RuntimeNotFoundError(FileNotFoundError):
    """Raised when a requirements file does not exist."""


class EnvironmentBuildError(RuntimeError):
    """Raised when venv creation or pip install fails."""
