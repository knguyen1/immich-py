# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Album API for the Immich API.

This module contains the AlbumAPI class for interacting with albums in the Immich API.
"""

from typing import Any

from immich_py.models.album import Album, AlbumInfo


class AlbumAPI:
    """API for interacting with albums in the Immich API."""

    def __init__(self, client):
        """
        Initialize the AlbumAPI.

        Args:
            client: The Immich client.
        """
        self.client = client

    def get_all_albums(self) -> list[Album]:
        """
        Get all albums.

        Returns
        -------
            A list of albums.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_all_albums()
        return [Album.from_dict(album) for album in data]

    def get_album_info(self, album_id: str, without_assets: bool = False) -> AlbumInfo:
        """
        Get information about an album.

        Args:
            album_id: The ID of the album.
            without_assets: Whether to exclude assets from the response.

        Returns
        -------
            Information about the album.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_album_info(album_id, without_assets)
        return AlbumInfo.from_dict(data)

    def add_assets_to_album(
        self, album_id: str, asset_ids: list[str]
    ) -> list[dict[str, Any]]:
        """
        Add assets to an album.

        Args:
            album_id: The ID of the album.
            asset_ids: The IDs of the assets to add.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.add_assets_to_album(album_id, asset_ids)

    def create_album(
        self,
        album_name: str,
        description: str = "",
        asset_ids: list[str] | None = None,
    ) -> Album:
        """
        Create an album.

        Args:
            album_name: The name of the album.
            description: The description of the album.
            asset_ids: The IDs of assets to add to the album.

        Returns
        -------
            The created album.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.create_album(album_name, description, asset_ids)
        return Album.from_dict(data)

    def get_asset_albums(self, asset_id: str) -> list[Album]:
        """
        Get all albums that an asset belongs to.

        Args:
            asset_id: The ID of the asset.

        Returns
        -------
            A list of albums.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_asset_albums(asset_id)
        return [Album.from_dict(album) for album in data]

    def delete_album(self, album_id: str) -> dict[str, Any]:
        """
        Delete an album.

        Args:
            album_id: The ID of the album.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.delete_album(album_id)
