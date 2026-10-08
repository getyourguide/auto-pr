import re
from pathlib import Path

UV_LOCK_PATH = Path(__file__).resolve().parent.parent / "uv.lock"


def _version_tuple(version: str) -> tuple:
    numeric_part = re.split(r"[-+]", version, maxsplit=1)[0]
    return tuple(int(part) for part in numeric_part.split("."))


def _locked_version(content: str, name: str) -> str:
    match = re.search(
        rf'\[\[package\]\]\nname = "{re.escape(name)}"\nversion = "([^"]+)"', content
    )
    assert match, f"No [[package]] entry for {name} found in uv.lock"
    return match.group(1)


def test_virtualenv_not_vulnerable_to_ghsa_p58f_9548_mpm2():
    content = UV_LOCK_PATH.read_text()
    locked_version = _locked_version(content, "virtualenv")

    assert _version_tuple(locked_version) >= (21, 7, 13), (
        f"uv.lock is locked at virtualenv {locked_version}, vulnerable to "
        "GHSA-p58f-9548-mpm2 (path injection via malicious activation scripts); "
        "need >= 21.7.13"
    )


def test_urllib3_not_vulnerable_to_ghsa_gh4c_6fx4_qh6g():
    content = UV_LOCK_PATH.read_text()
    locked_version = _locked_version(content, "urllib3")

    assert _version_tuple(locked_version) >= (2, 8, 0), (
        f"uv.lock is locked at urllib3 {locked_version}, vulnerable to "
        "GHSA-gh4c-6fx4-qh6g (infinite loop in chunked deflate decompression); "
        "need >= 2.8.0"
    )
