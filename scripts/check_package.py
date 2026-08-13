from __future__ import annotations

import argparse
import email
import tarfile
import zipfile
from pathlib import Path


def check_wheel(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        files = set(archive.namelist())
        metadata_path = next(name for name in files if name.endswith(".dist-info/METADATA"))
        metadata = email.message_from_bytes(archive.read(metadata_path))

    required = {
        "trueform_cloud/__init__.py",
        "trueform_cloud/_client.py",
        "trueform_cloud/_errors.py",
        "trueform_cloud/_models.py",
        "trueform_cloud/_transport.py",
        "trueform_cloud/_version.py",
        "trueform_cloud/py.typed",
    }
    missing = required - files
    if missing:
        raise SystemExit(f"Wheel is missing files: {', '.join(sorted(missing))}")
    if any(name.startswith("tests/") for name in files):
        raise SystemExit("Wheel unexpectedly contains tests")
    if metadata["Name"] != "trueform-cloud":
        raise SystemExit(f"Unexpected distribution name: {metadata['Name']}")
    if metadata["Requires-Python"] != ">=3.10":
        raise SystemExit(f"Unexpected Python requirement: {metadata['Requires-Python']}")


def check_sdist(path: Path) -> None:
    with tarfile.open(path, "r:gz") as archive:
        files = {Path(name).parts[1:] for name in archive.getnames() if "/" in name}

    required = {
        ("CHANGELOG.md",),
        ("LICENSE",),
        ("README.md",),
        ("pyproject.toml",),
        ("src", "trueform_cloud", "py.typed"),
    }
    missing = required - files
    if missing:
        formatted = ", ".join("/".join(parts) for parts in sorted(missing))
        raise SystemExit(f"Source distribution is missing files: {formatted}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Trueform package artifacts")
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()

    wheels = [path for path in args.artifacts if path.suffix == ".whl"]
    sdists = [path for path in args.artifacts if path.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit("Expected exactly one wheel and one source distribution")

    check_wheel(wheels[0])
    check_sdist(sdists[0])
    print(f"Verified {wheels[0]} and {sdists[0]}")


if __name__ == "__main__":
    main()