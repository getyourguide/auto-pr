from unittest.mock import Mock, patch

from autopr.config import FILTER_MODE_ADD, FILTER_MODE_REMOVE, Filter, PrTemplate
from autopr.database import Repository
from autopr.github import (
    FilterInfo,
    create_pr,
    gather_repository_list,
    generate_filters_from_repositories,
    group_repositories_by_owner,
)


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_no_filters(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="owner",
            name="name",
            public=True,
            archived=False,
        ),
    ]
    result = gather_repository_list(Mock(), [])

    assert len(result) == 1
    assert result[0].owner == "owner"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_public(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="owner",
            name="public",
            public=True,
            archived=False,
        ),
        _get_fake_repository_tuple(
            owner="owner",
            name="private",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(), filters=[Filter(FILTER_MODE_ADD, public=False)]
    )

    assert len(result) == 1
    assert result[0].name == "private"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_public_remove(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="owner",
            name="public",
            public=True,
            archived=False,
        ),
        _get_fake_repository_tuple(
            owner="owner",
            name="private",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(),
        filters=[
            Filter(FILTER_MODE_ADD, match_owner=".+"),
            Filter(FILTER_MODE_REMOVE, public=False),
        ],
    )

    assert len(result) == 1
    assert result[0].name == "public"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_archived(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="owner",
            name="archived",
            public=True,
            archived=True,
        ),
        _get_fake_repository_tuple(
            owner="owner",
            name="non-archived",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(), filters=[Filter(FILTER_MODE_ADD, archived=True)]
    )

    assert len(result) == 1
    assert result[0].name == "archived"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_archived_remove(
    mock_list_all_repositories: Mock,
):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="owner",
            name="archived",
            public=True,
            archived=True,
        ),
        _get_fake_repository_tuple(
            owner="owner",
            name="non-archived",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(),
        filters=[
            Filter(FILTER_MODE_ADD, match_owner=".+"),
            Filter(FILTER_MODE_REMOVE, archived=True),
        ],
    )

    assert len(result) == 1
    assert result[0].name == "non-archived"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_name(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="owner",
            name="good-repo",
            public=True,
            archived=True,
        ),
        _get_fake_repository_tuple(
            owner="owner",
            name="bad-repo",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(), filters=[Filter(FILTER_MODE_ADD, match_name=["^good.*"])]
    )

    assert len(result) == 1
    assert result[0].name == "good-repo"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_name_remove(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="owner",
            name="good-repo",
            public=True,
            archived=True,
        ),
        _get_fake_repository_tuple(
            owner="owner",
            name="bad-repo",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(),
        filters=[
            Filter(FILTER_MODE_ADD, match_owner=".+"),
            Filter(FILTER_MODE_REMOVE, match_name=["^bad.*"]),
        ],
    )

    assert len(result) == 1
    assert result[0].name == "good-repo"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_owner(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="fred",
            name="fred-repo",
            public=True,
            archived=True,
        ),
        _get_fake_repository_tuple(
            owner="boris",
            name="boris-repo",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(), filters=[Filter(FILTER_MODE_ADD, match_owner="^fred*")]
    )

    assert len(result) == 1
    assert result[0].name == "fred-repo"


@patch("autopr.github._list_all_repositories")
def test_gather_repository_list_filter_owner_remove(mock_list_all_repositories: Mock):
    mock_list_all_repositories.return_value = [
        _get_fake_repository_tuple(
            owner="fred",
            name="fred-repo",
            public=True,
            archived=True,
        ),
        _get_fake_repository_tuple(
            owner="boris",
            name="boris-repo",
            public=False,
            archived=False,
        ),
    ]

    result = gather_repository_list(
        Mock(),
        filters=[
            Filter(FILTER_MODE_ADD, match_owner=".+"),
            Filter(FILTER_MODE_REMOVE, match_owner="^fred*"),
        ],
    )

    assert len(result) == 1
    assert result[0].name == "boris-repo"


def test_create_pr_with_draft_false():
    """Test create_pr function with draft=False"""
    # Setup mocks
    mock_gh = Mock()
    mock_gh_repo = Mock()
    mock_pull_request = Mock()

    mock_gh.get_repo.return_value = mock_gh_repo
    mock_gh_repo.create_pull.return_value = mock_pull_request

    # Test data
    repository = Repository(
        owner="test-owner",
        name="test-repo",
        ssh_url="git@github.com:test-owner/test-repo.git",
        default_branch="main",
    )

    pr_template = PrTemplate(
        title="Test PR",
        message="Test message",
        branch="test-branch",
        body="Test body",
        draft=False,
    )

    # Execute
    result = create_pr(mock_gh, repository, pr_template)

    # Verify
    mock_gh.get_repo.assert_called_once_with("test-owner/test-repo")
    mock_gh_repo.create_pull.assert_called_once_with(
        base="main",
        head="test-branch",
        title="Test PR",
        body="Test body",
        maintainer_can_modify=True,
        draft=False,
    )
    assert result == mock_pull_request


def test_create_pr_with_draft_true():
    """Test create_pr function with draft=True"""
    # Setup mocks
    mock_gh = Mock()
    mock_gh_repo = Mock()
    mock_pull_request = Mock()

    mock_gh.get_repo.return_value = mock_gh_repo
    mock_gh_repo.create_pull.return_value = mock_pull_request

    # Test data
    repository = Repository(
        owner="test-owner",
        name="test-repo",
        ssh_url="git@github.com:test-owner/test-repo.git",
        default_branch="master",
    )

    pr_template = PrTemplate(
        title="Draft PR",
        message="Draft message",
        branch="draft-branch",
        body="Draft body",
        draft=True,
    )

    # Execute
    result = create_pr(mock_gh, repository, pr_template)

    # Verify
    mock_gh.get_repo.assert_called_once_with("test-owner/test-repo")
    mock_gh_repo.create_pull.assert_called_once_with(
        base="master",
        head="draft-branch",
        title="Draft PR",
        body="Draft body",
        maintainer_can_modify=True,
        draft=True,
    )
    assert result == mock_pull_request


def test_create_pr_with_default_template():
    """Test create_pr function with default PrTemplate (draft=False by default)"""
    # Setup mocks
    mock_gh = Mock()
    mock_gh_repo = Mock()
    mock_pull_request = Mock()

    mock_gh.get_repo.return_value = mock_gh_repo
    mock_gh_repo.create_pull.return_value = mock_pull_request

    # Test data
    repository = Repository(
        owner="test-owner",
        name="test-repo",
        ssh_url="git@github.com:test-owner/test-repo.git",
        default_branch="develop",
    )

    pr_template = PrTemplate()  # Using defaults

    # Execute
    result = create_pr(mock_gh, repository, pr_template)

    # Verify
    mock_gh.get_repo.assert_called_once_with("test-owner/test-repo")
    mock_gh_repo.create_pull.assert_called_once_with(
        base="develop",
        head="autopr",  # default branch
        title="Automatically generated PR",  # default title
        body="This is an automatically generated PR",  # default body
        maintainer_can_modify=True,
        draft=False,  # default draft value
    )
    assert result == mock_pull_request


def _get_fake_repository_tuple(
    owner: str,
    name: str,
    public: bool,
    archived: bool,
    ssh_url: str = "git@gitgitgit.com/git/repo",
    default_branch: str = "master",
):
    filter_info = FilterInfo(owner=owner, name=name, public=public, archived=archived)
    repository = Repository(
        owner=owner, name=name, ssh_url=ssh_url, default_branch=default_branch
    )

    return filter_info, repository


def test_group_repositories_by_owner():
    """Test grouping repositories by owner"""
    repos = [
        Repository(
            owner="org1", name="repo1", ssh_url="git@github.com", default_branch="main"
        ),
        Repository(
            owner="org1", name="repo2", ssh_url="git@github.com", default_branch="main"
        ),
        Repository(
            owner="org2", name="repo3", ssh_url="git@github.com", default_branch="main"
        ),
    ]

    grouped = group_repositories_by_owner(repos)

    assert len(grouped) == 2
    assert len(grouped["org1"]) == 2
    assert len(grouped["org2"]) == 1
    assert grouped["org1"][0].name == "repo1"
    assert grouped["org1"][1].name == "repo2"
    assert grouped["org2"][0].name == "repo3"


def test_group_repositories_by_owner_empty():
    """Test grouping empty list of repositories"""
    grouped = group_repositories_by_owner([])
    assert grouped == {}


def test_generate_filters_from_repositories_single_owner():
    """Test generating filters from repositories with a single owner"""
    repos = [
        Repository(
            owner="myorg",
            name="repo1",
            ssh_url="git@github.com",
            default_branch="main",
        ),
        Repository(
            owner="myorg",
            name="repo2",
            ssh_url="git@github.com",
            default_branch="main",
        ),
    ]

    filters, comment = generate_filters_from_repositories(
        repos, public_filter=True, archived_filter=False, filter_description="Test"
    )

    assert len(filters) == 1
    assert filters[0].mode == FILTER_MODE_ADD
    assert filters[0].match_owner == "myorg"  # Escaped, but no special chars
    assert len(filters[0].match_name) == 2
    assert "repo1" in filters[0].match_name
    assert "repo2" in filters[0].match_name
    assert filters[0].public is True
    assert filters[0].archived is False
    assert "Test" in comment
    assert "2 repositories" in comment


def test_generate_filters_from_repositories_multiple_owners():
    """Test generating filters from repositories with multiple owners"""
    repos = [
        Repository(
            owner="org1", name="repo1", ssh_url="git@github.com", default_branch="main"
        ),
        Repository(
            owner="org2", name="repo2", ssh_url="git@github.com", default_branch="main"
        ),
    ]

    filters, comment = generate_filters_from_repositories(
        repos, public_filter=None, archived_filter=None
    )

    assert len(filters) == 2
    # Find filters by owner
    org1_filter = next(f for f in filters if f.match_owner == "org1")
    org2_filter = next(f for f in filters if f.match_owner == "org2")

    assert org1_filter.mode == FILTER_MODE_ADD
    assert "repo1" in org1_filter.match_name
    assert org2_filter.mode == FILTER_MODE_ADD
    assert "repo2" in org2_filter.match_name


def test_generate_filters_from_repositories_empty():
    """Test generating filters from empty repository list"""
    filters, comment = generate_filters_from_repositories(
        [], public_filter=None, archived_filter=None
    )

    assert filters == []
    assert comment == ""


def test_generate_filters_escapes_special_chars():
    """Test that special regex characters in repo names are escaped"""
    repos = [
        Repository(
            owner="myorg",
            name="test.com",
            ssh_url="git@github.com",
            default_branch="main",
        ),
        Repository(
            owner="myorg",
            name="test[1]",
            ssh_url="git@github.com",
            default_branch="main",
        ),
    ]

    filters, _ = generate_filters_from_repositories(
        repos, public_filter=None, archived_filter=None
    )

    assert len(filters) == 1
    # Special chars should be escaped
    assert "test\\.com" in filters[0].match_name
    assert "test\\[1\\]" in filters[0].match_name
