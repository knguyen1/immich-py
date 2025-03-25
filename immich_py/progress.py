# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Progress bar utilities for the Immich API.

This module contains utilities for displaying progress bars during asset uploads.
"""

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.rule import Rule
from rich.text import Text


class ProgressManager:
    """Manages progress bars for multiple concurrent uploads."""

    def __init__(self, max_workers: int = 5):
        """
        Initialize the ProgressManager.

        Args:
            max_workers: Maximum number of concurrent uploads.
        """
        self.started = False
        self.console = Console()
        self.progress = Progress(
            TextColumn("[cyan]{task.description}"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
        )

        self.album_titles: list[str] = []
        self.prefix = Text.assemble(("Uploading ", "bold cyan"), overflow="ellipsis")
        self._text_cache = self._gen_title_text()
        self.live = Live(Group(self._text_cache, self.progress), refresh_per_second=10)

        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()
        self.tasks: dict[str, int] = {}  # Maps filename to task_id

    def get_callback(self, total: int, filename: str) -> "ProgressHandle":
        """
        Get a progress callback for a file upload.

        Args:
            total: Total size of the file in bytes.
            filename: Name of the file being uploaded.

        Returns
        -------
            A ProgressHandle object.
        """
        with self.lock:
            if not self.started:
                self.live.start()
                self.started = True

            task_id = self.progress.add_task(f"[cyan]{filename}", total=total)
            self.tasks[filename] = task_id

            def _callback_update(x: int) -> None:
                self.progress.update(task_id, advance=x)
                self.live.update(Group(self._get_title_text(), self.progress))

            def _callback_done(
                success: bool = True, hash_value: str | None = None
            ) -> None:
                with self.lock:
                    if success:
                        status = "[green]Done[/green]"
                        if hash_value:
                            status += f" [dim](Hash: {hash_value[:5]})[/dim]"
                    else:
                        status = "[red]Failed[/red]"

                    # Update the description to include the status
                    self.progress.update(
                        task_id,
                        description=f"[cyan]{filename}[/cyan] {status}",
                        completed=success,
                    )

            return ProgressHandle(_callback_update, _callback_done)

    def cleanup(self) -> None:
        """Clean up resources used by the progress manager."""
        with self.lock:
            if self.started:
                self.live.stop()
                self.started = False
                self.executor.shutdown(wait=False)

    def add_album(self, title: str) -> None:
        """
        Add an album title to the progress display.

        Args:
            title: The album title.
        """
        with self.lock:
            self.album_titles.append(title.strip())
            self._text_cache = self._gen_title_text()

    def remove_album(self, title: str) -> None:
        """
        Remove an album title from the progress display.

        Args:
            title: The album title.
        """
        with self.lock:
            self.album_titles.remove(title.strip())
            self._text_cache = self._gen_title_text()

    def _gen_title_text(self) -> Rule:
        """Generate the title text for the progress display."""
        if not self.album_titles:
            title_text = "Assets"
        else:
            titles = ", ".join(self.album_titles[:3])
            if len(self.album_titles) > 3:
                titles += "..."
            title_text = titles

        t = self.prefix + Text(title_text)
        return Rule(t)

    def _get_title_text(self) -> Rule:
        """Get the cached title text."""
        return self._text_cache


@dataclass
class ProgressHandle:
    """Handle for updating progress and marking tasks as done."""

    update: Callable[[int], None]
    done: Callable[[bool, str | None], None]

    def __enter__(self) -> Callable[[int], None]:
        """Enter the context manager."""
        return self.update

    def __exit__(self, *_) -> None:
        """Exit the context manager."""
        self.done(True)


# Global instance
_progress_manager = ProgressManager()


def get_progress_callback(enabled: bool, total: int, filename: str) -> ProgressHandle:
    """
    Get a progress callback for a file upload.

    Args:
        enabled: Whether progress reporting is enabled.
        total: Total size of the file in bytes.
        filename: Name of the file being uploaded.

    Returns
    -------
        A ProgressHandle object.
    """
    global _progress_manager
    if not enabled:
        return ProgressHandle(lambda _: None, lambda *_: None)
    return _progress_manager.get_callback(total, filename)


def add_album(title: str) -> None:
    """
    Add an album title to the progress display.

    Args:
        title: The album title.
    """
    global _progress_manager
    _progress_manager.add_album(title)


def remove_album(title: str) -> None:
    """
    Remove an album title from the progress display.

    Args:
        title: The album title.
    """
    global _progress_manager
    _progress_manager.remove_album(title)


def clear_progress() -> None:
    """Clean up resources used by the progress manager."""
    global _progress_manager
    _progress_manager.cleanup()


def set_max_workers(max_workers: int) -> None:
    """
    Set the maximum number of concurrent uploads.

    Args:
        max_workers: Maximum number of concurrent uploads.
    """
    global _progress_manager
    _progress_manager.cleanup()
    _progress_manager = ProgressManager(max_workers=max_workers)
