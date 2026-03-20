"""Tests for Migration models."""

import pytest
from datetime import datetime

from spotify_migrator.models.migration import MigrationResult, MigrationStatus, MigrationSummary


class TestMigrationResult:
    """Tests for MigrationResult model."""

    def test_default_values(self):
        """Test MigrationResult default values."""
        result = MigrationResult(
            playlist_name="Test",
            playlist_id=None,
            source_playlist_id="source_123",
        )

        assert result.tracks_copied == 0
        assert result.tracks_skipped == 0
        assert result.tracks_not_found == 0
        assert result.status == MigrationStatus.PENDING
        assert result.error_message is None

    def test_is_success_completed(self):
        """Test is_success for completed status."""
        result = MigrationResult(
            playlist_name="Test",
            playlist_id="123",
            source_playlist_id="source_123",
            status=MigrationStatus.COMPLETED,
        )

        assert result.is_success is True

    def test_is_success_failed(self):
        """Test is_success for failed status."""
        result = MigrationResult(
            playlist_name="Test",
            playlist_id=None,
            source_playlist_id="source_123",
            status=MigrationStatus.FAILED,
        )

        assert result.is_success is False

    def test_to_dict(self):
        """Test MigrationResult.to_dict()."""
        result = MigrationResult(
            playlist_name="Test",
            playlist_id="123",
            source_playlist_id="source_123",
            tracks_copied=10,
            status=MigrationStatus.COMPLETED,
        )

        result_dict = result.to_dict()

        assert result_dict["playlist_name"] == "Test"
        assert result_dict["playlist_id"] == "123"
        assert result_dict["tracks_copied"] == 10
        assert result_dict["status"] == "completed"


class TestMigrationSummary:
    """Tests for MigrationSummary model."""

    def test_initial_state(self):
        """Test MigrationSummary initial state."""
        summary = MigrationSummary()

        assert summary.total_playlists_copied == 0
        assert summary.total_playlists_skipped == 0
        assert summary.total_playlists_failed == 0
        assert summary.total_tracks_copied == 0
        assert summary.total_tracks_not_found == 0
        assert summary.results == []

    def test_add_completed_result(self):
        """Test adding a completed migration result."""
        summary = MigrationSummary()
        result = MigrationResult(
            playlist_name="Test",
            playlist_id="123",
            source_playlist_id="456",
            tracks_copied=10,
            tracks_not_found=2,
            status=MigrationStatus.COMPLETED,
        )

        summary.add_result(result)

        assert summary.total_playlists_copied == 1
        assert summary.total_tracks_copied == 10
        assert summary.total_tracks_not_found == 2

    def test_add_skipped_result(self):
        """Test adding a skipped migration result."""
        summary = MigrationSummary()
        result = MigrationResult(
            playlist_name="Test",
            playlist_id=None,
            source_playlist_id="456",
            status=MigrationStatus.SKIPPED,
            error_message="Playlist already exists",
        )

        summary.add_result(result)

        assert summary.total_playlists_skipped == 1
        assert summary.total_playlists_copied == 0

    def test_add_failed_result(self):
        """Test adding a failed migration result."""
        summary = MigrationSummary()
        result = MigrationResult(
            playlist_name="Test",
            playlist_id=None,
            source_playlist_id="456",
            status=MigrationStatus.FAILED,
            error_message="Network error",
        )

        summary.add_result(result)

        assert summary.total_playlists_failed == 1
        assert summary.total_playlists_copied == 0

    def test_total_playlists(self):
        """Test total_playlists property."""
        summary = MigrationSummary()
        summary.add_result(MigrationResult(playlist_name="P1", playlist_id="1", source_playlist_id="s1", status=MigrationStatus.COMPLETED))
        summary.add_result(MigrationResult(playlist_name="P2", playlist_id="2", source_playlist_id="s2", status=MigrationStatus.SKIPPED))

        assert summary.total_playlists == 2

    def test_get_completed(self):
        """Test get_completed method."""
        summary = MigrationSummary()
        r1 = MigrationResult(playlist_name="P1", playlist_id="1", source_playlist_id="s1", status=MigrationStatus.COMPLETED)
        r2 = MigrationResult(playlist_name="P2", playlist_id="2", source_playlist_id="s2", status=MigrationStatus.SKIPPED)
        r3 = MigrationResult(playlist_name="P3", playlist_id="3", source_playlist_id="s3", status=MigrationStatus.COMPLETED)

        summary.add_result(r1)
        summary.add_result(r2)
        summary.add_result(r3)

        completed = summary.get_completed()
        assert len(completed) == 2
        assert all(r.status == MigrationStatus.COMPLETED for r in completed)

    def test_get_skipped(self):
        """Test get_skipped method."""
        summary = MigrationSummary()
        r1 = MigrationResult(playlist_name="P1", playlist_id="1", source_playlist_id="s1", status=MigrationStatus.COMPLETED)
        r2 = MigrationResult(playlist_name="P2", playlist_id="2", source_playlist_id="s2", status=MigrationStatus.SKIPPED)

        summary.add_result(r1)
        summary.add_result(r2)

        skipped = summary.get_skipped()
        assert len(skipped) == 1
        assert skipped[0].status == MigrationStatus.SKIPPED

    def test_get_failed(self):
        """Test get_failed method."""
        summary = MigrationSummary()
        r1 = MigrationResult(playlist_name="P1", playlist_id="1", source_playlist_id="s1", status=MigrationStatus.COMPLETED)
        r2 = MigrationResult(playlist_name="P2", playlist_id=None, source_playlist_id="s2", status=MigrationStatus.FAILED)

        summary.add_result(r1)
        summary.add_result(r2)

        failed = summary.get_failed()
        assert len(failed) == 1
        assert failed[0].status == MigrationStatus.FAILED

    def test_to_dict(self):
        """Test MigrationSummary.to_dict()."""
        summary = MigrationSummary()
        summary.total_playlists_copied = 2
        summary.total_tracks_copied = 20

        result = summary.to_dict()

        assert result["total_playlists_copied"] == 2
        assert result["total_tracks_copied"] == 20
        assert "results" in result
