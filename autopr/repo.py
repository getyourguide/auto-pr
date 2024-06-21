import io
import os
import shutil
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path
from typing import IO, Dict, List, Optional

import click
from github import Github

from autopr import config, database, github, util
from autopr.database import Repository
from autopr.util import CliException, error
from autopr.workdir import WorkDir, write_database


def _pull_repository_task(
    user: database.GitUser,
    ssh_key_file: Path,
    repos_dir: Path,
    repository: database.Repository,
    update_repo_if_exists: bool,
) -> None:
    try:
        output_buffer = io.StringIO()

        try:
            pull_repository(
                user,
                ssh_key_file,
                repos_dir,
                repository,
                update_repo_if_exists,
                out=output_buffer,
            )
        except CliException as e:
            error(f"Error: {e}", file=output_buffer)

        click.echo(output_buffer.getvalue(), nl=False)
        output_buffer.close()
    except KeyboardInterrupt:
        pass  # will be handled on main thread


def pull_repositories_parallel(
    user: database.GitUser,
    ssh_key_file: Path,
    repos_dir: Path,
    repositories: List[database.Repository],
    update_repos: bool,
    process_count: int,
):
    parameters = []
    for repository in repositories:
        parameters.append(
            (
                user,
                ssh_key_file,
                repos_dir,
                repository,
                update_repos,
            )
        )

    with Pool(processes=process_count) as pool:
        pool.starmap(_pull_repository_task, parameters)


def pull_repository(
    user: database.GitUser,
    ssh_key_file: Path,
    repos_dir: Path,
    repository: database.Repository,
    update_repo_if_exists: bool,
    out: IO[str] = sys.stdout,
) -> None:
    repo_dir = repos_dir / repository.name
    repo_exists = repo_dir.exists()

    if not update_repo_if_exists and repo_exists:
        click.echo(f"Repository '{repository.name}' already exists", file=out)
        return

    click.echo(f"Pulling repository '{repository.name}':", file=out)

    pull_failed = False
    if repo_exists:
        click.echo(f"  - Checking out branch '{repository.default_branch}'", file=out)
        _git_checkout(repo_dir, repository.default_branch)

        click.echo("  - Pulling latest changes", file=out)
        try:
            _git_pull(repo_dir)
        except CliException as e:
            util.debug(f"Failed to pull: {e}")
            pull_failed = True

    if pull_failed:
        click.echo("  - Pull failed; deleting repo", file=out)
        shutil.rmtree(repo_dir)

    if not repo_exists or pull_failed:
        click.echo(f"  - Cloning branch '{repository.default_branch}'", file=out)
        _git_shallow_clone(
            ssh_key_file, repo_dir, repository.ssh_url, repository.default_branch
        )

        click.echo("  - Setting user and email", file=out)
    _git_config(repo_dir, "user.name", user.name)
    _git_config(repo_dir, "user.email", user.email)


def prepare_repository(repos_dir: Path, repository: database.Repository, branch: str):
    repo_dir = repos_dir / repository.name

    click.echo(f"Resetting repository '{repository.name}':")

    click.echo("  - Resetting changes")
    _git_reset_hard(repo_dir)

    click.echo(f"  - Checking out default branch '{repository.default_branch}'")
    _git_checkout(repo_dir, repository.default_branch)

    click.echo(f"  - Creating or resetting branch '{branch}'")
    _git_branch_checkout_reset(repo_dir, branch)


def run_update_command(
    repos_dir: Path, repository: database.Repository, command: List[str]
):
    repo_dir = repos_dir / repository.name

    click.echo(f"Running update command for repository '{repository.name}':")

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
) -> bool:
    repo_dir = repos_dir / repository.name
    if _git_staged_diff(repo_dir) == "":
        click.echo("  - No changes")
        return False

    click.echo("  - Committing and pushing changes")
    _git_commit(repo_dir, message)

    force_push = repository.existing_pr is not None
    _git_push(ssh_key_file, repo_dir, branch, force_push)

    return True


def run_cmd(cmd: List[str], additional_env: Optional[Dict[str, str]] = None) -> str:
    env = None
    if additional_env:
        env = os.environ.copy()
        env.update(additional_env)

    try:
        util.debug(f"Running: {' '.join(cmd)}")
        return subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            env=env,
        ).decode()
    except subprocess.CalledProcessError as exc:
        raise CliException(
            f"Command {' '.join(cmd)} failed (code: {exc.returncode}):\n{exc.output.decode()}"
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

    run_cmd(command, additional_env={"GIT_SSH_COMMAND": git_ssh_command})


def _git_checkout(repo_dir: Path, branch: str) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "checkout", branch])


def _git_branch_checkout_reset(repo_dir: Path, branch: str) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "checkout", "-B", branch])


def _git_reset_hard(repo_dir: Path) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "reset", "--hard"])


def _git_pull(repo_dir: Path) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "pull", "--depth", "1"])


def _git_config(repo_dir: Path, key: str, value: str) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "config", key, value])


def _git_get_global_config(key: str) -> str:
    return run_cmd(["git", "config", "--global", key])


def _git_staged_diff(repo_dir: Path) -> str:
    return run_cmd(
        ["git", "-c", "color.ui=always", "-C", f"{repo_dir}", "diff", "--staged"]
    )


def _git_add_all(repo_dir: Path) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "add", "--all"])


def _git_commit(repo_dir: Path, message) -> None:
    run_cmd(["git", "-C", f"{repo_dir}", "commit", "-m", message])


def _git_push(ssh_key_file: Path, repo_dir: Path, branch: str, force: bool) -> None:
    git_ssh_command = _get_git_ssh_command(ssh_key_file)
    cmd = ["git", "-C", f"{repo_dir}", "push", "-u", "origin", branch]
    if force:
        cmd.append("--force")

    run_cmd(cmd, additional_env={"GIT_SSH_COMMAND": git_ssh_command})


def reset_and_run_script(
    repository: Repository,
    db: database.Database,
    cfg: config.Config,
    workdir: WorkDir,
    pull_repo: bool,
):
    if db.user is None:
        raise Exception(
            "db.user is None - please report at github.com/getyourguide/auto-pr"
        )

    if pull_repo:
        pull_repository(
            db.user,
            Path(cfg.credentials.ssh_key_file),
            workdir.repos_dir,
            repository,
            True,
        )

    # reset repo and check out branch
    prepare_repository(workdir.repos_dir, repository, cfg.pr.branch)
    run_update_command(workdir.repos_dir, repository, cfg.update_command)


def push_changes(
    repository: Repository,
    db: database.Database,
    cfg: config.Config,
    gh: Github,
    workdir: WorkDir,
) -> bool:
    updated = commit_and_push_changes(
        Path(cfg.credentials.ssh_key_file),
        workdir.repos_dir,
        repository,
        cfg.pr.branch,
        cfg.pr.message,
    )

    if not updated:
        click.secho("  - Nothing updated")
        _mark_repository_as_done(repository, db, workdir)
        return False

    if repository.existing_pr:
        pull_request = github.get_pull_request(gh, repository)
        if (
            not pull_request.merged
            and pull_request.state != github.PullRequestState.CLOSED.value
        ):
            click.secho(f"  - Pull request: {pull_request.html_url}")
            _mark_repository_as_done(repository, db, workdir)
            return False

    pull_request = github.create_pr(gh, repository, cfg.pr)
    repository.existing_pr = pull_request.number

    click.secho(f"  - Pull request: {pull_request.html_url}")

    # persist database to be able to continue from there
    _mark_repository_as_done(repository, db, workdir)
    click.secho(f"Done updating repository '{repository.name}'")

    return True


def _mark_repository_as_done(
    repository: Repository, db: database.Database, workdir: WorkDir
):
    repository.done = True
    write_database(workdir, db)
