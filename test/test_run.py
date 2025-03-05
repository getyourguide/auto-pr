import subprocess
from pathlib import Path
from test.test_utils import (
    env_var_token_test_config,
    init_git_repos,
    run_cli,
    simple_test_config,
    simple_test_database,
)
from typing import Dict, List, Optional
from unittest.mock import Mock, patch

from autopr import workdir


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


@patch("autopr.repo.run_cmd", new=_test_cmd)
@patch("autopr.github.create_github_client")
def test_api_key_env_var(_create_github_client: Mock, monkeypatch, tmp_path):
    monkeypatch.setenv("APR_API_KEY", "env_var_test")
    wd = workdir.WorkDir(Path(tmp_path))
    db = simple_test_database()
    init_git_repos(wd, db)
    result = run_cli(
        wd,
        ["run"],
        cfg=env_var_token_test_config(),
        db=db,
    )

    assert (
        _create_github_client.call_args_list[0][0][0] == "env_var_test"
    ), f"wrong api_key used for create_github_client: {_create_github_client.call_args_list}"
