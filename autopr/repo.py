import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Dict

import click

from autopr import database
from autopr.util import CliException, error


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
            error(f"Error: {e}")


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
    run_cmd(command)
    os.chdir(cwd)

    _git_add_all(repo_dir)


def get_diff(repos_dir: Path, repository: database.Repository):
    repo_dir = repos_dir / repository.name
    return _git_staged_diff(repo_dir)


def commit_and_push_changes(
    ssh_key_file: Path,
    repos_dir: Path,
    repository: database.Repository,
    branch: str,
    message: str,
):
    click.secho(f"Committing and pushing changes for repository '{repository.name}'")
    repo_dir = repos_dir / repository.name
    _git_commit(repo_dir, message)

    force_push = repository.existing_pr is not None
    _git_push(ssh_key_file, repo_dir, branch, force_push)


def run_cmd(cmd: List[str], env: Optional[Dict[str, str]] = None) -> str:
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


def _get_git_ssh_command(ssh_key_file: Path) -> str:
    return f"ssh -i {ssh_key_file} -o IdentitiesOnly=yes"


def _git_shallow_clone(
    ssh_key_file: Path, repo_dir: Path, ssh_url: str, branch: str
) -> None:
    git_ssh_command = _get_git_ssh_command(ssh_key_file)
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
    run_cmd(command, env={"GIT_SSH_COMMAND": git_ssh_command})


def _git_checkout(repo_dir: Path, branch: str) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "checkout", branch])


def _git_branch_checkout_reset(repo_dir: Path, branch: str) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "checkout", "-B", branch])


def _git_reset_hard(repo_dir: Path) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "reset", "--hard"])


def _git_pull(repo_dir: Path) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "pull"])


def _git_config(repo_dir: Path, key: str, value: str) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "config", key, value])


def _git_staged_diff(repo_dir: Path) -> str:
    return run_cmd(["git", "-C", f"{repo_dir}", "diff", "--staged"])


def _git_add_all(repo_dir: Path) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "add", "--all"])


def _git_commit(repo_dir: Path, message) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "commit", "-m", message])


def _git_push(ssh_key_file: Path, repo_dir: Path, branch: str, force: bool) -> None:
    git_ssh_command = _get_git_ssh_command(ssh_key_file)
    cmd = ["git", "-C", f"{repo_dir}", "push", "-u", "origin", branch]
    if force:
        cmd.append("--force")

    run_cmd(cmd, env={"GIT_SSH_COMMAND": git_ssh_command})
