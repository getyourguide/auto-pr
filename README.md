# auto-pr

![CI](https://github.com/getyourguide/auto-pr/workflows/CI/badge.svg)

A command line tool to perform bulk updates across multiple repositories.

## How to install

```bash
pip install auto-pr
```

## Usage

### Init

First you need to initialise the project folder so run the `init` within a new folder.

```bash
auto-pr init --api-key=<github_token> --ssh-key-file=<path-to-ssh-key>
```

Where `<github_token>` is a Github personal token which has `repo` and `user:user:email` scope.

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
  title: '[XXX-YYY] My awesome change' # Title of the PR
repositories: # Rules that define what repos to update
  - mode: add
    match_owner: <org/user>
update_command:
  - touch
  - my-file
```

### Repositories

You can define the list of repositories to pull and build into the database to update using a list of rules.

- `mode` - either `add` or `remove` - used to either match or negate
- `public` (optional) - pull only public or private, leave out for both
- `archived` (optional) -  archived or non-archived, leave out for both
- `match_owner` (optional) - the owner or user to pull
- `match_name` (optional) - a list of regular expressions to match against to pull

###  Update Command

TBD

### Pull

Once you have configured the project you can now pull the repositories down that match your configuration.

```bash
auto-pr pull
```

### Test

Once the `pull` command has finished building the repo structure and DB containing the state you can now run test to check what the changes that will be made by the script will yield.

### Run

Once you're confident with the changes output from the `test` command you can finally excute `run`

```bash
auto-pr run
```

This will perform the changes to a branch on the locally cloned repo and push the branch upstream with the information you provided within `config.yaml`.

## Security

For sensitive security matters please contact [security@getyourguide.com](mailto:security@getyourguide.com).

## Legal

Copyright 2020 GetYourGuide GmbH.

auto-pr is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text.
