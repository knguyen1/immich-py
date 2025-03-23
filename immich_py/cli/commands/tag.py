# Copyright 2025 Kyle Nguyen
"""
Tag CLI commands for the Immich API.

This module contains CLI commands for interacting with tags in the Immich API.
"""

import click

from immich_py.api.tag import TagAPI


@click.group(name="tag")
def tag() -> None:
    """Commands for interacting with tags."""


@tag.command(name="list")
@click.pass_context
def list_tags(ctx: click.Context) -> None:
    """List all tags."""
    client = ctx.obj["client"]
    tag_api = TagAPI(client)

    try:
        tags = tag_api.get_all_tags()
        click.echo(f"Found {len(tags)} tags.")
        for tag in tags:
            click.echo(f"{tag.id} - {tag.name}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error: {e}", err=True)


@tag.command(name="create")
@click.argument("tags", nargs=-1)
@click.pass_context
def create(ctx: click.Context, tags: list[str]) -> None:
    """Create or update tags."""
    client = ctx.obj["client"]
    tag_api = TagAPI(client)

    try:
        result = tag_api.upsert_tags(list(tags))
        click.echo(f"Created or updated {len(result)} tags.")
        for tag in result:
            click.echo(f"{tag.id} - {tag.name}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error: {e}", err=True)


@tag.command(name="tag-assets")
@click.argument("tag_id")
@click.argument("asset_ids", nargs=-1)
@click.pass_context
def tag_assets(ctx: click.Context, tag_id: str, asset_ids: list[str]) -> None:
    """Tag assets."""
    client = ctx.obj["client"]
    tag_api = TagAPI(client)

    try:
        result = tag_api.tag_assets(tag_id, list(asset_ids))
        click.echo("Assets tagged.")
        for item in result:
            if item.get("success"):
                click.echo(f"Asset {item.get('id')} tagged successfully.")
            else:
                click.echo(f"Failed to tag asset {item.get('id')}: {item.get('error')}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error: {e}", err=True)


@tag.command(name="bulk-tag-assets")
@click.option(
    "--tag-id",
    multiple=True,
    required=True,
    help="The ID of a tag to apply. Can be specified multiple times.",
)
@click.argument("asset_ids", nargs=-1)
@click.pass_context
def bulk_tag_assets(
    ctx: click.Context, tag_id: list[str], asset_ids: list[str]
) -> None:
    """Tag multiple assets with multiple tags."""
    client = ctx.obj["client"]
    tag_api = TagAPI(client)

    try:
        result = tag_api.bulk_tag_assets(list(tag_id), list(asset_ids))
        click.echo(f"Tagged {result.get('count')} assets.")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error: {e}", err=True)
