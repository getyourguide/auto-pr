from unittest.mock import Mock

from autopr.database import Database
from test.test_utils import get_repository


def test_needs_pulling_empty():
    db = Database()
    assert db.needs_pulling()


def test_needs_pulling_not_empty():
    db = Database(user=Mock())
    assert not db.needs_pulling()


def test_reset_empty():
    db = Database(user=Mock(), repositories=[])
    db.reset()


def test_reset_non_empty():
    repo_first = get_repository("first")
    repo_first.done = True
    repo_second = get_repository("second")

    db = Database(
        user=Mock(),
        repositories=[
            repo_first,
            repo_second,
        ],
    )

    assert db.repositories[0].done
    assert not db.repositories[1].done

    db.reset()

    assert not db.repositories[0].done
    assert not db.repositories[1].done


def test_merge_into():
    db_first = Database(
        user=Mock(),
        repositories=[
            get_repository("first"),
            get_repository("second"),
        ],
    )

    db_second = Database(
        user=Mock(),
        repositories=[
            get_repository("third"),
            get_repository("fourth"),
        ],
    )

    db_first.merge_into(db_second)

    assert len(db_first.repositories) == 4
    assert db_first.repositories[0].name == "first"
    assert db_first.repositories[3].name == "fourth"
