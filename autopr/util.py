import click

DEBUG: bool = True


class CliException(Exception):
    pass


def set_debug(debug: bool) -> None:
    global DEBUG
    DEBUG = debug


def is_debug() -> bool:
    return DEBUG


def debug(msg: str) -> None:
    if not is_debug():
        return

    click.secho(msg)


def warning(msg: str) -> None:
    click.secho(msg, fg="yellow", err=True)


def error(msg: str, **kwargs) -> None:
    click.secho(msg, fg="red", err=True, **kwargs)
