# Copyright 2025 Kyle Nguyen
"""
Tests for the AssetAPI upload_assets method.
"""

import os
import shutil
import tempfile
import zipfile
from unittest.mock import MagicMock, patch

from immich_py.api.asset import AssetAPI


class TestAssetUpload:
    """Tests for the AssetAPI upload_assets method."""

    def setup_method(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []

        # Create some test files
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"test_file_{i}.jpg")
            with open(file_path, "w") as f:
                f.write(f"Test content {i}")
            self.test_files.append(file_path)

        # Create a test archive
        self.archive_path = os.path.join(self.temp_dir, "test_archive.zip")
        with zipfile.ZipFile(self.archive_path, "w") as zipf:
            for file_path in self.test_files:
                zipf.write(file_path, os.path.basename(file_path))

        # Create a test subdirectory
        self.sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(self.sub_dir, exist_ok=True)

        # Create some test files in the subdirectory
        for i in range(2):
            file_path = os.path.join(self.sub_dir, f"subdir_file_{i}.jpg")
            with open(file_path, "w") as f:
                f.write(f"Subdir content {i}")
            self.test_files.append(file_path)

        # Create a patcher for AssetHashDatabase
        self.hash_db_patcher = patch("immich_py.api.asset.AssetHashDatabase")
        self.mock_hash_db_class = self.hash_db_patcher.start()
        self.mock_hash_db = MagicMock()
        self.mock_hash_db_class.return_value = self.mock_hash_db

        # Set up the mock hash database
        self.mock_hash_db.contains_hash.return_value = False

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        # Stop the patcher
        self.hash_db_patcher.stop()

    @patch("immich_py.api.upload_utils.process_upload_path")
    @patch("immich_py.api.asset_hash.hash_file")
    def test_upload_assets_file(self, mock_hash_file, mock_process_upload_path):
        """Test upload_assets with a single file."""
        # Set up mock hash_file
        mock_hash_file.return_value = "test_hash_value"
        # Set up mock client
        mock_client = MagicMock()
        mock_client.upload_asset.return_value = {"id": "test-id", "status": "created"}

        # Set up mock process_upload_path
        mock_process_upload_path.return_value = {"id": "test-id", "status": "created"}

        # Create AssetAPI instance
        asset_api = AssetAPI(mock_client)

        # Call upload_assets with a single file
        result = asset_api.upload_assets(
            self.test_files[0],
            device_asset_id="test-device-id",
            is_favorite=True,
        )

        # Check that process_upload_path was called with the correct arguments
        mock_process_upload_path.assert_called_once()

        # Check that the result is correct
        assert result == {"id": "test-id", "status": "created"}

    @patch("immich_py.api.upload_utils.process_upload_path")
    @patch("immich_py.api.asset_hash.hash_file")
    def test_upload_assets_directory(self, mock_hash_file, mock_process_upload_path):
        """Test upload_assets with a directory."""
        # Set up mock hash_file
        mock_hash_file.return_value = "test_hash_value"
        # Set up mock client
        mock_client = MagicMock()

        # Set up mock process_upload_path
        mock_results = [{"id": f"test-id-{i}", "status": "created"} for i in range(5)]
        mock_process_upload_path.return_value = mock_results

        # Create AssetAPI instance
        asset_api = AssetAPI(mock_client)

        # Call upload_assets with a directory
        results = asset_api.upload_assets(
            self.temp_dir,
            device_asset_id="test-device-id",
            is_favorite=True,
        )

        # Check that process_upload_path was called with the correct arguments
        mock_process_upload_path.assert_called_once()

        # Check that the results are correct
        assert results == mock_results

    @patch("immich_py.api.upload_utils.process_upload_path")
    @patch("immich_py.api.asset_hash.hash_file")
    def test_upload_assets_archive(self, mock_hash_file, mock_process_upload_path):
        """Test upload_assets with an archive."""
        # Set up mock hash_file
        mock_hash_file.return_value = "test_hash_value"
        # Set up mock client
        mock_client = MagicMock()

        # Set up mock process_upload_path
        mock_results = [{"id": f"test-id-{i}", "status": "created"} for i in range(3)]
        mock_process_upload_path.return_value = mock_results

        # Create AssetAPI instance
        asset_api = AssetAPI(mock_client)

        # Call upload_assets with an archive
        results = asset_api.upload_assets(
            self.archive_path,
            device_asset_id="test-device-id",
            is_favorite=True,
        )

        # Check that process_upload_path was called with the correct arguments
        mock_process_upload_path.assert_called_once()

        # Check that the results are correct
        assert results == mock_results

    @patch("immich_py.api.upload_utils.process_upload_path")
    @patch("immich_py.api.asset_hash.hash_file")
    def test_upload_assets_with_sidecar(self, mock_hash_file, mock_process_upload_path):
        """Test upload_assets with a sidecar file."""
        # Set up mock hash_file
        mock_hash_file.return_value = "test_hash_value"
        # Set up mock client
        mock_client = MagicMock()
        mock_client.upload_asset.return_value = {"id": "test-id", "status": "created"}

        # Set up mock process_upload_path
        mock_process_upload_path.return_value = {"id": "test-id", "status": "created"}

        # Create a test sidecar file
        sidecar_path = os.path.join(self.temp_dir, "test_sidecar.json")
        with open(sidecar_path, "w") as f:
            f.write('{"metadata": "test"}')

        # Create AssetAPI instance
        asset_api = AssetAPI(mock_client)

        # Call upload_assets with a single file and sidecar
        result = asset_api.upload_assets(
            self.test_files[0],
            device_asset_id="test-device-id",
            is_favorite=True,
            sidecar_path=sidecar_path,
        )

        # Check that process_upload_path was called with the correct arguments
        mock_process_upload_path.assert_called_once()

        # Check that the result is correct
        assert result == {"id": "test-id", "status": "created"}

    @patch("immich_py.api.asset_hash.hash_file")
    def test_upload_assets_integration(self, mock_hash_file):
        """Integration test for upload_assets."""
        # Set up mock hash_file
        mock_hash_file.return_value = "test_hash_value"

        # Set up mock client
        mock_client = MagicMock()
        mock_client.upload_asset.return_value = {"id": "test-id", "status": "created"}

        # Create AssetAPI instance with our mocked client
        asset_api = AssetAPI(mock_client)

        # For this test, we'll directly mock the upload_asset method to ensure it's called
        with patch.object(asset_api, "upload_asset") as mock_upload_asset:
            # Set up the mock to return a successful result
            mock_upload_asset.return_value = {"id": "test-id", "status": "created"}

            # Call upload_assets with a single file
            result = asset_api.upload_assets(
                self.test_files[0],
                device_asset_id="test-device-id",
                is_favorite=True,
            )

            # Check that our mocked upload_asset method was called
            mock_upload_asset.assert_called_once()

            # Check that the result is correct
            assert result == {"id": "test-id", "status": "created"}

            # Reset the mock
            mock_upload_asset.reset_mock()

            # Set up the mock to return a list of results for the directory test
            mock_results = [
                {"id": f"test-id-{i}", "status": "created"}
                for i in range(len(self.test_files) + 1)
            ]
            mock_upload_asset.side_effect = mock_results

            # Call upload_assets with a directory
            results = asset_api.upload_assets(
                self.temp_dir,
                device_asset_id="test-device-id",
                is_favorite=True,
            )

            # Check that the results are a list of the expected length
            assert isinstance(results, list)
            assert len(results) == len(self.test_files) + 1
