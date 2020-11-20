import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Dict

import click

from autopr import database
from autopr.util import CliException


def pull_repositories(
    user: database.GitUser,
    ssh_key_file: Path,
    repos_dir: Path,
    repositories: List[database.Repository],
    update_repos: bool,
):
    for repository in repositories:
        try:
            _pull_repository(
                user,
                ssh_key_file,
                repos_dir,
                repository,
                update_repos,
            )
        except CliException as e:
            click.echo(f"Error: {e}", err=True)


def _pull_repository(
    user: database.GitUser,
    ssh_key_file: Path,
    repos_dir: Path,
    repository: database.Repository,
    update_repo: bool,
) -> None:
    repo_dir = repos_dir / repository.name
    repo_exists = repo_dir.exists()

    if not update_repo and repo_exists:
        click.secho(f"Repository already exists '{repository.name}':")
        return

    click.secho(f"Pulling repository '{repository.name}':")

    pull_failed = False
    if repo_exists:
        click.secho(f"  - Checking out branch '{repository.default_branch}'")
        _git_checkout(repo_dir, repository.default_branch)

        click.secho(f"  - Pulling latest changes")
        try:
            _git_pull(repo_dir)
        except CliException as e:
            pull_failed = True

    if pull_failed:
        click.secho(f"  - Pull failed; deleting repo")
        shutil.rmtree(repo_dir)

    if not repo_exists or pull_failed:
        click.secho(f"  - Cloning branch '{repository.default_branch}'")
        _git_shallow_clone(
            ssh_key_file, repo_dir, repository.ssh_url, repository.default_branch
        )

        click.secho(f"  - Setting user and email")
    _git_config(repo_dir, "user.name", user.name)
    _git_config(repo_dir, "user.email", user.email)


def prepare_repository(repos_dir: Path, repository: database.Repository, branch: str):
    repo_dir = repos_dir / repository.name

    click.secho(f"Resetting repository '{repository.name}':")

    click.secho(f"  - Resetting changes")
    _git_reset_hard(repo_dir)

    click.secho(f"  - Checking out default branch '{repository.default_branch}'")
    _git_checkout(repo_dir, repository.default_branch)

    click.secho(f"  - Creating or resetting branch '{branch}'")
    _git_branch_checkout_reset(repo_dir, branch)


def run_update_command(
    repos_dir: Path, repository: database.Repository, command: List[str]
):
    repo_dir = repos_dir / repository.name

    click.secho(f"Running update command for repository '{repository.name}':")

    cwd = os.getcwd()
    os.chdir(repo_dir)
    _cmd(command)
    os.chdir(cwd)

    _git_add_all(repo_dir)


def get_diff(repos_dir: Path, repository: database.Repository):
    repo_dir = repos_dir / repository.name
    return _git_staged_diff(repo_dir)


def _cmd(cmd: List[str], env: Optional[Dict[str, str]] = None) -> str:
    try:
        return subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            env=(env or {}),
        ).decode()
    except subprocess.CalledProcessError as exc:
        raise CliException(
            f"Command {' '.join(cmd)} failed (code: {exc.returncode}):\n{exc.output}"
        )


def _git_shallow_clone(
    ssh_key_file: Path, repo_dir: Path, ssh_url: str, branch: str
) -> None:
    git_ssh_command = f"ssh -i {ssh_key_file} -o IdentitiesOnly=yes"
    command = [
        "git",
        "clone",
        "--depth",
        "1",
        ssh_url,
        f"{repo_dir}",
        "--branch",
        branch,
    ]
    _cmd(command, env={"GIT_SSH_COMMAND": git_ssh_command})


def _git_checkout(repo_dir: Path, branch: str) -> None:
    _cmd(["git", "-C", f"{repo_dir}", "checkout", branch])


def _git_branch_checkout_reset(repo_dir: Path, branch: str) -> None:
    _cmd(["git", "-C", f"{repo_dir}", "checkout", "-B", branch])


def _git_reset_hard(repo_dir: Path) -> None:
    _cmd(["git", "-C", f"{repo_dir}", "reset", "--hard"])


def _git_pull(repo_dir: Path) -> None:
    _cmd(["git", "-C", f"{repo_dir}", "pull"])


def _git_config(repo_dir: Path, key: str, value: str) -> None:
    _cmd(["git", "-C", f"{repo_dir}", "config", key, value])


def _git_staged_diff(repo_dir: Path) -> str:
    return _cmd(["git", "-C", f"{repo_dir}", "diff", "--staged"])


def _git_add_all(repo_dir: Path) -> str:
    return _cmd(["git", "-C", f"{repo_dir}", "add", "--all"])
