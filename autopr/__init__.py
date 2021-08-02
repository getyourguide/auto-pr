import os
import time
from pathlib import Path
from typing import List, Optional

import click
from single_source import get_version

from autopr import config, database, github, repo, workdir
from autopr.util import CliException, error, is_debug, set_debug

__version__ = get_version(
    "auto-pr",
    Path(__file__).parent.parent,
)

DEFAULT_PUSH_DELAY = 30.0
WORKDIR: workdir.WorkDir


def main():
    try:
        cli()
    except CliException as e:
        error(f"Error: {e}")
        if is_debug():
            raise e
        else:
            exit(1)
    except KeyboardInterrupt:
        error("Aborted.")


def _ensure_set_up(cfg: config.Config, db: database.Database):
    if db.needs_pulling():
        raise CliException("No data found. Please run 'pull' first.")

    if len(cfg.update_command) == 0:
        raise CliException(
            "No update command found. Please set an update command in the config."
        )


@click.group("auto-pr")
@click.option(
    "-w",
    "--workdir",
    "wd_path",
    envvar="APR_WORKDIR",
    type=click.Path(
        exists=False, file_okay=False, dir_okay=True, writable=True, readable=True
    ),
    help="Working directory to store configuration and repositories",
)
@click.option(
    "--debug/--no-debug",
    envvar="APR_DEBUG",
    default=False,
    is_flag=True,
    help="Whether to enable debug mode or not",
)
@click.version_option(__version__, message="%(prog)s: %(version)s")
def cli(wd_path: str, debug: bool):
    global WORKDIR
    WORKDIR = workdir.get(wd_path)
    set_debug(debug)


@cli.command()
@click.option(
    "--api-key",
    envvar="APR_API_KEY",
    required=True,
    prompt="GitHub API key",
    hide_input=True,
    help="The GitHub API key to use, needs `repo` and `user->user:email` scope",
)
@click.option(
    "--ssh-key-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=False, readable=True
    ),
    required=True,
    prompt="Private SSH keyfile",
    help="Path to the SSH key to use when pushing to GitHub",
)
def init(api_key: str, ssh_key_file: str):
    """Initialise configuration and database"""
    credentials = config.Credentials(api_key=api_key, ssh_key_file=ssh_key_file)
    workdir.init(WORKDIR, credentials)


@cli.command()
@click.option(
    "--fetch-repo-list/--no-fetch-repo-list",
    default=True,
    is_flag=True,
    help="Whether to fetch the repo list from github or not",
)
@click.option(
    "--update-repos/--no-update-repos",
    default=False,
    is_flag=True,
    help="Whether to update the locally cloned repositories to latest changes",
)
@click.option(
    "--process-count",
    "-j",
    default=os.cpu_count() or 1,
    type=int,
    help="How many repositories to pull in parallel",
)
def pull(fetch_repo_list: bool, update_repos: bool, process_count: int):
    """Pull down repositories based on configuration"""
    cfg = workdir.read_config(WORKDIR)
    gh = github.create_github_client(cfg.credentials.api_key)
    user = github.get_user(gh)

    click.secho(f"Running under user '{user.name}' with email '{user.email}'")

    # get repositories
    db_old = workdir.read_database(WORKDIR)

    if fetch_repo_list:
        click.secho("Gathering repository list...")
        repositories = github.gather_repository_list(gh, cfg.repositories)

        # merge existing database with new one
        click.secho("Updating database")
        db_new = database.Database(user=user, repositories=repositories)
        db_old.merge_into(db_new)
        workdir.write_database(WORKDIR, db_old)
    else:
        click.secho("Not gathering repository list")
        repositories = db_old.repositories_to_process()

    # pull all repositories
    click.secho("Pulling repositories...")
    repo.pull_repositories_parallel(
        user,
        Path(cfg.credentials.ssh_key_file),
        WORKDIR.repos_dir,
        repositories,
        update_repos,
        process_count,
    )


@cli.command()
@click.option(
    "--pull-repos/--no-pull-repos",
    default=False,
    is_flag=True,
    help="Whether to pull repositories before testing",
)
def test(pull_repos: bool):
    """Check what expected diff will be for command execution"""
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)
    _ensure_set_up(cfg, db)

    for repository in db.repositories_to_process():
        try:
            repo.reset_and_run_script(repository, db, cfg, WORKDIR, pull_repos)
            diff = repo.get_diff(WORKDIR.repos_dir, repository)
            click.secho(f"Diff for repository '{repository.name}':\n{diff}")
        except CliException as e:
            error(f"Error: {e}")

        if not click.confirm("Continue?"):
            return

        click.secho("\n")


@cli.command()
@click.option(
    "--pull-repos/--no-pull-repos",
    default=True,
    is_flag=True,
    help="Whether to pull repositories before running",
)
@click.option(
    "--push-delay",
    type=click.FloatRange(min=0.0, max=None, clamp=True),
    default=DEFAULT_PUSH_DELAY,
    help="Delay in seconds between pushing changes to repositories",
)
def run(pull_repos: bool, push_delay: Optional[float]):
    """Run update logic and create pull requests if changes made"""
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)
    _ensure_set_up(cfg, db)
    gh = github.create_github_client(cfg.credentials.api_key)

    repositories = db.repositories_to_process()

    change_pushed = False
    for i, repository in enumerate(repositories, start=1):
        if change_pushed and push_delay is not None:
            click.secho(f"Sleeping for {push_delay} seconds...")
            time.sleep(push_delay)

        click.secho(
            f"[{i}/{len(repositories)}] Updating '{repository.name}'", bold=True
        )

        try:
            repo.reset_and_run_script(repository, db, cfg, WORKDIR, pull_repos)
            change_pushed = repo.push_changes(repository, db, cfg, gh, WORKDIR)
        except CliException as e:
            error(f"Error: {e}")

    click.secho(f"Done!", bold=True)


@cli.command()
def reset():
    """Mark all mapped repositories as not done"""
    db = workdir.read_database(WORKDIR)
    db.reset()
    workdir.write_database(WORKDIR, db)
    click.secho("Repositories marked as not done")


def _print_repository_list(
    title: str, repositories: List[database.Repository], total: int
):
    click.secho(f"{title} [{len(repositories)}/{total}]:", bold=True)
    for repository in repositories:
        link_str = ""
        if repository.existing_pr is not None:
            link_str = (
                f": https://github.com/{repository.full_name}"
                f"/pull/{repository.existing_pr}"
            )
        click.secho(f"-   {repository.name}{link_str}")


@cli.command()
def status():
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)
    gh = github.create_github_client(cfg.credentials.api_key)

    click.secho("Collecting data...")

    if len(db.repositories) == 0:
        error("No repositories in database.")
        return

    pr_missing = []
    pr_merged = []
    pr_open = []
    pr_closed = []

    # group repositories by PR state
    for repository in db.repositories:
        if repository.existing_pr is None:
            pr_missing.append(repository)
            continue

        pull_request = github.get_pull_request(gh, repository)
        if pull_request.merged:
            pr_merged.append(repository)
        elif pull_request.state == github.PullRequestState.OPEN.value:
            pr_open.append(repository)
        elif pull_request.state == github.PullRequestState.CLOSED.value:
            pr_closed.append(repository)

    total = len(db.repositories)
    _print_repository_list("Merged PRs", pr_merged, total)
    _print_repository_list("Closed PRs", pr_closed, total)
    _print_repository_list("Open PRs", pr_open, total)
    _print_repository_list("Missing PRs", pr_missing, total)


def _set_all_pull_requests_state(state: github.PullRequestState):
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)
    gh = github.create_github_client(cfg.credentials.api_key)

    for repository in db.repositories:
        if repository.existing_pr is not None:
            try:
                github.set_pull_request_state(gh, repository, state)
                click.secho(
                    f"Updated {repository.name} pull request state to {state.value}"
                )
            except ValueError as e:
                click.secho(f"{e}")


@cli.command()
def close():
    """Close all open pull requests"""
    _set_all_pull_requests_state(github.PullRequestState.CLOSED)
    click.secho("Finished closing all open pull requests")


@cli.command()
def reopen():
    """Reopen all un-merged pull requests"""
    _set_all_pull_requests_state(github.PullRequestState.OPEN)
    click.secho("Finished reopening all closed unmerged pull requests")


if __name__ == "__main__":
    main()
