# Copyright 2025 Kyle Nguyen
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
