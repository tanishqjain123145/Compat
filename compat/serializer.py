"""
Serializer: encode/decode function payloads and results.
by Tanishq Jain

Transport format: raw pickle bytes written directly to files.

Why not base64+ASCII?
  Previously we base64-encoded pickle bytes into ASCII strings for argv
  transport. Now that we use files for IPC (no command-line length limits,
  no encoding concerns), we write raw pickle bytes directly. This is:
    - Faster (no encode/decode step)
    - Simpler (no ASCII constraint)
    - Safer (works with any binary data pickle produces)

The only encoding-aware step is error envelope text fields (strings), which
are always valid Unicode and pickle handles naturally.
"""

import pickle
import traceback

from compat.exceptions import SerializationError


# Use the highest protocol available on the HOST Python.
# The worker uses the same Python version (same venv base), so this is safe.
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL


def encode_payload(data: dict) -> bytes:
    """Pickle a payload dict to raw bytes."""
    try:
        return pickle.dumps(data, protocol=PICKLE_PROTOCOL)
    except (pickle.PicklingError, TypeError, AttributeError) as exc:
        raise SerializationError(
            f"Cannot serialize call payload: {exc}\n"
            "Arguments must be picklable. Lambdas, open file handles, "
            "and some closures are not supported."
        ) from exc


def decode_payload(data: bytes) -> dict:
    """Unpickle a payload dict from raw bytes."""
    return pickle.loads(data)


def encode_result(value) -> bytes:
    """Encode a successful return value as a result envelope (bytes)."""
    try:
        envelope = {"ok": True, "value": value}
        return pickle.dumps(envelope, protocol=PICKLE_PROTOCOL)
    except (pickle.PicklingError, TypeError, AttributeError) as exc:
        return encode_error(
            SerializationError(
                f"Return value is not serializable: {exc}\n"
                "The function's return value must be picklable."
            )
        )


def encode_error(exc: Exception) -> bytes:
    """Encode an exception as an error envelope (bytes)."""
    envelope = {
        "ok": False,
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
        "traceback": traceback.format_exc(),
    }
    return pickle.dumps(envelope, protocol=PICKLE_PROTOCOL)


def decode_result(data: bytes):
    """
    Decode a result envelope from bytes.
    Raises WorkerError (preserving original type + traceback) on failure.
    """
    from compat.exceptions import WorkerError
    envelope = pickle.loads(data)
    if envelope["ok"]:
        return envelope["value"]
    raise WorkerError(
        error_type=envelope["error_type"],
        error_msg=envelope["error_msg"],
        worker_traceback=envelope["traceback"],
    )
