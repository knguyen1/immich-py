# Copyright (c) 2025. All rights reserved.
# Licensed under the MIT License. See LICENSE file for details.
"""
Tests for the progress module.
"""

from unittest.mock import MagicMock, patch

import pytest
from rich.rule import Rule

from immich_py.progress import (
    ProgressHandle,
    ProgressManager,
    add_album,
    clear_progress,
    get_progress_callback,
    remove_album,
    set_max_workers,
)


class TestProgressHandle:
    """Tests for the ProgressHandle class."""

    def test_init(self):
        """Test initialization of ProgressHandle."""
        update_mock = MagicMock()
        done_mock = MagicMock()

        handle = ProgressHandle(update_mock, done_mock)

        assert handle.update is update_mock
        assert handle.done is done_mock

    def test_context_manager(self):
        """Test using ProgressHandle as a context manager."""
        update_mock = MagicMock()
        done_mock = MagicMock()

        handle = ProgressHandle(update_mock, done_mock)

        # Test __enter__
        with handle as update_func:
            assert update_func is update_mock
            # Call the update function to verify it works
            update_func(100)
            update_mock.assert_called_once_with(100)

        # Test __exit__ - should call done with True
        done_mock.assert_called_once_with(True)


class TestProgressManager:
    """Tests for the ProgressManager class."""

    def setup_method(self):
        """Set up test environment."""
        # Create a ProgressManager instance for testing
        with patch("rich.live.Live.start"):  # Prevent live display from starting
            self.progress_manager = ProgressManager(max_workers=3)

    def test_init(self):
        """Test initialization of ProgressManager."""
        # Need to patch Live.start to prevent it from actually starting
        with patch("rich.live.Live.start"):
            # Test with default max_workers
            manager = ProgressManager()

            # Verify attributes
            assert manager.started is False
            assert manager.album_titles == []
            assert manager.tasks == {}

            # Test with custom max_workers
            manager = ProgressManager(max_workers=10)
            assert manager.executor._max_workers == 10

    def test_get_callback_first_call(self):
        """Test get_callback method when called for the first time."""
        with (
            patch.object(self.progress_manager.live, "start") as mock_start,
            patch.object(self.progress_manager.progress, "add_task") as mock_add_task,
        ):
            mock_add_task.return_value = 1  # Task ID

            # Call get_callback for the first time
            handle = self.progress_manager.get_callback(100, "test.jpg")

            # Verify live.start was called
            mock_start.assert_called_once()
            # Verify started flag was set
            assert self.progress_manager.started is True
            # Verify add_task was called with correct parameters
            mock_add_task.assert_called_once_with("[cyan]test.jpg", total=100)
            # Verify task was added to tasks dict
            assert self.progress_manager.tasks["test.jpg"] == 1
            # Verify handle is a ProgressHandle
            assert isinstance(handle, ProgressHandle)

    def test_get_callback_subsequent_call(self):
        """Test get_callback method when called after the first time."""
        # Set started to True to simulate previous call
        self.progress_manager.started = True

        with (
            patch.object(self.progress_manager.live, "start") as mock_start,
            patch.object(self.progress_manager.progress, "add_task") as mock_add_task,
        ):
            mock_add_task.return_value = 2  # Task ID

            # Call get_callback
            handle = self.progress_manager.get_callback(200, "other.jpg")

            # Verify live.start was not called again
            mock_start.assert_not_called()
            # Verify add_task was called with correct parameters
            mock_add_task.assert_called_once_with("[cyan]other.jpg", total=200)
            # Verify task was added to tasks dict
            assert self.progress_manager.tasks["other.jpg"] == 2
            # Verify handle is a ProgressHandle
            assert isinstance(handle, ProgressHandle)

    def test_callback_update(self):
        """Test the update callback returned by get_callback."""
        with (
            patch.object(self.progress_manager.live, "start"),
            patch.object(self.progress_manager.progress, "add_task") as mock_add_task,
            patch.object(self.progress_manager.progress, "update") as mock_update,
            patch.object(self.progress_manager.live, "update") as mock_live_update,
        ):
            mock_add_task.return_value = 1  # Task ID

            # Get the callback
            handle = self.progress_manager.get_callback(100, "test.jpg")

            # Call the update callback
            handle.update(10)

            # Verify progress.update was called with correct parameters
            mock_update.assert_called_once_with(1, advance=10)
            # Verify live.update was called
            mock_live_update.assert_called_once()

    @pytest.mark.parametrize(
        ("hash_value", "expected_description"),
        [
            (None, "[cyan]test.jpg[/cyan] [green]Done[/green]"),
            (
                "abcdef12345",
                "[cyan]test.jpg[/cyan] [green]Done[/green] [dim](Hash: abcde)[/dim]",
            ),
        ],
        ids=["without_hash", "with_hash"],
    )
    def test_callback_done_success(self, hash_value, expected_description):
        """Test the done callback returned by get_callback with success=True."""
        with (
            patch.object(self.progress_manager.live, "start"),
            patch.object(self.progress_manager.progress, "add_task") as mock_add_task,
            patch.object(self.progress_manager.progress, "update") as mock_update,
        ):
            mock_add_task.return_value = 1  # Task ID

            # Get the callback
            handle = self.progress_manager.get_callback(100, "test.jpg")

            # Call the done callback with success=True and optional hash_value
            handle.done(True, hash_value)

            # Verify progress.update was called with correct parameters
            mock_update.assert_called_once_with(
                1,
                description=expected_description,
                completed=True,
            )

    def test_callback_done_failure(self):
        """Test the done callback returned by get_callback with success=False."""
        with (
            patch.object(self.progress_manager.live, "start"),
            patch.object(self.progress_manager.progress, "add_task") as mock_add_task,
            patch.object(self.progress_manager.progress, "update") as mock_update,
        ):
            mock_add_task.return_value = 1  # Task ID

            # Get the callback
            handle = self.progress_manager.get_callback(100, "test.jpg")

            # Call the done callback with success=False
            handle.done(False)

            # Verify progress.update was called with correct parameters
            mock_update.assert_called_once_with(
                1,
                description="[cyan]test.jpg[/cyan] [red]Failed[/red]",
                completed=False,
            )

    def test_cleanup(self):
        """Test cleanup method."""
        # Set started to True to simulate previous call
        self.progress_manager.started = True

        with (
            patch.object(self.progress_manager.live, "stop") as mock_stop,
            patch.object(self.progress_manager.executor, "shutdown") as mock_shutdown,
        ):
            # Call cleanup
            self.progress_manager.cleanup()

            # Verify live.stop was called
            mock_stop.assert_called_once()
            # Verify executor.shutdown was called with wait=False
            mock_shutdown.assert_called_once_with(wait=False)
            # Verify started flag was reset
            assert self.progress_manager.started is False

    def test_cleanup_not_started(self):
        """Test cleanup method when not started."""
        # Ensure started is False
        self.progress_manager.started = False

        with (
            patch.object(self.progress_manager.live, "stop") as mock_stop,
            patch.object(self.progress_manager.executor, "shutdown") as mock_shutdown,
        ):
            # Call cleanup
            self.progress_manager.cleanup()

            # Verify live.stop was not called
            mock_stop.assert_not_called()
            # Verify executor.shutdown was not called
            mock_shutdown.assert_not_called()
            # Verify started flag is still False
            assert self.progress_manager.started is False

    @pytest.mark.parametrize(
        ("album_title", "expected_title"),
        [
            ("Test Album", "Test Album"),
            ("  Test Album  ", "Test Album"),
        ],
        ids=["normal", "with_whitespace"],
    )
    def test_add_album(self, album_title, expected_title):
        """Test add_album method."""
        # Call add_album
        self.progress_manager.add_album(album_title)

        # Verify album was added to album_titles with whitespace stripped if necessary
        assert expected_title in self.progress_manager.album_titles
        # Verify _text_cache was updated
        assert self.progress_manager._text_cache is not None

    @pytest.mark.parametrize(
        "remove_title",
        [
            "Test Album",
            "  Test Album  ",
        ],
        ids=["normal", "with_whitespace"],
    )
    def test_remove_album(self, remove_title):
        """Test remove_album method."""
        # Add an album first
        self.progress_manager.add_album("Test Album")

        # Call remove_album
        self.progress_manager.remove_album(remove_title)

        # Verify album was removed from album_titles
        assert "Test Album" not in self.progress_manager.album_titles
        # Verify _text_cache was updated
        assert self.progress_manager._text_cache is not None

    @pytest.mark.parametrize(
        ("albums", "expected_text"),
        [
            ([], "Assets"),
            (["Album 1", "Album 2"], "Album 1, Album 2"),
            (
                ["Album 1", "Album 2", "Album 3", "Album 4", "Album 5"],
                "Album 1, Album 2, Album 3...",
            ),
        ],
        ids=["no_albums", "few_albums", "many_albums"],
    )
    def test_gen_title_text(self, albums, expected_text):
        """Test _gen_title_text method with different album configurations."""
        # Set album_titles
        self.progress_manager.album_titles = albums

        # Call _gen_title_text
        result = self.progress_manager._gen_title_text()

        # Verify result is a Rule
        assert isinstance(result, Rule)
        # Verify the rule contains the expected text
        assert expected_text in str(result)

    def test_get_title_text(self):
        """Test _get_title_text method."""
        # Set _text_cache
        mock_rule = MagicMock(spec=Rule)
        self.progress_manager._text_cache = mock_rule

        # Call _get_title_text
        result = self.progress_manager._get_title_text()

        # Verify result is the cached rule
        assert result is mock_rule


class TestGlobalFunctions:
    """Tests for the global functions in the progress module."""

    @pytest.mark.parametrize(
        ("enabled", "should_call_manager"),
        [
            (True, True),
            (False, False),
        ],
        ids=["enabled", "disabled"],
    )
    def test_get_progress_callback(self, enabled, should_call_manager):
        """Test get_progress_callback with different enabled values."""
        with patch("immich_py.progress._progress_manager") as mock_manager:
            if should_call_manager:
                mock_manager.get_callback.return_value = MagicMock(spec=ProgressHandle)

            # Call get_progress_callback
            result = get_progress_callback(enabled, 100, "test.jpg")

            # Verify _progress_manager.get_callback was called or not based on enabled
            if should_call_manager:
                mock_manager.get_callback.assert_called_once_with(100, "test.jpg")
                assert result is mock_manager.get_callback.return_value
            else:
                mock_manager.get_callback.assert_not_called()
                assert isinstance(result, ProgressHandle)
                # Call the callbacks to verify they don't raise exceptions
                result.update(10)
                result.done(True)
                result.done(False)

    def test_add_album(self):
        """Test add_album global function."""
        with patch("immich_py.progress._progress_manager") as mock_manager:
            # Call add_album
            add_album("Test Album")

            # Verify _progress_manager.add_album was called
            mock_manager.add_album.assert_called_once_with("Test Album")

    def test_remove_album(self):
        """Test remove_album global function."""
        with patch("immich_py.progress._progress_manager") as mock_manager:
            # Call remove_album
            remove_album("Test Album")

            # Verify _progress_manager.remove_album was called
            mock_manager.remove_album.assert_called_once_with("Test Album")

    def test_clear_progress(self):
        """Test clear_progress global function."""
        with patch("immich_py.progress._progress_manager") as mock_manager:
            # Call clear_progress
            clear_progress()

            # Verify _progress_manager.cleanup was called
            mock_manager.cleanup.assert_called_once()

    def test_set_max_workers(self):
        """Test set_max_workers global function."""
        with (
            patch("immich_py.progress._progress_manager") as mock_manager,
            patch("immich_py.progress.ProgressManager") as mock_progress_manager_class,
        ):
            mock_instance = MagicMock()
            mock_progress_manager_class.return_value = mock_instance

            # Call set_max_workers
            set_max_workers(10)

            # Verify _progress_manager.cleanup was called
            mock_manager.cleanup.assert_called_once()
            # Verify ProgressManager was instantiated with correct max_workers
            mock_progress_manager_class.assert_called_once_with(max_workers=10)
