# Copyright 2025 Kyle Nguyen
"""Common fixtures for API tests."""

from unittest.mock import MagicMock

import httpx
import pytest

from immich_py.api.client import ImmichClient


@pytest.fixture
def mock_client() -> ImmichClient:
    """Create a mock ImmichClient instance.

    Returns:
        ImmichClient: A mocked client instance.
    """
    client = ImmichClient(
        endpoint="https://immich.example.com",
        api_key="test_api_key",
        verify_ssl=False,
        timeout=10.0,
    )
    # Replace the actual httpx client with a mock
    client._client = MagicMock()
    return client


@pytest.fixture
def mock_response() -> MagicMock:
    """Create a mock HTTP response.

    Returns:
        MagicMock: A mocked httpx.Response object.
    """
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {"success": True}
    response.text = '{"success": true}'
    response.content = b'{"success": true}'
    response.request = MagicMock()
    response.request.method = "GET"
    response.request.url = "https://immich.example.com/api/test"
    return response
