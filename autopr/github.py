import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

from github import Github
from github.PullRequest import PullRequest

from autopr import config, database
from autopr.repo import _git_get_global_config
from autopr.util import CliException


@dataclass
class FilterInfo:
    owner: str
    name: str
    public: bool
    archived: bool


class PullRequestState(Enum):
    OPEN = "open"
    CLOSED = "closed"


def create_github_client(api_key: str) -> Github:
    gh = Github(api_key, per_page=150)
    return gh


def get_user(gh: Github, use_global_git_config: bool = False) -> database.GitUser:
    gh_user = gh.get_user()

    login = gh_user.login  # need to do this first to trigger lazy loading
    name = gh_user.name

    if use_global_git_config:
        primary_email = _git_get_global_config("user.email").strip()
        name = _git_get_global_config("user.name").strip()
        if not name or not primary_email:
            raise CliException(
                "You don't have a globally set Git config. "
                "Please set your config with `git config --global user.email <EMAIL>` or `git config --global user.name <NAME>`"
            )
    else:
        emails = gh_user.get_emails()
        primary_email = None
        for email in emails:
            if email.primary:
                primary_email = email.email
                break

        user_name = name or login
        if user_name is None or primary_email is None:
            raise CliException(
                "Please provide an API key with access to the user name and email address."
            )

    user = database.GitUser(name=name or login, email=primary_email)
    return user


def create_pr(
    gh: Github, repository: database.Repository, pr_template: config.PrTemplate
) -> PullRequest:
    gh_repo = gh.get_repo(repository.full_name)
    pull_request = gh_repo.create_pull(
        pr_template.title,
        pr_template.body,
        repository.default_branch,
        pr_template.branch,
        maintainer_can_modify=True,
    )
    return pull_request


def get_pull_request(gh: Github, repository: database.Repository) -> PullRequest:
    gh_repo = gh.get_repo(repository.full_name)
    return gh_repo.get_pull(repository.existing_pr)


def set_pull_request_state(
    gh: Github, repository: database.Repository, state: PullRequestState
):
    if repository.existing_pr is None:
        raise ValueError(f"No existing pull request for {repository.name}")

    gh_repo = gh.get_repo(repository.full_name)
    pull_request = gh_repo.get_pull(repository.existing_pr)

    if pull_request.merged:
        raise ValueError(
            f"Pull request already merged for {repository.name} ({pull_request.html_url})"
        )

    pull_request.edit(state=state.value)


def gather_repository_list(
    gh: Github, filters: List[config.Filter]
) -> List[database.Repository]:
    all_repositories = _list_all_repositories(gh)
    filtered_repositories = _apply_filters(all_repositories, filters)
    return filtered_repositories


def _list_all_repositories(
    gh: Github,
) -> List[Tuple[FilterInfo, database.Repository]]:
    repository_list = []
    gh_repo_list = gh.get_user().get_repos()
    for gh_repo in gh_repo_list:
        repository = database.Repository(
            owner=gh_repo.owner.login,
            name=gh_repo.name,
            ssh_url=gh_repo.ssh_url,
            default_branch=gh_repo.default_branch,
        )
        filter_info = FilterInfo(
            owner=gh_repo.owner.login,
            name=gh_repo.name,
            public=not gh_repo.private,
            archived=gh_repo.archived,
        )
        repository_list.append((filter_info, repository))

    return repository_list


def _apply_filters(
    all_repositories: List[Tuple[FilterInfo, database.Repository]],
    filters: List[config.Filter],
) -> List[database.Repository]:
    # need to create a dict with (owner, name) as the key, as the type is not hashable
    selected_repositories: Dict[
        Tuple[str, str], Tuple[FilterInfo, database.Repository]
    ] = {}

    if len(filters) == 0:
        return [repository for _filter_info, repository in all_repositories]

    for filter in filters:
        if filter.mode == config.FILTER_MODE_ADD:
            added_repositories = {
                (repository.owner, repository.name): (filter_info, repository)
                for filter_info, repository in all_repositories
                if _filter_matches(filter, filter_info)
            }
            selected_repositories.update(added_repositories)
        elif filter.mode == config.FILTER_MODE_REMOVE:
            selected_repositories = {
                (repository.owner, repository.name): (filter_info, repository)
                for filter_info, repository in selected_repositories.values()
                if not _filter_matches(filter, filter_info)
            }
        else:
            raise CliException(f"Unsupported filter.mode passed: {filter.mode}")

    return [repository for _filter_info, repository in selected_repositories.values()]


def _filter_matches(filter: config.Filter, filter_info: FilterInfo):
    if filter.public is not None:
        if filter_info.public != filter.public:
            return False

    if filter.archived is not None:
        if filter_info.archived != filter.archived:
            return False

    if filter.match_name is not None:
        if all(
            not re.fullmatch(pattern, filter_info.name) for pattern in filter.match_name
        ):
            return False

    if filter.match_owner is not None:
        if not re.fullmatch(filter.match_owner, filter_info.owner):
            return False

    return True
