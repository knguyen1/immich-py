# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Tag API for the Immich API.

This module contains the TagAPI class for interacting with tags in the Immich API.
"""

from typing import Any

from immich_py.models.tag import Tag


class TagAPI:
    """API for interacting with tags in the Immich API."""

    def __init__(self, client):
        """
        Initialize the TagAPI.

        Args:
            client: The Immich client.
        """
        self.client = client

    def get_all_tags(self) -> list[Tag]:
        """
        Get all tags.

        Returns
        -------
            A list of tags.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_all_tags()
        return [Tag.from_dict(tag) for tag in data]

    def upsert_tags(self, tags: list[str]) -> list[Tag]:
        """
        Create or update tags.

        Args:
            tags: The tags to create or update.

        Returns
        -------
            The created or updated tags.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.upsert_tags(tags)
        return [Tag.from_dict(tag) for tag in data]

    def tag_assets(self, tag_id: str, asset_ids: list[str]) -> list[dict[str, Any]]:
        """
        Tag assets.

        Args:
            tag_id: The ID of the tag.
            asset_ids: The IDs of the assets to tag.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.tag_assets(tag_id, asset_ids)

    def bulk_tag_assets(
        self, tag_ids: list[str], asset_ids: list[str]
    ) -> dict[str, Any]:
        """
        Tag multiple assets with multiple tags.

        Args:
            tag_ids: The IDs of the tags.
            asset_ids: The IDs of the assets to tag.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.bulk_tag_assets(tag_ids, asset_ids)
