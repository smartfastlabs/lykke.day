"""Dependency injection modules for routers."""

from .container import RepositoryContainer, get_repository_container

__all__ = ["RepositoryContainer", "get_repository_container"]
