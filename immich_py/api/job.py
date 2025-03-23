# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Job API for the Immich API.

This module contains the JobAPI class for interacting with jobs in the Immich API.
"""

from typing import Any

from immich_py.models.job import Job, JobCommand, JobName


class JobAPI:
    """API for interacting with jobs in the Immich API."""

    def __init__(self, client):
        """
        Initialize the JobAPI.

        Args:
            client: The Immich client.
        """
        self.client = client

    def get_jobs(self) -> dict[str, Job]:
        """
        Get all jobs.

        Returns
        -------
            A dictionary of jobs.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        data = self.client.get_jobs()
        return {key: Job.from_dict(value) for key, value in data.items()}

    def send_job_command(
        self, job_id: str, command: JobCommand, force: bool = False
    ) -> dict[str, Any]:
        """
        Send a command to a job.

        Args:
            job_id: The ID of the job.
            command: The command to send.
            force: Whether to force the command.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.send_job_command(job_id, command.value, force)

    def create_job(self, name: JobName) -> dict[str, Any]:
        """
        Create a job.

        Args:
            name: The name of the job.

        Returns
        -------
            The response from the server.

        Raises
        ------
            ImmichClientError: If the request fails.
        """
        return self.client.create_job(name.value)
