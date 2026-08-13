import json
import unittest
from dataclasses import FrozenInstanceError
from email.utils import formatdate
from typing import Any
from unittest.mock import patch
from urllib.error import URLError

from trueform_cloud import (
    APIError,
    InvalidRequestError,
    RateLimitError,
    Trueform,
    Validation,
    __version__,
)
from trueform_cloud import (
    ConnectionError as TrueformConnectionError,
)
from trueform_cloud import (
    TimeoutError as TrueformTimeoutError,
)
from trueform_cloud._transport import HTTPResponse

VALIDATION = {
    "email": "user@example.com",
    "is_valid_format": True,
    "is_freemail": False,
    "is_disposable": False,
    "has_mx_records": True,
    "did_you_mean": None,
    "is_deliverable": True,
}


class StubTransport:
    def __init__(self, *responses: HTTPResponse | Exception) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request(self, **request: Any) -> HTTPResponse:
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def response(
    body: object,
    *,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> HTTPResponse:
    return HTTPResponse(
        status=status,
        body=json.dumps(body).encode(),
        headers=headers or {},
    )


class TrueformTest(unittest.TestCase):
    def test_creates_an_immutable_validation(self) -> None:
        transport = StubTransport(response(VALIDATION))
        trueform = Trueform(transport=transport)

        validation = trueform.validations.create(email="User@Example.com")

        self.assertEqual(
            validation,
            Validation(
                email="user@example.com",
                is_valid_format=True,
                is_freemail=False,
                is_disposable=False,
                has_mx_records=True,
                did_you_mean=None,
                is_deliverable=True,
            ),
        )
        self.assertTrue(validation.is_deliverable)
        with self.assertRaises(FrozenInstanceError):
            validation.email = "changed@example.com"  # type: ignore[misc]

        request = transport.requests[0]
        self.assertEqual(request["method"], "POST")
        self.assertEqual(
            request["url"],
            "https://api.trueform.cloud/v1/validations",
        )
        self.assertEqual(json.loads(request["body"]), {"email": "User@Example.com"})
        self.assertEqual(
            request["headers"]["User-Agent"],
            f"trueform-cloud/{__version__}",
        )

    def test_supports_a_custom_base_url_and_request_options(self) -> None:
        transport = StubTransport(response(VALIDATION))
        trueform = Trueform(
            base_url="http://localhost:8787/",
            timeout=5,
            transport=transport,
        )

        trueform.validations.create(
            email="user@example.com",
            timeout=1.5,
            max_retries=0,
        )

        request = transport.requests[0]
        self.assertEqual(request["url"], "http://localhost:8787/v1/validations")
        self.assertEqual(request["timeout"], 1.5)

    def test_rejects_an_empty_email_without_a_request(self) -> None:
        transport = StubTransport()
        trueform = Trueform(transport=transport)

        with self.assertRaises(InvalidRequestError) as raised:
            trueform.validations.create(email="  ")

        self.assertEqual(raised.exception.code, "invalid_email")
        self.assertEqual(transport.requests, [])

    def test_maps_an_invalid_request_error(self) -> None:
        transport = StubTransport(
            response(
                {"error": "Missing or empty email field."},
                status=400,
                headers={"X-Request-Id": "req_123"},
            )
        )
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(InvalidRequestError) as raised:
            trueform.validations.create(email="bad")

        self.assertEqual(raised.exception.code, "invalid_request")
        self.assertEqual(raised.exception.status, 400)
        self.assertEqual(raised.exception.request_id, "req_123")

    def test_exposes_rate_limit_retry_delay_in_seconds(self) -> None:
        transport = StubTransport(
            response(
                {"error": "Too Many Requests"},
                status=429,
                headers={"Retry-After": "2"},
            )
        )
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(RateLimitError) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertEqual(raised.exception.retry_after, 2.0)

    def test_retries_a_transient_api_error(self) -> None:
        transport = StubTransport(
            response({"error": "Unavailable"}, status=503),
            response(VALIDATION),
        )
        trueform = Trueform(transport=transport, max_retries=1)

        with patch("trueform_cloud._client.time.sleep"):
            validation = trueform.validations.create(email="user@example.com")

        self.assertTrue(validation.is_deliverable)
        self.assertEqual(len(transport.requests), 2)

    def test_maps_timeout_errors(self) -> None:
        transport = StubTransport(TimeoutError("timed out"))
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(TrueformTimeoutError) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertEqual(raised.exception.code, "request_timeout")
        self.assertIsInstance(raised.exception.__cause__, TimeoutError)

    def test_maps_connection_errors(self) -> None:
        transport = StubTransport(URLError("getaddrinfo failed"))
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(TrueformConnectionError) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertEqual(raised.exception.code, "connection_error")
        self.assertIsInstance(raised.exception.__cause__, URLError)

    def test_rejects_invalid_json_from_a_successful_response(self) -> None:
        transport = StubTransport(HTTPResponse(status=200, body=b"not json", headers={}))
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(APIError) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertEqual(raised.exception.code, "invalid_response")
        self.assertEqual(raised.exception.status, 200)

    def test_rejects_an_incomplete_validation_response(self) -> None:
        transport = StubTransport(response({"email": "user@example.com"}))
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(APIError) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertEqual(raised.exception.code, "invalid_response")

    def test_stops_after_the_configured_retry_count(self) -> None:
        transport = StubTransport(
            response({"error": "Unavailable"}, status=503),
            response({"error": "Unavailable"}, status=503),
        )
        trueform = Trueform(transport=transport, max_retries=1)

        with patch("trueform_cloud._client.time.sleep"), self.assertRaises(
            APIError
        ) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertEqual(raised.exception.status, 503)
        self.assertEqual(len(transport.requests), 2)

    def test_request_retry_count_can_disable_client_retries(self) -> None:
        transport = StubTransport(
            response({"error": "Unavailable"}, status=503),
            response(VALIDATION),
        )
        trueform = Trueform(transport=transport, max_retries=1)

        with self.assertRaises(APIError):
            trueform.validations.create(
                email="user@example.com",
                max_retries=0,
            )

        self.assertEqual(len(transport.requests), 1)

    def test_parses_an_http_date_retry_after_header(self) -> None:
        transport = StubTransport(
            response(
                {"error": "Too Many Requests"},
                status=429,
                headers={"Retry-After": formatdate(timeval=None, usegmt=True)},
            )
        )
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(RateLimitError) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertEqual(raised.exception.retry_after, 0.0)

    def test_ignores_a_malformed_retry_after_header(self) -> None:
        transport = StubTransport(
            response(
                {"error": "Too Many Requests"},
                status=429,
                headers={"Retry-After": "NaN"},
            )
        )
        trueform = Trueform(transport=transport, max_retries=0)

        with self.assertRaises(RateLimitError) as raised:
            trueform.validations.create(email="user@example.com")

        self.assertIsNone(raised.exception.retry_after)

    def test_rejects_invalid_client_and_request_options(self) -> None:
        invalid_clients = (
            {"timeout": 0},
            {"timeout": True},
            {"max_retries": -1},
            {"max_retries": False},
            {"base_url": "ftp://example.com"},
        )
        for options in invalid_clients:
            with self.subTest(options=options), self.assertRaises(
                (TypeError, ValueError)
            ):
                Trueform(**options)

        trueform = Trueform(transport=StubTransport(response(VALIDATION)))
        with self.assertRaises(ValueError):
            trueform.validations.create(
                email="user@example.com",
                timeout=False,
            )


if __name__ == "__main__":
    unittest.main()