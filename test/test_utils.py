import subprocess
from typing import Optional, List

from click.testing import CliRunner, Result

from autopr import cli, database, config, workdir
from autopr.database import Repository


def run_cli(
    wd: workdir.WorkDir,
    cmd: List[str],
    cfg: Optional[config.Config] = None,
    db: Optional[database.Database] = None,
    should_fail: bool = False,
) -> Result:
    if cfg:
        workdir.write_config(wd, cfg)
    if db:
        workdir.write_database(wd, db)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        cmd,
        env={"APR_WORKDIR": f"{wd.location}", "APR_DEBUG": "1"},
        catch_exceptions=True,
    )
    if result.exception is not None:
        print(f"Exception:\n{result.output}")
        raise result.exception

    if (should_fail and result.exit_code == 0) or (
        not should_fail and result.exit_code != 0
    ):
        print(
            f"Failure (should_fail={should_fail}, exit_code={result.exit_code}):\n{result.output}"
        )
        assert False

    return result


def init_git_repos(wd: workdir.WorkDir, db: database.Database):
    if db is None:
        raise Exception(
            "A database needs to be passed if repository directories should be created."
        )

    for repository in db.repositories:
        repo_dir = wd.repos_dir / repository.name
        repo_dir.mkdir(parents=True, exist_ok=True)
        subprocess.check_output(["git", "-C", f"{repo_dir}", "init"])
        subprocess.check_output(
            ["git", "-C", f"{repo_dir}", "config", "user.name", "Test"]
        )
        subprocess.check_output(
            ["git", "-C", f"{repo_dir}", "config", "user.email", "test@test.com"]
        )
        subprocess.check_output(
            ["git", "-C", f"{repo_dir}", "config", "commit.gpgsign", "false"]
        )
        subprocess.check_output(
            ["git", "-C", f"{repo_dir}", "commit", "--allow-empty", "-m", "test"]
        )


def simple_test_config() -> config.Config:
    credentials = config.Credentials(api_key="test", ssh_key_file="test")
    pr = config.PrTemplate()
    cmd = ["bash", "-c", "echo 'test' > testfile.txt"]
    return config.Config(credentials=credentials, pr=pr, update_command=cmd)


def simple_test_database() -> database.Database:
    repo = database.Repository(
        owner="test", name="test", ssh_url="test@testytest.com", default_branch="master"
    )
    user = database.GitUser(name="Joe Schmoe", email="joe86@hotmail.com")
    return database.Database(user=user, repositories=[repo])


def get_repository(
    name: str,
    owner: str = "den",
    ssh_url: str = "git@gitgitgit.com/git/git.git",
    default_branch: str = "main",
) -> Repository:
    return Repository(
        owner=owner, name=name, ssh_url=ssh_url, default_branch=default_branch
    )
