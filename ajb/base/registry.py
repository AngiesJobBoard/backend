"""
This registry class is used to register repositories throughout the application
It's main purpose is to be used in the BaseUseCase class so that difference use cases
can call up any given repository without having to import it directly.
"""

import typing as t
from ajb.base.repository import BaseRepository


Repo = t.TypeVar("Repo", bound=BaseRepository)


class RepositoryRegistry(t.Generic[Repo]):
    repositories: dict[str, Repo] = {}

    @classmethod
    def register(cls, repo: t.Any) -> None:
        cls.repositories[repo.collection] = repo

    @classmethod
    def get(cls, collection: str) -> Repo:
        repo = cls.repositories.get(collection)
        if repo is None:
            raise RuntimeError(
                f"Repository for collection {collection} is not registered"
            )
        return repo
