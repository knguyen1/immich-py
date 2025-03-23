# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Utility functions for the CLI.

This module contains utility functions for the CLI.
"""

import sys
from functools import wraps

import click


def validate_client(f):
    """Validate that a client is available in the context."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()
        if ctx.obj is None or ctx.obj.get("client") is None:
            # Check if we're showing help
            if "--help" in sys.argv or any(
                arg in sys.argv for arg in ctx.help_option_names
            ):
                return f(*args, **kwargs)
            msg = "Missing required options: --endpoint / -e and --api-key / -k are required for this command."
            raise click.UsageError(msg)
        return f(*args, **kwargs)

    return wrapper
