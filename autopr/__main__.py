import click

from autopr import cli
from autopr.util import CliException, is_debug, error

if __name__ == "__main__":
    try:
        cli()
    except CliException as e:
        error(f"Error: {e}")
        if is_debug():
            raise e
        else:
            exit(1)
