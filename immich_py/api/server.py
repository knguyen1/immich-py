# Copyright 2025 Kyle Nguyen
"""
Server API for the Immich API.

This module contains the ServerAPI class for interacting with server-related endpoints in the Immich API.
"""

from typing import Any


class ServerAPI:
    """API for interacting with server-related endpoints in the Immich API."""

    def __init__(self, client):
        """
        Initialize the ServerAPI.

        Args:
            client: The Immich client.
        """
        self.client = client

    def ping_server(self) -> bool:
        """
        Ping the server to check if it's available.

        Returns
        -------
            True if the server responds with "pong", False otherwise.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.ping_server()

    def get_server_statistics(self) -> dict[str, Any]:
        """
        Get server statistics.

        Returns
        -------
            The server statistics.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.get_server_statistics()

    def get_asset_statistics(self) -> dict[str, Any]:
        """
        Get asset statistics for the current user.

        Returns
        -------
            The asset statistics.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.get_asset_statistics()

    def get_supported_media_types(self) -> dict[str, str]:
        """
        Get the media types supported by the server.

        Returns
        -------
            A dictionary mapping file extensions to media types.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.get_supported_media_types()

    def get_about_info(self) -> dict[str, Any]:
        """
        Get information about the server.

        Returns
        -------
            Information about the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.get_about_info()

    def is_extension_supported(self, extension: str) -> bool:
        """
        Check if a file extension is supported.

        Args:
            extension: The file extension.

        Returns
        -------
            True if the extension is supported, False otherwise.
        """
        return self.client.is_extension_supported(extension)

    def is_extension_ignored(self, extension: str) -> bool:
        """
        Check if a file extension is ignored.

        Args:
            extension: The file extension.

        Returns
        -------
            True if the extension is ignored, False otherwise.
        """
        return self.client.is_extension_ignored(extension)
