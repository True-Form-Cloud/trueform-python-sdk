from dataclasses import dataclass
from typing import Any

from ._errors import APIError


@dataclass(frozen=True, slots=True)
class Validation:
    email: str
    is_valid_format: bool
    is_freemail: bool
    is_disposable: bool
    has_mx_records: bool
    did_you_mean: str | None
    is_deliverable: bool

    @classmethod
    def _from_api_response(cls, value: object) -> "Validation":
        if not isinstance(value, dict):
            raise _invalid_response()

        fields: dict[str, Any] = value
        boolean_fields = (
            "is_valid_format",
            "is_freemail",
            "is_disposable",
            "has_mx_records",
            "is_deliverable",
        )
        if (
            not isinstance(fields.get("email"), str)
            or any(not isinstance(fields.get(name), bool) for name in boolean_fields)
            or not (
                fields.get("did_you_mean") is None
                or isinstance(fields.get("did_you_mean"), str)
            )
        ):
            raise _invalid_response()

        return cls(
            email=fields["email"],
            is_valid_format=fields["is_valid_format"],
            is_freemail=fields["is_freemail"],
            is_disposable=fields["is_disposable"],
            has_mx_records=fields["has_mx_records"],
            did_you_mean=fields["did_you_mean"],
            is_deliverable=fields["is_deliverable"],
        )


def _invalid_response() -> APIError:
    return APIError(
        "The API returned an invalid validation response.",
        code="invalid_response",
    )