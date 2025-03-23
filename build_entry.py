#!/usr/bin/env python3
# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Entry point script for the immich-py executable.

This script is used by PyInstaller to create the executable.
"""

import sys

from immich_py.cli import main

if __name__ == "__main__":
    sys.exit(main())
