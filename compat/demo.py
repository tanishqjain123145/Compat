"""
demo.py — compat_runtime Phase 1 showcase.
by Tanishq Jain

Run from anywhere:
    python examples/demo.py

Or after `pip install -e .`:
    python examples/demo.py
"""

from compat import runtime

# ---------------------------------------------------------------------------
# Test 1 — Version isolation
# The classic case: two incompatible versions of the same library.
# ---------------------------------------------------------------------------

@runtime("../runtimes/old_requirements.txt")
def get_old_pydantic_version():
    import pydantic
    return pydantic.__version__


@runtime("../runtimes/new_requirements.txt")
def get_new_pydantic_version():
    import pydantic
    return pydantic.__version__


# ---------------------------------------------------------------------------
# Test 2 — Rich argument and return value passing (pickle transport)
# ---------------------------------------------------------------------------

@runtime("../runtimes/old_requirements.txt")
def validate_with_old_pydantic(data: dict) -> dict:
    """Use pydantic v1 BaseModel — .dict() API."""
    from pydantic import BaseModel

    class Product(BaseModel):
        name: str
        price: float
        in_stock: bool = True

    item = Product(**data)
    return item.dict()  # pydantic v1 API


@runtime("../runtimes/new_requirements.txt")
def validate_with_new_pydantic(data: dict) -> dict:
    """Use pydantic v2 BaseModel — .model_dump() API."""
    from pydantic import BaseModel

    class Product(BaseModel):
        name: str
        price: float
        in_stock: bool = True

    item = Product(**data)
    return item.model_dump()  # pydantic v2 API


# ---------------------------------------------------------------------------
# Test 3 — Exception propagation
# Errors inside the worker should surface clearly in the host.
# ---------------------------------------------------------------------------

@runtime("../runtimes/new_requirements.txt")
def will_raise(x: int):
    if x < 0:
        raise ValueError(f"x must be non-negative, got {x}")
    return x * 2


# ---------------------------------------------------------------------------
# Test 4 — Functions with no arguments / return None
# ---------------------------------------------------------------------------

@runtime("../runtimes/old_requirements.txt")
def environment_info() -> dict:
    import sys
    import pydantic
    return {
        "python": sys.version.split()[0],
        "pydantic": pydantic.__version__,
        "platform": sys.platform,
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_test(label, fn, *args):
    print(f"  {label}")
    try:
        result = fn(*args)
        print(f"    → {result}")
    except Exception as e:
        first_line = str(e).splitlines()[0]
        print(f"    ✗ {type(e).__name__}: {first_line}")
    print()


if __name__ == "__main__":
    sep = "─" * 58

    print()
    print("  compat_runtime — Phase 1 Demo")
    print(sep)

    print("\n[1] Version isolation")
    run_test("old pydantic", get_old_pydantic_version)
    run_test("new pydantic", get_new_pydantic_version)

    print("[2] Rich argument / return value passing")
    product = {"name": "Flux Capacitor", "price": 1.21}
    run_test("pydantic v1 validate", validate_with_old_pydantic, product)
    run_test("pydantic v2 validate", validate_with_new_pydantic, product)

    print("[3] Exception propagation")
    run_test("valid call  (x=5)", will_raise, 5)
    run_test("invalid call (x=-1)", will_raise, -1)

    print("[4] Environment introspection")
    run_test("runtime info", environment_info)

    print(sep)
    print("  ✓ All tests complete\n")
