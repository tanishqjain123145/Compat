from compat import runtime


@runtime("runtimes/old_requirements.txt")
def get_old_pydantic_version():
    import pydantic
    return pydantic.__version__


@runtime("runtimes/new_requirements.txt")
def get_new_pydantic_version():
    import pydantic
    return pydantic.__version__


@runtime("runtimes/new_requirements.txt")
def fail_fast(x: int):
    if x < 0:
        raise ValueError(f"x must be non-negative, got {x}")
    return x
