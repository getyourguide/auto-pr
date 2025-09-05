# Changelog

## 1.1.0

- Add `draft` PR property to allows you to create draft PRs instead of regular PRs

## 1.0.11

- Fix Github API call error

## 1.0.10

- Fix Github API auth issue by upgrading `PyGithub` lib

## 1.0.9

- Add `--api-key` flag to `auto-pr run` command
  - Allows you to pass the API key as a flag (or as the env APR_API_KEY variable) instead of storing
  it in the configuration file

## 1.0.7
- Add `--exclude-missing` when running `auto-pr status`
  - Allows you to remove the `Missing PRs` section from the output

## 1.0.6
- Add `--use-global-git-config` when running `auto-pr pull`
  - Allows you to use the globally set git config in your device instead of using the authenticated Github user's primary email

## 1.0.4
- Extend `auto-pr reset` to `auto-pr reset all` and `auto-pr reset from FILE`
  - `all` resets everything
  - `from FILE` resets just repositories listed in the input file

## 1.0.2

### Fixed
-   Fix for user env into sub-processes (3b597971)
-   Pin top-level dependencies (#54)

## 1.0.1

### Fixed
-   Correct debug log on repository pull (#44)
-   Don't copy user env into sub-processes (#44)
-   Fix email access from GitHub API (#51)

### Updated
-   Improved error output on command failures (#44)
-   Improve DB access for repositories to process (#48)

### Chore
-   Migrated from pipenv to poetry (#49)
-   Added isort pre-commit hook (#50)

## 1.0.0

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
