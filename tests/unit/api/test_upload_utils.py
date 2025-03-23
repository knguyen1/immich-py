# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Tests for the upload_utils module.
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from immich_py.api.upload_utils import (
    extract_archive,
    is_supported_archive,
    process_archive,
    process_directory,
    process_upload_path,
)


class TestUploadUtils:
    """Tests for the upload_utils module."""

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

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_is_supported_archive(self):
        """Test is_supported_archive function."""
        # Test supported archive formats
        assert is_supported_archive("test.zip")
        assert is_supported_archive("test.tar")
        assert is_supported_archive("test.gz")
        assert is_supported_archive("test.bz2")
        assert is_supported_archive("test.xz")
        assert is_supported_archive("test.tgz")
        assert is_supported_archive("test.tbz2")
        assert is_supported_archive("test.txz")
        assert is_supported_archive(Path("test.zip"))

        # Test unsupported formats
        assert not is_supported_archive("test.jpg")
        assert not is_supported_archive("test.txt")
        assert not is_supported_archive(Path("test.jpg"))

    def test_extract_archive(self, monkeypatch):
        """Test extract_archive function."""
        extract_dir = os.path.join(self.temp_dir, "extract")
        os.makedirs(extract_dir, exist_ok=True)

        # Mock click.echo to capture calls
        echo_calls = []
        monkeypatch.setattr("click.echo", lambda msg: echo_calls.append(msg))

        # Extract the test archive
        extract_archive(self.archive_path, extract_dir)

        # Check that all files were extracted
        for file_name in [os.path.basename(f) for f in self.test_files]:
            extracted_path = os.path.join(extract_dir, file_name)
            assert os.path.exists(extracted_path)

        # Verify that the expected messages were echoed
        assert any(
            f"Archive detected: {os.path.basename(self.archive_path)}" in call
            for call in echo_calls
        )
        assert any(f"Extracting to: {extract_dir}" in call for call in echo_calls)

        # Verify progress messages were echoed
        progress_messages = [
            call
            for call in echo_calls
            if f"{os.path.basename(self.archive_path)}:" in call
        ]
        assert len(progress_messages) > 0

        # The last progress message should show 100% completion
        last_progress = progress_messages[-1]
        assert "100.0%" in last_progress or "100%" in last_progress

        # Test with unsupported format
        echo_calls.clear()
        with pytest.raises(ValueError, match=r"Unsupported archive format:*"):
            extract_archive(self.test_files[0], extract_dir)

    def test_process_directory(self):
        """Test process_directory function."""
        # Create a mock upload function
        upload_func = MagicMock(return_value={"id": "test-id", "status": "created"})

        # Process the directory
        results = process_directory(self.temp_dir, upload_func, test_arg="test_value")

        # Check that the upload function was called for each file
        assert upload_func.call_count == len(self.test_files) + 1  # +1 for the archive
        assert len(results) == len(self.test_files) + 1

        # Check that the kwargs were passed correctly
        for call in upload_func.call_args_list:
            assert call[1]["test_arg"] == "test_value"

    def test_process_archive(self, monkeypatch):
        """Test process_archive function."""
        # Create a mock upload function
        upload_func = MagicMock(return_value={"id": "test-id", "status": "created"})

        # Mock click.echo to capture calls
        echo_calls = []
        monkeypatch.setattr("click.echo", lambda msg: echo_calls.append(msg))

        # Process the archive
        results = process_archive(self.archive_path, upload_func, test_arg="test_value")

        # Check that the upload function was called for each file in the archive
        assert upload_func.call_count == len(self.test_files)
        assert len(results) == len(self.test_files)

        # Check that the kwargs were passed correctly
        for call in upload_func.call_args_list:
            assert call[1]["test_arg"] == "test_value"

        # Verify that the expected messages were echoed
        assert any(
            f"Archive detected: {os.path.basename(self.archive_path)}" in call
            for call in echo_calls
        )
        assert any(
            f"Extraction of {os.path.basename(self.archive_path)} complete" in call
            for call in echo_calls
        )

    def test_process_upload_path_file(self):
        """Test process_upload_path with a file."""
        # Create a mock upload function
        upload_func = MagicMock(return_value={"id": "test-id", "status": "created"})

        # Process a single file
        result = process_upload_path(
            self.test_files[0], upload_func, test_arg="test_value"
        )

        # Check that the upload function was called once
        upload_func.assert_called_once()
        assert result == {"id": "test-id", "status": "created"}

        # Check that the kwargs were passed correctly
        assert upload_func.call_args[1]["test_arg"] == "test_value"

    def test_process_upload_path_directory(self):
        """Test process_upload_path with a directory."""
        # Create a mock upload function
        upload_func = MagicMock(return_value={"id": "test-id", "status": "created"})

        # Process a directory
        results = process_upload_path(self.temp_dir, upload_func, test_arg="test_value")

        # Check that the upload function was called for each file
        assert upload_func.call_count == len(self.test_files) + 1  # +1 for the archive
        assert len(results) == len(self.test_files) + 1

        # Check that the kwargs were passed correctly
        for call in upload_func.call_args_list:
            assert call[1]["test_arg"] == "test_value"

    def test_process_upload_path_archive(self):
        """Test process_upload_path with an archive."""
        # Create a mock upload function
        upload_func = MagicMock(return_value={"id": "test-id", "status": "created"})

        # Process an archive
        results = process_upload_path(
            self.archive_path, upload_func, test_arg="test_value"
        )

        # Check that the upload function was called for each file in the archive
        assert upload_func.call_count == len(self.test_files)
        assert len(results) == len(self.test_files)

        # Check that the kwargs were passed correctly
        for call in upload_func.call_args_list:
            assert call[1]["test_arg"] == "test_value"

    def test_process_upload_path_not_found(self):
        """Test process_upload_path with a non-existent file."""
        # Create a mock upload function
        upload_func = MagicMock()

        # Process a non-existent file
        with pytest.raises(FileNotFoundError):
            process_upload_path("non_existent_file.jpg", upload_func)
