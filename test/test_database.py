import unittest
from unittest.mock import Mock
from autopr.database import Database
from test.test_utils import get_repository


class DatabaseTest(unittest.TestCase):
    def test_needs_pulling_empty(self):
        db = Database()
        self.assertTrue(db.needs_pulling())

    def test_needs_pulling_not_empty(self):
        db = Database(user=Mock())
        self.assertFalse(db.needs_pulling())

    def test_reset_empty(self):
        db = Database(user=Mock(), repositories=[])
        db.reset()
        self.assertEqual(0, len(db.repositories))

    def test_reset_non_empty(self):
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

        self.assertTrue(db.repositories[0].done)
        self.assertFalse(db.repositories[1].done)

        db.reset()

        self.assertFalse(db.repositories[0].done)
        self.assertFalse(db.repositories[1].done)

    def test_merge_into(self):
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

        self.assertEqual(4, len(db_first.repositories))
        self.assertEqual("first", db_first.repositories[0].name)
        self.assertEqual("fourth", db_first.repositories[3].name)

    def test_repositories_to_process(self):
        db = Database(
            user=Mock(),
            repositories=[
                get_repository("removed", removed=True),
                get_repository("done", done=True),
                get_repository("non-removed"),
            ],
        )

        repositories = db.repositories_to_process()
        self.assertEqual(1, len(repositories))
        self.assertEqual("non-removed", repositories[0].name)


if __name__ == "__main__":
    unittest.main()
