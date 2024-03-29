from unittest.mock import Mock, patch

from autopr.config import FILTER_MODE_ADD, FILTER_MODE_REMOVE, Filter
from autopr.database import Repository
from autopr.github import FilterInfo, gather_repository_list


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
