"""
Output Schema Validator — JSON Schema conformance for LLM output (Section 7).

Extracts JSON from output text (handles markdown code blocks, trailing text),
validates against expected schema, and generates corrective re-prompts.
"""

from __future__ import annotations

import json
import re
from typing import Any

from trust_safety.guardrails.output.models import SchemaValidationResult


class OutputSchemaValidator:
    """Validate LLM output against expected JSON schemas.

    Usage::

        validator = OutputSchemaValidator()
        result = validator.validate(
            '```json\n{"name": "John", "age": 30}\n```',
            {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
        )
    """

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def validate(
        self,
        output_text: str,
        expected_schema: dict[str, Any] | None = None,
    ) -> SchemaValidationResult:
        """Validate *output_text* against *expected_schema*.

        If *expected_schema* is None, only JSON parsing is checked
        (useful for "the output must be valid JSON" cases).
        """
        errors: list[str] = []
        warnings: list[str] = []
        parsed: dict[str, Any] | None = None

        # 1. Extract JSON from text
        json_str = self._extract_json(output_text)
        if json_str is None:
            return SchemaValidationResult(
                passed=False,
                errors=["No JSON structure found in output."],
                retry_prompt=self._build_retry_prompt(
                    "The output must contain a valid JSON object or array.",
                    expected_schema,
                ),
            )

        # 2. Parse JSON
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as exc:
            return SchemaValidationResult(
                passed=False,
                errors=[f"Invalid JSON: {exc}"],
                retry_prompt=self._build_retry_prompt(
                    f"The JSON is malformed: {exc}. Please output valid JSON.",
                    expected_schema,
                ),
            )

        if not isinstance(parsed, (dict, list)):
            errors.append("Output must be a JSON object or array.")

        # Allow arrays through when schema expects them
        if isinstance(parsed, list):
            if expected_schema and expected_schema.get("type") != "array":
                errors.append("Output is an array but schema expects an object.")
            # Array validation passes — items validation could be added in future

        # 3. Schema validation
        if expected_schema:
            schema_errors = self._validate_against_schema(
                parsed, expected_schema
            )
            errors.extend(schema_errors)

        # 4. Value-range checks (if schema has value constraints)
        if expected_schema and isinstance(parsed, dict):
            range_errors = self._check_value_ranges(parsed, expected_schema)
            errors.extend(range_errors)

        passed = len(errors) == 0

        return SchemaValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            retry_prompt=(
                self._build_retry_prompt(
                    "; ".join(errors), expected_schema
                ) if not passed else None
            ),
            extracted_json=parsed if passed else None,
        )

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> str | None:
        """Extract JSON from text that may contain markdown or commentary.

        Handles:
        - `` ```json ... ``` `` code blocks
        - `` ``` ... ``` `` generic code blocks
        - Bare JSON objects/arrays
        """
        # Try markdown code block with json tag
        m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if m:
            return m.group(1).strip()

        # Try bare JSON object or array
        m = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
        if m:
            return m.group(0)

        return None

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def _validate_against_schema(
        self, data: Any, schema: dict[str, Any], path: str = ""
    ) -> list[str]:
        """Validate *data* against a JSON Schema subset."""
        errors: list[str] = []

        schema_type = schema.get("type", "object")

        # Type check
        if schema_type == "object":
            if not isinstance(data, dict):
                errors.append(f"{path or 'root'}: expected object, got {type(data).__name__}")
                return errors

            # Required fields
            for field in schema.get("required", []):
                if field not in data:
                    errors.append(f"Missing required field: '{self._join_path(path, field)}'")

            # Property validation
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if prop_name in data:
                    prop_path = self._join_path(path, prop_name)
                    prop_type = prop_schema.get("type", "string")

                    if prop_type == "string" and not isinstance(data[prop_name], str):
                        errors.append(
                            f"'{prop_path}': expected string, got {type(data[prop_name]).__name__}"
                        )
                    elif prop_type == "integer" and not isinstance(data[prop_name], int):
                        errors.append(
                            f"'{prop_path}': expected integer, got {type(data[prop_name]).__name__}"
                        )
                    elif prop_type == "number" and not isinstance(data[prop_name], (int, float)):
                        errors.append(
                            f"'{prop_path}': expected number, got {type(data[prop_name]).__name__}"
                        )
                    elif prop_type == "boolean" and not isinstance(data[prop_name], bool):
                        errors.append(
                            f"'{prop_path}': expected boolean, got {type(data[prop_name]).__name__}"
                        )
                    elif prop_type == "array" and not isinstance(data[prop_name], list):
                        errors.append(
                            f"'{prop_path}': expected array, got {type(data[prop_name]).__name__}"
                        )

        elif schema_type == "array":
            if not isinstance(data, list):
                errors.append(f"{path or 'root'}: expected array, got {type(data).__name__}")

        return errors

    # ------------------------------------------------------------------
    # Value-range checks
    # ------------------------------------------------------------------

    @staticmethod
    def _check_value_ranges(
        data: dict[str, Any], schema: dict[str, Any]
    ) -> list[str]:
        """Check numeric value constraints from the schema."""
        errors: list[str] = []
        properties = schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            if prop_name not in data:
                continue

            value = data[prop_name]
            if not isinstance(value, (int, float)):
                continue

            minimum = prop_schema.get("minimum")
            maximum = prop_schema.get("maximum")

            if minimum is not None and value < minimum:
                errors.append(
                    f"'{prop_name}': value {value} is below minimum {minimum}"
                )
            if maximum is not None and value > maximum:
                errors.append(
                    f"'{prop_name}': value {value} is above maximum {maximum}"
                )

        return errors

    # ------------------------------------------------------------------
    # Retry prompt generation
    # ------------------------------------------------------------------

    @staticmethod
    def _build_retry_prompt(
        error_detail: str, schema: dict[str, Any] | None
    ) -> str:
        """Build a corrective re-prompt to send back to the LLM."""
        lines = [
            "The previous output was invalid. Please correct the following issues:",
            "",
            f"  {error_detail}",
            "",
        ]
        if schema:
            lines.append("Expected JSON Schema:")
            lines.append(f"  {json.dumps(schema)}")
            lines.append("")
        lines.append("Respond with ONLY the corrected JSON, no additional text.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _join_path(base: str, field: str) -> str:
        """Join JSON path segments."""
        if not base:
            return field
        return f"{base}.{field}"
