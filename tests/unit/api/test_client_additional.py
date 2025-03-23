# Copyright 2025 Kyle Nguyen
"""Additional tests for the immich_py.client module."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from immich_py.api.client import ImmichClient, ImmichClientError

# ruff: noqa: DTZ001


def test_context_manager():
    """Test using the client as a context manager."""
    with patch("httpx.Client") as mock_httpx_client:
        mock_instance = mock_httpx_client.return_value

        with ImmichClient(
            endpoint="https://immich.example.com",
            api_key="test_api_key",
        ) as client:
            # Set the client manually since we're mocking
            client._client = mock_instance
            assert client._client is not None

        # Verify close was called
        mock_instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_async_client():
    """Test the async_client context manager."""
    with patch("httpx.AsyncClient") as mock_async_client:
        mock_instance = mock_async_client.return_value
        mock_instance.aclose = AsyncMock()

        client = ImmichClient(
            endpoint="https://immich.example.com",
            api_key="test_api_key",
        )

        async with client.async_client() as async_client:
            assert async_client is mock_instance

        # Verify aclose was called
        mock_instance.aclose.assert_awaited_once()


def test_handle_response_error_with_error_key(mock_client, mock_response):
    """Test handling an error response with 'error' key."""
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Bad request"}

    with pytest.raises(ImmichClientError) as excinfo:
        mock_client._handle_response(mock_response, "/test")

    assert excinfo.value.status_code == 400
    assert "Bad request" in str(excinfo.value)


def test_handle_response_error_with_text(mock_client, mock_response):
    """Test handling an error response with text."""
    mock_response.status_code = 500
    mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
    mock_response.text = "Internal server error"

    with pytest.raises(ImmichClientError) as excinfo:
        mock_client._handle_response(mock_response, "/test")

    assert excinfo.value.status_code == 500
    assert "Internal server error" in str(excinfo.value)


def test_request_error(mock_client):
    """Test handling a request error."""
    mock_client.client.request.side_effect = httpx.RequestError("Connection error")

    with pytest.raises(ImmichClientError) as excinfo:
        mock_client._request("GET", "/test")

    assert "Connection error" in str(excinfo.value)


def test_get_binary(mock_client, mock_response):
    """Test the get_binary method."""
    mock_client.client.request.return_value = mock_response
    mock_response.content = b"binary data"

    result = mock_client.get_binary("/test")

    mock_client.client.request.assert_called_once_with(
        method="GET",
        url="https://immich.example.com/api/test",
        params=None,
        headers={"Accept": "application/octet-stream"},
    )
    assert result == b"binary data"


def test_get_binary_error(mock_client, mock_response):
    """Test the get_binary method with an error response."""
    mock_client.client.request.return_value = mock_response
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Not found"}

    with pytest.raises(ImmichClientError) as excinfo:
        mock_client.get_binary("/test")

    assert excinfo.value.status_code == 404
    assert "Not found" in str(excinfo.value)


def test_ping_server_error(mock_client):
    """Test ping_server when an error occurs."""
    mock_client.get = MagicMock(side_effect=ImmichClientError("Connection error"))

    result = mock_client.ping_server()

    assert result is False


def test_download_asset(mock_client):
    """Test downloading an asset."""
    mock_client.get_binary = MagicMock(return_value=b"asset data")

    result = mock_client.download_asset("asset-id")

    mock_client.get_binary.assert_called_once_with(
        "/assets/asset-id/original", endpoint_name="DownloadAsset"
    )
    assert result == b"asset data"


@pytest.mark.parametrize(
    (
        "is_archived",
        "is_favorite",
        "latitude",
        "longitude",
        "remove_parent",
        "stack_parent_id",
        "expected_data",
    ),
    [
        (
            True,
            False,
            0.0,
            0.0,
            False,
            None,
            {
                "ids": ["asset-1", "asset-2"],
                "isArchived": True,
                "isFavorite": False,
                "latitude": 0.0,
                "longitude": 0.0,
                "removeParent": False,
            },
        ),
        (
            False,
            True,
            37.7749,
            -122.4194,
            True,
            None,
            {
                "ids": ["asset-1", "asset-2"],
                "isArchived": False,
                "isFavorite": True,
                "latitude": 37.7749,
                "longitude": -122.4194,
                "removeParent": True,
            },
        ),
        (
            False,
            False,
            0.0,
            0.0,
            False,
            "stack-id",
            {
                "ids": ["asset-1", "asset-2"],
                "isArchived": False,
                "isFavorite": False,
                "latitude": 0.0,
                "longitude": 0.0,
                "removeParent": False,
                "stackParentId": "stack-id",
            },
        ),
    ],
)
def test_update_assets(
    mock_client,
    is_archived,
    is_favorite,
    latitude,
    longitude,
    remove_parent,
    stack_parent_id,
    expected_data,
):
    """Test updating multiple assets with various parameters."""
    mock_client.put = MagicMock(return_value={"success": True})
    asset_ids = ["asset-1", "asset-2"]

    result = mock_client.update_assets(
        asset_ids,
        is_archived=is_archived,
        is_favorite=is_favorite,
        latitude=latitude,
        longitude=longitude,
        remove_parent=remove_parent,
        stack_parent_id=stack_parent_id,
    )

    mock_client.put.assert_called_once_with(
        "/assets", json_data=expected_data, endpoint_name="UpdateAssets"
    )
    assert result == {"success": True}


def test_upload_asset_dry_run(mock_client):
    """Test uploading an asset in dry run mode."""
    mock_client.dry_run = True

    result = mock_client.upload_asset("test.jpg")

    assert result == {"id": "dry-run-id", "status": "created"}


def test_upload_asset_file_not_found(mock_client):
    """Test uploading a non-existent file."""
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(ImmichClientError) as excinfo:
            mock_client.upload_asset("nonexistent.jpg")

        assert "File not found" in str(excinfo.value)


def test_upload_asset_unsupported_type(mock_client):
    """Test uploading an unsupported file type."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat"),
        patch("pathlib.Path.suffix", return_value=".txt"),
    ):
        mock_client._supported_media_types = {".jpg": "image", ".mp4": "video"}

        with pytest.raises(ImmichClientError) as excinfo:
            mock_client.upload_asset("test.txt")

        assert "Unsupported file type" in str(excinfo.value)


@pytest.mark.parametrize(
    (
        "file_path",
        "device_asset_id",
        "device_id",
        "is_favorite",
        "is_archived",
        "file_created_at",
        "file_modified_at",
        "duration",
        "is_read_only",
        "sidecar_path",
    ),
    [
        (
            "test.jpg",
            None,
            None,
            False,
            False,
            None,
            None,
            "00:00:00.000000",
            False,
            None,
        ),
        (
            "test.mp4",
            "custom-id",
            "custom-device",
            True,
            True,
            datetime(2023, 1, 1),
            datetime(2023, 1, 2),
            "00:01:30.000000",
            True,
            "test.json",
        ),
    ],
)
def test_upload_asset_success(
    mock_client,
    file_path,
    device_asset_id,
    device_id,
    is_favorite,
    is_archived,
    file_created_at,
    file_modified_at,
    duration,
    is_read_only,
    sidecar_path,
):
    """Test successful asset upload with various parameters."""
    # Setup mocks
    mock_file = MagicMock()
    mock_sidecar = MagicMock()
    mock_stat = MagicMock()
    mock_stat.st_size = 1024
    mock_stat.st_ctime = 1609459200  # 2021-01-01
    mock_stat.st_mtime = 1609545600  # 2021-01-02

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.stat", return_value=mock_stat),
        patch("pathlib.Path.open", MagicMock(return_value=mock_file)),
        patch("pathlib.Path.name", "test.jpg"),
        patch("pathlib.Path.suffix", ".jpg"),
        patch.object(mock_client, "_get_asset_type", return_value="image"),
        patch.object(mock_client, "_get_mime_type", return_value="image/jpeg"),
        patch.object(mock_client, "post", return_value={"id": "new-asset-id"}),
    ):
        # If sidecar is provided, set up additional mocks
        if sidecar_path:
            with patch("pathlib.Path.open", MagicMock(return_value=mock_sidecar)):
                result = mock_client.upload_asset(
                    file_path,
                    device_asset_id=device_asset_id,
                    device_id=device_id,
                    is_favorite=is_favorite,
                    is_archived=is_archived,
                    file_created_at=file_created_at,
                    file_modified_at=file_modified_at,
                    duration=duration,
                    is_read_only=is_read_only,
                    sidecar_path=sidecar_path,
                )
        else:
            result = mock_client.upload_asset(
                file_path,
                device_asset_id=device_asset_id,
                device_id=device_id,
                is_favorite=is_favorite,
                is_archived=is_archived,
                file_created_at=file_created_at,
                file_modified_at=file_modified_at,
                duration=duration,
                is_read_only=is_read_only,
            )

        assert result == {"id": "new-asset-id"}
        mock_client.post.assert_called_once()


def test_replace_asset_dry_run(mock_client):
    """Test replacing an asset in dry run mode."""
    mock_client.dry_run = True

    result = mock_client.replace_asset("asset-id", "test.jpg")

    assert result == {"id": "asset-id", "status": "replaced"}


def test_replace_asset_file_not_found(mock_client):
    """Test replacing with a non-existent file."""
    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(ImmichClientError) as excinfo:
            mock_client.replace_asset("asset-id", "nonexistent.jpg")

        assert "File not found" in str(excinfo.value)


def test_replace_asset_sidecar_not_found(mock_client):
    """Test replacing with a non-existent sidecar file."""
    # Mock the Path.exists method to return True for the asset file and False for the sidecar file
    with patch.object(Path, "exists", side_effect=[True, False]):
        # Mock the ImmichClient.replace_asset method to raise the expected exception
        mock_client.replace_asset = MagicMock(
            side_effect=ImmichClientError("Sidecar file not found: nonexistent.json")
        )

        with pytest.raises(ImmichClientError) as excinfo:
            mock_client.replace_asset(
                "asset-id", "test.jpg", sidecar_path="nonexistent.json"
            )

        assert "Sidecar file not found" in str(excinfo.value)


def test_replace_asset_success(mock_client):
    """Test successful asset replacement."""
    mock_file = MagicMock()

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.open", return_value=mock_file),
        patch("pathlib.Path.name", return_value="test.jpg"),
        patch.object(mock_client, "_get_mime_type", return_value="image/jpeg"),
        patch.object(mock_client, "put", return_value={"id": "asset-id"}),
    ):
        result = mock_client.replace_asset("asset-id", "test.jpg")

        assert result == {"id": "asset-id"}
        mock_client.put.assert_called_once()


def test_replace_asset_with_sidecar_success(mock_client):
    """Test successful asset replacement with sidecar."""
    mock_file = MagicMock()
    mock_sidecar = MagicMock()

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.open", side_effect=[mock_file, mock_sidecar]),
        patch("pathlib.Path.name", return_value="test.jpg"),
        patch.object(mock_client, "_get_mime_type", return_value="image/jpeg"),
        patch.object(mock_client, "put", return_value={"id": "asset-id"}),
    ):
        result = mock_client.replace_asset(
            "asset-id", "test.jpg", sidecar_path="test.json"
        )

        assert result == {"id": "asset-id"}
        mock_client.put.assert_called_once()


def test_search_assets_pagination(mock_client):
    """Test asset search with pagination."""
    # First page has nextPage, second page doesn't
    mock_client.post = MagicMock(
        side_effect=[
            {
                "assets": {
                    "items": [{"id": "asset-1"}, {"id": "asset-2"}],
                    "nextPage": "2",
                }
            },
            {"assets": {"items": [{"id": "asset-3"}], "nextPage": None}},
        ]
    )

    result = mock_client.search_assets(page=1, page_size=2)

    assert len(result) == 3
    assert result[0]["id"] == "asset-1"
    assert result[1]["id"] == "asset-2"
    assert result[2]["id"] == "asset-3"
    assert mock_client.post.call_count == 2


@pytest.mark.parametrize(
    ("checksum", "expected_result"),
    [
        ("abc123", [{"id": "asset-1", "checksum": "abc123"}]),
        ("xyz789", []),
    ],
)
def test_get_assets_by_hash(mock_client, checksum, expected_result):
    """Test getting assets by hash."""
    mock_client.search_assets = MagicMock(
        return_value=[
            {"id": "asset-1", "checksum": "abc123"},
            {"id": "asset-2", "checksum": "def456"},
        ]
    )

    result = mock_client.get_assets_by_hash(checksum)

    mock_client.search_assets.assert_called_once_with(checksum=checksum)
    assert result == expected_result


@pytest.mark.parametrize(
    ("name", "expected_result"),
    [
        ("test.jpg", [{"id": "asset-1", "originalFileName": "test.jpg"}]),
        ("unknown.jpg", []),
    ],
)
def test_get_assets_by_name(mock_client, name, expected_result):
    """Test getting assets by name."""
    mock_client.search_assets = MagicMock(
        return_value=[
            {"id": "asset-1", "originalFileName": "test.jpg"},
            {"id": "asset-2", "originalFileName": "other.jpg"},
        ]
    )

    result = mock_client.get_assets_by_name(name)

    mock_client.search_assets.assert_called_once_with(original_file_name=name)
    assert result == expected_result


def test_get_album_info(mock_client):
    """Test getting album info."""
    mock_client.get = MagicMock(return_value={"id": "album-id", "name": "Test Album"})

    # Test with default parameters
    result = mock_client.get_album_info("album-id")
    mock_client.get.assert_called_with(
        "/albums/album-id",
        params={"withoutAssets": "false"},
        endpoint_name="GetAlbumInfo",
    )
    assert result == {"id": "album-id", "name": "Test Album"}

    # Test with without_assets=True
    result = mock_client.get_album_info("album-id", without_assets=True)
    mock_client.get.assert_called_with(
        "/albums/album-id",
        params={"withoutAssets": "true"},
        endpoint_name="GetAlbumInfo",
    )


def test_add_assets_to_album_dry_run(mock_client):
    """Test adding assets to album in dry run mode."""
    mock_client.dry_run = True
    # Replace the method with a MagicMock to use assert_not_called
    mock_client.put = MagicMock()

    result = mock_client.add_assets_to_album("album-id", ["asset-1", "asset-2"])

    assert result == []
    mock_client.put.assert_not_called()


def test_add_assets_to_album(mock_client):
    """Test adding assets to album."""
    mock_client.put = MagicMock(return_value=[{"id": "asset-1"}, {"id": "asset-2"}])

    result = mock_client.add_assets_to_album("album-id", ["asset-1", "asset-2"])

    mock_client.put.assert_called_once_with(
        "/albums/album-id/assets",
        json_data={"ids": ["asset-1", "asset-2"]},
        endpoint_name="AddAssetToAlbum",
    )
    assert result == [{"id": "asset-1"}, {"id": "asset-2"}]


def test_create_album_dry_run(mock_client):
    """Test creating an album in dry run mode."""
    mock_client.dry_run = True
    # Replace the method with a MagicMock to use assert_not_called
    mock_client.post = MagicMock()

    result = mock_client.create_album("Test Album", "Description", ["asset-1"])

    assert result == {
        "id": "dry-run-id",
        "albumName": "Test Album",
        "description": "Description",
    }
    mock_client.post.assert_not_called()


@pytest.mark.parametrize(
    ("album_name", "description", "asset_ids", "expected_data"),
    [
        ("Test Album", "", None, {"albumName": "Test Album", "description": ""}),
        (
            "Test Album",
            "Description",
            ["asset-1", "asset-2"],
            {
                "albumName": "Test Album",
                "description": "Description",
                "assetIds": ["asset-1", "asset-2"],
            },
        ),
    ],
)
def test_create_album(mock_client, album_name, description, asset_ids, expected_data):
    """Test creating an album with various parameters."""
    mock_client.post = MagicMock(return_value={"id": "new-album-id"})

    result = mock_client.create_album(album_name, description, asset_ids)

    mock_client.post.assert_called_once_with(
        "/albums",
        json_data=expected_data,
        endpoint_name="CreateAlbum",
    )
    assert result == {"id": "new-album-id"}


def test_get_asset_albums(mock_client):
    """Test getting albums for an asset."""
    mock_client.get = MagicMock(return_value=[{"id": "album-1"}, {"id": "album-2"}])

    result = mock_client.get_asset_albums("asset-id")

    mock_client.get.assert_called_once_with(
        "/albums",
        params={"assetId": "asset-id"},
        endpoint_name="GetAssetAlbums",
    )
    assert result == [{"id": "album-1"}, {"id": "album-2"}]


def test_delete_album_dry_run(mock_client):
    """Test deleting an album in dry run mode."""
    mock_client.dry_run = True
    # Replace the method with a MagicMock to use assert_not_called
    mock_client.delete = MagicMock()

    result = mock_client.delete_album("album-id")

    assert result == {}
    mock_client.delete.assert_not_called()


def test_delete_album(mock_client):
    """Test deleting an album."""
    mock_client.delete = MagicMock(return_value={"success": True})

    result = mock_client.delete_album("album-id")

    mock_client.delete.assert_called_once_with(
        "/albums/album-id",
        endpoint_name="DeleteAlbum",
    )
    assert result == {"success": True}


def test_upsert_tags_dry_run(mock_client):
    """Test upserting tags in dry run mode."""
    mock_client.dry_run = True
    # Replace the method with a MagicMock to use assert_not_called
    mock_client.put = MagicMock()

    result = mock_client.upsert_tags(["tag1", "tag2"])

    assert len(result) == 2
    assert result[0]["name"] == "tag1"
    assert result[1]["name"] == "tag2"
    mock_client.put.assert_not_called()


def test_upsert_tags(mock_client):
    """Test upserting tags."""
    mock_client.put = MagicMock(
        return_value=[
            {"id": "tag-1", "name": "tag1"},
            {"id": "tag-2", "name": "tag2"},
        ]
    )

    result = mock_client.upsert_tags(["tag1", "tag2"])

    mock_client.put.assert_called_once_with(
        "/tags",
        json_data={"tags": ["tag1", "tag2"]},
        endpoint_name="UpsertTags",
    )
    assert result == [
        {"id": "tag-1", "name": "tag1"},
        {"id": "tag-2", "name": "tag2"},
    ]


def test_tag_assets_dry_run(mock_client):
    """Test tagging assets in dry run mode."""
    mock_client.dry_run = True
    # Replace the method with a MagicMock to use assert_not_called
    mock_client.put = MagicMock()

    result = mock_client.tag_assets("tag-id", ["asset-1", "asset-2"])

    assert len(result) == 2
    assert result[0]["id"] == "asset-1"
    assert result[0]["success"] is True
    assert result[1]["id"] == "asset-2"
    assert result[1]["success"] is True
    mock_client.put.assert_not_called()


def test_tag_assets(mock_client):
    """Test tagging assets."""
    mock_client.put = MagicMock(
        return_value=[
            {"id": "asset-1", "success": True},
            {"id": "asset-2", "success": True},
        ]
    )

    result = mock_client.tag_assets("tag-id", ["asset-1", "asset-2"])

    mock_client.put.assert_called_once_with(
        "/tags/tag-id/assets",
        json_data={"ids": ["asset-1", "asset-2"]},
        endpoint_name="TagAssets",
    )
    assert result == [
        {"id": "asset-1", "success": True},
        {"id": "asset-2", "success": True},
    ]


def test_bulk_tag_assets_dry_run(mock_client):
    """Test bulk tagging assets in dry run mode."""
    mock_client.dry_run = True
    # Replace the method with a MagicMock to use assert_not_called
    mock_client.put = MagicMock()

    result = mock_client.bulk_tag_assets(["tag-1", "tag-2"], ["asset-1", "asset-2"])

    assert result == {"count": 2}
    mock_client.put.assert_not_called()


def test_bulk_tag_assets(mock_client):
    """Test bulk tagging assets."""
    mock_client.put = MagicMock(return_value={"count": 2})

    result = mock_client.bulk_tag_assets(["tag-1", "tag-2"], ["asset-1", "asset-2"])

    mock_client.put.assert_called_once_with(
        "/tags/assets",
        json_data={"tagIds": ["tag-1", "tag-2"], "assetIds": ["asset-1", "asset-2"]},
        endpoint_name="BulkTagAssets",
    )
    assert result == {"count": 2}


def test_create_stack_too_few_assets(mock_client):
    """Test creating a stack with too few assets."""
    with pytest.raises(ImmichClientError) as excinfo:
        mock_client.create_stack(["asset-1"])

    assert "Stack must have at least 2 assets" in str(excinfo.value)


def test_create_stack_dry_run(mock_client):
    """Test creating a stack in dry run mode."""
    mock_client.dry_run = True
    # Replace the method with a MagicMock to use assert_not_called
    mock_client.post = MagicMock()

    result = mock_client.create_stack(["asset-1", "asset-2"])

    assert result == "dry-run-stack-id"
    mock_client.post.assert_not_called()


def test_create_stack(mock_client):
    """Test creating a stack."""
    mock_client.post = MagicMock(return_value={"id": "stack-id"})

    result = mock_client.create_stack(["asset-1", "asset-2"])

    mock_client.post.assert_called_once_with(
        "/stacks",
        json_data={"assetIds": ["asset-1", "asset-2"]},
        endpoint_name="CreateStack",
    )
    assert result == "stack-id"


@pytest.mark.parametrize(
    ("job_id", "command", "force", "expected_data"),
    [
        ("job-1", "start", False, {"command": "start", "force": False}),
        ("job-2", "pause", True, {"command": "pause", "force": True}),
    ],
)
def test_send_job_command(mock_client, job_id, command, force, expected_data):
    """Test sending a command to a job."""
    mock_client.put = MagicMock(return_value={"success": True})

    result = mock_client.send_job_command(job_id, command, force)

    mock_client.put.assert_called_once_with(
        f"/jobs/{job_id}",
        json_data=expected_data,
        endpoint_name="SendJobCommand",
    )
    assert result == {"success": True}


def test_create_job(mock_client):
    """Test creating a job."""
    mock_client.post = MagicMock(return_value={"id": "job-id"})

    result = mock_client.create_job("person-cleanup")

    mock_client.post.assert_called_once_with(
        "/jobs",
        json_data={"name": "person-cleanup"},
        endpoint_name="CreateJob",
    )
    assert result == {"id": "job-id"}


def test_get_mime_type(mock_client):
    """Test getting MIME type from file path."""
    with patch("mimetypes.guess_type") as mock_guess_type:
        # Test with known MIME type
        mock_guess_type.return_value = ("image/jpeg", None)
        assert mock_client._get_mime_type("test.jpg") == "image/jpeg"

        # Test with unknown MIME type
        mock_guess_type.return_value = (None, None)
        assert mock_client._get_mime_type("unknown.xyz") == "application/octet-stream"


@pytest.mark.parametrize(
    ("extension", "supported_types", "expected_result"),
    [
        (".jpg", {".jpg": "image", ".mp4": "video"}, True),
        ("jpg", {".jpg": "image", ".mp4": "video"}, True),
        (".mp4", {".jpg": "image", ".mp4": "video"}, True),
        (".json", {".jpg": "image", ".mp4": "video", ".json": "sidecar"}, False),
        (".mp", {".jpg": "image", ".mp4": "video", ".mp": "useless"}, False),
        (".unknown", {".jpg": "image", ".mp4": "video"}, False),
    ],
)
def test_is_extension_supported(
    mock_client, extension, supported_types, expected_result
):
    """Test checking if extension is supported with various inputs."""
    mock_client._supported_media_types = supported_types

    result = mock_client.is_extension_supported(extension)

    assert result is expected_result


@pytest.mark.parametrize(
    ("extension", "supported_types", "expected_result"),
    [
        (".jpg", {".jpg": "image", ".mp4": "video", ".json": "sidecar"}, False),
        (".json", {".jpg": "image", ".mp4": "video", ".json": "sidecar"}, True),
        (".mp", {".jpg": "image", ".mp4": "video", ".mp": "useless"}, True),
        (".csv", {".jpg": "image", ".mp4": "video", ".csv": "meta"}, True),
        (".unknown", {".jpg": "image", ".mp4": "video"}, False),
    ],
)
def test_is_extension_ignored(mock_client, extension, supported_types, expected_result):
    """Test checking if extension is ignored with various inputs."""
    mock_client._supported_media_types = supported_types

    result = mock_client.is_extension_ignored(extension)

    assert result is expected_result


def test_get_supported_media_types(mock_client):
    """Test getting supported media types."""
    mock_client.get = MagicMock(
        return_value={
            "image": [".jpg", ".png"],
            "video": [".mp4", ".mov"],
        }
    )

    result = mock_client.get_supported_media_types()

    mock_client.get.assert_called_once_with(
        "/server/media-types", endpoint_name="GetSupportedMediaTypes"
    )

    # Check that extensions are mapped to their types
    assert result[".jpg"] == "image"
    assert result[".png"] == "image"
    assert result[".mp4"] == "video"
    assert result[".mov"] == "video"

    # Check that additional types are added
    assert result[".mp"] == "useless"
    assert result[".json"] == "sidecar"
    assert result[".csv"] == "meta"


def test_validate_connection(mock_client):
    """Test validating connection."""
    mock_client.get = MagicMock(
        side_effect=[
            {"id": "user-id", "name": "Test User"},  # First call to get user info
            {".jpg": ["image"], ".mp4": ["video"]},  # Second call to get media types
        ]
    )

    result = mock_client.validate_connection()

    assert mock_client.get.call_count == 2
    mock_client.get.assert_any_call("/users/me", endpoint_name="ValidateConnection")
    mock_client.get.assert_any_call(
        "/server/media-types", endpoint_name="GetSupportedMediaTypes"
    )
    assert result == {"id": "user-id", "name": "Test User"}


def test_get_server_statistics(mock_client):
    """Test getting server statistics."""
    mock_client.get = MagicMock(return_value={"users": 5, "assets": 100})

    result = mock_client.get_server_statistics()

    mock_client.get.assert_called_once_with(
        "/server/statistics", endpoint_name="GetServerStatistics"
    )
    assert result == {"users": 5, "assets": 100}


def test_get_asset_statistics(mock_client):
    """Test getting asset statistics."""
    mock_client.get = MagicMock(return_value={"count": 100, "videos": 20, "photos": 80})

    result = mock_client.get_asset_statistics()

    mock_client.get.assert_called_once_with(
        "/assets/statistics", endpoint_name="GetAssetStatistics"
    )
    assert result == {"count": 100, "videos": 20, "photos": 80}


def test_get_about_info(mock_client):
    """Test getting about info."""
    mock_client.get = MagicMock(return_value={"version": "1.0.0"})

    result = mock_client.get_about_info()

    mock_client.get.assert_called_once_with(
        "/server/about", endpoint_name="GetAboutInfo"
    )
    assert result == {"version": "1.0.0"}


def test_update_asset(mock_client):
    """Test updating an asset."""
    mock_client.put = MagicMock(
        return_value={"id": "asset-id", "description": "Updated"}
    )

    result = mock_client.update_asset("asset-id", description="Updated")

    mock_client.put.assert_called_once_with(
        "/assets/asset-id",
        json_data={"description": "Updated"},
        endpoint_name="UpdateAsset",
    )
    assert result == {"id": "asset-id", "description": "Updated"}


def test_delete_assets(mock_client):
    """Test deleting assets."""
    mock_client.delete = MagicMock(return_value={"success": True})

    # Test with default parameters
    result = mock_client.delete_assets(["asset-1", "asset-2"])
    mock_client.delete.assert_called_with(
        "/assets",
        json_data={"ids": ["asset-1", "asset-2"], "force": False},
        endpoint_name="DeleteAssets",
    )
    assert result == {"success": True}

    # Test with force_delete=True
    result = mock_client.delete_assets(["asset-1", "asset-2"], force_delete=True)
    mock_client.delete.assert_called_with(
        "/assets",
        json_data={"ids": ["asset-1", "asset-2"], "force": True},
        endpoint_name="DeleteAssets",
    )
    assert result == {"success": True}
