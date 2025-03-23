# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Server CLI commands for the Immich API.

This module contains CLI commands for interacting with server-related endpoints in the Immich API.
"""

import json

import click

from immich_py.api.server import ServerAPI

# ruff: noqa: BLE001


@click.group(name="server")
def server() -> None:
    """Commands for interacting with the Immich server."""


@server.command(name="ping")
@click.pass_context
def ping(ctx: click.Context) -> None:
    """Ping the server to check if it's available."""
    client = ctx.obj["client"]
    server_api = ServerAPI(client)

    try:
        result = server_api.ping_server()
        if result:
            click.echo("Server is available.")
        else:
            click.echo("Server is not available.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@server.command(name="stats")
@click.pass_context
def stats(ctx: click.Context) -> None:
    """Get server statistics."""
    client = ctx.obj["client"]
    server_api = ServerAPI(client)

    try:
        result = server_api.get_server_statistics()
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@server.command(name="asset-stats")
@click.pass_context
def asset_stats(ctx: click.Context) -> None:
    """Get asset statistics for the current user."""
    client = ctx.obj["client"]
    server_api = ServerAPI(client)

    try:
        result = server_api.get_asset_statistics()
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@server.command(name="media-types")
@click.pass_context
def media_types(ctx: click.Context) -> None:
    """Get the media types supported by the server."""
    client = ctx.obj["client"]
    server_api = ServerAPI(client)

    try:
        result = server_api.get_supported_media_types()
        # Group by media type
        grouped: dict[str, list] = {}
        for ext, media_type in result.items():
            if media_type not in grouped:
                grouped[media_type] = []
            grouped[media_type].append(ext)

        click.echo(json.dumps(grouped, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@server.command(name="about")
@click.pass_context
def about(ctx: click.Context) -> None:
    """Get information about the server."""
    client = ctx.obj["client"]
    server_api = ServerAPI(client)

    try:
        result = server_api.get_about_info()
        click.echo(json.dumps(result, indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@server.command(name="check-extension")
@click.argument("extension")
@click.pass_context
def check_extension(ctx: click.Context, extension: str) -> None:
    """Check if a file extension is supported."""
    client = ctx.obj["client"]
    server_api = ServerAPI(client)

    try:
        is_supported = server_api.is_extension_supported(extension)
        is_ignored = server_api.is_extension_ignored(extension)

        if is_supported:
            click.echo(f"Extension '{extension}' is supported.")
        elif is_ignored:
            click.echo(f"Extension '{extension}' is ignored.")
        else:
            click.echo(f"Extension '{extension}' is not supported.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
