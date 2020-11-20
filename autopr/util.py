import click

DEBUG: bool = True


class CliException(Exception):
    pass


def warning(msg: str) -> None:
    click.secho(msg, fg="yellow", err=True)


def error(msg: str) -> None:
    click.secho(msg, fg="red", err=True)


def set_debug(debug: bool) -> None:
    global DEBUG
    DEBUG = debug


def is_debug() -> bool:
    return DEBUG
