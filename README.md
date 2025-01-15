<img width="128" src="https://github.com/getyourguide/auto-pr/raw/master/img/logo.svg" alt="auto-pr logo" />

![CI](https://github.com/getyourguide/auto-pr/workflows/CI/badge.svg)
[![Publish](https://github.com/getyourguide/auto-pr/actions/workflows/publish.yml/badge.svg)](https://github.com/getyourguide/auto-pr/actions/workflows/publish.yml)
[![PyPI version](https://badge.fury.io/py/auto-pr.svg)](https://badge.fury.io/py/auto-pr)
![PyPI downloads](https://img.shields.io/pypi/dm/auto-pr)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# auto-pr

A command line tool to perform bulk updates across multiple GitHub repositories.

## How to install

With [pipx](https://pipxproject.github.io/pipx/) (recommended):

```bash
pipx install auto-pr
```
With pip:

```bash
pip install auto-pr
```

## Usage

[![Usage](https://github.com/getyourguide/auto-pr/raw/master/img/workflow.svg)](https://github.com/getyourguide/auto-pr/raw/master/img/workflow.svg)

### Init

First initialise the project directory by running the `init` command within an empty directory.

```bash
auto-pr init --api-key=<github_token> --ssh-key-file=<path-to-ssh-key>
```

Where `<github_token>` is a GitHub [personal access token](https://github.com/settings/tokens) which has `repo` and `user:user:email` scope.

Next modify the generated `config.yaml` file with your desired configurations.

```yaml
credentials:
  api_key: <github_token>
  ssh_key_file: /path/to/ssh/key/to/push/.ssh/id_rsa
pr:
  body: >
    Body of the PR that will be generated

    Can be multi-line :)
  branch: auto-pr # The branch name to use when making changes
  message: Replace default pipelines with modules # Commit message
  title: 'My awesome change' # Title of the PR
repositories: # Rules that define what repos to update
  - mode: add
    match_owner: <org/user>
update_command:
  - touch
  - my-file
```

If you wish to keep your API Key outside of `config.yaml`, set the env var `APR_API_KEY` with your GitHub Token

### Repositories

You can define the list of repositories to pull and build into the database to update using a list of rules.

-   `mode` - either `add` or `remove` - used to either match or negate
-   `public` (optional) - pull only public or private, leave out for both
-   `archived` (optional) -  archived or non-archived, leave out for both
-   `match_owner` (optional) - the owner or user to pull
-   `match_name` (optional) - a list of regular expressions to match against to pull

The flags of the filter rules are optional not specifying will run the command on all repositories that the token has access too.

### Update Command

This is the list containing the command to be executed along with the arguments passed to it. It will be executed from
the root of each repository that is processed.

If an error occurs during the execution it will be displayed in the output but will not halt the execution.

See [example commands](docs/examples.md#commands)

### Pull

After you have configured the project you can now pull the repositories down that match your rules.

```bash
auto-pr pull
```

This will generate a `db.json` file within your workdir containing a list of mapped repositories and their state.

This command can be run multiple times, if there are new matching repositories found they will be merged into the existing database.

If you would like to use your globally set config, you can pass the option `--use-global-git-config` when pulling the repos. If you had already pulled the repos before this and you would like to change the config for those repos, you would also need to pass `--update-repos` alongside the global-git-config option when pulling.

### Test

Once the `pull` command has finished setting up the work directory you can now run test to check what the changes that will be made by the script will yield.

### Run

When you're confident with the changes output from the `test` command you can finally execute `run`.

```bash
auto-pr run
```

This will perform the changes to a branch on the locally cloned repository and push the branch upstream with the information you provided within `config.yaml`.

By default, the commits will be associated with your primary email and name, which were set on the repo level for those repos when you ran `auto-pr pull`. If you would like to use your global git config for the repos that you already pulled, you need to run pull again with:

```
auto-pr pull --update-repos --use-global-git-config
```

See `--help` for more information about other commands and their  usage.

### Reset
You can reset the list of repos in `db.json` using `auto-pr reset all`, or `auto-pr reset from FILE`

When using `auto-pr reset from FILE`, the list of repos should be provided as a newline separated list of repos like `<owner>/<name>`, e.g:

```text
getyourguide/test
getyourguide/auto-pr
```

## Security

For sensitive security matters please contact [security@getyourguide.com](mailto:security@getyourguide.com).

## Legal

Copyright 2021 GetYourGuide GmbH.

auto-pr is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text.
