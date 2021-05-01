# Changelog

## _Unreleased_

### Added
-   Added flags `--pull-repos`/`--no-pull-repos` to `test` and `run` (#34)
-   For the `test` command: (#34)
    -   Add flags `--pull-repos`/`--no-pull-repos`, with default to `--no-pull-repos`
    -   Show diff in color
-   For the `run` command: (#34)
    -   Add flags `--pull-repos`/`--no-pull-repos`, with default to `--pull-repos`
    -   Show progress
    -   Don't sleep after pushing the last PR
    -   Set a default `--push_delay`
-   Ask for the API key if not passed via parameters


## 0.2.0

### Added
-   Added `--version` flag (#23)

### Fixed
-   Only show diff if it exists (#22)


## 0.1.2

Initial release.
