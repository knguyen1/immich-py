# Copyright 2025 Kyle Nguyen
"""
User models for the Immich API.

This module contains data models for users in the Immich API.
"""

import contextlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class User:
    """User model for the Immich API."""

    id: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    storage_label: str = ""
    external_path: str = ""
    profile_image_path: str = ""
    should_change_password: bool = False
    is_admin: bool = False
    created_at: datetime | None = None
    deleted_at: datetime | None = None
    updated_at: datetime | None = None
    oauth_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """
        Create a User instance from a dictionary.

        Args:
            data: The dictionary containing user information.

        Returns
        -------
            A User instance.
        """
        created_at = None
        if data.get("createdAt"):
            with contextlib.suppress(ValueError, TypeError):
                created_at = datetime.fromisoformat(
                    data["createdAt"].replace("Z", "+00:00")
                )

        deleted_at = None
        if data.get("deletedAt"):
            with contextlib.suppress(ValueError, TypeError):
                deleted_at = datetime.fromisoformat(
                    data["deletedAt"].replace("Z", "+00:00")
                )

        updated_at = None
        if data.get("updatedAt"):
            with contextlib.suppress(ValueError, TypeError):
                updated_at = datetime.fromisoformat(
                    data["updatedAt"].replace("Z", "+00:00")
                )

        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            storage_label=data.get("storageLabel", ""),
            external_path=data.get("externalPath", ""),
            profile_image_path=data.get("profileImagePath", ""),
            should_change_password=data.get("shouldChangePassword", False),
            is_admin=data.get("isAdmin", False),
            created_at=created_at,
            deleted_at=deleted_at,
            updated_at=updated_at,
            oauth_id=data.get("oauthId", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the User instance to a dictionary.

        Returns
        -------
            A dictionary containing user information.
        """
        result = {
            "id": self.id,
            "email": self.email,
            "firstName": self.first_name,
            "lastName": self.last_name,
            "storageLabel": self.storage_label,
            "externalPath": self.external_path,
            "profileImagePath": self.profile_image_path,
            "shouldChangePassword": self.should_change_password,
            "isAdmin": self.is_admin,
            "oauthId": self.oauth_id,
        }

        if self.created_at:
            result["createdAt"] = self.created_at.isoformat()
        if self.deleted_at:
            result["deletedAt"] = self.deleted_at.isoformat()
        if self.updated_at:
            result["updatedAt"] = self.updated_at.isoformat()

        return result
