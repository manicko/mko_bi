"""OpenAPI schema verification tests.

Verifies that error response schemas are properly documented in the OpenAPI spec.
"""

from mkobi.models.error_response import ErrorResponse


class TestOpenAPIErrorSchemas:
    """Verify OpenAPI schema contains proper error response documentation."""

    def test_error_response_model_exists(self) -> None:
        """ErrorResponse model should be properly defined."""
        assert ErrorResponse is not None

        # Verify required fields per RFC 7807
        fields = ErrorResponse.model_fields
        required_fields = ["type", "title", "status", "detail", "code"]
        for field in required_fields:
            assert field in fields, f"ErrorResponse should have '{field}' field"

    def test_error_response_optional_details(self) -> None:
        """ErrorResponse should have optional details field for additional context."""
        fields = ErrorResponse.model_fields
        assert "details" in fields, "ErrorResponse should have 'details' field"
        assert not fields["details"].is_required(), "'details' should be optional"

    def test_error_response_model_schema_generation(self) -> None:
        """ErrorResponse model should generate valid OpenAPI schema."""
        schema = ErrorResponse.model_json_schema()

        # Verify schema has all required properties
        properties = schema.get("properties", {})
        required_fields = ["type", "title", "status", "detail", "code"]
        for field in required_fields:
            assert field in properties, f"ErrorResponse schema should have '{field}' property"