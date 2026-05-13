import pickle

import pytest

from compat.exceptions import SerializationError, WorkerError
from compat.serializer import decode_payload, decode_result, encode_payload, encode_result


def test_payload_round_trip_uses_pickle_bytes():
    payload = {"args": (1, 2), "kwargs": {"name": "compat"}}

    encoded = encode_payload(payload)

    assert isinstance(encoded, bytes)
    assert decode_payload(encoded) == payload


def test_encode_payload_rejects_unpicklable_values():
    with pytest.raises(SerializationError, match="Arguments must be picklable"):
        encode_payload({"callback": lambda value: value})


def test_decode_result_returns_success_value():
    assert decode_result(encode_result({"ok": True})) == {"ok": True}


def test_decode_result_raises_worker_error_for_error_envelope():
    envelope = {
        "ok": False,
        "error_type": "ValueError",
        "error_msg": "boom",
        "traceback": "Traceback details",
    }

    with pytest.raises(WorkerError) as exc_info:
        decode_result(pickle.dumps(envelope, protocol=pickle.HIGHEST_PROTOCOL))

    assert exc_info.value.original_type == "ValueError"
    assert "boom" in str(exc_info.value)
