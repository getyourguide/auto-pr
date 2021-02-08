import re
from dataclasses import dataclass
from typing import List, Tuple, Dict

from github import Github

from autopr import database, config
from autopr.util import CliException


@dataclass
class FilterInfo:
    owner: str
    name: str
    public: bool
    archived: bool


def create_github_client(api_key: str) -> Github:
    gh = Github(api_key, per_page=150)
    return gh


def get_user(gh: Github) -> database.GitUser:
    gh_user = gh.get_user()

    login = gh_user.login  # need to do this first to trigger lazy loading
    name = gh_user.name

    emails = gh_user.get_emails()
    primary_email = None
    for email in emails:
        if email.get("primary"):
            primary_email = email["email"]

    user_name = name or login
    if user_name is None or primary_email is None:
        raise CliException(
            "Please provide an API key with access to the user name and email address."
        )

    user = database.GitUser(name=name or login, email=primary_email)
    return user


def create_pr(
    gh: Github, repository: database.Repository, pr_template: config.PrTemplate
) -> int:
    gh_repo = gh.get_repo(repository.full_name)
    gh_pr = gh_repo.create_pull(
        pr_template.title,
        pr_template.body,
        repository.default_branch,
        pr_template.branch,
        maintainer_can_modify=True,
    )
    return gh_pr.number


def set_pr_open(gh: Github, repository: database.Repository, open: bool) -> None:
    if repository.existing_pr is None:
        raise ValueError()

    gh_repo = gh.get_repo(repository.name)
    gh_pr = gh_repo.get_pull(repository.existing_pr)

    status = "open" if open else "closed"
    gh_pr.edit(status=status)


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
    pglist = gh.get_user().get_repos()
    for gh_repo in pglist:
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
        if filter.mode == config.FILTER_MODE_REMOVE:
            selected_repositories = {
                (repository.owner, repository.name): (filter_info, repository)
                for filter_info, repository in selected_repositories.values()
                if not _filter_matches(filter, filter_info)
            }

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
            not re.match(pattern, filter_info.name) for pattern in filter.match_name
        ):
            return False

    if filter.match_owner is not None:
        if not re.match(filter.match_owner, filter_info.owner):
            return False

    return True
