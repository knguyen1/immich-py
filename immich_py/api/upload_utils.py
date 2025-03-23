# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Utility functions for uploading assets to Immich.

This module contains utility functions for uploading assets to Immich,
including handling directories and compressed archives.
"""

import concurrent.futures
import logging
import tarfile
import tempfile
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from immich_py.progress import add_album, remove_album

logger = logging.getLogger(__name__)


def is_supported_archive(file_path: str | Path) -> bool:
    """
    Check if a file is a supported archive format.

    Args:
        file_path: The path to the file.

    Returns
    -------
        True if the file is a supported archive format, False otherwise.
    """
    file_path = Path(file_path)
    lower_suffix = file_path.suffix.lower()
    return lower_suffix in [
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".tgz",
        ".tbz2",
        ".txz",
    ]


def extract_archive(archive_path: str | Path, extract_dir: str | Path) -> None:
    """
    Extract an archive to a directory.

    Args:
        archive_path: The path to the archive.
        extract_dir: The directory to extract to.

    Raises
    ------
        ValueError: If the archive format is not supported.
    """
    import click

    archive_path = Path(archive_path)
    extract_dir = Path(extract_dir)

    lower_suffix = archive_path.suffix.lower()

    # Echo that an archive is detected
    click.echo(f"Archive detected: {archive_path.name}")
    click.echo(f"Extracting to: {extract_dir}")

    if lower_suffix == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            # Get total number of files
            file_list = zip_ref.namelist()
            total_files = len(file_list)

            # Extract files with progress
            for i, file in enumerate(file_list, 1):
                zip_ref.extract(file, extract_dir)
                percent = (i / total_files) * 100
                click.echo(
                    f"\r{archive_path.name}: {i} / {total_files} ({percent:.1f}%)",
                    nl=False,
                )
            click.echo("\n")  # Print a newline after the progress is complete
    elif lower_suffix in [
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".tgz",
        ".tbz2",
        ".txz",
    ] or archive_path.name.endswith((".tar.gz", ".tar.bz2", ".tar.xz")):
        with tarfile.open(archive_path) as tar_ref:
            # Get total number of files
            members = tar_ref.getmembers()
            total_files = len(members)
            extracted_count = 0

            # Filter out potentially dangerous paths and extract with progress
            for member in members:
                member_path = Path(member.name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    continue  # Skip potentially dangerous paths

                tar_ref.extract(member, extract_dir)
                extracted_count += 1
                percent = (extracted_count / total_files) * 100
                click.echo(
                    f"\r{archive_path.name}: {extracted_count} / {total_files} ({percent:.1f}%)",
                    nl=False,
                )
            click.echo("\n")  # Print a newline after the progress is complete
    else:
        msg = f"Unsupported archive format: {archive_path}"
        raise ValueError(msg)


def process_directory(
    directory_path: str | Path,
    upload_func: Callable[[str | Path, dict[str, Any]], dict[str, Any]],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Process a directory and upload all supported assets.

    Args:
        directory_path: The path to the directory.
        upload_func: The function to call for each asset.
        **kwargs: Additional arguments to pass to the upload function.

    Returns
    -------
        A list of responses from the upload function.
    """
    directory_path = Path(directory_path)
    results = []

    # Get all files in the directory
    files = [
        item
        for item in directory_path.rglob("*")
        if item.is_file() and not item.name.startswith(".")
    ]

    # Add directory name as album title for progress display
    album_name = directory_path.name
    add_album(album_name)

    try:
        # Use ThreadPoolExecutor for parallel uploads
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit all upload tasks
            future_to_file = {
                executor.submit(upload_file, upload_func, file_path, kwargs): file_path
                for file_path in files
            }

            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception:
                    logger.exception("Error uploading %s", file_path)
                    # Log the error but continue with other files
    finally:
        # Remove album title from progress display
        remove_album(album_name)

    return results


def upload_file(
    upload_func: Callable[[str | Path, dict[str, Any]], dict[str, Any]],
    file_path: Path,
    kwargs: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Upload a single file.

    Args:
        upload_func: The function to call for the file.
        file_path: The path to the file.
        kwargs: Additional arguments to pass to the upload function.

    Returns
    -------
        The response from the upload function, or None if an error occurred.
    """
    try:
        return upload_func(file_path, **kwargs)
    except Exception:
        logger.exception("Error uploading %s", file_path)
        return None


def process_archive(
    archive_path: str | Path,
    upload_func: Callable[[str | Path, dict[str, Any]], dict[str, Any]],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """
    Process an archive and upload all supported assets.

    Args:
        archive_path: The path to the archive.
        upload_func: The function to call for each asset.
        **kwargs: Additional arguments to pass to the upload function.

    Returns
    -------
        A list of responses from the upload function.

    Raises
    ------
        ValueError: If the archive format is not supported.
    """
    import click

    archive_path = Path(archive_path)

    if not is_supported_archive(archive_path):
        msg = f"Unsupported archive format: {archive_path}"
        raise ValueError(msg)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract the archive
        extract_archive(archive_path, temp_dir)

        # Echo completion of extraction
        click.echo(f"Extraction of {archive_path.name} complete. Processing files...")

        # Process the extracted files
        return process_directory(temp_dir, upload_func, **kwargs)


def process_upload_path(
    file_path: str | Path,
    upload_func: Callable[[str | Path, dict[str, Any]], dict[str, Any]],
    **kwargs: Any,
) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Process a file path and upload assets.

    If the path is a directory, upload all assets in the directory.
    If the path is an archive, extract it and upload all assets.
    If the path is a file, upload it directly.

    Args:
        file_path: The path to the file or directory.
        upload_func: The function to call for each asset.
        **kwargs: Additional arguments to pass to the upload function.

    Returns
    -------
        A list of responses from the upload function if multiple files were uploaded,
        or a single response if only one file was uploaded.

    Raises
    ------
        FileNotFoundError: If the file or directory does not exist.
        ValueError: If the archive format is not supported.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        msg = f"File or directory not found: {file_path}"
        raise FileNotFoundError(msg)

    if file_path.is_dir():
        return process_directory(file_path, upload_func, **kwargs)
    if is_supported_archive(file_path):
        return process_archive(file_path, upload_func, **kwargs)
    # Single file upload
    return upload_func(file_path, **kwargs)
