import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from github import Github
from github.GithubException import GithubException, RateLimitExceededException
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
        base=repository.default_branch,
        head=pr_template.branch,
        title=pr_template.title,
        body=pr_template.body,
        maintainer_can_modify=True,
        draft=pr_template.draft,
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


def search_code_for_repositories(
    gh: Github,
    query: str,
    max_repos: int = 100,
    public_filter: Optional[bool] = None,
    archived_filter: Optional[bool] = None,
) -> List[database.Repository]:
    """
    Execute GitHub code search and extract unique repositories.

    Args:
        gh: GitHub client
        query: GitHub code search query string
        max_repos: Maximum number of unique repositories to return
        public_filter: Filter by public/private (None = no filter)
        archived_filter: Filter by archived status (None = no filter)

    Returns:
        List of unique Repository objects found in search results

    Raises:
        CliException: If search fails or rate limit exceeded
    """
    try:
        # Execute code search
        code_results = gh.search_code(query)

        # Extract unique repositories
        seen_repos = set()
        repositories = []

        for code_file in code_results:
            repo = code_file.repository
            repo_key = (repo.owner.login, repo.name)

            # Skip if we've already seen this repo
            if repo_key in seen_repos:
                continue

            # Apply visibility filter
            if public_filter is not None:
                is_public = not repo.private
                if is_public != public_filter:
                    continue

            # Apply archived filter
            if archived_filter is not None:
                if repo.archived != archived_filter:
                    continue

            # Add to results
            seen_repos.add(repo_key)
            repository = database.Repository(
                owner=repo.owner.login,
                name=repo.name,
                ssh_url=repo.ssh_url,
                default_branch=repo.default_branch,
            )
            repositories.append(repository)

            # Check max repos limit
            if len(repositories) >= max_repos:
                break

        return repositories

    except RateLimitExceededException as e:
        rate_limit = gh.get_rate_limit()
        reset_time = rate_limit.search.reset
        raise CliException(
            f"GitHub API rate limit exceeded. "
            f"Resets at {reset_time}. "
            f"Try using a more specific query or wait until rate limit resets."
        ) from e
    except GithubException as e:
        if e.status == 422:
            raise CliException(
                f"Invalid search query syntax: {e.data.get('message', str(e))}"
            ) from e
        raise CliException(f"GitHub API error: {e}") from e


def group_repositories_by_owner(
    repositories: List[database.Repository],
) -> Dict[str, List[database.Repository]]:
    """
    Group repositories by owner for filter generation.

    Args:
        repositories: List of repositories to group

    Returns:
        Dict mapping owner name to list of repositories
    """
    grouped: Dict[str, List[database.Repository]] = {}

    for repo in repositories:
        if repo.owner not in grouped:
            grouped[repo.owner] = []
        grouped[repo.owner].append(repo)

    return grouped


def generate_filters_from_repositories(
    repositories: List[database.Repository],
    public_filter: Optional[bool],
    archived_filter: Optional[bool],
    filter_description: Optional[str] = None,
) -> Tuple[List[config.Filter], str]:
    """
    Generate filter rules from list of repositories.

    Args:
        repositories: List of repositories to convert to filters
        public_filter: Public/private filter value
        archived_filter: Archived filter value
        filter_description: Optional description for YAML comment

    Returns:
        Tuple of (list of Filter objects, comment string for YAML)
    """
    if not repositories:
        return ([], "")

    # Group repos by owner
    grouped = group_repositories_by_owner(repositories)

    # Generate filters (one per owner)
    filters = []
    for owner, owner_repos in grouped.items():
        # Escape special regex characters in repo names for literal matching
        repo_names = [re.escape(repo.name) for repo in owner_repos]

        filter_obj = config.Filter(
            mode=config.FILTER_MODE_ADD,
            match_owner=re.escape(owner),  # Exact match on owner
            match_name=repo_names,
            public=public_filter,
            archived=archived_filter,
        )
        filters.append(filter_obj)

    # Generate comment
    today = datetime.now().strftime("%Y-%m-%d")
    if filter_description:
        comment = f"Added by auto-pr search: {filter_description} ({today})"
    else:
        comment = f"Added by auto-pr search ({today})"
    comment += f"\nFound {len(repositories)} repositories"

    return (filters, comment)
