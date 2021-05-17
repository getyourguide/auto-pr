# Changelog

## _Unreleased_

### Added
-   `auto-pr test`:
    -   Add flags `--pull-repos`/`--no-pull-repos`, with default to `--no-pull-repos` (#34)
    -   Show diff in color (#34)
-   `auto-pr run`:
    -   Add flags `--pull-repos`/`--no-pull-repos`, with default to `--pull-repos` (#34)
    -   Show progress (#34)
    -   Don't sleep after pushing the last PR (#34)
    -   Set a default `--push_delay` (#34)
-   `auto-pr init`:
    -   Ask for the API key if not passed via parameters (#34)
-   `auto-pr pull`:
    -   Pull repositories in parallel (#36)
    -   Add `-j` flag (#36)
-   Add `auto-pr progress` command (#35)

## 0.2.0

### Added
-   Added `--version` flag (#23)

### Fixed
-   Only show diff if it exists (#22)


## 0.1.2

Initial release.
