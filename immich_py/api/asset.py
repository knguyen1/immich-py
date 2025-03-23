# Copyright 2025 Kyle Nguyen
"""
Asset API for the Immich API.

This module contains the AssetAPI class for interacting with assets in the Immich API.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from immich_py.models.asset import Asset


class AssetAPI:
    """API for interacting with assets in the Immich API."""

    def __init__(self, client):
        """
        Initialize the AssetAPI.

        Args:
            client: The Immich client.
        """
        self.client = client

    def get_asset_info(self, asset_id: str) -> Asset:
        """
        Get information about an asset.

        Args:
            asset_id: The ID of the asset.

        Returns
        -------
            Information about the asset.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_asset_info(asset_id)
        return Asset.from_dict(data)

    def download_asset(self, asset_id: str) -> bytes:
        """
        Download an asset.

        Args:
            asset_id: The ID of the asset.

        Returns
        -------
            The asset data.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.download_asset(asset_id)

    def update_asset(
        self,
        asset_id: str,
        *,
        is_archived: bool | None = None,
        is_favorite: bool | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        description: str | None = None,
        rating: int | None = None,
        date_time_original: datetime | None = None,
    ) -> Asset:
        """
        Update an asset.

        Args:
            asset_id: The ID of the asset.
            is_archived: Whether the asset is archived.
            is_favorite: Whether the asset is a favorite.
            latitude: The latitude of the asset.
            longitude: The longitude of the asset.
            description: The description of the asset.
            rating: The rating of the asset.
            date_time_original: The original date and time of the asset.

        Returns
        -------
            The updated asset information.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        fields = {}
        if is_archived is not None:
            fields["isArchived"] = is_archived
        if is_favorite is not None:
            fields["isFavorite"] = is_favorite
        if latitude is not None:
            fields["latitude"] = latitude
        if longitude is not None:
            fields["longitude"] = longitude
        if description is not None:
            fields["description"] = description
        if rating is not None:
            fields["rating"] = rating
        if date_time_original is not None:
            fields["dateTimeOriginal"] = date_time_original.isoformat()

        data = self.client.update_asset(asset_id, **fields)
        return Asset.from_dict(data)

    def delete_assets(
        self, asset_ids: list[str], force_delete: bool = False
    ) -> dict[str, Any]:
        """
        Delete assets.

        Args:
            asset_ids: The IDs of the assets to delete.
            force_delete: If True, permanently delete the assets.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.delete_assets(asset_ids, force_delete)

    def update_assets(
        self,
        asset_ids: list[str],
        *,
        is_archived: bool = False,
        is_favorite: bool = False,
        latitude: float = 0.0,
        longitude: float = 0.0,
        remove_parent: bool = False,
        stack_parent_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Update multiple assets.

        Args:
            asset_ids: The IDs of the assets to update.
            is_archived: Whether the assets are archived.
            is_favorite: Whether the assets are favorites.
            latitude: The latitude of the assets.
            longitude: The longitude of the assets.
            remove_parent: Whether to remove the parent stack.
            stack_parent_id: The ID of the parent stack.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.update_assets(
            asset_ids,
            is_archived=is_archived,
            is_favorite=is_favorite,
            latitude=latitude,
            longitude=longitude,
            remove_parent=remove_parent,
            stack_parent_id=stack_parent_id,
        )

    def upload_asset(
        self,
        file_path: str | Path,
        *,
        device_asset_id: str | None = None,
        device_id: str | None = None,
        is_favorite: bool = False,
        is_archived: bool = False,
        file_created_at: datetime | None = None,
        file_modified_at: datetime | None = None,
        duration: str = "00:00:00.000000",
        is_read_only: bool = False,
        sidecar_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Upload an asset.

        Args:
            file_path: The path to the file to upload.
            device_asset_id: The device asset ID.
            device_id: The device ID.
            is_favorite: Whether the asset is a favorite.
            is_archived: Whether the asset is archived.
            file_created_at: The creation date of the file.
            file_modified_at: The modification date of the file.
            duration: The duration of the asset (for videos).
            is_read_only: Whether the asset is read-only.
            sidecar_path: The path to a sidecar file to upload.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.upload_asset(
            file_path,
            device_asset_id=device_asset_id,
            device_id=device_id,
            is_favorite=is_favorite,
            is_archived=is_archived,
            file_created_at=file_created_at,
            file_modified_at=file_modified_at,
            duration=duration,
            is_read_only=is_read_only,
            sidecar_path=sidecar_path,
        )

    def replace_asset(
        self,
        asset_id: str,
        file_path: str | Path,
        *,
        sidecar_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Replace an asset.

        Args:
            asset_id: The ID of the asset to replace.
            file_path: The path to the file to upload.
            sidecar_path: The path to a sidecar file to upload.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.replace_asset(
            asset_id,
            file_path,
            sidecar_path=sidecar_path,
        )

    def get_all_assets(self) -> list[Asset]:
        """
        Get all assets.

        Returns
        -------
            A list of assets.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_all_assets()
        return [Asset.from_dict(asset) for asset in data]

    def search_assets(
        self,
        *,
        page: int = 1,
        page_size: int = 1000,
        with_exif: bool = True,
        is_visible: bool = True,
        with_deleted: bool = False,
        with_archived: bool = False,
        taken_before: str | None = None,
        taken_after: str | None = None,
        model: str | None = None,
        make: str | None = None,
        checksum: str | None = None,
        original_file_name: str | None = None,
    ) -> list[Asset]:
        """
        Search for assets.

        Args:
            page: The page number.
            page_size: The number of assets per page.
            with_exif: Whether to include EXIF data.
            is_visible: Whether to include visible assets.
            with_deleted: Whether to include deleted assets.
            with_archived: Whether to include archived assets.
            taken_before: Only include assets taken before this date.
            taken_after: Only include assets taken after this date.
            model: Only include assets with this camera model.
            make: Only include assets with this camera make.
            checksum: Only include assets with this checksum.
            original_file_name: Only include assets with this original file name.

        Returns
        -------
            A list of assets.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.search_assets(
            page=page,
            page_size=page_size,
            with_exif=with_exif,
            is_visible=is_visible,
            with_deleted=with_deleted,
            with_archived=with_archived,
            taken_before=taken_before,
            taken_after=taken_after,
            model=model,
            make=make,
            checksum=checksum,
            original_file_name=original_file_name,
        )
        return [Asset.from_dict(asset) for asset in data]

    def get_assets_by_hash(self, checksum: str) -> list[Asset]:
        """
        Get assets by hash.

        Args:
            checksum: The checksum to search for.

        Returns
        -------
            A list of assets with the given checksum.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_assets_by_hash(checksum)
        return [Asset.from_dict(asset) for asset in data]

    def get_assets_by_name(self, name: str) -> list[Asset]:
        """
        Get assets by original file name.

        Args:
            name: The original file name to search for.

        Returns
        -------
            A list of assets with the given original file name.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_assets_by_name(name)
        return [Asset.from_dict(asset) for asset in data]
