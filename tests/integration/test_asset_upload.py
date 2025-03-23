# Copyright 2025 Kyle Nguyen
"""Integration tests for asset upload functionality."""

import shutil
import tempfile
import time
import zipfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from immich_py.api.asset import AssetAPI
from immich_py.api.client import ImmichClient


@pytest.fixture
def temp_test_dir() -> Generator[Path, Any, Any]:
    """
    Create a temporary directory for test files.

    Returns:
        Path: Path to temporary directory
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_directory(temp_test_dir: Path, sample_image: Path) -> Path:
    """
    Create a test directory with multiple images.

    Args:
        temp_test_dir: Temporary directory
        sample_image: Sample image path

    Returns:
        Path: Path to test directory with images
    """
    # Create a test directory
    test_dir = temp_test_dir / "test_dir"
    test_dir.mkdir(exist_ok=True)

    # Create multiple copies of the sample image with different names
    for i in range(3):
        dest_path = test_dir / f"test_image_{i}.jpg"
        shutil.copy(sample_image, dest_path)

    # Create a subdirectory
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir(exist_ok=True)

    # Create images in the subdirectory
    for i in range(2):
        dest_path = sub_dir / f"subdir_image_{i}.jpg"
        shutil.copy(sample_image, dest_path)

    return test_dir


@pytest.fixture
def test_archive(temp_test_dir: Path, sample_image: Path) -> Path:
    """
    Create a test archive with multiple images.

    Args:
        temp_test_dir: Temporary directory
        sample_image: Sample image path

    Returns:
        Path: Path to test archive
    """
    # Create a temporary directory for the archive contents
    archive_content_dir = temp_test_dir / "archive_contents"
    archive_content_dir.mkdir(exist_ok=True)

    # Create multiple copies of the sample image with different names
    image_paths = []
    for i in range(3):
        dest_path = archive_content_dir / f"archive_image_{i}.jpg"
        shutil.copy(sample_image, dest_path)
        image_paths.append(dest_path)

    # Create the archive
    archive_path = temp_test_dir / "test_archive.zip"
    with zipfile.ZipFile(archive_path, "w") as zipf:
        for image_path in image_paths:
            zipf.write(image_path, image_path.name)

    return archive_path


def test_upload_single_asset(
    integration_client: ImmichClient, sample_image: Path
) -> None:
    """Test uploading a single asset using upload_assets."""
    # Create AssetAPI instance
    asset_api = AssetAPI(integration_client)

    # Generate a unique device asset ID
    device_asset_id = f"test-asset-{int(time.time())}"

    # Upload the asset using upload_assets
    response = asset_api.upload_assets(
        file_path=sample_image,
        device_asset_id=device_asset_id,
        is_favorite=False,
    )

    # Check the response
    assert isinstance(response, dict)
    assert "id" in response
    assert response.get("status") in ["created", "duplicate"]

    # Clean up
    asset_id = response.get("id")
    if asset_id:
        integration_client.delete_assets([asset_id], force_delete=True)


def test_upload_directory(
    integration_client: ImmichClient, test_directory: Path
) -> None:
    """Test uploading a directory of assets."""
    # Create AssetAPI instance
    asset_api = AssetAPI(integration_client)

    # Generate a unique device asset ID prefix
    device_asset_id_prefix = f"test-dir-{int(time.time())}"

    # Upload the directory
    responses = asset_api.upload_assets(
        file_path=test_directory,
        device_asset_id=device_asset_id_prefix,
        is_favorite=False,
    )

    # Check the responses
    assert isinstance(responses, list)
    # Should have 5 responses (3 in root dir + 2 in subdir)
    assert len(responses) == 5

    # Check each response
    asset_ids = []
    for response in responses:
        assert "id" in response
        assert response.get("status") in ["created", "duplicate"]
        asset_ids.append(response.get("id"))

    # Clean up
    if asset_ids:
        integration_client.delete_assets(asset_ids, force_delete=True)


def test_upload_archive(integration_client: ImmichClient, test_archive: Path) -> None:
    """Test uploading an archive of assets."""
    # Create AssetAPI instance
    asset_api = AssetAPI(integration_client)

    # Generate a unique device asset ID prefix
    device_asset_id_prefix = f"test-archive-{int(time.time())}"

    # Upload the archive
    responses = asset_api.upload_assets(
        file_path=test_archive,
        device_asset_id=device_asset_id_prefix,
        is_favorite=False,
    )

    # Check the responses
    assert isinstance(responses, list)
    # Should have 3 responses (3 images in the archive)
    assert len(responses) == 3

    # Check each response
    asset_ids = []
    for response in responses:
        assert "id" in response
        assert response.get("status") in ["created", "duplicate"]
        asset_ids.append(response.get("id"))

    # Clean up
    if asset_ids:
        integration_client.delete_assets(asset_ids, force_delete=True)


def test_upload_with_sidecar(
    integration_client: ImmichClient, sample_image: Path, temp_test_dir: Path
) -> None:
    """Test uploading a single asset with a sidecar file."""
    # Create a sidecar file
    sidecar_path = temp_test_dir / "test_sidecar.json"
    with open(sidecar_path, "w") as f:
        f.write('{"metadata": "test"}')

    # Create AssetAPI instance
    asset_api = AssetAPI(integration_client)

    # Generate a unique device asset ID
    device_asset_id = f"test-sidecar-{int(time.time())}"

    # Upload the asset with sidecar
    response = asset_api.upload_assets(
        file_path=sample_image,
        device_asset_id=device_asset_id,
        is_favorite=False,
        sidecar_path=sidecar_path,
    )

    # Check the response
    assert isinstance(response, dict)
    assert "id" in response
    assert response.get("status") in ["created", "duplicate"]

    # Clean up
    asset_id = response.get("id")
    if asset_id:
        integration_client.delete_assets([asset_id], force_delete=True)
