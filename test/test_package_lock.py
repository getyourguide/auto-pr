import json
from pathlib import Path

PACKAGE_LOCK_PATH = Path(__file__).resolve().parent.parent / "package-lock.json"


def _version_tuple(version: str) -> tuple:
    return tuple(int(part) for part in version.split("."))


def test_brace_expansion_not_vulnerable_to_ghsa_3jxr_9vmj_r5cp():
    with open(PACKAGE_LOCK_PATH) as f:
        lockfile = json.load(f)

    locked_version = lockfile["packages"]["node_modules/brace-expansion"]["version"]

    assert _version_tuple(locked_version) >= (2, 1, 2), (
        f"brace-expansion {locked_version} is vulnerable to GHSA-3jxr-9vmj-r5cp "
        "(DoS via exponential-time expansion of consecutive non-expanding {} groups); "
        "need >= 2.1.2"
    )
