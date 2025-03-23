# Copyright 2025 Kyle Nguyen
"""
Album CLI commands for the Immich API.

This module contains CLI commands for interacting with albums in the Immich API.
"""

import json

import click

from immich_py.api.album import AlbumAPI

# ruff: noqa: BLE001


@click.group(name="album")
def album() -> None:
    """Commands for interacting with albums."""


@album.command(name="list")
@click.pass_context
def list_albums(ctx: click.Context) -> None:
    """List all albums."""
    client = ctx.obj["client"]
    album_api = AlbumAPI(client)

    try:
        albums = album_api.get_all_albums()
        click.echo(f"Found {len(albums)} albums.")
        for album in albums:
            click.echo(f"{album.id} - {album.album_name}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@album.command(name="info")
@click.argument("album_id")
@click.option(
    "--with-assets/--without-assets",
    default=True,
    help="Include assets in the response.",
)
@click.pass_context
def info(ctx: click.Context, album_id: str, with_assets: bool) -> None:
    """Get information about an album."""
    client = ctx.obj["client"]
    album_api = AlbumAPI(client)

    try:
        album = album_api.get_album_info(album_id, not with_assets)
        click.echo(json.dumps(album.to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@album.command(name="create")
@click.argument("album_name")
@click.option(
    "--description",
    default="",
    help="The description of the album.",
)
@click.option(
    "--asset-id",
    multiple=True,
    help="The ID of an asset to add to the album. Can be specified multiple times.",
)
@click.pass_context
def create(
    ctx: click.Context, album_name: str, description: str, asset_id: list[str]
) -> None:
    """Create an album."""
    client = ctx.obj["client"]
    album_api = AlbumAPI(client)

    try:
        album = album_api.create_album(
            album_name, description, list(asset_id) if asset_id else None
        )
        click.echo(f"Album created with ID: {album.id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@album.command(name="add-assets")
@click.argument("album_id")
@click.argument("asset_ids", nargs=-1)
@click.pass_context
def add_assets(ctx: click.Context, album_id: str, asset_ids: list[str]) -> None:
    """Add assets to an album."""
    client = ctx.obj["client"]
    album_api = AlbumAPI(client)

    try:
        result = album_api.add_assets_to_album(album_id, list(asset_ids))
        click.echo("Assets added to album.")
        for item in result:
            if item.get("success"):
                click.echo(f"Asset {item.get('id')} added successfully.")
            else:
                click.echo(f"Failed to add asset {item.get('id')}: {item.get('error')}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@album.command(name="delete")
@click.argument("album_id")
@click.pass_context
def delete(ctx: click.Context, album_id: str) -> None:
    """Delete an album."""
    client = ctx.obj["client"]
    album_api = AlbumAPI(client)

    try:
        album_api.delete_album(album_id)
        click.echo("Album deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@album.command(name="asset-albums")
@click.argument("asset_id")
@click.pass_context
def asset_albums(ctx: click.Context, asset_id: str) -> None:
    """Get all albums that an asset belongs to."""
    client = ctx.obj["client"]
    album_api = AlbumAPI(client)

    try:
        albums = album_api.get_asset_albums(asset_id)
        click.echo(f"Asset belongs to {len(albums)} albums.")
        for album in albums:
            click.echo(f"{album.id} - {album.album_name}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
