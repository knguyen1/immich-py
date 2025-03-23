# Copyright 2025 Kyle Nguyen
"""
Album models for the Immich API.

This module contains data models for albums in the Immich API.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Album:
    """Album model for the Immich API."""

    id: str = ""
    album_name: str = ""
    description: str = ""
    asset_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Album":
        """
        Create an Album instance from a dictionary.

        Args:
            data: The dictionary containing album information.

        Returns
        -------
            An Album instance.
        """
        return cls(
            id=data.get("id", ""),
            album_name=data.get("albumName", ""),
            description=data.get("description", ""),
            asset_ids=data.get("assetIds", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Album instance to a dictionary.

        Returns
        -------
            A dictionary containing album information.
        """
        return {
            "id": self.id,
            "albumName": self.album_name,
            "description": self.description,
            "assetIds": self.asset_ids,
        }


@dataclass
class AlbumInfo:
    """Album information model for the Immich API."""

    id: str = ""
    album_name: str = ""
    description: str = ""
    shared: bool = False
    assets: list[dict[str, Any]] = field(default_factory=list)
    asset_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlbumInfo":
        """
        Create an AlbumInfo instance from a dictionary.

        Args:
            data: The dictionary containing album information.

        Returns
        -------
            An AlbumInfo instance.
        """
        return cls(
            id=data.get("id", ""),
            album_name=data.get("albumName", ""),
            description=data.get("description", ""),
            shared=data.get("shared", False),
            assets=data.get("assets", []),
            asset_ids=data.get("assetIds", []),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the AlbumInfo instance to a dictionary.

        Returns
        -------
            A dictionary containing album information.
        """
        return {
            "id": self.id,
            "albumName": self.album_name,
            "description": self.description,
            "shared": self.shared,
            "assets": self.assets,
            "assetIds": self.asset_ids,
        }
