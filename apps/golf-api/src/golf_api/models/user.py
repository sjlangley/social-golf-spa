"""An authenticated user."""

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def validate_name_colon_value_keys(d: dict[str, bool]) -> dict[str, bool]:
    """Validate that the keys in the dict are in the format 'name:value'."""
    for key in d.keys():
        if key.count(':') != 1 or not all(
            part.strip() for part in key.split(':', 1)
        ):
            raise ValueError(
                f"Invalid key format: '{key}'. Expected format 'name:value'"
            )
    return d


class User(BaseModel):
    """An authenticated user."""

    model_config = ConfigDict(extra='forbid')

    email: str | None = Field(
        default=None,
        description="The user's email address.",
        json_schema_extra={'example': 'user@example.com'},
    )
    userid: str = Field(
        ...,
        description="The user's stable id.",
    )
    name: str | None = Field(
        default=None,
        description="The user's full name.",
        json_schema_extra={'example': 'John Doe'},
    )
    # Roles associated with the user, for example: ['admin', 'writer']
    roles: list[str] = Field(
        default=[], json_schema_extra={'example': ['admin', 'writer']}
    )

    # Fine grained permissions associated with the user, for example:
    # {'part:read': True, 'part:write': False}
    permissions: dict[str, bool] = Field(
        default={},
        json_schema_extra={'example': {'part:read': True, 'part:write': False}},
    )

    @field_validator('permissions')
    @classmethod
    def validate_permission_keys(cls, v):
        if isinstance(v, dict):
            return validate_name_colon_value_keys(v)
        raise ValueError(
            'Permissions must be a dictionary with keys in the format '
            '"name:value"'
        )

    @model_validator(mode='before')
    @classmethod
    def handle_deprecated_fields(cls, values: Any) -> Any:
        """Remove __name__ that is used in testing."""

        if isinstance(values, dict):
            if '__name__' in values:
                values.pop('__name__')

        return values
