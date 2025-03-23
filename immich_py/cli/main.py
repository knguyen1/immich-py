# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Main CLI entry point for the Immich API.

This module contains the main CLI entry point for interacting with the Immich API.
"""

import sys

import click

from immich_py.api.client import ImmichClient, ImmichClientError

from . import commands

# ruff: noqa: BLE001


@click.group()
@click.option(
    "--endpoint",
    "-e",
    envvar="IMMICH_ENDPOINT",
    help="Immich API endpoint URL. Can also be set with IMMICH_ENDPOINT environment variable.",
    required=True,
)
@click.option(
    "--api-key",
    "-k",
    envvar="IMMICH_API_KEY",
    help="Immich API key. Can also be set with IMMICH_API_KEY environment variable.",
    required=True,
)
@click.option(
    "--no-verify-ssl",
    is_flag=True,
    help="Disable SSL certificate verification.",
)
@click.option(
    "--timeout",
    type=float,
    default=60.0,
    help="Timeout for API requests in seconds.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't send any data to the server.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output.",
)
@click.pass_context
def main(
    ctx: click.Context,
    endpoint: str,
    api_key: str,
    no_verify_ssl: bool,
    timeout: float,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Command-line interface for interacting with the Immich API."""
    # Create the Immich client
    client = ImmichClient(
        endpoint=endpoint,
        api_key=api_key,
        verify_ssl=not no_verify_ssl,
        timeout=timeout,
        dry_run=dry_run,
    )

    # Store the client in the context
    ctx.obj = {
        "client": client,
        "verbose": verbose,
    }


# Add commands
main.add_command(commands.server)
main.add_command(commands.asset)
main.add_command(commands.album)
main.add_command(commands.tag)
main.add_command(commands.job)


if __name__ == "__main__":
    try:
        main()
    except ImmichClientError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)
