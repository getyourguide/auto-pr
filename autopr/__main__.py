from autopr import cli
from autopr.util import CliException, is_debug, error


def main():
    try:
        cli(prog_name="auto-pr")
    except CliException as e:
        error(f"Error: {e}")
        if is_debug():
            raise e
        else:
            exit(1)


if __name__ == "__main__":
    main()
