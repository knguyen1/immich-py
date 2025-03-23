# Copyright 2025 Kyle Nguyen
"""Integration tests for server-related functionality."""

import pytest

from immich_py.api.client import ImmichClient


def test_ping_server(integration_client: ImmichClient) -> None:
    """Test that we can ping the server."""
    result = integration_client.ping_server()
    assert result is True


def test_get_server_info(integration_client: ImmichClient) -> None:
    """Test that we can get server information."""
    info = integration_client.get_about_info()
    assert "version" in info


def test_get_supported_media_types(integration_client: ImmichClient) -> None:
    """Test that we can get supported media types."""
    media_types = integration_client.get_supported_media_types()
    assert len(media_types) > 0
    # Check that common image formats are supported
    assert ".jpg" in media_types
    assert media_types[".jpg"] == "image"


@pytest.mark.parametrize(
    ("extension", "expected_result"),
    [
        (".jpg", True),
        (".jpeg", True),
        (".png", True),
        (".mp4", True),
        (".txt", False),
        (".xyz", False),
    ],
)
def test_is_extension_supported(
    integration_client: ImmichClient, extension: str, expected_result: bool
) -> None:
    """Test checking if extensions are supported."""
    # Make sure supported media types are loaded
    if not integration_client._supported_media_types:
        integration_client._supported_media_types = (
            integration_client.get_supported_media_types()
        )

    result = integration_client.is_extension_supported(extension)
    assert result is expected_result
