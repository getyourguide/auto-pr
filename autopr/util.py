DEBUG: bool = True


def set_debug(debug: bool) -> None:
    global DEBUG
    DEBUG = debug


def is_debug() -> bool:
    return DEBUG


class CliException(Exception):
    pass
