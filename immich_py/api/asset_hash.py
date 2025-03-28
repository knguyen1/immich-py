# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Asset hashing utilities for the Immich API.

This module contains utilities for hashing assets and tracking them in a database.
"""

import hashlib
import threading
from collections.abc import Callable
from pathlib import Path

# Default chunk size for file reading
CHUNK_SIZE = 4096


def _create_hash_function(hash_obj) -> Callable[[Path], str]:
    """
    Create a file hashing function using the provided hash object.

    Args:
        hash_obj: A hash object with update() and hexdigest() methods

    Returns
    -------
        A function that calculates the hash of a file
    """

    def hasher(file_path: Path) -> str:
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        with file_path.open("rb") as f:
            # Read and update hash in chunks to avoid loading large files into memory
            for byte_block in iter(lambda: f.read(CHUNK_SIZE), b""):
                hash_obj.update(byte_block)

        return hash_obj.hexdigest()

    return hasher


# Try to use xxHash for better performance, fall back to SHA256 if unavailable
try:
    import xxhash

    def hash_file(file_path: str | Path) -> str:
        """
        Calculate the xxHash3_64 hash of a file.

        xxHash3 is a non-cryptographic hash function that is extremely fast
        and has excellent collision resistance for file identification.
        It's much faster than SHA256 while still being suitable for this use case.

        Args:
            file_path: The path to the file.

        Returns
        -------
            The xxHash3_64 hash of the file as a hexadecimal string.

        Raises
        ------
            FileNotFoundError: If the file does not exist.
        """
        return _create_hash_function(xxhash.xxh3_64())(Path(file_path))

except ImportError:

    def hash_file(file_path: str | Path) -> str:
        """
        Calculate the SHA256 hash of a file.

        Falls back to SHA256 if xxHash is not available.

        Args:
            file_path: The path to the file.

        Returns
        -------
            The SHA256 hash of the file as a hexadecimal string.

        Raises
        ------
            FileNotFoundError: If the file does not exist.
        """
        return _create_hash_function(hashlib.sha256())(Path(file_path))


class AssetHashDatabase:
    """Thread-safe database for tracking uploaded asset hashes."""

    def __init__(self, db_path: str | Path | None = None):
        """
        Initialize the asset hash database.

        Args:
            db_path: The path to the database file. If None, defaults to ~/.immich-py/uploaded_assets.db
        """
        if db_path is None:
            # Use the default path
            home_dir = Path.home()
            db_dir = home_dir / ".immich-py"
            db_dir.mkdir(exist_ok=True)
            self.db_path = db_dir / "uploaded_assets.db"
        else:
            self.db_path = Path(db_path)
            # Ensure the directory exists
            self.db_path.parent.mkdir(exist_ok=True)

        # Create the file if it doesn't exist
        if not self.db_path.exists():
            self.db_path.touch()

        # Initialize in-memory cache
        self._hash_cache = set()

        # Initialize lock for thread-safety
        self._lock = threading.Lock()

        self._load_cache()

    def _load_cache(self) -> None:
        """Load all hashes from the database file into memory."""
        with self._lock:
            if not self.db_path.exists():
                self._hash_cache.clear()
                return

            # Clear the cache before reloading
            self._hash_cache.clear()

            with self.db_path.open("r") as f:
                for line in f:
                    hash_value = line.strip()
                    if hash_value:
                        self._hash_cache.add(hash_value)

    def contains_hash(self, file_hash: str) -> bool:
        """
        Check if a hash is in the database.

        Args:
            file_hash: The hash to check.

        Returns
        -------
            True if the hash is in the database, False otherwise.
        """
        with self._lock:
            if not self.db_path.exists():
                return False
            return file_hash in self._hash_cache

    def add_hash(self, file_hash: str) -> None:
        """
        Add a hash to the database.

        Args:
            file_hash: The hash to add.
        """
        with self._lock:
            if file_hash in self._hash_cache:
                return

            # Add to in-memory cache
            self._hash_cache.add(file_hash)

            # Write to file
            with self.db_path.open("a") as f:
                f.write(f"{file_hash}\n")
