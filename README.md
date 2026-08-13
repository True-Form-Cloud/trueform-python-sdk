# Trueform Python SDK

The official Python client for the [Trueform email validation API](https://trueform.cloud/docs/).

[Python SDK documentation](https://trueform.cloud/docs/python/) | [API reference](https://trueform.cloud/docs/api-reference/)

## Install

```bash
pip install trueform-cloud
```

Requires Python 3.10 or newer. The SDK has no runtime dependencies and requires no API key.

## Quickstart

```python
from trueform_cloud import Trueform

trueform = Trueform()
validation = trueform.validations.create(email="user@example.com")

if validation.is_deliverable:
    print("Email looks good")
```

## Handle validation results

Validation results are frozen, slotted dataclasses with complete type annotations:

```python
if validation.did_you_mean:
    print(f"Did you mean {validation.did_you_mean}?")

if validation.is_disposable:
    print("Ask for a permanent email address")
```

Available attributes:

- `email`
- `is_valid_format`
- `is_freemail`
- `is_disposable`
- `has_mx_records`
- `did_you_mean`
- `is_deliverable`

`is_deliverable` is a domain-level verdict. It does not prove that a specific mailbox exists.

## Configure the client

Timeout values and retry delays use seconds:

```python
trueform = Trueform(timeout=5, max_retries=2)
```

Override options for one request:

```python
validation = trueform.validations.create(
    email="user@example.com",
    timeout=2,
    max_retries=0,
)
```

The client retries connection failures, timeouts, rate limits, and server errors. A `Retry-After`
response header controls the delay when present. Use `base_url=` to point the client at a different
Trueform-compatible endpoint.

## Errors

```python
from trueform_cloud import InvalidRequestError, RateLimitError, Trueform

trueform = Trueform()

try:
    validation = trueform.validations.create(email="user@example.com")
except RateLimitError as error:
    print(f"Retry after {error.retry_after} seconds")
except InvalidRequestError as error:
    print(error)
```

Exported exceptions:

- `TrueformError`
- `APIError`
- `InvalidRequestError`
- `RateLimitError`
- `ConnectionError`
- `TimeoutError`

Exceptions expose `code`, `status`, `request_id`, and `retry_after` when available.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy
python -m pytest
python -m build
python -m twine check dist/*
python scripts/check_package.py dist/*
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report vulnerabilities
through the process in [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).