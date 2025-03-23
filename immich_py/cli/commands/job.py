# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Job CLI commands for the Immich API.

This module contains CLI commands for interacting with jobs in the Immich API.
"""

import json

import click

from immich_py.api.job import JobAPI
from immich_py.models.job import JobCommand, JobName


@click.group(name="job")
def job() -> None:
    """Commands for interacting with jobs."""


@job.command(name="list")
@click.pass_context
def list_jobs(ctx: click.Context) -> None:
    """List all jobs."""
    client = ctx.obj["client"]
    job_api = JobAPI(client)

    try:
        jobs = job_api.get_jobs()
        click.echo(f"Found {len(jobs)} jobs.")
        for job_id, job_info in jobs.items():
            click.echo(f"{job_id}:")
            click.echo(f"  Active: {job_info.job_counts.active}")
            click.echo(f"  Completed: {job_info.job_counts.completed}")
            click.echo(f"  Failed: {job_info.job_counts.failed}")
            click.echo(f"  Delayed: {job_info.job_counts.delayed}")
            click.echo(f"  Waiting: {job_info.job_counts.waiting}")
            click.echo(f"  Paused: {job_info.job_counts.paused}")
            click.echo(f"  Is Active: {job_info.queue_status.is_active}")
            click.echo(f"  Is Paused: {job_info.queue_status.is_paused}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error: {e}", err=True)


@job.command(name="command")
@click.argument("job_id")
@click.argument(
    "command",
    type=click.Choice([cmd.value for cmd in JobCommand]),
)
@click.option(
    "--force",
    is_flag=True,
    help="Whether to force the command.",
)
@click.pass_context
def send_command(ctx: click.Context, job_id: str, command: str, force: bool) -> None:
    """Send a command to a job."""
    client = ctx.obj["client"]
    job_api = JobAPI(client)

    try:
        job_command = JobCommand(command)
        result = job_api.send_job_command(job_id, job_command, force)
        click.echo(f"Command {command} sent to job {job_id}.")
        click.echo(json.dumps(result, indent=2))
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error: {e}", err=True)


@job.command(name="create")
@click.argument(
    "name",
    type=click.Choice([name.value for name in JobName]),
)
@click.pass_context
def create_job(ctx: click.Context, name: str) -> None:
    """Create a job."""
    client = ctx.obj["client"]
    job_api = JobAPI(client)

    try:
        job_name = JobName(name)
        job_api.create_job(job_name)
        click.echo(f"Job {name} created.")
    except Exception as e:  # noqa: BLE001
        click.echo(f"Error: {e}", err=True)
