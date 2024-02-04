"""
A UseCase is responsible for running business actions that interacts with multiple collections.

This baseclass allows individual usecases to get access to repositories without having to
import them directly.

An example of a usecase would be a posting a job, where multiple interactions between 
the company repo, job repo, and approval repos are required.
"""

import typing as t

from ajb.base.registry import RepositoryRegistry
from ajb.base.repository import BaseRepository, ParentRepository
from ajb.base.models import RequestScope
from ajb.base.schema import Collection


class BaseUseCase:
    def __init__(
        self,
        request_scope: RequestScope,
    ):
        self.request_scope = request_scope

    def get_repository(
        self,
        name: Collection,
        request_scope: RequestScope | None = None,
        parent_id: str | None = None,
    ) -> BaseRepository:
        repo_instance: t.Any = RepositoryRegistry.get(name.value)
        if issubclass(repo_instance, ParentRepository):
            return repo_instance(request_scope or self.request_scope)
        return repo_instance(request_scope or self.request_scope, parent_id)

    def get_object(
        self,
        name: Collection,
        object_id: str,
        request_scope: RequestScope | None = None,
        parent_id: str | None = None,
    ):
        return self.get_repository(
            name, request_scope=request_scope, parent_id=parent_id
        ).get(object_id)
