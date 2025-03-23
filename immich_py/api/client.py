# Copyright 2025 Kyle Nguyen
"""Provide a client for interacting with the Immich API."""

import json
import logging
import mimetypes
import platform
import types
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

import httpx

T = TypeVar("T")


class ImmichClientError(Exception):
    """Base exception for Immich client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        endpoint: str | None = None,
        method: str | None = None,
        url: str | None = None,
    ):
        self.status_code = status_code
        self.endpoint = endpoint
        self.method = method
        self.url = url
        super().__init__(message)

    def __str__(self) -> str:
        """Get the error information."""
        parts = []
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        if self.method and self.url:
            parts.append(f"Request: {self.method} {self.url}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        parts.append(f"Error: {super().__str__()}")
        return ", ".join(parts)


class ImmichClient:
    """
    Client for interacting with the Immich API.

    This client provides methods for interacting with the Immich API, including
    authentication, asset management, album management, and more.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        *,
        verify_ssl: bool = True,
        timeout: float = 60.0,
        dry_run: bool = False,
    ):
        """
        Initialize the Immich client.

        Args:
            endpoint: The base URL of the Immich API.
            api_key: The API key for authentication.
            verify_ssl: Whether to verify SSL certificates.
            timeout: The timeout for API requests in seconds.
            dry_run: If True, don't send any data to the server.
        """
        self.endpoint = endpoint.rstrip("/") + "/api"
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.dry_run = dry_run
        self.device_uuid = platform.node()
        self.retries = 1
        self.retry_delay = 1.0
        self.logger = logging.getLogger("immich_client")
        self._supported_media_types: dict[str, str] = {}
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                verify=self.verify_ssl,
                headers={"x-api-key": self.api_key},
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "ImmichClient":
        """Get the ImmichClient object."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Close the ImmichClient object."""
        self.close()

    @asynccontextmanager
    async def async_client(self) -> AsyncIterator[httpx.AsyncClient]:
        """Get an async HTTP client as a context manager."""
        client = httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
            headers={"x-api-key": self.api_key},
        )
        try:
            yield client
        finally:
            await client.aclose()

    def _make_url(self, path: str) -> str:
        """
        Create a full URL from a path.

        Args:
            path: The path to append to the endpoint.

        Returns
        -------
            The full URL.
        """
        return f"{self.endpoint}{path}"

    def _handle_response(
        self,
        response: httpx.Response,
        endpoint: str,
        expected_status: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Handle an API response.

        Args:
            response: The HTTP response.
            endpoint: The API endpoint for error reporting.
            expected_status: List of expected HTTP status codes.

        Returns
        -------
            The parsed JSON response.

        Raises
        ------
            ImmichClientError: If the response status is not in expected_status.
        """
        if expected_status is None:
            expected_status = [200]
        if response.status_code in expected_status:
            if response.status_code == 204:  # No content
                return {}
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"text": response.text}
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_msg = error_data["message"]
                elif "error" in error_data:
                    error_msg = error_data["error"]
            except (json.JSONDecodeError, KeyError):
                if response.text:
                    error_msg = response.text

            raise ImmichClientError(
                message=error_msg,
                status_code=response.status_code,
                endpoint=endpoint,
                method=response.request.method,
                url=str(response.request.url),
            )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: list[int] | None = None,
        endpoint_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the Immich API.

        Args:
            method: The HTTP method.
            path: The API path.
            params: Query parameters.
            json_data: JSON data for the request body.
            data: Form data for the request body.
            files: Files to upload.
            headers: Additional headers.
            expected_status: List of expected HTTP status codes.
            endpoint_name: Name of the endpoint for error reporting.

        Returns
        -------
            The parsed JSON response.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if expected_status is None:
            expected_status = [200]
        if self.dry_run and method.upper() not in ["GET", "HEAD"]:
            msg = f"DRY RUN: {method} {path}"
            self.logger.info(msg)
            return {}

        url = self._make_url(path)
        request_headers = {"Accept": "application/json"}
        if headers:
            request_headers.update(headers)

        try:
            response = self.client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                data=data,
                files=files,
                headers=request_headers,
            )
            return self._handle_response(
                response, endpoint_name or path, expected_status
            )
        except httpx.RequestError as e:
            raise ImmichClientError(
                message=f"Request failed: {e!s}",
                endpoint=endpoint_name or path,
                method=method,
                url=url,
            ) from e

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: list[int] | None = None,
        endpoint_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Make a GET request to the Immich API.

        Args:
            path: The API path.
            params: Query parameters.
            headers: Additional headers.
            expected_status: List of expected HTTP status codes.
            endpoint_name: Name of the endpoint for error reporting.

        Returns
        -------
            The parsed JSON response.
        """
        if expected_status is None:
            expected_status = [200]
        return self._request(
            "GET",
            path,
            params=params,
            headers=headers,
            expected_status=expected_status,
            endpoint_name=endpoint_name,
        )

    def post(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: list[int] | None = None,
        endpoint_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Make a POST request to the Immich API.

        Args:
            path: The API path.
            params: Query parameters.
            json_data: JSON data for the request body.
            data: Form data for the request body.
            files: Files to upload.
            headers: Additional headers.
            expected_status: List of expected HTTP status codes.
            endpoint_name: Name of the endpoint for error reporting.

        Returns
        -------
            The parsed JSON response.
        """
        if expected_status is None:
            expected_status = [200, 201]
        return self._request(
            "POST",
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
            headers=headers,
            expected_status=expected_status,
            endpoint_name=endpoint_name,
        )

    def put(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: list[int] | None = None,
        endpoint_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Make a PUT request to the Immich API.

        Args:
            path: The API path.
            params: Query parameters.
            json_data: JSON data for the request body.
            data: Form data for the request body.
            files: Files to upload.
            headers: Additional headers.
            expected_status: List of expected HTTP status codes.
            endpoint_name: Name of the endpoint for error reporting.

        Returns
        -------
            The parsed JSON response.
        """
        if expected_status is None:
            expected_status = [200]
        return self._request(
            "PUT",
            path,
            params=params,
            json_data=json_data,
            data=data,
            files=files,
            headers=headers,
            expected_status=expected_status,
            endpoint_name=endpoint_name,
        )

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_status: list[int] | None = None,
        endpoint_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Make a DELETE request to the Immich API.

        Args:
            path: The API path.
            params: Query parameters.
            json_data: JSON data for the request body.
            headers: Additional headers.
            expected_status: List of expected HTTP status codes.
            endpoint_name: Name of the endpoint for error reporting.

        Returns
        -------
            The parsed JSON response.
        """
        if expected_status is None:
            expected_status = [200, 204]
        return self._request(
            "DELETE",
            path,
            params=params,
            json_data=json_data,
            headers=headers,
            expected_status=expected_status,
            endpoint_name=endpoint_name,
        )

    def get_binary(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        endpoint_name: str | None = None,
    ) -> bytes:
        """
        Make a GET request to the Immich API and return binary data.

        Args:
            path: The API path.
            params: Query parameters.
            headers: Additional headers.
            endpoint_name: Name of the endpoint for error reporting.

        Returns
        -------
            The binary response content.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        url = self._make_url(path)
        request_headers = {"Accept": "application/octet-stream"}
        if headers:
            request_headers.update(headers)

        try:
            response = self.client.request(
                method="GET",
                url=url,
                params=params,
                headers=request_headers,
            )
            if response.status_code == 200:
                return response.content
            self._handle_response(response, endpoint_name or path)
        except httpx.RequestError as e:
            raise ImmichClientError(
                message=f"Request failed: {e!s}",
                endpoint=endpoint_name or path,
                method="GET",
                url=url,
            ) from e
        else:
            return b""  # This line will never be reached

    # Server API methods

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
        try:
            response = self.get("/server/ping", endpoint_name="PingServer")
            return response.get("res") == "pong"
        except ImmichClientError:
            return False

    def validate_connection(self) -> dict[str, Any]:
        """
        Validate the connection by querying the identity of the user.

        Returns
        -------
            The user information.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        result = self.get("/users/me", endpoint_name="ValidateConnection")
        self._load_supported_media_types()
        return result

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
        return self.get("/server/statistics", endpoint_name="GetServerStatistics")

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
        return self.get("/assets/statistics", endpoint_name="GetAssetStatistics")

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
        response = self.get(
            "/server/media-types", endpoint_name="GetSupportedMediaTypes"
        )
        media_types: dict[str, str] = {}
        for media_type, extensions in response.items():
            for ext in extensions:
                media_types[ext] = media_type

        # Add some additional types
        media_types[".mp"] = "useless"
        media_types[".json"] = "sidecar"
        media_types[".csv"] = "meta"

        return media_types

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
        return self.get("/server/about", endpoint_name="GetAboutInfo")

    # Asset API methods

    def get_asset_info(self, asset_id: str) -> dict[str, Any]:
        """
        Get information about an asset.

        Args:
            asset_id: The ID of the asset.

        Returns
        -------
            Information about the asset.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.get(f"/assets/{asset_id}", endpoint_name="GetAssetInfo")

    def download_asset(self, asset_id: str) -> bytes:
        """
        Download an asset.

        Args:
            asset_id: The ID of the asset.

        Returns
        -------
            The asset data.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.get_binary(
            f"/assets/{asset_id}/original", endpoint_name="DownloadAsset"
        )

    def update_asset(self, asset_id: str, **fields) -> dict[str, Any]:
        """
        Update an asset.

        Args:
            asset_id: The ID of the asset.
            **fields: Fields to update.

        Returns
        -------
            The updated asset information.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.put(
            f"/assets/{asset_id}",
            json_data=fields,
            endpoint_name="UpdateAsset",
        )

    def delete_assets(
        self, asset_ids: list[str], force_delete: bool = False
    ) -> dict[str, Any]:
        """
        Delete assets.

        Args:
            asset_ids: The IDs of the assets to delete.
            force_delete: If True, permanently delete the assets.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.delete(
            "/assets",
            json_data={"ids": asset_ids, "force": force_delete},
            endpoint_name="DeleteAssets",
        )

    def update_assets(
        self,
        asset_ids: list[str],
        *,
        is_archived: bool = False,
        is_favorite: bool = False,
        latitude: float = 0.0,
        longitude: float = 0.0,
        remove_parent: bool = False,
        stack_parent_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Update multiple assets.

        Args:
            asset_ids: The IDs of the assets to update.
            is_archived: Whether the assets are archived.
            is_favorite: Whether the assets are favorites.
            latitude: The latitude of the assets.
            longitude: The longitude of the assets.
            remove_parent: Whether to remove the parent stack.
            stack_parent_id: The ID of the parent stack.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = {
            "ids": asset_ids,
            "isArchived": is_archived,
            "isFavorite": is_favorite,
            "latitude": latitude,
            "longitude": longitude,
            "removeParent": remove_parent,
        }
        if stack_parent_id:
            data["stackParentId"] = stack_parent_id

        return self.put("/assets", json_data=data, endpoint_name="UpdateAssets")

    def upload_asset(
        self,
        file_path: str | Path,
        *,
        device_asset_id: str | None = None,
        device_id: str | None = None,
        is_favorite: bool = False,
        is_archived: bool = False,
        file_created_at: datetime | None = None,
        file_modified_at: datetime | None = None,
        duration: str = "00:00:00.000000",
        is_read_only: bool = False,
        sidecar_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Upload an asset.

        Args:
            file_path: The path to the file to upload.
            device_asset_id: The device asset ID.
            device_id: The device ID.
            is_favorite: Whether the asset is a favorite.
            is_archived: Whether the asset is archived.
            file_created_at: The creation date of the file.
            file_modified_at: The modification date of the file.
            duration: The duration of the asset (for videos).
            is_read_only: Whether the asset is read-only.
            sidecar_path: The path to a sidecar file to upload.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return {"id": "dry-run-id", "status": "created"}

        file_path = Path(file_path)
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ImmichClientError(msg)

        file_stat = file_path.stat()
        file_size = file_stat.st_size
        file_name = file_path.name
        file_ext = file_path.suffix.lower()

        # Determine asset type from extension
        asset_type = self._get_asset_type(file_ext)
        if asset_type not in ["image", "video"]:
            msg = f"Unsupported file type: {file_ext}"
            raise ImmichClientError(msg)

        # Prepare form data
        form_data = {
            "deviceAssetId": device_asset_id or f"{file_name}-{file_size}",
            "deviceId": device_id or self.device_uuid,
            "assetType": asset_type,
            "fileCreatedAt": (
                file_created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if file_created_at
                else datetime.fromtimestamp(file_stat.st_ctime).strftime(  # noqa: DTZ006
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            ),
            "fileModifiedAt": (
                file_modified_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if file_modified_at
                else datetime.fromtimestamp(file_stat.st_mtime).strftime(  # noqa: DTZ006
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            ),
            "isFavorite": str(is_favorite).lower(),
            "isArchived": str(is_archived).lower(),
            "fileExtension": file_ext,
            "duration": duration,
            "isReadOnly": str(is_read_only).lower(),
        }

        # Use context managers for file resources
        with Path.open(file_path, "rb") as asset_file:
            files = {
                "assetData": (
                    file_name,
                    asset_file,
                    self._get_mime_type(file_path),
                )
            }

            # Add sidecar if provided
            if sidecar_path:
                sidecar_path = Path(sidecar_path)
                if not sidecar_path.exists():
                    msg = f"Sidecar file not found: {sidecar_path}"
                    raise ImmichClientError(msg)

                with Path.open(sidecar_path, "rb") as sidecar_file:
                    files["sidecarData"] = (
                        sidecar_path.name,
                        sidecar_file,
                        self._get_mime_type(sidecar_path),
                    )

                    # Make the API request with all files now properly managed
                    return self.post(
                        "/assets",
                        data=form_data,
                        files=files,
                        endpoint_name="AssetUpload",
                    )

            # If no sidecar, just make the request with the asset file
            return self.post(
                "/assets",
                data=form_data,
                files=files,
                endpoint_name="AssetUpload",
            )

    def replace_asset(
        self,
        asset_id: str,
        file_path: str | Path,
        *,
        sidecar_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """
        Replace an asset.

        Args:
            asset_id: The ID of the asset to replace.
            file_path: The path to the file to upload.
            sidecar_path: The path to a sidecar file to upload.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return {"id": asset_id, "status": "replaced"}

        file_path = Path(file_path)
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ImmichClientError(msg)

        # Use context managers with Path.open
        with file_path.open("rb") as asset_file:
            files = {
                "assetData": (
                    file_path.name,
                    asset_file,
                    self._get_mime_type(file_path),
                )
            }

            # Add sidecar if provided
            if sidecar_path:
                sidecar_path = Path(sidecar_path)
                if not sidecar_path.exists():
                    msg = f"Sidecar file not found: {sidecar_path}"
                    raise ImmichClientError(msg)

                with sidecar_path.open("rb") as sidecar_file:
                    files["sidecarData"] = (
                        sidecar_path.name,
                        sidecar_file,
                        self._get_mime_type(sidecar_path),
                    )

                    # Make API request with both files properly managed
                    return self.put(
                        f"/assets/{asset_id}/original",
                        files=files,
                        endpoint_name="AssetReplace",
                    )

            # If no sidecar, just make the request with the asset file
            return self.put(
                f"/assets/{asset_id}/original",
                files=files,
                endpoint_name="AssetReplace",
            )

    def get_all_assets(self) -> list[dict[str, Any]]:
        """
        Get all assets.

        Returns
        -------
            A list of assets.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.search_assets(with_exif=True, is_visible=True, with_deleted=True)

    def search_assets(
        self,
        *,
        page: int = 1,
        page_size: int = 1000,
        with_exif: bool = True,
        is_visible: bool = True,
        with_deleted: bool = False,
        with_archived: bool = False,
        taken_before: str | None = None,
        taken_after: str | None = None,
        model: str | None = None,
        make: str | None = None,
        checksum: str | None = None,
        original_file_name: str | None = None,
        id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for assets.

        Args:
            page: The page number.
            page_size: The number of assets per page.
            with_exif: Whether to include EXIF data.
            is_visible: Whether to include visible assets.
            with_deleted: Whether to include deleted assets.
            with_archived: Whether to include archived assets.
            taken_before: Only include assets taken before this date.
            taken_after: Only include assets taken after this date.
            model: Only include assets with this camera model.
            make: Only include assets with this camera make.
            checksum: Only include assets with this checksum.
            original_file_name: Only include assets with this original file name.

        Returns
        -------
            A list of assets.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        query = {
            "page": page,
            "size": page_size,
            "withExif": with_exif,
            "isVisible": is_visible,
            "withDeleted": with_deleted,
            "withArchived": with_archived,
        }

        if taken_before:
            query["takenBefore"] = taken_before
        if taken_after:
            query["takenAfter"] = taken_after
        if model:
            query["model"] = model
        if make:
            query["make"] = make
        if checksum:
            query["checksum"] = checksum
        if original_file_name:
            query["originalFileName"] = original_file_name
        if id:
            query["id"] = id

        assets = []
        while True:
            response = self.post(
                "/search/metadata",
                json_data=query,
                endpoint_name="SearchMetadata",
            )
            items = response.get("assets", {}).get("items", [])
            assets.extend(items)

            next_page = response.get("assets", {}).get("nextPage")
            if not next_page:
                break
            query["page"] = int(next_page)

        return assets

    def get_assets_by_hash(self, checksum: str) -> list[dict[str, Any]]:
        """
        Get assets by hash.

        Args:
            checksum: The checksum to search for.

        Returns
        -------
            A list of assets with the given checksum.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        assets = self.search_assets(checksum=checksum)
        return [asset for asset in assets if asset.get("checksum") == checksum]

    def get_assets_by_name(self, name: str) -> list[dict[str, Any]]:
        """
        Get assets by original file name.

        Args:
            name: The original file name to search for.

        Returns
        -------
            A list of assets with the given original file name.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        assets = self.search_assets(original_file_name=name)
        return [asset for asset in assets if asset.get("originalFileName") == name]

    # Album API methods

    def get_all_albums(self) -> list[dict[str, Any]]:
        """
        Get all albums.

        Returns
        -------
            A list of albums.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.get("/albums", endpoint_name="GetAllAlbums")

    def get_album_info(
        self, album_id: str, without_assets: bool = False
    ) -> dict[str, Any]:
        """
        Get information about an album.

        Args:
            album_id: The ID of the album.
            without_assets: Whether to exclude assets from the response.

        Returns
        -------
            Information about the album.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.get(
            f"/albums/{album_id}",
            params={"withoutAssets": str(without_assets).lower()},
            endpoint_name="GetAlbumInfo",
        )

    def add_assets_to_album(
        self, album_id: str, asset_ids: list[str]
    ) -> list[dict[str, Any]]:
        """
        Add assets to an album.

        Args:
            album_id: The ID of the album.
            asset_ids: The IDs of the assets to add.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return []

        return self.put(
            f"/albums/{album_id}/assets",
            json_data={"ids": asset_ids},
            endpoint_name="AddAssetToAlbum",
        )

    def create_album(
        self,
        album_name: str,
        description: str = "",
        asset_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create an album.

        Args:
            album_name: The name of the album.
            description: The description of the album.
            asset_ids: The IDs of assets to add to the album.

        Returns
        -------
            The created album.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return {
                "id": "dry-run-id",
                "albumName": album_name,
                "description": description,
            }

        data = {
            "albumName": album_name,
            "description": description,
        }
        if asset_ids:
            data["assetIds"] = asset_ids

        return self.post(
            "/albums",
            json_data=data,
            endpoint_name="CreateAlbum",
        )

    def get_asset_albums(self, asset_id: str) -> list[dict[str, Any]]:
        """
        Get all albums that an asset belongs to.

        Args:
            asset_id: The ID of the asset.

        Returns
        -------
            A list of albums.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.get(
            "/albums",
            params={"assetId": asset_id},
            endpoint_name="GetAssetAlbums",
        )

    def delete_album(self, album_id: str) -> dict[str, Any]:
        """
        Delete an album.

        Args:
            album_id: The ID of the album.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return {}

        return self.delete(
            f"/albums/{album_id}",
            endpoint_name="DeleteAlbum",
        )

    # Tag API methods

    def get_all_tags(self) -> list[dict[str, Any]]:
        """
        Get all tags.

        Returns
        -------
            A list of tags.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.get("/tags", endpoint_name="GetAllTags")

    def upsert_tags(self, tags: list[str]) -> list[dict[str, Any]]:
        """
        Create or update tags.

        Args:
            tags: The tags to create or update.

        Returns
        -------
            The created or updated tags.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return [
                {"id": f"dry-run-id-{i}", "name": tag, "value": tag}
                for i, tag in enumerate(tags)
            ]

        return self.put(
            "/tags",
            json_data={"tags": tags},
            endpoint_name="UpsertTags",
        )

    def tag_assets(self, tag_id: str, asset_ids: list[str]) -> list[dict[str, Any]]:
        """
        Tag assets.

        Args:
            tag_id: The ID of the tag.
            asset_ids: The IDs of the assets to tag.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return [{"id": asset_id, "success": True} for asset_id in asset_ids]

        return self.put(
            f"/tags/{tag_id}/assets",
            json_data={"ids": asset_ids},
            endpoint_name="TagAssets",
        )

    def bulk_tag_assets(
        self, tag_ids: list[str], asset_ids: list[str]
    ) -> dict[str, Any]:
        """
        Tag multiple assets with multiple tags.

        Args:
            tag_ids: The IDs of the tags.
            asset_ids: The IDs of the assets to tag.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if self.dry_run:
            return {"count": len(asset_ids)}

        return self.put(
            "/tags/assets",
            json_data={"tagIds": tag_ids, "assetIds": asset_ids},
            endpoint_name="BulkTagAssets",
        )

    # Stack API methods

    def create_stack(self, asset_ids: list[str]) -> str:
        """
        Create a stack with the given assets.

        Args:
            asset_ids: The IDs of the assets to stack. The first asset will be the cover.

        Returns
        -------
            The ID of the created stack.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        if len(asset_ids) < 2:
            msg = "Stack must have at least 2 assets"
            raise ImmichClientError(msg)

        if self.dry_run:
            return "dry-run-stack-id"

        response = self.post(
            "/stacks",
            json_data={"assetIds": asset_ids},
            endpoint_name="CreateStack",
        )
        return response.get("id", "")

    # Job API methods

    def get_jobs(self) -> dict[str, Any]:
        """
        Get all jobs.

        Returns
        -------
            A dictionary of jobs.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.get("/jobs", endpoint_name="GetJobs")

    def send_job_command(
        self, job_id: str, command: str, force: bool = False
    ) -> dict[str, Any]:
        """
        Send a command to a job.

        Args:
            job_id: The ID of the job.
            command: The command to send (start, pause, resume, empty, clear-failed).
            force: Whether to force the command.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.put(
            f"/jobs/{job_id}",
            json_data={"command": command, "force": force},
            endpoint_name="SendJobCommand",
        )

    def create_job(self, name: str) -> dict[str, Any]:
        """
        Create a job.

        Args:
            name: The name of the job (person-cleanup, tag-cleanup, user-cleanup).

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.post(
            "/jobs",
            json_data={"name": name},
            endpoint_name="CreateJob",
        )

    # Helper methods

    def _get_asset_type(self, extension: str) -> str:
        """
        Get the asset type from a file extension.

        Args:
            extension: The file extension.

        Returns
        -------
            The asset type.
        """
        self._load_supported_media_types()
        extension = extension.lower()
        if not extension.startswith("."):
            extension = f".{extension}"

        return self._supported_media_types.get(extension, "unknown")

    def _load_supported_media_types(self) -> None:
        # Lazily populate supported media types if empty
        if not self._supported_media_types:
            self._supported_media_types = self.get_supported_media_types()

    def _get_mime_type(self, file_path: str | Path) -> str:
        """
        Get the MIME type of a file.

        Args:
            file_path: The path to the file.

        Returns
        -------
            The MIME type.
        """
        file_path = str(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            # Default to binary
            mime_type = "application/octet-stream"
        return mime_type

    def is_extension_supported(self, extension: str) -> bool:
        """
        Check if a file extension is supported.

        Args:
            extension: The file extension.

        Returns
        -------
            True if the extension is supported, False otherwise.
        """
        self._load_supported_media_types()

        extension = extension.lower()
        if not extension.startswith("."):
            extension = f".{extension}"

        return extension in self._supported_media_types and self._supported_media_types[
            extension
        ] in ["image", "video"]

    def is_extension_ignored(self, extension: str) -> bool:
        """
        Check if a file extension is ignored.

        Args:
            extension: The file extension.

        Returns
        -------
            True if the extension is ignored, False otherwise.
        """
        self._load_supported_media_types()

        extension = extension.lower()
        if not extension.startswith("."):
            extension = f".{extension}"

        return extension in self._supported_media_types and self._supported_media_types[
            extension
        ] in ["useless", "sidecar", "meta"]
