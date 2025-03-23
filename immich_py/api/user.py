# Copyright 2025 Kyle Nguyen
"""
User API for the Immich API.

This module contains the UserAPI class for interacting with users in the Immich API.
"""

from immich_py.models.user import User


class UserAPI:
    """API for interacting with users in the Immich API."""

    def __init__(self, client):
        """
        Initialize the UserAPI.

        Args:
            client: The Immich client.
        """
        self.client = client

    def get_current_user(self) -> User:
        """
        Get the current user.

        Returns
        -------
            The current user.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.validate_connection()
        return User.from_dict(data)
