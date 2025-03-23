# Copyright 2025 Kyle Nguyen
"""Integration tests for asset-related functionality."""

import time
from collections.abc import Generator
from pathlib import Path

import pytest

from immich_py.api.client import ImmichClient


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
        # Create test_files directory if it doesn't exist
        test_image_path.parent.mkdir(exist_ok=True)

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
def uploaded_asset(
    integration_client: ImmichClient, sample_image: Path
) -> Generator[dict, None, None]:
    """
    Upload a test asset and yield its info, then clean up.

    Args:
        integration_client: ImmichClient instance
        sample_image: Path to sample image

    Yields:
        dict: Asset information
    """
    # Upload the asset
    response = integration_client.upload_asset(
        file_path=sample_image,
        device_asset_id=f"test-asset-{int(time.time())}",
        is_favorite=False,
    )

    # Get the asset ID
    asset_id = response.get("id")
    if not asset_id:
        pytest.skip("Failed to upload test asset")

    # Get full asset info
    asset_info = integration_client.get_asset_info(asset_id)

    # Yield the asset info for the test
    yield asset_info

    # Clean up after the test
    try:
        integration_client.delete_assets([asset_id], force_delete=True)
    except Exception as e:  # noqa: BLE001
        print(f"Warning: Failed to clean up test asset {asset_id}: {e}")


def test_upload_asset(integration_client: ImmichClient, sample_image: Path) -> None:
    """Test uploading an asset."""
    # Generate a unique device asset ID
    device_asset_id = f"test-asset-{int(time.time())}"

    # Upload the asset
    response = integration_client.upload_asset(
        file_path=sample_image,
        device_asset_id=device_asset_id,
        is_favorite=False,
    )

    # Check the response
    assert "id" in response
    assert response.get("status") in ["created", "duplicate"]

    # Clean up
    asset_id = response.get("id")
    if asset_id:
        integration_client.delete_assets([asset_id], force_delete=True)


def test_get_asset_info(integration_client: ImmichClient, uploaded_asset: dict) -> None:
    """Test getting asset information."""
    # Get the asset ID
    asset_id = uploaded_asset.get("id")
    assert asset_id is not None

    # Get the asset info
    asset_info = integration_client.get_asset_info(asset_id)

    # Check the asset info
    assert asset_info.get("id") == asset_id
    assert "originalFileName" in asset_info
    assert "originalPath" in asset_info


def test_update_asset(integration_client: ImmichClient, uploaded_asset: dict) -> None:
    """Test updating an asset."""
    # Get the asset ID
    asset_id = uploaded_asset.get("id")
    assert asset_id is not None

    # Update the asset
    new_description = f"Test description {int(time.time())}"
    updated_asset = integration_client.update_asset(
        asset_id,
        description=new_description,
        isFavorite=True,
    )

    # Check the updated asset
    assert updated_asset.get("id") == asset_id
    assert updated_asset.get("exifInfo").get("description") == new_description
    assert updated_asset.get("isFavorite") is True


def test_search_assets(integration_client: ImmichClient, uploaded_asset: dict) -> None:
    """Test searching for assets."""
    # Get the asset ID
    asset_id = uploaded_asset.get("id")
    assert asset_id is not None

    # Search for assets
    assets = integration_client.search_assets(
        with_exif=True,
        is_visible=True,
        id=asset_id,
    )

    # Check that our asset is in the results
    asset_ids = [asset.get("id") for asset in assets]
    assert asset_id in asset_ids


def test_delete_asset(integration_client: ImmichClient, sample_image: Path) -> None:
    """Test deleting an asset."""
    # Upload an asset
    device_asset_id = f"test-asset-delete-{int(time.time())}"
    response = integration_client.upload_asset(
        file_path=sample_image,
        device_asset_id=device_asset_id,
    )

    # Get the asset ID
    asset_id = response.get("id")
    assert asset_id is not None

    # Delete the asset
    delete_response = integration_client.delete_assets([asset_id], force_delete=True)

    # Check the response
    assert delete_response is not None
