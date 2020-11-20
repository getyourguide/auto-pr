from dataclasses import dataclass, field
from typing import Optional, List

from marshmallow import post_load
from marshmallow_annotations import AnnotationSchema


@dataclass
class Repository:
    owner: str
    name: str
    ssh_url: str
    default_branch: str
    existing_pr: Optional[int] = None
    removed: bool = False  # true if the repo is not in the config's filters anymore, but still has a PR open
    done: bool = False  # true if a PR has been opened and 'restart' was not called


class RepositorySchema(AnnotationSchema):
    class Meta:
        target = Repository
        register_as_scheme = True

    @post_load
    def build(self, data, **kwargs):
        return Repository(**data)


@dataclass
class GitUser:
    name: str
    email: str


class GitUserSchema(AnnotationSchema):
    class Meta:
        target = GitUser
        register_as_scheme = True

    @post_load
    def build(self, data, **kwargs):
        return GitUser(**data)


@dataclass
class Database:
    user: Optional[GitUser] = None
    repositories: List[Repository] = field(
        default_factory=list
    )  # is equal to assigning []

    def needs_pulling(self) -> bool:
        return self.user is None

    def merge_into(self, from_db: "Database") -> None:
        new_repos = set(
            (repository.owner, repository.name) for repository in self.repositories
        )
        for repository in from_db.repositories:
            if (repository.owner, repository.name) not in new_repos:
                repository.removed = True
                self.repositories.append(repository)

    def restart(self) -> None:
        for repository in self.repositories:
            repository.done = False


class DatabaseSchema(AnnotationSchema):
    class Meta:
        target = Database
        register_as_scheme = True

    @post_load
    def build(self, data, **kwargs):
        return Database(**data)
