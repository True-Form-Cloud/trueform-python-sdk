# Trueform Python SDK

[![PyPI version][pypi-version-badge]][pypi-package]
[![CI][ci-badge]][ci]
[![Python versions][python-badge]][pypi-package]
[![MIT License][license-badge]][license]

The official Python client for the [Trueform email validation API](https://trueform.cloud/docs/).
Validate email format, disposable and freemail providers, common domain typos, and mail routing
without an API key.

[Documentation](https://trueform.cloud/docs/python/) | [API reference](https://trueform.cloud/docs/api-reference/) | [PyPI][pypi-package] | [Changelog](https://github.com/True-Form-Cloud/trueform-python-sdk/blob/main/CHANGELOG.md) | [Issues](https://github.com/True-Form-Cloud/trueform-python-sdk/issues)

## Features

- Frozen, slotted result dataclasses with complete type annotations
- Zero runtime dependencies
- Built-in retries for connection failures, timeouts, rate limits, and server errors
- Client-level and per-request configuration

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

Read the [contributing guide](https://github.com/True-Form-Cloud/trueform-python-sdk/blob/main/CONTRIBUTING.md)
before opening a pull request. Report vulnerabilities through the process in the
[security policy](https://github.com/True-Form-Cloud/trueform-python-sdk/blob/main/SECURITY.md).

## Trueform SDKs

| Platform | Registry | Source |
| --- | --- | --- |
| Node.js | [`trueform-node` on npm](https://www.npmjs.com/package/trueform-node) | [GitHub](https://github.com/True-Form-Cloud/trueform-node-sdk) |
| Ruby | [`trueform` on RubyGems](https://rubygems.org/gems/trueform) | [GitHub](https://github.com/True-Form-Cloud/trueform-ruby-sdk) |
| Python | [`trueform-cloud` on PyPI][pypi-package] | [GitHub](https://github.com/True-Form-Cloud/trueform-python-sdk) |

## License

MIT. See the [license][license].

[pypi-package]: https://pypi.org/project/trueform-cloud/
[pypi-version-badge]: https://img.shields.io/pypi/v/trueform-cloud?logo=pypi&logoColor=white
[ci]: https://github.com/True-Form-Cloud/trueform-python-sdk/actions/workflows/ci.yml
[ci-badge]: https://github.com/True-Form-Cloud/trueform-python-sdk/actions/workflows/ci.yml/badge.svg
[python-badge]: https://img.shields.io/pypi/pyversions/trueform-cloud?logo=python&logoColor=white
[license]: https://github.com/True-Form-Cloud/trueform-python-sdk/blob/main/LICENSE
[license-badge]: https://img.shields.io/github/license/True-Form-Cloud/trueform-python-sdk