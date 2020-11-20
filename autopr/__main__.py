import click

from autopr import cli
from autopr.util import CliException, is_debug

if __name__ == "__main__":
    try:
        cli()
    except CliException as e:
        click.echo(f"Error: {e}", err=True)
        if is_debug():
            raise e
        else:
            exit(1)
