from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional

import marshmallow_dataclass


@dataclass
class Repository:
    owner: str
    name: str
    ssh_url: str
    default_branch: str
    existing_pr: Optional[int] = None
    removed: bool = False  # true if the repo is not in the config's filters anymore, but still has a PR open
    done: bool = False  # true if a PR has been opened and 'reset' was not called

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

    def repositories_to_process(self) -> List[Repository]:
        """Get all repositories filtering out done and removed"""
        return [
            repo for repo in self.repositories if not repo.removed and not repo.done
        ]

    def needs_pulling(self) -> bool:
        return self.user is None

    def merge_into(self, from_db: "Database") -> None:
        self.user = from_db.user

        # add repositories that are new
        existing_repos = set(
            (repository.owner, repository.name) for repository in self.repositories
        )
        for repository in from_db.repositories:
            if (repository.owner, repository.name) not in existing_repos:
                self.repositories.append(repository)

        # mark repositories that are gone as removed
        new_repos = set(
            (repository.owner, repository.name) for repository in from_db.repositories
        )
        for repository in self.repositories:
            if (repository.owner, repository.name) not in new_repos:
                repository.removed = True

    def reset_from(self, selected_repos: Iterator[str]):
        resets: Dict[str, bool] = {name: False for name in selected_repos}
        for repository in self.repositories:
            repo_id = f"{repository.owner}/{repository.name}"
            if repo_id in resets:
                print(f"{repo_id} was reset")
                resets[repo_id] = True
                repository.done = False

        for name, done in resets.items():
            if not done:
                print(f"{name} was not in the database")

    def reset_all(self) -> None:
        for repository in self.repositories:
            repository.done = False


DATABASE_SCHEMA = marshmallow_dataclass.class_schema(Database)()
