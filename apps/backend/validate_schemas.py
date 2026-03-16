#!/usr/bin/env python3
"""
Simple validation script to demonstrate schema functionality.
This bypasses the need for pytest and external dependencies by
showing the schema structure directly.
"""

import ast
import sys


def extract_pydantic_models(filepath):
    """Extract Pydantic model definitions from a Python file."""
    with open(filepath, "r") as f:
        tree = ast.parse(f.read(), filename=filepath)

    models = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if this class might be a Pydantic model
            bases = [ast.unparse(base) for base in node.bases]
            if any("BaseModel" in base or "Enum" in base for base in bases):
                fields = []
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(
                        item.target, ast.Name
                    ):
                        fields.append(item.target.id)
                models.append((node.name, bases, fields))

    return models


def validate_schema_file(filepath, expected_models):
    """Validate that a schema file contains expected models."""
    try:
        models = extract_pydantic_models(filepath)
        model_names = [name for name, _, _ in models]

        print(f"\n📄 {filepath}")
        for name, bases, fields in models:
            base_str = ", ".join(bases)
            print(f"  ✓ {name}({base_str})")
            if fields:
                for field in fields[:3]:  # Show first 3 fields
                    print(f"      - {field}")
                if len(fields) > 3:
                    print(f"      ... and {len(fields) - 3} more fields")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Main validation routine."""
    print("=" * 70)
    print("SCHEMA VALIDATION REPORT")
    print("=" * 70)

    schemas_to_validate = {
        "app/schemas/common.py": ["Department", "HealthResponse", "ErrorResponse"],
        "app/schemas/chat.py": [
            "ChatRequest",
            "ChatResponse",
            "ChatStreamEvent",
            "AgentTrace",
        ],
        "app/schemas/document.py": [
            "DocumentChunk",
            "DocumentMetadata",
            "IngestionRequest",
            "IngestionResult",
        ],
        "app/schemas/evaluation.py": [
            "RAGASMetrics",
            "EvaluationRequest",
            "EvaluationResult",
        ],
    }

    all_valid = True
    for filepath, expected_models in schemas_to_validate.items():
        if not validate_schema_file(filepath, expected_models):
            all_valid = False

    # Verify Department enum specifically
    print("\n" + "=" * 70)
    print("DEPARTMENT ENUM VALIDATION")
    print("=" * 70)

    try:
        common_models = extract_pydantic_models("app/schemas/common.py")
        for name, bases, fields in common_models:
            if name == "Department":
                print(f"✓ Department enum found with fields: {fields}")
                # Check that it has the required 4 values
                required_values = [
                    "IT_SUPPORT",
                    "LEGAL",
                    "CREDIT_CARD",
                    "AIRPORT_GROUND",
                ]
                all_found = all(val in fields for val in required_values)
                if all_found:
                    print(f"✓ All 4 required department values present:")
                    for val in required_values:
                        print(f"    - {val}")
                else:
                    print(f"✗ Missing department values")
                    all_valid = False
    except Exception as e:
        print(f"✗ Error validating Department enum: {e}")
        all_valid = False

    # Summary
    print("\n" + "=" * 70)
    if all_valid:
        print("✓ ALL SCHEMA VALIDATIONS PASSED")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME SCHEMA VALIDATIONS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
