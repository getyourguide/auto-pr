from dataclasses import dataclass, field
from typing import Optional, List, Generator

import marshmallow_dataclass


@dataclass
class Repository:
    owner: str
    name: str
    ssh_url: str
    default_branch: str
    existing_pr: Optional[int] = None
    removed: bool = False  # true if the repo is not in the config's filters anymore, but still has a PR open
    done: bool = False  # true if a PR has been opened and 'restart' was not called

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


repository_schema = marshmallow_dataclass.class_schema(Repository)()


@dataclass
class GitUser:
    name: str
    email: str


GIT_USER_SCHEMA = marshmallow_dataclass.class_schema(GitUser)()


@dataclass
class Database:
    user: Optional[GitUser] = None
    repositories: List[Repository] = field(
        default_factory=list
    )  # is equal to assigning []

    def non_removed_repositories(self) -> List[Repository]:
        return [repo for repo in self.repositories if not repo.removed]

    def needs_pulling(self) -> bool:
        return self.user is None

    def merge_into(self, from_db: "Database") -> None:
        existing_repos = set(
            (repository.owner, repository.name) for repository in self.repositories
        )

        for repository in from_db.repositories:
            if (repository.owner, repository.name) not in existing_repos:
                self.repositories.append(repository)

        new_repos = set(
            (repository.owner, repository.name) for repository in from_db.repositories
        )
        for repository in self.repositories:
            if (repository.owner, repository.name) not in new_repos:
                repository.removed = True

    def restart(self) -> None:
        for repository in self.repositories:
            repository.done = False


DATABASE_SCHEMA = marshmallow_dataclass.class_schema(Database)()
