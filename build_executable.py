#!/usr/bin/env python3
# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Build script for creating the immich-py executable using PyInstaller.

This script is called by Poetry's build command to create the executable.
"""

import logging
import platform
import shutil
import sys
from pathlib import Path

import PyInstaller.__main__

logger = logging.getLogger(__name__)


def build_executable():
    """Build the immich-py executable using PyInstaller."""
    # Get the current directory
    current_dir = Path.cwd()

    # Define PyInstaller arguments
    pyinstaller_args = [
        "build_entry.py",  # Entry point script
        "--name=immich-py",
        "--onefile",
        "--clean",
        "--console",
        "--hidden-import=immich_py.cli.commands",
        "--hidden-import=immich_py.cli.commands.album",
        "--hidden-import=immich_py.cli.commands.asset",
        "--hidden-import=immich_py.cli.commands.job",
        "--hidden-import=immich_py.cli.commands.server",
        "--hidden-import=immich_py.cli.commands.tag",
    ]

    # Build the executable
    try:
        PyInstaller.__main__.run(pyinstaller_args)
    except Exception:  # noqa: BLE001
        sys.exit(1)

    # Get the path to the built executable
    dist_dir = current_dir / "dist"
    exe_name = "immich-py"
    if platform.system() == "Windows":
        exe_name += ".exe"

    exe_path = dist_dir / exe_name

    # Check if the executable was built
    if not exe_path.exists():
        sys.exit(1)

    # Create a build directory if it doesn't exist
    build_dir = current_dir / "build" / "executable"
    Path(build_dir).mkdir(parents=True, exist_ok=True)

    # Copy the executable to the build directory
    target_path = build_dir / exe_name
    shutil.copy2(exe_path, target_path)


if __name__ == "__main__":
    build_executable()
