"""
Script to check version consistency in the Minerva project.

This script checks if the version numbers are consistent in the following locations:
1. src/minerva/__version__.py
2. pyproject.toml
"""

import os
import re
import sys
import tomllib
from pathlib import Path


def get_version_from_version_py():
    """Get version number from __version__.py"""
    version_file = (
        Path(__file__).resolve().parent.parent / "src" / "minerva" / "__version__.py"
    )
    with open(version_file, "r") as f:
        content = f.read()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Failed to extract version from __version__.py")
    return match.group(1)


def get_version_from_pyproject():
    """Get version number from pyproject.toml"""
    pyproject_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "pyproject.toml",
    )
    with open(pyproject_file, "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


def main():
    """Check version consistency"""
    try:
        version_py_version = get_version_from_version_py()
        pyproject_version = get_version_from_pyproject()

        print(f"__version__.py: {version_py_version}")
        print(f"pyproject.toml: {pyproject_version}")

        if version_py_version != pyproject_version:
            print(
                f"Error: Version numbers do not match ({version_py_version} != {pyproject_version})"
            )
            return 1

        print("OK: All version numbers match")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
