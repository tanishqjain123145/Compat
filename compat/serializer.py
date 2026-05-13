"""
Serializer: encode/decode function payloads and results.
by Tanishq Jain

Transport format: raw pickle bytes written directly to files.
"""

import pickle
import traceback

from compat.exceptions import SerializationError


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
    """Encode a successful return value as a result envelope."""
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
    """Encode an exception as an error envelope."""
    envelope = {
        "ok": False,
        "error_type": type(exc).__name__,
        "error_msg": str(exc),
        "traceback": traceback.format_exc(),
    }
    return pickle.dumps(envelope, protocol=PICKLE_PROTOCOL)


def decode_result(data: bytes):
    """Decode a result envelope, raising WorkerError for error envelopes."""
    from compat.exceptions import WorkerError

    envelope = pickle.loads(data)
    if envelope["ok"]:
        return envelope["value"]
    raise WorkerError(
        error_type=envelope["error_type"],
        error_msg=envelope["error_msg"],
        worker_traceback=envelope["traceback"],
    )
