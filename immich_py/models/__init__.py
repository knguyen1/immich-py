# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Models for the Immich API.

This package contains data models for the Immich API.
"""

from .album import Album, AlbumInfo
from .asset import Asset, AssetType, ExifInfo
from .job import Job, JobCommand, JobName
from .tag import Tag
from .user import User

__all__ = [
    "Album",
    "AlbumInfo",
    "Asset",
    "AssetType",
    "ExifInfo",
    "Job",
    "JobCommand",
    "JobName",
    "Tag",
    "User",
]
