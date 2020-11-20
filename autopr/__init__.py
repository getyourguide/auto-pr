from pathlib import Path

import click

from autopr import workdir, config, github, repo, database

__version__ = "0.1.0"

from autopr.util import CliException, set_debug

WORKDIR: workdir.WorkDir


@click.group("auto-pr")
@click.option(
    "-w",
    "--workdir",
    "wd_path",
    envvar="APR_WORKDIR",
    type=click.Path(
        exists=False, file_okay=False, dir_okay=True, writable=True, readable=True
    ),
)
@click.option("--debug/--no-debug", default=False, is_flag=True)
def cli(wd_path: str, debug: bool):
    global WORKDIR
    WORKDIR = workdir.get(wd_path)
    set_debug(debug)


@cli.command()
@click.option("--api-key", envvar="APR_API_KEY", required=True)
@click.option(
    "--ssh-key-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=False, readable=True
    ),
    required=True,
)
def init(api_key: str, ssh_key_file: str):
    credentials = config.Credentials(api_key=api_key, ssh_key_file=ssh_key_file)
    workdir.init(WORKDIR, credentials)


@cli.command()
@click.option("--fetch-repo-list/--no-fetch-repo-list", default=True, is_flag=True)
@click.option("--update-repos/--no-update-repos", default=False, is_flag=True)
def pull(fetch_repo_list: bool, update_repos: bool):
    cfg = workdir.read_config(WORKDIR)
    gh = github.create_github_client(cfg.credentials.api_key)
    user = gh.get_user(gh)

    click.secho(f"Running under user '{user.name}' with email '{user.email}'")

    # get repositories
    db_old = workdir.read_database(WORKDIR)
    repositories = db_old.repositories

    if fetch_repo_list:
        click.secho("Gathering repository list...")
        repositories = gh.gather_repository_list(gh, cfg.repositories)

        # merge existing database with new one
        click.secho("Updating database")
        db_new = database.Database(user=user, repositories=repositories)
        db_new.merge_into(db_old)
        workdir.write_database(WORKDIR, db_new)
    else:
        click.secho("Not gathering repository list")

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
    cfg = workdir.read_config(WORKDIR)
    db = workdir.read_database(WORKDIR)

    if db.needs_pulling():
        raise CliException("No data found. Please run 'pull' first.")

    if len(cfg.update_command) == 0:
        raise CliException(
            "No update command found. Please set an update command in the config."
        )

    for repository in db.repositories:
        # reset repo and check out branch
        repo.prepare_repository(WORKDIR.repos_dir, repository, cfg.pr.branch)
        repo.run_update_command(WORKDIR.repos_dir, repository, cfg.update_command)
        diff = repo.get_diff(WORKDIR.repos_dir, repository)

        click.secho(f"Diff for repository '{repository.name}:\n{diff}'")
        if not click.confirm("Continue?"):
            return

        click.secho("\n")


@cli.command()
def run():
    pass


@cli.command()
def restart():
    db = workdir.read_database(WORKDIR)
    db.restart()
    workdir.write_database(db)


@cli.command()
def close():
    pass
