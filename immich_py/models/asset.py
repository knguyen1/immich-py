# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Asset models for the Immich API.

This module contains data models for assets in the Immich API.
"""

import contextlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AssetType(str, Enum):
    """Asset type enumeration."""

    IMAGE = "image"
    VIDEO = "video"
    UNKNOWN = "unknown"


@dataclass
class ExifInfo:
    """EXIF information for an asset."""

    make: str = ""
    model: str = ""
    exif_image_width: int = 0
    exif_image_height: int = 0
    file_size_in_byte: int = 0
    orientation: str = ""
    date_time_original: datetime | None = None
    time_zone: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExifInfo":
        """
        Create an ExifInfo instance from a dictionary.

        Args:
            data: The dictionary containing EXIF information.

        Returns
        -------
            An ExifInfo instance.
        """
        date_time_original = None
        if data.get("dateTimeOriginal"):
            with contextlib.suppress(ValueError, TypeError):
                date_time_original = datetime.fromisoformat(
                    data["dateTimeOriginal"].replace("Z", "+00:00")
                )

        return cls(
            make=data.get("make", ""),
            model=data.get("model", ""),
            exif_image_width=data.get("exifImageWidth", 0),
            exif_image_height=data.get("exifImageHeight", 0),
            file_size_in_byte=data.get("fileSizeInByte", 0),
            orientation=data.get("orientation", ""),
            date_time_original=date_time_original,
            time_zone=data.get("timeZone", ""),
            latitude=data.get("latitude", 0.0),
            longitude=data.get("longitude", 0.0),
            description=data.get("description", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the ExifInfo instance to a dictionary.

        Returns
        -------
            A dictionary containing EXIF information.
        """
        result = {
            "make": self.make,
            "model": self.model,
            "exifImageWidth": self.exif_image_width,
            "exifImageHeight": self.exif_image_height,
            "fileSizeInByte": self.file_size_in_byte,
            "orientation": self.orientation,
            "timeZone": self.time_zone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
        }

        if self.date_time_original:
            result["dateTimeOriginal"] = self.date_time_original.isoformat()

        return result


@dataclass
class Asset:
    """Asset model for the Immich API."""

    id: str = ""
    device_asset_id: str = ""
    owner_id: str = ""
    device_id: str = ""
    type: AssetType = AssetType.UNKNOWN
    original_path: str = ""
    original_file_name: str = ""
    resized: bool = False
    thumbhash: str = ""
    file_created_at: datetime | None = None
    file_modified_at: datetime | None = None
    updated_at: datetime | None = None
    is_favorite: bool = False
    is_archived: bool = False
    is_trashed: bool = False
    duration: str = ""
    rating: int = 0
    exif_info: ExifInfo = field(default_factory=ExifInfo)
    live_photo_video_id: str = ""
    checksum: str = ""
    stack_parent_id: str = ""
    tags: list[dict[str, Any]] = field(default_factory=list)
    library_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Asset":
        """
        Create an Asset instance from a dictionary.

        Args:
            data: The dictionary containing asset information.

        Returns
        -------
            An Asset instance.
        """
        asset_type = AssetType.UNKNOWN
        if data.get("type") in [e.value for e in AssetType]:
            asset_type = AssetType(data["type"])

        file_created_at = None
        if data.get("fileCreatedAt"):
            with contextlib.suppress(ValueError, TypeError):
                file_created_at = datetime.fromisoformat(
                    data["fileCreatedAt"].replace("Z", "+00:00")
                )

        file_modified_at = None
        if data.get("fileModifiedAt"):
            with contextlib.suppress(ValueError, TypeError):
                file_modified_at = datetime.fromisoformat(
                    data["fileModifiedAt"].replace("Z", "+00:00")
                )

        updated_at = None
        if data.get("updatedAt"):
            with contextlib.suppress(ValueError, TypeError):
                updated_at = datetime.fromisoformat(
                    data["updatedAt"].replace("Z", "+00:00")
                )

        exif_info = ExifInfo()
        if data.get("exifInfo"):
            exif_info = ExifInfo.from_dict(data["exifInfo"])

        return cls(
            id=data.get("id", ""),
            device_asset_id=data.get("deviceAssetId", ""),
            owner_id=data.get("ownerId", ""),
            device_id=data.get("deviceId", ""),
            type=asset_type,
            original_path=data.get("originalPath", ""),
            original_file_name=data.get("originalFileName", ""),
            resized=data.get("resized", False),
            thumbhash=data.get("thumbhash", ""),
            file_created_at=file_created_at,
            file_modified_at=file_modified_at,
            updated_at=updated_at,
            is_favorite=data.get("isFavorite", False),
            is_archived=data.get("isArchived", False),
            is_trashed=data.get("isTrashed", False),
            duration=data.get("duration", ""),
            rating=data.get("rating", 0),
            exif_info=exif_info,
            live_photo_video_id=data.get("livePhotoVideoId", ""),
            checksum=data.get("checksum", ""),
            stack_parent_id=data.get("stackParentId", ""),
            tags=data.get("tags", []),
            library_id=data.get("libraryId", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Asset instance to a dictionary.

        Returns
        -------
            A dictionary containing asset information.
        """
        result = {
            "id": self.id,
            "deviceAssetId": self.device_asset_id,
            "ownerId": self.owner_id,
            "deviceId": self.device_id,
            "type": self.type.value,
            "originalPath": self.original_path,
            "originalFileName": self.original_file_name,
            "resized": self.resized,
            "thumbhash": self.thumbhash,
            "isFavorite": self.is_favorite,
            "isArchived": self.is_archived,
            "isTrashed": self.is_trashed,
            "duration": self.duration,
            "rating": self.rating,
            "exifInfo": self.exif_info.to_dict(),
            "livePhotoVideoId": self.live_photo_video_id,
            "checksum": self.checksum,
            "stackParentId": self.stack_parent_id,
            "tags": self.tags,
            "libraryId": self.library_id,
        }

        if self.file_created_at:
            result["fileCreatedAt"] = self.file_created_at.isoformat()
        if self.file_modified_at:
            result["fileModifiedAt"] = self.file_modified_at.isoformat()
        if self.updated_at:
            result["updatedAt"] = self.updated_at.isoformat()

        return result
