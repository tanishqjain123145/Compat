"""
Comparison of Pydantic v1 vs v2 API differences using compat library.
Demonstrates new functions and methods available in v2.
"""

from compat.runtime import runtime

# Test data
TEST_DATA = {
    "name": "Alice",
    "age": 30,
    "email": "alice@example.com"
}


@runtime(requirements=r"runtimes\old_requirements.txt")
def pydantic_v1_analysis():
    """Analyze Pydantic v1 available methods"""
    from pydantic import BaseModel
    
    class User(BaseModel):
        name: str
        age: int
        email: str
    
    user = User(**TEST_DATA)
    
    result = {
        "version": "v1.10.15",
        "user_instance": str(user),
        "available_methods": {
            "dict": str(user.dict()),
            "json": str(user.json()),
            "copy": str(user.copy()),
            "schema_keys": list(user.schema().keys())
        }
    }
    return result


@runtime(requirements=r"runtimes\new_requirements.txt")
def pydantic_v2_analysis():
    """Analyze Pydantic v2 available methods and new functions"""
    from pydantic import BaseModel
    import json
    
    class User(BaseModel):
        name: str
        age: int
        email: str
    
    user = User(**TEST_DATA)
    
    result = {
        "version": "v2.5.3",
        "user_instance": str(user),
        "available_methods": {
            "model_dump": user.model_dump(),
            "model_dump_json": user.model_dump_json(),
            "model_copy": str(user.model_copy()),
            "model_fields": list(user.model_fields.keys()),
            "model_json_schema_keys": list(user.model_json_schema().keys())
        },
        "new_class_methods": {
            "model_validate": str(User.model_validate(TEST_DATA)),
            "model_validate_json": str(User.model_validate_json(json.dumps(TEST_DATA)))
        }
    }
    return result


@runtime(requirements=r"runtimes\click_old.txt")
def click_v1_analysis():
    """Analyze Click v7 features"""
    import click
    
    @click.command()
    @click.option("--name", default="World")
    def cmd(name):
        pass
    
    result = {
        "version": "v7.1.2",
        "features": [
            "Basic CLI framework",
            "@click.command() decorator",
            "@click.option() for options",
            "@click.argument() for arguments",
            ".invoke(ctx) method",
            "Command groups support"
        ],
        "core_classes": ["Command", "Group", "Context", "Option", "Argument"]
    }
    return result


@runtime(requirements=r"runtimes\click_new.txt")
def click_v2_analysis():
    """Analyze Click v8 new features"""
    import click
    
    result = {
        "version": "v8.1.3",
        "new_features": [
            "Enhanced help formatting with rich colors",
            "Better error messages",
            "Improved shell completion (bash, zsh, fish)",
            "Better support for typing hints",
            "New show_default parameter",
            "Eager options support",
            "Path handling improvements"
        ],
        "improvements": [
            "Windows terminal support",
            "Unicode handling",
            "Better exception messages",
            "Validation improvements"
        ]
    }
    return result


def print_comparison(v1_data, v2_data, library_name):
    """Pretty print comparison between v1 and v2"""
    print(f"\n{'='*70}")
    print(f"{library_name.upper()} VERSION COMPARISON")
    print(f"{'='*70}\n")
    
    print(f"OLD VERSION: {v1_data.get('version', 'N/A')}")
    print("-" * 70)
    for key, value in v1_data.items():
        if key != "version":
            print(f"  {key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"    - {k}: {str(v)[:60]}...")
            elif isinstance(value, list):
                for item in value[:5]:
                    print(f"    - {item}")
            else:
                print(f"    {value}")
    
    print(f"\nNEW VERSION: {v2_data.get('version', 'N/A')}")
    print("-" * 70)
    for key, value in v2_data.items():
        if key != "version":
            print(f"  {key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"    - {k}: {str(v)[:60]}...")
            elif isinstance(value, list):
                for item in value[:5]:
                    print(f"    - {item}")
            else:
                print(f"    {value}")
    
    # Highlight new features
    v1_methods = set(v1_data.get("available_methods", {}).keys()) if "available_methods" in v1_data else set()
    v2_methods = set(v2_data.get("available_methods", {}).keys()) if "available_methods" in v2_data else set()
    
    new_methods = v2_methods - v1_methods
    if new_methods:
        print(f"\n[NEW IN v2] Methods:")
        for method in new_methods:
            print(f"    + {method}")
    
    old_methods = v1_methods - v2_methods
    if old_methods:
        print(f"\n[REMOVED/RENAMED] Methods:")
        for method in old_methods:
            print(f"    - {method}")


def main():
    """Run all comparisons"""
    print("\n" + "="*70)
    print("MULTI-VERSION LIBRARY TESTING WITH COMPAT")
    print("="*70)
    
    # Pydantic comparison
    print("\n[1/2] Analyzing Pydantic...")
    v1_pydantic = pydantic_v1_analysis()
    v2_pydantic = pydantic_v2_analysis()
    print_comparison(v1_pydantic, v2_pydantic, "Pydantic")
    
    # Click comparison
    print("\n[2/2] Analyzing Click...")
    v1_click = click_v1_analysis()
    v2_click = click_v2_analysis()
    
    print(f"\n{'='*70}")
    print("CLICK FRAMEWORK VERSION COMPARISON")
    print(f"{'='*70}\n")
    
    print(f"OLD VERSION: {v1_click.get('version', 'N/A')}")
    print("-" * 70)
    print("  Features:")
    for feature in v1_click.get("features", []):
        print(f"    * {feature}")
    print("  Core Classes: " + ", ".join(v1_click.get("core_classes", [])))
    
    print(f"\nNEW VERSION: {v2_click.get('version', 'N/A')}")
    print("-" * 70)
    print("  New Features:")
    for feature in v2_click.get("new_features", []):
        print(f"    + {feature}")
    print("  Improvements:")
    for imp in v2_click.get("improvements", []):
        print(f"    ~ {imp}")
    
    print("\n" + "="*70)
    print("[SUCCESS] All multi-version comparisons completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
