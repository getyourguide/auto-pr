# auto-pr

## Purpose

auto-pr is a command-line tool designed to perform bulk updates across multiple GitHub repositories. It automates the process of cloning repositories, applying changes via custom scripts, and creating pull requests at scale.

## What It Does

auto-pr provides a streamlined workflow for managing updates across an organization's repositories:

1. **Repository Discovery**: Queries GitHub API to gather repositories based on configurable filter rules (owner, name patterns, visibility, archived status)
2. **Local Cloning**: Clones matching repositories to a local working directory
3. **Change Application**: Executes user-defined commands across all repositories
4. **PR Creation**: Automatically creates pull requests with the changes
5. **PR Management**: Provides commands to check status, close, or reopen pull requests in bulk

Key features:
- Parallel repository processing for performance
- Configurable filters for repository selection
- Environment variable expansion in configuration
- Custom working directory support for large repository sets
- Draft PR support
- Reset functionality to re-run operations

## Who Uses It

This tool is primarily used by:
- **Platform/Infrastructure Engineers**: For rolling out dependency updates, configuration changes, or tooling updates across many repositories
- **Developer Productivity Teams**: For standardizing repository configurations, CI/CD pipelines, or development tooling
- **Security Teams**: For applying security patches or updating vulnerable dependencies across the organization

Common use cases:
- Updating dependencies (e.g., Python packages, GitHub Actions versions)
- Standardizing CI/CD configurations
- Rolling out security fixes
- Migrating from one tool/framework to another
- Applying consistent code formatting or linting rules

## Recent Development Activity

### Dependency Management & Security (Jan 2026)
- **Security improvements**: Fixed security issues in dependencies (#291)
- **Dependency updates**: Bumped PyNaCl to 1.6.2, virtualenv to 20.36.1, setuptools to 80.10.1, marshmallow to 4.2.0, coverage to 7.13.1, pre-commit to 4.5.1
- **Python version update**: Raised minimum Python version to 3.10 and updated marshmallow (#279)
- **Build tooling**: Removed pip dependency from publish workflow, fully migrated to uv (#284)

### Major Features (Late 2025)
- **Custom repos directory support** (#278): Added ability to point to an existing directory of cloned repositories instead of cloning fresh copies, useful for organizations with 1000+ repositories
  - New `custom_repos_dir` config option with environment variable expansion
  - CLI flag `--repos-dir` for runtime override
  - Reduces disk space usage and setup time

### Build System Migration
- **Migrated from Poetry to uv**: Complete migration to uv for dependency management and builds
  - Removed `poetry.lock`, added `uv.lock`
  - Updated all CI/CD workflows to use uv
  - Added comprehensive `DEVELOPMENT.md` guide

## Architecture

### Core Modules

- **autopr/__init__.py**: CLI entry point using Click framework, defines all commands (init, pull, test, run, reset, status, close, reopen)
- **autopr/config.py**: Configuration schema and environment variable expansion logic
  - Supports `${VAR_NAME}` syntax for credentials and paths
  - Validates PR templates, filter rules, and update commands
- **autopr/workdir.py**: Working directory management
  - Handles config.yaml and db.json file I/O
  - Manages repos directory with support for custom locations
- **autopr/github.py**: GitHub API interactions
  - Repository listing and filtering
  - Pull request creation and management
- **autopr/repo.py**: Repository operations
  - Git clone/pull operations
  - Command execution and diff generation
  - Parallel processing support
- **autopr/database.py**: State tracking for processed repositories

### Workflow

1. **init**: Creates config.yaml template and empty db.json
2. **pull**: Fetches repo list from GitHub, clones/updates local copies, updates db.json
3. **test**: Runs update command and shows diffs without creating PRs
4. **run**: Executes update command, commits changes, pushes branches, creates PRs
5. **status**: Shows PR state (merged, open, closed, missing)
6. **reset**: Marks repositories as not-done to allow reruns

### Configuration Structure

```yaml
credentials:
  api_key: ${GITHUB_API_KEY}  # Supports env var expansion
  ssh_key_file: ${HOME}/.ssh/id_rsa
pr:
  title: 'PR title'
  branch: auto-pr
  message: Commit message
  body: PR description
  draft: false
repositories:
  - mode: add  # or remove
    match_owner: myorg
    match_name: ['pattern.*']
    public: true
    archived: false
update_command:
  - script.sh
  - --arg
custom_repos_dir: /path/to/repos  # Optional
```

## Testing

- Uses pytest for testing
- Test coverage includes:
  - Configuration parsing and env var expansion
  - Custom repos directory functionality
  - GitHub API interactions
  - Working directory operations
- Pre-commit hooks for code quality (black, ruff, mypy)

## Dependencies

- **Click**: CLI framework
- **PyGithub**: GitHub API client
- **marshmallow**: Schema validation and serialization
- **PyYAML**: YAML configuration parsing
- **GitPython**: Git operations
- **single-source**: Version management

## Development Setup

Requires Python 3.10+, uses uv for dependency management:

```bash
uv sync --extra dev
uv run pytest
uv run auto-pr --help
```

## Publishing

Published to PyPI as `auto-pr`. Workflow publishes on new tags using GitHub Actions and uv build.
