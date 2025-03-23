# Copyright 2025 Kyle Nguyen
"""
Tag models for the Immich API.

This module contains data models for tags in the Immich API.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Tag:
    """Tag model for the Immich API."""

    id: str = ""
    name: str = ""
    value: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tag":
        """
        Create a Tag instance from a dictionary.

        Args:
            data: The dictionary containing tag information.

        Returns
        -------
            A Tag instance.
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            value=data.get("value", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Tag instance to a dictionary.

        Returns
        -------
            A dictionary containing tag information.
        """
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
        }
