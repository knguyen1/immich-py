# Copyright 2025 Kyle Nguyen
"""Configuration for integration tests using httpx."""

import os
import time
from pathlib import Path

import httpx
import pytest

from immich_py.api.client import ImmichClient


def is_server_ready(
    url: str, max_retries: int = 30, retry_interval: float = 2.0
) -> bool:
    """
    Check if the Immich server is ready to accept connections.

    Args:
        url: The URL to check
        max_retries: Maximum number of retries
        retry_interval: Time between retries in seconds

    Returns:
        bool: True if server is ready, False otherwise
    """
    with httpx.Client(timeout=5) as client:
        for _ in range(max_retries):
            try:
                response = client.get(f"{url}/api/server/ping")
                if response.status_code == 200 and response.json().get("res") == "pong":
                    return True
            except httpx.RequestError:
                pass

            time.sleep(retry_interval)

    return False


@pytest.fixture(scope="session")
def integration_server_url() -> str:
    """
    Get the URL of the integration test server.

    Returns:
        str: The server URL
    """
    return os.environ.get("IMMICH_TEST_SERVER_URL", "http://localhost:3001")


@pytest.fixture(scope="session")
def integration_api_key(integration_server_url: str) -> str:
    """
    Get or create an API key for integration tests.

    Args:
        integration_server_url: The server URL

    Returns:
        str: The API key
    """
    api_key = os.environ.get("IMMICH_TEST_API_KEY")
    if api_key:
        return api_key

    if os.environ.get("CI") == "true":
        pytest.fail(
            "IMMICH_TEST_API_KEY environment variable must be set in CI environment"
        )

    return "test_api_key_placeholder"


@pytest.fixture(scope="session")
def integration_client(
    integration_server_url: str, integration_api_key: str
) -> ImmichClient:
    """
    Create an ImmichClient instance for integration tests.

    Args:
        integration_server_url: The server URL
        integration_api_key: The API key

    Returns:
        ImmichClient: A client instance
    """
    if not is_server_ready(integration_server_url):
        pytest.skip(f"Immich server at {integration_server_url} is not ready")

    client = ImmichClient(
        endpoint=integration_server_url,
        api_key=integration_api_key,
        verify_ssl=False,
    )

    if not client.ping_server():
        pytest.skip(f"Could not connect to Immich server at {integration_server_url}")

    return client


@pytest.fixture
def test_image_path() -> Path:
    """
    Get the path to a test image file.

    Returns:
        Path: Path to test image
    """
    test_files_dir = Path(__file__).parent / "test_files"
    test_files_dir.mkdir(exist_ok=True)

    return test_files_dir / "test_image.jpg"


@pytest.fixture
def sample_image(test_image_path: Path) -> Path:
    """
    Ensure we have a sample image for testing.

    Args:
        test_image_path: Path to test image from conftest

    Returns:
        Path: Path to sample image
    """
    # If test_image_path doesn't exist, create a simple test image
    if not test_image_path.exists():
        # Create a simple test image using PIL if available
        try:
            from PIL import Image

            # Create a 100x100 red image
            img = Image.new("RGB", (100, 100), color="red")
            img.save(test_image_path)
        except ImportError:
            # If PIL is not available, create an empty file
            # This will be skipped in the test
            with open(test_image_path, "wb") as f:
                f.write(b"")
            pytest.skip("PIL not available to create test image")

    return test_image_path


@pytest.fixture
def test_video_path() -> Path:
    """
    Get the path to a test video file.

    Returns:
        Path: Path to test video
    """
    test_files_dir = Path(__file__).parent / "test_files"
    test_files_dir.mkdir(exist_ok=True)

    test_video = test_files_dir / "test_video.mp4"
    if not test_video.exists():
        pytest.skip(f"Test video not found at {test_video}")

    return test_video
