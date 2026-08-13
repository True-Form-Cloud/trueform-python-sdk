# Contributing

## Set up the repository

Use Python 3.10 or newer and install the package with its development tools:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Make a change

Keep the public interface backward compatible unless the change is planned for a major release.
Add or update tests for behavior changes, and update the README when the documented interface
changes.

Run the complete local check before opening a pull request:

```bash
python -m ruff check .
python -m mypy
python -m pytest
rm -rf build dist
python -m build
python -m twine check dist/*
python scripts/check_package.py dist/*
```

## Pull requests

Keep each pull request focused. Describe the user-facing behavior, testing performed, and any
compatibility impact. Do not commit generated packages from `dist`.

Report security problems through [GitHub Security Advisories](SECURITY.md), not a public pull
request or issue.