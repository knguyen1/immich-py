# Copyright 2025 Kyle Nguyen
"""
CLI command modules for the Immich API.

This package contains CLI command modules for interacting with the Immich API.
"""

from .album import album
from .asset import asset
from .job import job
from .server import server
from .tag import tag

__all__ = [
    "album",
    "asset",
    "job",
    "server",
    "tag",
]
