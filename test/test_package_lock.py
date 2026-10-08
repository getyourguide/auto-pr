import json
import re
from pathlib import Path

PACKAGE_LOCK_PATH = Path(__file__).resolve().parent.parent / "package-lock.json"


def _version_tuple(version: str) -> tuple:
    numeric_part = re.split(r"[-+]", version, maxsplit=1)[0]
    return tuple(int(part) for part in numeric_part.split("."))


def _brace_expansion_paths(packages: dict) -> list:
    return [
        path
        for path in packages
        if path == "node_modules/brace-expansion"
        or path.endswith("/node_modules/brace-expansion")
    ]


def test_brace_expansion_not_vulnerable_to_ghsa_3jxr_9vmj_r5cp():
    with open(PACKAGE_LOCK_PATH) as f:
        lockfile = json.load(f)

    packages = lockfile["packages"]
    brace_expansion_paths = _brace_expansion_paths(packages)

    assert brace_expansion_paths, "No brace-expansion entry found in package-lock.json"

    for path in brace_expansion_paths:
        locked_version = packages[path].get("version")
        assert locked_version, f"{path} has no 'version' field in package-lock.json"
        assert _version_tuple(locked_version) >= (2, 1, 2), (
            f"{path} is locked at brace-expansion {locked_version}, vulnerable to "
            "GHSA-3jxr-9vmj-r5cp (DoS via exponential-time expansion of consecutive "
            "non-expanding {} groups); need >= 2.1.2"
        )
