"""Base model configuration for Google Docs API Pydantic models."""

from pydantic import BaseModel, ConfigDict


class GoogleDocsBaseModel(BaseModel):
    """Base model for all Google Docs API models."""

    model_config = ConfigDict(
        # Allow population by field name (camelCase from API)
        populate_by_name=True,
        # Allow extra fields for forward compatibility
        extra="allow",
        # Validate assignment (catch errors early)
        validate_assignment=True,
        # Use enum values (not names)
        use_enum_values=True,
    )
