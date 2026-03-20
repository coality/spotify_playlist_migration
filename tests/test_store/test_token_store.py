"""Tests for TokenStore."""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from spotify_migrator.store import TokenStore, TokenData


class TestTokenData:
    """Tests for TokenData."""

    def test_token_data_creation(self):
        """Test creating TokenData."""
        token = TokenData(
            access_token="access_123",
            token_type="Bearer",
            expires_in=3600,
            expires_at=1234567890.0,
            refresh_token="refresh_123",
            scope="playlist-read",
            user_id="user_123",
            display_name="Test User",
        )

        assert token.access_token == "access_123"
        assert token.token_type == "Bearer"
        assert token.user_id == "user_123"
        assert token.display_name == "Test User"


class TestTokenStore:
    """Tests for TokenStore."""

    def test_init_sets_account(self, tmp_path):
        """Test __init__ sets account name."""
        store = TokenStore("source")
        assert store.account == "source"

    def test_token_file_path(self, tmp_path):
        """Test token file path includes account name."""
        with patch("spotify_migrator.store.token_store.STORE_DIR", tmp_path):
            store = TokenStore("source")
            assert "source_tokens.json" in str(store.token_file)

    def test_save_and_load(self, tmp_path):
        """Test saving and loading token data."""
        with patch("spotify_migrator.store.token_store.STORE_DIR", tmp_path):
            store = TokenStore("source")

            token = TokenData(
                access_token="access_123",
                token_type="Bearer",
                expires_in=3600,
                expires_at=1234567890.0,
                refresh_token="refresh_123",
                scope="playlist-read",
            )

            store.save(token)
            assert store.token_file.exists()

            loaded = store.load()
            assert loaded is not None
            assert loaded.access_token == "access_123"
            assert loaded.refresh_token == "refresh_123"

    def test_load_nonexistent(self, tmp_path):
        """Test loading when no token exists."""
        with patch("spotify_migrator.store.token_store.STORE_DIR", tmp_path):
            store = TokenStore("source")
            loaded = store.load()
            assert loaded is None

    def test_clear(self, tmp_path):
        """Test clearing token data."""
        with patch("spotify_migrator.store.token_store.STORE_DIR", tmp_path):
            store = TokenStore("source")

            token = TokenData(
                access_token="access_123",
                token_type="Bearer",
                expires_in=3600,
                expires_at=1234567890.0,
                refresh_token="refresh_123",
                scope="playlist-read",
            )

            store.save(token)
            assert store.token_file.exists()

            store.clear()
            assert not store.token_file.exists()

    def test_exists(self, tmp_path):
        """Test exists method."""
        with patch("spotify_migrator.store.token_store.STORE_DIR", tmp_path):
            store = TokenStore("source")

            assert store.exists() is False

            token = TokenData(
                access_token="access_123",
                token_type="Bearer",
                expires_in=3600,
                expires_at=1234567890.0,
                refresh_token="refresh_123",
                scope="playlist-read",
            )

            store.save(token)
            assert store.exists() is True


class TestConfigStore:
    """Tests for ConfigStore."""

    def test_init(self, tmp_path):
        """Test __init__ sets config file path."""
        from spotify_migrator.store import ConfigStore

        with patch("spotify_migrator.store.config_store.STORE_DIR", tmp_path):
            store = ConfigStore()
            assert "config.json" in str(store.config_file)

    def test_save_and_load(self, tmp_path):
        """Test saving and loading config."""
        from spotify_migrator.store import ConfigStore, AppConfig

        with patch("spotify_migrator.store.config_store.STORE_DIR", tmp_path):
            store = ConfigStore()

            config = AppConfig(
                source_client_id="source_123",
                source_client_secret="source_secret",
                source_redirect_uri="http://localhost:8080",
                target_client_id="target_123",
                target_client_secret="target_secret",
                target_redirect_uri="http://localhost:8080",
                log_level="DEBUG",
            )

            store.save(config)
            assert store.config_file.exists()

            loaded = store.load()
            assert loaded is not None
            assert loaded.source_client_id == "source_123"
            assert loaded.target_client_id == "target_123"
            assert loaded.log_level == "DEBUG"

    def test_clear(self, tmp_path):
        """Test clearing config."""
        from spotify_migrator.store import ConfigStore, AppConfig

        with patch("spotify_migrator.store.config_store.STORE_DIR", tmp_path):
            store = ConfigStore()

            config = AppConfig(
                source_client_id="source_123",
                source_client_secret=None,
                source_redirect_uri="http://localhost:8080",
                target_client_id="target_123",
                target_client_secret=None,
                target_redirect_uri="http://localhost:8080",
            )

            store.save(config)
            store.clear()
            assert not store.config_file.exists()
