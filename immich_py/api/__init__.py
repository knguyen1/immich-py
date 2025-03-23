# Copyright 2025 Kyle Nguyen
"""
API modules for the Immich API.

This package contains API modules for interacting with the Immich API.
"""

from .album import AlbumAPI
from .asset import AssetAPI
from .job import JobAPI
from .server import ServerAPI
from .tag import TagAPI
from .user import UserAPI

__all__ = [
    "AlbumAPI",
    "AssetAPI",
    "JobAPI",
    "ServerAPI",
    "TagAPI",
    "UserAPI",
]
