import builtins
import json
import math
import time
from email.utils import parsedate_to_datetime
from http.client import HTTPException
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit

from ._errors import (
    APIError,
    ConnectionError,
    InvalidRequestError,
    RateLimitError,
    TrueformError,
)
from ._errors import (
    TimeoutError as TrueformTimeoutError,
)
from ._models import Validation
from ._transport import HTTPResponse, Transport, UrllibTransport
from ._version import __version__

DEFAULT_BASE_URL = "https://api.trueform.cloud"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_RETRIES = 2
MAX_RETRY_DELAY = 60.0


class Validations:
    def __init__(self, client: "Trueform") -> None:
        self._client = client

    def create(
        self,
        *,
        email: str,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> Validation:
        if not isinstance(email, str) or not email.strip():
            raise InvalidRequestError(
                "The email parameter must be a non-empty string.",
                code="invalid_email",
            )

        response = self._client._request(
            path="/v1/validations",
            body={"email": email},
            timeout=timeout,
            max_retries=max_retries,
        )
        return Validation._from_api_response(response)


class Trueform:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        transport: Transport | None = None,
    ) -> None:
        self._base_url = _normalize_base_url(base_url)
        self._timeout = _positive_number(timeout, "timeout")
        self._max_retries = _non_negative_integer(max_retries, "max_retries")
        self._transport = transport if transport is not None else UrllibTransport()
        self.validations = Validations(self)

    def _request(
        self,
        *,
        path: str,
        body: dict[str, object],
        timeout: float | None,
        max_retries: int | None,
    ) -> object:
        request_timeout = _positive_number(
            self._timeout if timeout is None else timeout,
            "timeout",
        )
        retries = _non_negative_integer(
            self._max_retries if max_retries is None else max_retries,
            "max_retries",
        )

        for attempt in range(retries + 1):
            try:
                response = self._transport.request(
                    method="POST",
                    url=f"{self._base_url}{path}",
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                        "User-Agent": f"trueform-cloud/{__version__}",
                    },
                    body=json.dumps(body, separators=(",", ":")).encode(),
                    timeout=request_timeout,
                )
                return _parse_response(response)
            except TrueformError as error:
                if attempt >= retries or not _retryable(error):
                    raise
                time.sleep(_retry_delay(error, attempt))
            except builtins.TimeoutError as error:
                timeout_error = TrueformTimeoutError(
                    f"Request timed out after {request_timeout:g} seconds.",
                    code="request_timeout",
                )
                if attempt >= retries:
                    raise timeout_error from error
                time.sleep(_retry_delay(timeout_error, attempt))
            except URLError as error:
                if isinstance(error.reason, builtins.TimeoutError):
                    url_error: TrueformError = TrueformTimeoutError(
                        f"Request timed out after {request_timeout:g} seconds.",
                        code="request_timeout",
                    )
                else:
                    url_error = ConnectionError(
                        "Unable to connect to the Trueform API.",
                        code="connection_error",
                    )
                if attempt >= retries:
                    raise url_error from error
                time.sleep(_retry_delay(url_error, attempt))
            except (HTTPException, OSError) as error:
                connection_error = ConnectionError(
                    "Unable to connect to the Trueform API.",
                    code="connection_error",
                )
                if attempt >= retries:
                    raise connection_error from error
                time.sleep(_retry_delay(connection_error, attempt))

        raise AssertionError("unreachable")


def _parse_response(response: HTTPResponse) -> object:
    request_id = _header(response, "x-request-id") or _header(response, "cf-ray")
    body = _parse_body(response, request_id)

    if 200 <= response.status < 300:
        if not isinstance(body, dict):
            raise APIError(
                "The API returned an invalid JSON response.",
                code="invalid_response",
                status=response.status,
                request_id=request_id,
            )
        return body

    message = (
        body["error"]
        if isinstance(body, dict) and isinstance(body.get("error"), str)
        else f"Request failed with status {response.status}."
    )
    if response.status == 400:
        raise InvalidRequestError(
            message,
            code="invalid_request",
            status=response.status,
            request_id=request_id,
        )
    if response.status == 429:
        raise RateLimitError(
            message,
            code="rate_limit",
            status=response.status,
            request_id=request_id,
            retry_after=_parse_retry_after(_header(response, "retry-after")),
        )
    raise APIError(
        message,
        code="api_error",
        status=response.status,
        request_id=request_id,
    )


def _parse_body(response: HTTPResponse, request_id: str | None) -> object:
    if not response.body:
        return None
    try:
        return json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        if not 200 <= response.status < 300:
            return None
        raise APIError(
            "The API returned an invalid JSON response.",
            code="invalid_response",
            status=response.status,
            request_id=request_id,
        ) from error


def _header(response: HTTPResponse, name: str) -> str | None:
    return next(
        (value for key, value in response.headers.items() if key.lower() == name),
        None,
    )


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        seconds = float(value)
        return max(seconds, 0.0) if math.isfinite(seconds) else None
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
            return max(retry_at.timestamp() - time.time(), 0.0)
        except (TypeError, ValueError, OverflowError):
            return None


def _retryable(error: TrueformError) -> bool:
    if isinstance(error, (RateLimitError, TrueformTimeoutError)):
        return True
    if isinstance(error, ConnectionError):
        return error.code == "connection_error"
    return isinstance(error, APIError) and (
        error.status == 408 or (error.status is not None and error.status >= 500)
    )


def _retry_delay(error: TrueformError, attempt: int) -> float:
    if error.retry_after is not None:
        return min(float(error.retry_after), MAX_RETRY_DELAY)
    return min(0.25 * (2.0**attempt), 2.0)


def _normalize_base_url(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("base_url must be an HTTP or HTTPS URL")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("base_url must be an HTTP or HTTPS URL")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url must not include a query string or fragment")
    return value.rstrip("/")


def _positive_number(value: Any, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a positive number")
    return float(value)


def _non_negative_integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value