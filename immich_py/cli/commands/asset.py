# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Asset CLI commands for the Immich API.

This module contains CLI commands for interacting with assets in the Immich API.
"""

import json
from pathlib import Path

import click

from immich_py.api.asset import AssetAPI

# ruff: noqa: BLE001


@click.group(name="asset")
def asset() -> None:
    """Commands for interacting with assets."""


@asset.command(name="list")
@click.option(
    "--with-exif/--without-exif",
    default=True,
    help="Include EXIF data in the response.",
)
@click.option(
    "--with-deleted/--without-deleted",
    default=False,
    help="Include deleted assets in the response.",
)
@click.option(
    "--with-archived/--without-archived",
    default=False,
    help="Include archived assets in the response.",
)
@click.option(
    "--taken-before",
    help="Only include assets taken before this date (ISO 8601 format).",
)
@click.option(
    "--taken-after",
    help="Only include assets taken after this date (ISO 8601 format).",
)
@click.option(
    "--model",
    help="Only include assets with this camera model.",
)
@click.option(
    "--make",
    help="Only include assets with this camera make.",
)
@click.option(
    "--checksum",
    help="Only include assets with this checksum.",
)
@click.option(
    "--original-file-name",
    help="Only include assets with this original file name.",
)
@click.pass_context
def list_assets(
    ctx: click.Context,
    with_exif: bool,
    with_deleted: bool,
    with_archived: bool,
    taken_before: str | None,
    taken_after: str | None,
    model: str | None,
    make: str | None,
    checksum: str | None,
    original_file_name: str | None,
) -> None:
    """List assets."""
    client = ctx.obj["client"]
    asset_api = AssetAPI(client)

    try:
        assets = asset_api.search_assets(
            with_exif=with_exif,
            with_deleted=with_deleted,
            with_archived=with_archived,
            taken_before=taken_before,
            taken_after=taken_after,
            model=model,
            make=make,
            checksum=checksum,
            original_file_name=original_file_name,
        )
        click.echo(f"Found {len(assets)} assets.")
        for asset in assets:
            click.echo(
                f"{asset.id} - {asset.original_file_name} - {asset.file_created_at}"
            )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@asset.command(name="info")
@click.argument("asset_id")
@click.pass_context
def info(ctx: click.Context, asset_id: str) -> None:
    """Get information about an asset."""
    client = ctx.obj["client"]
    asset_api = AssetAPI(client)

    try:
        asset = asset_api.get_asset_info(asset_id)
        click.echo(json.dumps(asset.to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@asset.command(name="download")
@click.argument("asset_id")
@click.option(
    "--output",
    "-o",
    help="Output file path. If not provided, the original file name will be used.",
)
@click.pass_context
def download(ctx: click.Context, asset_id: str, output: str | None) -> None:
    """Download an asset."""
    client = ctx.obj["client"]
    asset_api = AssetAPI(client)

    try:
        # Get asset info to get the original file name
        asset = asset_api.get_asset_info(asset_id)
        output_path = output or asset.original_file_name

        # Download the asset
        data = asset_api.download_asset(asset_id)

        # Write the data to the output file
        with Path.open(output_path, "wb") as f:
            f.write(data)

        click.echo(f"Asset downloaded to {output_path}.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@asset.command(name="upload")
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--device-asset-id",
    help="Device asset ID.",
)
@click.option(
    "--device-id",
    help="Device ID.",
)
@click.option(
    "--favorite/--no-favorite",
    default=False,
    help="Whether the asset is a favorite.",
)
@click.option(
    "--archived/--no-archived",
    default=False,
    help="Whether the asset is archived.",
)
@click.option(
    "--sidecar-path",
    type=click.Path(exists=True),
    help="Path to a sidecar file to upload (only used for single file uploads).",
)
@click.option(
    "--recursive/--no-recursive",
    default=False,
    help="Process directories and archives recursively.",
)
@click.option(
    "--ignore-db/--no-ignore-db",
    default=False,
    help="Ignore the hash database check (but still hash and append after successful upload).",
)
@click.pass_context
def upload(
    ctx: click.Context,
    file_path: str,
    device_asset_id: str | None,
    device_id: str | None,
    favorite: bool,
    archived: bool,
    sidecar_path: str | None,
    recursive: bool,
    ignore_db: bool,
) -> None:
    """
    Upload an asset, directory of assets, or archive of assets.

    If --recursive is specified and the file_path is a directory, all assets in the directory
    will be uploaded. If file_path is an archive (zip, tar, etc.), it will be extracted to a
    temporary directory and all assets will be uploaded.

    The upload process can be visualized with progress bars and can utilize multiple concurrent
    uploads for better performance.
    """
    client = ctx.obj["client"]
    asset_api = AssetAPI(client)

    try:
        # Get progress settings from context
        progress = ctx.obj.get("progress", True)

        if recursive:
            results = asset_api.upload_assets(
                file_path,
                device_asset_id=device_asset_id,
                device_id=device_id,
                is_favorite=favorite,
                is_archived=archived,
                sidecar_path=sidecar_path,
                ignore_db=ignore_db,
            )

            # Handle the case where a single file was uploaded
            if isinstance(results, dict):
                click.echo(f"Asset uploaded with ID: {results.get('id')}")
                click.echo(f"Status: {results.get('status')}")
                if results.get("message"):
                    click.echo(f"Message: {results.get('message')}")
            else:
                # Handle the case where multiple files were uploaded
                click.echo(f"Uploaded {len(results)} assets:")
                for i, result in enumerate(results, 1):
                    status_msg = (
                        f"  {i}. ID: {result.get('id')}, Status: {result.get('status')}"
                    )
                    if result.get("message"):
                        status_msg += f", Message: {result.get('message')}"
                    click.echo(status_msg)
        else:
            # Use the original upload_asset method for single file uploads
            result = asset_api.upload_asset(
                file_path,
                device_asset_id=device_asset_id,
                device_id=device_id,
                is_favorite=favorite,
                is_archived=archived,
                sidecar_path=sidecar_path,
                ignore_db=ignore_db,
                show_progress=progress,
            )
            click.echo(f"Asset uploaded with ID: {result.get('id')}")
            click.echo(f"Status: {result.get('status')}")
            if result.get("message"):
                click.echo(f"Message: {result.get('message')}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@asset.command(name="delete")
@click.argument("asset_ids", nargs=-1)
@click.option(
    "--force",
    is_flag=True,
    help="Permanently delete the assets.",
)
@click.pass_context
def delete(ctx: click.Context, asset_ids: list[str], force: bool) -> None:
    """Delete assets."""
    client = ctx.obj["client"]
    asset_api = AssetAPI(client)

    try:
        asset_api.delete_assets(list(asset_ids), force)
        click.echo("Assets deleted.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@asset.command(name="update")
@click.argument("asset_id")
@click.option(
    "--favorite/--no-favorite",
    help="Whether the asset is a favorite.",
)
@click.option(
    "--archived/--no-archived",
    help="Whether the asset is archived.",
)
@click.option(
    "--latitude",
    type=float,
    help="The latitude of the asset.",
)
@click.option(
    "--longitude",
    type=float,
    help="The longitude of the asset.",
)
@click.option(
    "--description",
    help="The description of the asset.",
)
@click.option(
    "--rating",
    type=int,
    help="The rating of the asset.",
)
@click.pass_context
def update(
    ctx: click.Context,
    asset_id: str,
    favorite: bool | None,
    archived: bool | None,
    latitude: float | None,
    longitude: float | None,
    description: str | None,
    rating: int | None,
) -> None:
    """Update an asset."""
    client = ctx.obj["client"]
    asset_api = AssetAPI(client)

    try:
        asset = asset_api.update_asset(
            asset_id,
            is_favorite=favorite,
            is_archived=archived,
            latitude=latitude,
            longitude=longitude,
            description=description,
            rating=rating,
        )
        click.echo("Asset updated.")
        click.echo(json.dumps(asset.to_dict(), indent=2))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@asset.command(name="batch-update")
@click.argument("asset_ids", nargs=-1)
@click.option(
    "--favorite/--no-favorite",
    default=False,
    help="Whether the assets are favorites.",
)
@click.option(
    "--archived/--no-archived",
    default=False,
    help="Whether the assets are archived.",
)
@click.option(
    "--latitude",
    type=float,
    default=0.0,
    help="The latitude of the assets.",
)
@click.option(
    "--longitude",
    type=float,
    default=0.0,
    help="The longitude of the assets.",
)
@click.option(
    "--remove-parent",
    is_flag=True,
    help="Whether to remove the parent stack.",
)
@click.option(
    "--stack-parent-id",
    help="The ID of the parent stack.",
)
@click.pass_context
def batch_update(
    ctx: click.Context,
    asset_ids: list[str],
    favorite: bool,
    archived: bool,
    latitude: float,
    longitude: float,
    remove_parent: bool,
    stack_parent_id: str | None,
) -> None:
    """Update multiple assets."""
    client = ctx.obj["client"]
    asset_api = AssetAPI(client)

    try:
        asset_api.update_assets(
            list(asset_ids),
            is_favorite=favorite,
            is_archived=archived,
            latitude=latitude,
            longitude=longitude,
            remove_parent=remove_parent,
            stack_parent_id=stack_parent_id,
        )
        click.echo("Assets updated.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
