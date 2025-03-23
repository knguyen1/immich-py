# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""Tests for the immich_py.client module."""

import platform
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from immich_py.api.client import ImmichClient, ImmichClientError


class TestImmichClientError:
    """Tests for the ImmichClientError class."""

    @pytest.mark.parametrize(
        ("error_params", "expected_substrings"),
        [
            (
                {
                    "message": "Test error",
                    "status_code": 404,
                    "endpoint": "/test",
                    "method": "GET",
                    "url": "https://immich.example.com/api/test",
                },
                [
                    "Endpoint: /test",
                    "Request: GET https://immich.example.com/api/test",
                    "Status: 404",
                    "Error: Test error",
                ],
            ),
            (
                {"message": "Test error"},
                ["Error: Test error"],
            ),
        ],
    )
    def test_error_str(
        self, error_params: dict[str, Any], expected_substrings: list[str]
    ) -> None:
        """Test the string representation of ImmichClientError.

        Args:
            error_params: Parameters to create the error.
            expected_substrings: Substrings that should be in the error string.
        """
        error = ImmichClientError(**error_params)
        error_str = str(error)

        for substring in expected_substrings:
            assert substring in error_str


class TestImmichClient:
    """Tests for the ImmichClient class."""

    def test_init(self) -> None:
        """Test client initialization."""
        client = ImmichClient(
            endpoint="https://immich.example.com",
            api_key="test_api_key",
            verify_ssl=False,
            timeout=10.0,
            dry_run=True,
        )
        assert client.endpoint == "https://immich.example.com/api"
        assert client.api_key == "test_api_key"
        assert client.verify_ssl is False
        assert client.timeout == 10.0
        assert client.dry_run is True
        assert client.device_uuid == platform.node()
        assert client.retries == 1
        assert client.retry_delay == 1.0
        assert client._client is None

    def test_client_property(self) -> None:
        """Test the client property creates a new httpx client if needed."""
        client = ImmichClient(
            endpoint="https://immich.example.com",
            api_key="test_api_key",
        )
        assert client._client is None
        httpx_client = client.client
        assert isinstance(httpx_client, httpx.Client)
        assert httpx_client.headers["x-api-key"] == "test_api_key"
        # Second call should return the same client
        assert client.client is httpx_client

    def test_close(self, mock_client: ImmichClient) -> None:
        """Test closing the client.

        Args:
            mock_client: A mocked ImmichClient instance.
        """
        # Save the mock client before closing
        mock_http_client = mock_client._client
        mock_client.close()
        mock_http_client.close.assert_called_once()

    def test_make_url(self, mock_client: ImmichClient) -> None:
        """Test creating a full URL from a path.

        Args:
            mock_client: A mocked ImmichClient instance.
        """
        url = mock_client._make_url("/test")
        assert url == "https://immich.example.com/api/test"

    @pytest.mark.parametrize(
        ("status_code", "response_data", "expected_status", "expected_result"),
        [
            (200, {"success": True}, [200], {"success": True}),
            (204, None, [204], {}),
        ],
    )
    def test_handle_response_success(
        self,
        mock_client: ImmichClient,
        mock_response: MagicMock,
        status_code: int,
        response_data: dict[str, Any] | None,
        expected_status: list[int],
        expected_result: dict[str, Any],
    ) -> None:
        """Test handling a successful response.

        Args:
            mock_client: A mocked ImmichClient instance.
            mock_response: A mocked httpx.Response object.
            status_code: The HTTP status code to simulate.
            response_data: The response data to simulate.
            expected_status: The expected status codes to check against.
            expected_result: The expected result from handling the response.
        """
        mock_response.status_code = status_code
        if response_data is not None:
            mock_response.json.return_value = response_data

        result = mock_client._handle_response(
            mock_response, "/test", expected_status=expected_status
        )
        assert result == expected_result

    def test_handle_response_error(
        self, mock_client: ImmichClient, mock_response: MagicMock
    ) -> None:
        """Test handling an error response.

        Args:
            mock_client: A mocked ImmichClient instance.
            mock_response: A mocked httpx.Response object.
        """
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not found"}

        with pytest.raises(ImmichClientError) as excinfo:
            mock_client._handle_response(mock_response, "/test")

        assert excinfo.value.status_code == 404
        assert excinfo.value.endpoint == "/test"
        assert "Not found" in str(excinfo.value)

    def test_request_success(
        self, mock_client: ImmichClient, mock_response: MagicMock
    ) -> None:
        """Test making a successful request.

        Args:
            mock_client: A mocked ImmichClient instance.
            mock_response: A mocked httpx.Response object.
        """
        mock_client.client.request.return_value = mock_response

        result = mock_client._request("GET", "/test")

        mock_client.client.request.assert_called_once_with(
            method="GET",
            url="https://immich.example.com/api/test",
            params=None,
            json=None,
            data=None,
            files=None,
            headers={"Accept": "application/json"},
        )
        assert result == {"success": True}

    def test_request_dry_run(self, mock_client: ImmichClient) -> None:
        """Test making a request in dry run mode.

        Args:
            mock_client: A mocked ImmichClient instance.
        """
        mock_client.dry_run = True

        result = mock_client._request("POST", "/test")

        mock_client.client.request.assert_not_called()
        assert result == {}

    @pytest.mark.parametrize(
        (
            "method",
            "path",
            "kwargs",
            "expected_method",
            "expected_url",
            "expected_params",
            "expected_json",
            "expected_data",
            "expected_files",
        ),
        [
            (
                "get",
                "/test",
                {"params": {"key": "value"}},
                "GET",
                "https://immich.example.com/api/test",
                {"key": "value"},
                None,
                None,
                None,
            ),
            (
                "post",
                "/test",
                {"json_data": {"key": "value"}, "expected_status": [200, 201]},
                "POST",
                "https://immich.example.com/api/test",
                None,
                {"key": "value"},
                None,
                None,
            ),
            (
                "put",
                "/test",
                {"json_data": {"key": "value"}},
                "PUT",
                "https://immich.example.com/api/test",
                None,
                {"key": "value"},
                None,
                None,
            ),
            (
                "delete",
                "/test",
                {"json_data": {"key": "value"}, "expected_status": [200, 204]},
                "DELETE",
                "https://immich.example.com/api/test",
                None,
                {"key": "value"},
                None,
                None,
            ),
        ],
    )
    def test_http_methods(
        self,
        mock_client: ImmichClient,
        mock_response: MagicMock,
        method: str,
        path: str,
        kwargs: dict[str, Any],
        expected_method: str,
        expected_url: str,
        expected_params: dict[str, Any] | None,
        expected_json: dict[str, Any] | None,
        expected_data: dict[str, Any] | None,
        expected_files: dict[str, Any] | None,
    ) -> None:
        """Test the HTTP method wrappers (get, post, put, delete).

        Args:
            mock_client: A mocked ImmichClient instance.
            mock_response: A mocked httpx.Response object.
            method: The HTTP method to test.
            path: The API path to use.
            kwargs: Additional keyword arguments for the method.
            expected_method: The expected HTTP method in the request.
            expected_url: The expected URL in the request.
            expected_params: The expected query parameters in the request.
            expected_json: The expected JSON data in the request.
            expected_data: The expected form data in the request.
            expected_files: The expected files in the request.
        """
        mock_client.client.request.return_value = mock_response

        # Call the method dynamically
        result = getattr(mock_client, method)(path, **kwargs)

        mock_client.client.request.assert_called_once_with(
            method=expected_method,
            url=expected_url,
            params=expected_params,
            json=expected_json,
            data=expected_data,
            files=expected_files,
            headers={"Accept": "application/json"},
        )
        assert result == {"success": True}

    @pytest.mark.parametrize(
        ("response_value", "expected_result"),
        [
            ({"res": "pong"}, True),
            ({"res": "error"}, False),
        ],
    )
    def test_ping_server(
        self,
        mock_client: ImmichClient,
        response_value: dict[str, str],
        expected_result: bool,
    ) -> None:
        """Test server ping with different responses.

        Args:
            mock_client: A mocked ImmichClient instance.
            response_value: The value to return from the mock get method.
            expected_result: The expected result of ping_server.
        """
        mock_client.get = MagicMock(return_value=response_value)

        result = mock_client.ping_server()

        mock_client.get.assert_called_once_with(
            "/server/ping", endpoint_name="PingServer"
        )
        assert result is expected_result

    @pytest.mark.parametrize(
        (
            "method_name",
            "endpoint",
            "response_value",
            "expected_args",
            "expected_kwargs",
        ),
        [
            (
                "get_asset_info",
                "/assets/asset-id",
                {"id": "asset-id", "name": "test.jpg"},
                ["asset-id"],
                {"endpoint_name": "GetAssetInfo"},
            ),
            (
                "get_all_albums",
                "/albums",
                [{"id": "album-1"}, {"id": "album-2"}],
                [],
                {"endpoint_name": "GetAllAlbums"},
            ),
            (
                "get_all_tags",
                "/tags",
                [{"id": "tag-1"}, {"id": "tag-2"}],
                [],
                {"endpoint_name": "GetAllTags"},
            ),
            (
                "get_jobs",
                "/jobs",
                {"jobs": [{"id": "job-1"}, {"id": "job-2"}]},
                [],
                {"endpoint_name": "GetJobs"},
            ),
        ],
    )
    def test_api_methods(
        self,
        mock_client: ImmichClient,
        method_name: str,
        endpoint: str,
        response_value: Any,
        expected_args: list[Any],
        expected_kwargs: dict[str, Any],
    ) -> None:
        """Test various API methods.

        Args:
            mock_client: A mocked ImmichClient instance.
            method_name: The name of the method to test.
            endpoint: The expected endpoint in the get call.
            response_value: The value to return from the mock get method.
            expected_args: The expected positional arguments for the get call.
            expected_kwargs: The expected keyword arguments for the get call.
        """
        mock_client.get = MagicMock(return_value=response_value)

        # Call the method dynamically
        result = getattr(mock_client, method_name)(*expected_args)

        mock_client.get.assert_called_once_with(endpoint, **expected_kwargs)
        assert result == response_value

    @pytest.mark.parametrize(
        ("extension", "expected_type"),
        [
            (".jpg", "image"),
            ("jpg", "image"),
            (".mp4", "video"),
            (".json", "sidecar"),
            (".unknown", "unknown"),
        ],
    )
    def test_get_asset_type(
        self, mock_client: ImmichClient, extension: str, expected_type: str
    ) -> None:
        """Test getting asset type from extension.

        Args:
            mock_client: A mocked ImmichClient instance.
            extension: The file extension to test.
            expected_type: The expected asset type.
        """
        mock_client._supported_media_types = {
            ".jpg": "image",
            ".mp4": "video",
            ".json": "sidecar",
        }

        assert mock_client._get_asset_type(extension) == expected_type

    @pytest.mark.parametrize(
        ("extension", "expected_result"),
        [
            (".jpg", True),
            ("jpg", True),
            (".mp4", True),
            (".json", False),
            (".unknown", False),
        ],
    )
    def test_is_extension_supported(
        self, mock_client: ImmichClient, extension: str, expected_result: bool
    ) -> None:
        """Test checking if extension is supported.

        Args:
            mock_client: A mocked ImmichClient instance.
            extension: The file extension to test.
            expected_result: Whether the extension is expected to be supported.
        """
        mock_client._supported_media_types = {
            ".jpg": "image",
            ".mp4": "video",
            ".json": "sidecar",
        }

        assert mock_client.is_extension_supported(extension) is expected_result

    @pytest.mark.parametrize(
        ("extension", "expected_result"),
        [
            (".jpg", False),
            (".json", True),
            (".mp", True),
            (".unknown", False),
        ],
    )
    def test_is_extension_ignored(
        self, mock_client: ImmichClient, extension: str, expected_result: bool
    ) -> None:
        """Test checking if extension is ignored.

        Args:
            mock_client: A mocked ImmichClient instance.
            extension: The file extension to test.
            expected_result: Whether the extension is expected to be ignored.
        """
        mock_client._supported_media_types = {
            ".jpg": "image",
            ".mp4": "video",
            ".json": "sidecar",
            ".mp": "useless",
        }

        assert mock_client.is_extension_ignored(extension) is expected_result
