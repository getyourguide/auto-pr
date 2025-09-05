from unittest.mock import Mock, patch

from autopr.config import FILTER_MODE_ADD, FILTER_MODE_REMOVE, Filter, PrTemplate
from autopr.database import Repository
from autopr.github import FilterInfo, create_pr, gather_repository_list


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
