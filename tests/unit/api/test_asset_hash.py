# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Tests for the asset_hash module.
"""

import os
import shutil
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from immich_py.api.asset_hash import (
    AssetHashDatabase,
    _create_hash_function,
    hash_file,
)


class TestAssetHash:
    """Tests for the asset_hash module."""

    def setup_method(self):
        """Set up test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

        # Create a test file with known content
        self.test_file_path = Path(self.temp_dir) / "test_file.txt"
        with open(self.test_file_path, "w") as f:
            f.write("Test content for hashing")

        # Create a temporary directory for the database
        self.db_dir = tempfile.mkdtemp()
        self.db_path = Path(self.db_dir) / "test_hash_db.txt"

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.db_dir)

    def test_hash_file_exists(self):
        """Test hash_file with an existing file."""
        # Get the hash of the test file
        file_hash = hash_file(self.test_file_path)

        # Verify the hash is a non-empty string
        assert isinstance(file_hash, str)
        assert len(file_hash) > 0

    def test_hash_file_not_found(self):
        """Test hash_file with a non-existent file."""
        non_existent_file = Path(self.temp_dir) / "non_existent_file.txt"

        # Verify that FileNotFoundError is raised
        with pytest.raises(FileNotFoundError):
            hash_file(non_existent_file)

    def test_hash_file_different_contents(self):
        """Test hash_file with different file contents."""
        # Create two files with different contents
        file1_path = Path(self.temp_dir) / "file1.txt"
        file2_path = Path(self.temp_dir) / "file2.txt"

        with open(file1_path, "w") as f:
            f.write("Content for file 1")

        with open(file2_path, "w") as f:
            f.write("Different content for file 2")

        # Get hashes for both files
        hash1 = hash_file(file1_path)
        hash2 = hash_file(file2_path)

        # Verify that the hashes are different
        assert hash1 != hash2

    def test_hash_file_same_contents(self):
        """Test hash_file with identical file contents."""
        # Create two files with the same content
        file1_path = Path(self.temp_dir) / "file1_same.txt"
        file2_path = Path(self.temp_dir) / "file2_same.txt"

        identical_content = "Identical content for both files"

        with open(file1_path, "w") as f:
            f.write(identical_content)

        with open(file2_path, "w") as f:
            f.write(identical_content)

        # Get hashes for both files
        hash1 = hash_file(file1_path)
        hash2 = hash_file(file2_path)

        # Verify that the hashes are the same
        assert hash1 == hash2

    def test_hash_file_accepts_string_path(self):
        """Test hash_file accepts string paths."""
        # Test with string path
        string_path = str(self.test_file_path)
        file_hash = hash_file(string_path)

        # Verify the hash is a non-empty string
        assert isinstance(file_hash, str)
        assert len(file_hash) > 0

    def test_create_hash_function(self):
        """Test the _create_hash_function utility."""

        # Create a mock hash object
        class MockHashObj:
            def __init__(self):
                self.data = b""

            def update(self, data):
                self.data += data

            def hexdigest(self):
                return "mock_hash_digest"

        mock_hash = MockHashObj()
        hasher_func = _create_hash_function(mock_hash)

        # Test the hasher function
        result = hasher_func(self.test_file_path)
        assert result == "mock_hash_digest"

        # Verify that the hash object was updated with the file content
        assert len(mock_hash.data) > 0

    def test_asset_hash_database_init_default(self):
        """Test AssetHashDatabase initialization with default path."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path(self.temp_dir)

            # Initialize with default path
            db = AssetHashDatabase()

            # Verify the default path
            expected_path = Path(self.temp_dir) / ".immich-py" / "uploaded_assets.db"
            assert db.db_path == expected_path

            # Verify the directory was created
            assert (Path(self.temp_dir) / ".immich-py").exists()

    def test_asset_hash_database_init_custom(self):
        """Test AssetHashDatabase initialization with custom path."""
        # Initialize with custom path
        db = AssetHashDatabase(self.db_path)

        # Verify the path
        assert db.db_path == self.db_path

        # Verify the directory was created
        assert self.db_path.parent.exists()

    def test_asset_hash_database_contains_hash_empty(self):
        """Test contains_hash with an empty database."""
        # Initialize the database
        db = AssetHashDatabase(self.db_path)

        # Check for a hash in the empty database
        result = db.contains_hash("test_hash")

        # Verify the result
        assert result is False

    def test_asset_hash_database_contains_hash_nonexistent(self):
        """Test contains_hash with a non-existent database."""
        # Initialize the database but delete the file
        db = AssetHashDatabase(self.db_path)
        os.remove(self.db_path)

        # Check for a hash in the non-existent database
        result = db.contains_hash("test_hash")

        # Verify the result
        assert result is False

    def test_asset_hash_database_add_and_contains_hash(self):
        """Test add_hash and contains_hash methods."""
        # Initialize the database
        db = AssetHashDatabase(self.db_path)

        # Add a hash to the database
        test_hash = "test_hash_value"
        db.add_hash(test_hash)

        # Check if the hash is in the database
        result = db.contains_hash(test_hash)

        # Verify the result
        assert result is True

        # Check for a hash that's not in the database
        result = db.contains_hash("different_hash")
        assert result is False

    def test_asset_hash_database_add_multiple_hashes(self):
        """Test adding multiple hashes to the database."""
        # Initialize the database
        db = AssetHashDatabase(self.db_path)

        # Add multiple hashes
        hashes = ["hash1", "hash2", "hash3"]
        for h in hashes:
            db.add_hash(h)

        # Check if all hashes are in the database
        for h in hashes:
            assert db.contains_hash(h) is True

        # Check for a hash that's not in the database
        assert db.contains_hash("not_in_db") is False

    def test_asset_hash_database_file_content(self):
        """Test the content of the database file."""
        # Initialize the database
        db = AssetHashDatabase(self.db_path)

        # Add hashes to the database
        hashes = ["hash1", "hash2", "hash3"]
        for h in hashes:
            db.add_hash(h)

        # Read the file content
        with open(self.db_path) as f:
            content = f.read()

        # Verify the content
        expected_content = "hash1\nhash2\nhash3\n"
        assert content == expected_content

    def test_xxhash_implementation(self):
        """Test the xxHash implementation of hash_file."""
        # Create a mock xxhash module
        xxhash_mock = MagicMock()
        xxh3_mock = MagicMock()
        xxhash_mock.xxh3_64.return_value = xxh3_mock
        xxh3_mock.hexdigest.return_value = "mock_xxhash_digest"

        # Save the original modules dictionary and xxhash import status
        original_modules = dict(sys.modules)
        had_xxhash = "xxhash" in sys.modules

        try:
            # Add our mock to sys.modules
            sys.modules["xxhash"] = xxhash_mock

            # Force reload of the asset_hash module to use our mock
            import importlib

            import immich_py.api.asset_hash

            importlib.reload(immich_py.api.asset_hash)

            # Import the reloaded hash_file function
            from immich_py.api.asset_hash import hash_file as mocked_hash_file

            # Test the xxHash implementation
            result = mocked_hash_file(self.test_file_path)
            assert result == "mock_xxhash_digest"

            # Verify xxhash was used
            xxhash_mock.xxh3_64.assert_called_once()
            xxh3_mock.hexdigest.assert_called_once()
        finally:
            # Restore the original modules dictionary
            if had_xxhash:
                sys.modules["xxhash"] = original_modules["xxhash"]
            elif "xxhash" in sys.modules:
                del sys.modules["xxhash"]

            # Reload the module to restore the original implementation
            importlib.reload(immich_py.api.asset_hash)

    def test_asset_hash_database_thread_safety(self):
        """Test thread safety of the AssetHashDatabase."""
        db = AssetHashDatabase(self.db_path)

        num_threads = 10
        hashes_per_thread = 50

        def add_hashes(thread_id):
            for i in range(hashes_per_thread):
                hash_value = f"thread_{thread_id}_hash_{i}"
                db.add_hash(hash_value)
                # Small sleep to increase the chance of thread interleaving
                time.sleep(0.001)

        # Create and start threads
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(add_hashes, i) for i in range(num_threads)]

            # Wait for all threads to complete
            for future in futures:
                future.result()

        # Verify that all hashes are added correctly
        # First, reload the database to ensure we're reading from disk
        new_db = AssetHashDatabase(self.db_path)

        # Check that all expected hashes are in the database
        for thread_id in range(num_threads):
            for i in range(hashes_per_thread):
                hash_value = f"thread_{thread_id}_hash_{i}"
                assert new_db.contains_hash(hash_value), f"Missing hash: {hash_value}"

        # Count the number of lines in the file to ensure no duplicates
        with Path.open(self.db_path) as f:
            lines = f.readlines()

        assert len(set(lines)) == len(lines), (
            "Duplicate hashes found in the database file"
        )

    def test_hash_keep_adding_a_duplicate(self):
        """Test that adding the same hash multiple times only writes it once."""
        db = AssetHashDatabase(self.db_path)

        test_hash = "duplicate_test_hash"
        for _ in range(5):
            db.add_hash(test_hash)

        with Path.open(self.db_path) as f:
            content = f.readlines()

        occurences = content.count(f"{test_hash}\n")
        assert occurences == 1, f"Hash was written {occurences} times"
