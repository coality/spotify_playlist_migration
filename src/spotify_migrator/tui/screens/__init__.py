"""Screens package."""

from spotify_migrator.tui.screens.home import HomeScreen
from spotify_migrator.tui.screens.auth import AuthSourceScreen, AuthTargetScreen
from spotify_migrator.tui.screens.playlists import PlaylistsScreen
from spotify_migrator.tui.screens.migrate import MigrateOneScreen, MigrateAllScreen
from spotify_migrator.tui.screens.logs import LogsScreen
from spotify_migrator.tui.screens.setup import SetupScreen

__all__ = [
    "HomeScreen",
    "AuthSourceScreen",
    "AuthTargetScreen",
    "PlaylistsScreen",
    "MigrateOneScreen",
    "MigrateAllScreen",
    "LogsScreen",
    "SetupScreen",
]
