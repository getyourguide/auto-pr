import time
from pathlib import Path
from typing import Optional

import click

from autopr import workdir, config, github, repo, database

__version__ = "0.1.0"

from autopr.util import CliException, set_debug

WORKDIR: workdir.WorkDir


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
    help="The working directory to store configuration and repositories",
)
@click.option(
    "--debug/--no-debug",
    envvar="APR_DEBUG",
    default=False,
    is_flag=True,
    help="Whether to enable debug mode or not",
)
def cli(wd_path: str, debug: bool):
    global WORKDIR
    WORKDIR = workdir.get(wd_path)
    set_debug(debug)


@cli.command()
@click.option(
    "--api-key", envvar="APR_API_KEY", required=True, help="The Github API key to use"
)
@click.option(
    "--ssh-key-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=False, readable=True
    ),
    required=True,
    help="Path to the SSH key to use when pushing to Github",
)
def init(api_key: str, ssh_key_file: str):
    """ Initialise the configuration and database. """
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
    help="Whether to update the locally cloned repoitories to latest changes",
)
def pull(fetch_repo_list: bool, update_repos: bool):
    """ Pull down repositories based on configuration """
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
        repositories = db_old.non_removed_repositories()

    # pull all repositories
    click.secho("Pulling repositories...")
    repo.pull_repositories(
        user,
        Path(cfg.credentials.ssh_key_file),
        WORKDIR.repos_dir,
        repositories,
        update_repos,
    )


@cli.command()
def test():
    """ Check what expected diff will be for command execution. """
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)
    _ensure_set_up(cfg, db)

    for repository in db.non_removed_repositories():
        # reset repo and check out branch
        repo.prepare_repository(WORKDIR.repos_dir, repository, cfg.pr.branch)
        repo.run_update_command(WORKDIR.repos_dir, repository, cfg.update_command)
        diff = repo.get_diff(WORKDIR.repos_dir, repository)

        click.secho(f"Diff for repository '{repository.name}':\n{diff}")
        if not click.confirm("Continue?"):
            return

        click.secho("\n")


@cli.command()
@click.option(
    "--delay",
    type=click.FLOAT,
    default=None,
    help="Delay in seconds between updating repositories",
)
def run(delay: Optional[float]):
    """ Perform execution of update and create pull requests. """
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)
    _ensure_set_up(cfg, db)

    gh = github.create_github_client(cfg.credentials.api_key)

    for repository in db.non_removed_repositories():
        if repository.done:
            continue

        # reset repo and check out branch
        repo.prepare_repository(WORKDIR.repos_dir, repository, cfg.pr.branch)
        repo.run_update_command(WORKDIR.repos_dir, repository, cfg.update_command)
        updated = repo.commit_and_push_changes(
            Path(cfg.credentials.ssh_key_file),
            WORKDIR.repos_dir,
            repository,
            cfg.pr.branch,
            cfg.pr.message,
        )

        if updated and repository.existing_pr is None:
            repository.existing_pr = github.create_pr(gh, repository, cfg.pr)

        repository.done = True
        # persist database to be able to continue from there
        workdir.write_database(WORKDIR, db)
        click.secho(f"Done updating repository '{repository.name}'")

        if delay is not None:
            click.secho(f"Sleeping for {delay} seconds...")
            time.sleep(delay)


@cli.command()
def restart():
    db = workdir.read_database(WORKDIR)
    db.restart()
    workdir.write_database(WORKDIR, db)
    click.secho("Repositories marked as not done")


def _set_all_prs_open(open: bool):
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)
    gh = github.create_github_client(cfg.credentials.api_key)

    for repository in db.repositories:
        if repository.existing_pr is not None:
            github.set_pr_open(gh, repository, open)


@cli.command()
def close():
    _set_all_prs_open(False)


@cli.command()
def reopen():
    _set_all_prs_open(True)
