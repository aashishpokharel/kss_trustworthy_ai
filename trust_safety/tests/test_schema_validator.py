"""Tests for OutputSchemaValidator — JSON Schema conformance."""

from trust_safety.guardrails.output.schema_validator import OutputSchemaValidator


class TestOutputSchemaValidator:
    """JSON Schema validation for LLM outputs."""

    # -- Valid JSON ----------------------------------------------------

    def test_valid_json_bare(self):
        validator = OutputSchemaValidator()
        result = validator.validate('{"name": "John", "age": 30}')
        assert result.passed
        assert result.extracted_json == {"name": "John", "age": 30}

    def test_valid_json_code_block(self):
        validator = OutputSchemaValidator()
        result = validator.validate('```json\n{"name": "John"}\n```')
        assert result.passed
        assert result.extracted_json == {"name": "John"}

    def test_valid_json_generic_code_block(self):
        validator = OutputSchemaValidator()
        result = validator.validate('```\n{"name": "John"}\n```')
        assert result.passed
        assert result.extracted_json == {"name": "John"}

    def test_valid_json_with_surrounding_text(self):
        validator = OutputSchemaValidator()
        result = validator.validate('Here is the result: {"name": "John"}. Hope that helps!')
        assert result.passed
        assert result.extracted_json == {"name": "John"}

    # -- Invalid JSON --------------------------------------------------

    def test_no_json_found(self):
        validator = OutputSchemaValidator()
        result = validator.validate("Just some plain text, no JSON here.")
        assert not result.passed
        assert "No JSON" in result.errors[0]

    def test_malformed_json(self):
        validator = OutputSchemaValidator()
        result = validator.validate('{"name": "John", age: 30}')
        assert not result.passed
        assert any("Invalid JSON" in e for e in result.errors)

    # -- Schema validation ---------------------------------------------

    def test_schema_missing_required_field(self):
        validator = OutputSchemaValidator()
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        result = validator.validate('{"name": "John"}', schema)
        assert not result.passed
        assert any("age" in e.lower() for e in result.errors)

    def test_schema_wrong_type(self):
        validator = OutputSchemaValidator()
        schema = {
            "type": "object",
            "properties": {"count": {"type": "integer"}},
            "required": ["count"],
        }
        result = validator.validate('{"count": "not-a-number"}', schema)
        assert not result.passed
        assert any("count" in e.lower() for e in result.errors)

    def test_schema_valid(self):
        validator = OutputSchemaValidator()
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "active": {"type": "boolean"},
            },
            "required": ["name", "age"],
        }
        result = validator.validate(
            '{"name": "John", "age": 30, "active": true}', schema
        )
        assert result.passed

    # -- Value range checks --------------------------------------------

    def test_value_below_minimum(self):
        validator = OutputSchemaValidator()
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer", "minimum": 18}},
            "required": ["age"],
        }
        result = validator.validate('{"age": 15}', schema)
        assert not result.passed
        assert any("below minimum" in e.lower() for e in result.errors)

    def test_value_above_maximum(self):
        validator = OutputSchemaValidator()
        schema = {
            "type": "object",
            "properties": {"score": {"type": "number", "maximum": 100}},
            "required": ["score"],
        }
        result = validator.validate('{"score": 150}', schema)
        assert not result.passed
        assert any("above maximum" in e.lower() for e in result.errors)

    def test_value_within_range(self):
        validator = OutputSchemaValidator()
        schema = {
            "type": "object",
            "properties": {"age": {"type": "integer", "minimum": 0, "maximum": 150}},
            "required": ["age"],
        }
        result = validator.validate('{"age": 42}', schema)
        assert result.passed

    # -- Retry prompt --------------------------------------------------

    def test_retry_prompt_generated_on_failure(self):
        validator = OutputSchemaValidator()
        schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        result = validator.validate("plain text", schema)
        assert not result.passed
        assert result.retry_prompt is not None
        assert "correct" in result.retry_prompt.lower()

    def test_retry_prompt_includes_schema(self):
        validator = OutputSchemaValidator()
        schema = {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}
        result = validator.validate("nope", schema)
        assert result.retry_prompt and "x" in result.retry_prompt

    # -- Array validation ----------------------------------------------

    def test_array_type_expected(self):
        validator = OutputSchemaValidator()
        schema = {"type": "array"}
        result = validator.validate('[{"name": "a"}, {"name": "b"}]', schema)
        assert result.passed

    # -- Empty output --------------------------------------------------

    def test_empty_output(self):
        validator = OutputSchemaValidator()
        result = validator.validate("")
        assert not result.passed
