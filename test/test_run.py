import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from unittest.mock import patch, Mock

from autopr import workdir
from test.test_utils import (
    run_cli,
    simple_test_config,
    simple_test_database,
    init_git_repos,
)


def _test_cmd(
    cmd: List[str], additional_env: Optional[Dict[str, str]] = None
) -> Optional[str]:
    commands = ["reset", "checkout", "add", "commit", "bash"]
    if any(subcommand in cmd for subcommand in commands):
        try:
            return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        except subprocess.CalledProcessError as exc:
            raise Exception(
                f"Command {' '.join(cmd)} failed (code: {exc.returncode}):\n{exc.output}"
            )

    return None


@patch("autopr.repo.run_cmd", new=_test_cmd)
@patch("autopr.github.create_github_client")
def test_create_files(_create_github_client: Mock, tmp_path):
    testkey = Path(tmp_path) / "testkey"
    testkey.touch()

    wd = workdir.WorkDir(Path(tmp_path))
    db = simple_test_database()
    init_git_repos(wd, db)
    result = run_cli(
        wd,
        ["run"],
        cfg=simple_test_config(),
        db=db,
    )
    print(result.output)
