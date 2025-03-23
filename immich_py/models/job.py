# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Job models for the Immich API.

This module contains data models for jobs in the Immich API.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobCommand(str, Enum):
    """Job command enumeration."""

    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    EMPTY = "empty"
    CLEAR_FAILED = "clear-failed"


class JobName(str, Enum):
    """Job name enumeration."""

    PERSON_CLEANUP = "person-cleanup"
    TAG_CLEANUP = "tag-cleanup"
    USER_CLEANUP = "user-cleanup"


@dataclass
class JobCounts:
    """Job counts model for the Immich API."""

    active: int = 0
    completed: int = 0
    failed: int = 0
    delayed: int = 0
    waiting: int = 0
    paused: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobCounts":
        """
        Create a JobCounts instance from a dictionary.

        Args:
            data: The dictionary containing job counts information.

        Returns
        -------
            A JobCounts instance.
        """
        return cls(
            active=data.get("active", 0),
            completed=data.get("completed", 0),
            failed=data.get("failed", 0),
            delayed=data.get("delayed", 0),
            waiting=data.get("waiting", 0),
            paused=data.get("paused", 0),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the JobCounts instance to a dictionary.

        Returns
        -------
            A dictionary containing job counts information.
        """
        return {
            "active": self.active,
            "completed": self.completed,
            "failed": self.failed,
            "delayed": self.delayed,
            "waiting": self.waiting,
            "paused": self.paused,
        }


@dataclass
class QueueStatus:
    """Queue status model for the Immich API."""

    is_active: bool = False
    is_paused: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueueStatus":
        """
        Create a QueueStatus instance from a dictionary.

        Args:
            data: The dictionary containing queue status information.

        Returns
        -------
            A QueueStatus instance.
        """
        return cls(
            is_active=data.get("isActive", False),
            is_paused=data.get("isPaused", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the QueueStatus instance to a dictionary.

        Returns
        -------
            A dictionary containing queue status information.
        """
        return {
            "isActive": self.is_active,
            "isPaused": self.is_paused,
        }


@dataclass
class Job:
    """Job model for the Immich API."""

    job_counts: JobCounts = field(default_factory=JobCounts)
    queue_status: QueueStatus = field(default_factory=QueueStatus)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        """
        Create a Job instance from a dictionary.

        Args:
            data: The dictionary containing job information.

        Returns
        -------
            A Job instance.
        """
        job_counts = JobCounts()
        if data.get("jobCounts"):
            job_counts = JobCounts.from_dict(data["jobCounts"])

        queue_status = QueueStatus()
        if data.get("queueStatus"):
            queue_status = QueueStatus.from_dict(data["queueStatus"])

        return cls(
            job_counts=job_counts,
            queue_status=queue_status,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the Job instance to a dictionary.

        Returns
        -------
            A dictionary containing job information.
        """
        return {
            "jobCounts": self.job_counts.to_dict(),
            "queueStatus": self.queue_status.to_dict(),
        }
