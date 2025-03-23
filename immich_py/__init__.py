# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Immich Python Client.

This package provides a client for interacting with the Immich API.
"""

from .api.album import AlbumAPI
from .api.asset import AssetAPI
from .api.client import ImmichClient, ImmichClientError
from .api.job import JobAPI
from .api.server import ServerAPI
from .api.tag import TagAPI
from .api.user import UserAPI
from .models.album import Album, AlbumInfo
from .models.asset import Asset, AssetType, ExifInfo
from .models.job import Job, JobCommand, JobName
from .models.tag import Tag
from .models.user import User

__version__ = "0.1.0"

__all__ = [
    "Album",
    "AlbumAPI",
    "AlbumInfo",
    "Asset",
    "AssetAPI",
    "AssetType",
    "ExifInfo",
    "ImmichClient",
    "ImmichClientError",
    "Job",
    "JobAPI",
    "JobCommand",
    "JobName",
    "ServerAPI",
    "Tag",
    "TagAPI",
    "User",
    "UserAPI",
]
