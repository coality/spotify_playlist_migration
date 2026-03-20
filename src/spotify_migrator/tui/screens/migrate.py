"""Migration screen."""

from typing import Any

from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Header, Input, Static, Log, ProgressBar


class MigrateOneScreen(Screen):
    """Screen for migrating a single playlist."""

    CSS = """
    MigrateOneScreen {
        background: $surface;
    }

    #migrate-container {
        height: 100%;
        width: 100%;
    }

    .section-title {
        text-align: center;
        margin-bottom: 2;
    }

    .input-section {
        margin-bottom: 2;
    }

    .progress-section {
        height: 30%;
        margin-bottom: 2;
    }

    .log-section {
        height: 40%;
        border: solid $primary;
    }

    .button-row {
        width: 100%;
        height: auto;
    }
    """

    def __init__(self, playlist_name: str | None = None) -> None:
        super().__init__()
        self.playlist_name = playlist_name
        self.is_migrating = False

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with VerticalScroll(id="migrate-container"):
            yield Static("📤 Migration d'une playlist", classes="section-title")

            with Vertical(classes="input-section"):
                yield Static("Nom de la playlist à migrer:", classes="input-label")
                yield Input(
                    value=self.playlist_name or "",
                    id="playlist-name-input",
                    placeholder="Entrez le nom de la playlist...",
                )
                yield Static("Ou laissez vide et migrerez depuis la liste", classes="hint")

            with Vertical(classes="progress-section"):
                yield Static("", id="progress-playlist-name")
                yield ProgressBar(id="progress-gauge")
                yield Static("", id="progress-track-info")

            with VerticalScroll(classes="log-section"):
                yield Log("Logs de migration:", id="migration-log")

            with VerticalScroll(classes="button-row"):
                yield Button("← Retour", id="btn-back", variant="default")
                yield Button("▶ Migrer", id="btn-migrate", variant="success")
                yield Button("🧪 Dry Run", id="btn-dry-run", variant="primary")

    @on(Button.Pressed, "#btn-back")
    def on_back(self) -> None:
        """Go back to home screen."""
        if self.is_migrating:
            self.app.notify("Migration en cours, patience...", severity="warning")
            return
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-migrate")
    @work(exclusive=True)
    async def on_migrate(self) -> None:
        """Start migration."""
        await self._do_migrate(dry_run=False)

    @on(Button.Pressed, "#btn-dry-run")
    @work(exclusive=True)
    async def on_dry_run(self) -> None:
        """Start dry run migration."""
        await self._do_migrate(dry_run=True)

    async def _do_migrate(self, dry_run: bool) -> None:
        """Perform the migration."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig
        from spotify_migrator.api import SpotifyAPIClient
        from spotify_migrator.services import PlaylistMigrator
        from spotify_migrator.store import ConfigStore

        self.is_migrating = True
        btn_migrate = self.query_one("#btn-migrate", Button)
        btn_dry_run = self.query_one("#btn-dry-run", Button)
        btn_migrate.disabled = True
        btn_dry_run.disabled = True

        log = self.query_one("#migration-log", Log)
        name_input = self.query_one("#playlist-name-input", Input)
        playlist_name = name_input.value

        if not playlist_name:
            self.app.notify("Veuillez entrer un nom de playlist", severity="warning")
            self.is_migrating = False
            btn_migrate.disabled = False
            btn_dry_run.disabled = False
            return

        mode = "[DRY RUN]" if dry_run else "[MIGRATION]"
        log.write_line(f"{mode} Démarrage pour: {playlist_name}")

        try:
            config_store = ConfigStore()
            config = config_store.load()

            if config is None:
                log.write_line("❌ Veuillez configurer les identifiants Spotify")
                self.app.push_screen("setup")
                return

            source_config = SpotifyAppConfig(
                client_id=config.source_client_id,
                client_secret=config.source_client_secret,
                redirect_uri=config.source_redirect_uri,
            )
            target_config = SpotifyAppConfig(
                client_id=config.target_client_id,
                client_secret=config.target_client_secret,
                redirect_uri=config.target_redirect_uri,
            )

            source_auth = SpotifyAuthManager("source", source_config)
            target_auth = SpotifyAuthManager("target", target_config)

            source_state = source_auth.load_cached_auth()
            target_state = target_auth.load_cached_auth()

            if not source_state or not source_state.is_authenticated:
                log.write_line("❌ Non connecté au compte source")
                return
            if not target_state or not target_state.is_authenticated:
                log.write_line("❌ Non connecté au compte target")
                return

            source_sp = source_auth.get_client()
            target_sp = target_auth.get_client()

            source_api = SpotifyAPIClient(source_sp)
            target_api = SpotifyAPIClient(target_sp)

            migrator = PlaylistMigrator(source_api, target_api)

            def progress_callback(progress: Any) -> None:
                log.write_line(
                    f"  → {progress.current_track}/{progress.total_tracks}: {progress.track_name}"
                )

            result = migrator.migrate_by_name(
                playlist_name,
                dry_run=dry_run,
                progress_callback=progress_callback,
            )

            if result.is_success:
                log.write_line(f"✓ Succès: {result.tracks_copied} titres copiés")
                if result.tracks_not_found > 0:
                    log.write_line(f"⚠ {result.tracks_not_found} titres non trouvés")
                self.app.notify(
                    f"✓ Playlist migrée: {result.tracks_copied} titres", severity="information"
                )
            else:
                log.write_line(f"❌ Échec: {result.error_message}")
                self.app.notify(f"❌ Échec: {result.error_message}", severity="error")

        except Exception as e:
            log.write_line(f"❌ Erreur: {e}")
            self.app.notify(f"❌ Erreur: {e}", severity="error")

        finally:
            self.is_migrating = False
            btn_migrate.disabled = False
            btn_dry_run.disabled = False


class MigrateAllScreen(Screen):
    """Screen for migrating all playlists."""

    CSS = """
    MigrateAllScreen {
        background: $surface;
    }

    #migrate-container {
        height: 100%;
        width: 100%;
    }

    .section-title {
        text-align: center;
        margin-bottom: 2;
    }

    .progress-section {
        height: 20%;
        margin-bottom: 2;
    }

    .current-playlist {
        margin-bottom: 1;
    }

    .progress-info {
        margin-bottom: 1;
    }

    .summary-section {
        height: 40%;
        border: solid $primary;
        margin-bottom: 2;
    }

    .button-row {
        width: 100%;
        height: auto;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.is_migrating = False
        self.current_result: Any = None

    def compose(self) -> ComposeResult:
        """Compose the screen."""
        yield Header()

        with VerticalScroll(id="migrate-container"):
            yield Static("📤 Migration de toutes les playlists", classes="section-title")

            with Vertical(classes="progress-section"):
                yield Static("", id="current-playlist-name", classes="current-playlist")
                yield ProgressBar(id="playlist-gauge")
                yield Static("", id="progress-info", classes="progress-info")
                yield Static("", id="current-track-info")

            with VerticalScroll(classes="summary-section"):
                yield Static("📊 Résumé", classes="section-title")
                yield Static("Playlists copiées: ", id="summary-copied")
                yield Static("Playlists ignorées: ", id="summary-skipped")
                yield Static("Playlists échouées: ", id="summary-failed")
                yield Static("Titres copiés: ", id="summary-tracks-copied")
                yield Static("Titres non trouvés: ", id="summary-tracks-not-found")

            with VerticalScroll(classes="button-row"):
                yield Button("← Retour", id="btn-back", variant="default")
                yield Button("▶ Tout migrer", id="btn-migrate", variant="success")
                yield Button("🧪 Dry Run", id="btn-dry-run", variant="primary")

    @on(Button.Pressed, "#btn-back")
    def on_back(self) -> None:
        """Go back to home screen."""
        if self.is_migrating:
            self.app.notify("Migration en cours, patience...", severity="warning")
            return
        self.app.pop_screen()

    @on(Button.Pressed, "#btn-migrate")
    @work(exclusive=True)
    async def on_migrate(self) -> None:
        """Start migration."""
        await self._do_migrate(dry_run=False)

    @on(Button.Pressed, "#btn-dry-run")
    @work(exclusive=True)
    async def on_dry_run(self) -> None:
        """Start dry run migration."""
        await self._do_migrate(dry_run=True)

    async def _do_migrate(self, dry_run: bool) -> None:
        """Perform the migration."""
        from spotify_migrator.auth import SpotifyAuthManager, SpotifyAppConfig
        from spotify_migrator.api import SpotifyAPIClient
        from spotify_migrator.services import PlaylistMigrator
        from spotify_migrator.store import ConfigStore

        self.is_migrating = True
        btn_migrate = self.query_one("#btn-migrate", Button)
        btn_dry_run = self.query_one("#btn-dry-run", Button)
        btn_migrate.disabled = True
        btn_dry_run.disabled = True

        mode = "[DRY RUN]" if dry_run else "[MIGRATION]"
        self._update_progress(f"{mode} Démarrage...")

        try:
            config_store = ConfigStore()
            config = config_store.load()

            if config is None:
                self._update_progress("❌ Veuillez configurer les identifiants Spotify")
                self.app.push_screen("setup")
                return

            source_config = SpotifyAppConfig(
                client_id=config.source_client_id,
                client_secret=config.source_client_secret,
                redirect_uri=config.source_redirect_uri,
            )
            target_config = SpotifyAppConfig(
                client_id=config.target_client_id,
                client_secret=config.target_client_secret,
                redirect_uri=config.target_redirect_uri,
            )

            source_auth = SpotifyAuthManager("source", source_config)
            target_auth = SpotifyAuthManager("target", target_config)

            source_state = source_auth.load_cached_auth()
            target_state = target_auth.load_cached_auth()

            if not source_state or not source_state.is_authenticated:
                self._update_progress("❌ Non connecté au compte source")
                return
            if not target_state or not target_state.is_authenticated:
                self._update_progress("❌ Non connecté au compte target")
                return

            source_sp = source_auth.get_client()
            target_sp = target_auth.get_client()

            source_api = SpotifyAPIClient(source_sp)
            target_api = SpotifyAPIClient(target_sp)

            migrator = PlaylistMigrator(source_api, target_api)

            def progress_callback(progress: Any) -> None:
                self._update_current_track(progress)

            summary = migrator.migrate_all(dry_run=dry_run, progress_callback=progress_callback)

            self._update_summary(summary)

            if summary.total_playlists_copied > 0:
                self.app.notify(
                    f"✓ {summary.total_playlists_copied} playlists migrées", severity="information"
                )
            if summary.total_playlists_failed > 0:
                self.app.notify(
                    f"⚠ {summary.total_playlists_failed} playlists échouées", severity="warning"
                )

        except Exception as e:
            self._update_progress(f"❌ Erreur: {e}")
            self.app.notify(f"❌ Erreur: {e}", severity="error")

        finally:
            self.is_migrating = False
            btn_migrate.disabled = False
            btn_dry_run.disabled = False

    def _update_progress(self, message: str) -> None:
        """Update progress display."""
        playlist_name = self.query_one("#current-playlist-name", Static)
        playlist_name.update(message)

    def _update_current_track(self, progress: Any) -> None:
        """Update current track display."""
        playlist_name = self.query_one("#current-playlist-name", Static)
        playlist_name.update(f"📤 {progress.playlist_name}")

        gauge = self.query_one("#playlist-gauge", ProgressBar)
        if progress.total_tracks > 0:
            gauge.update(progress=progress.current_track / progress.total_tracks)

        progress_info = self.query_one("#progress-info", Static)
        progress_info.update(f"Piste {progress.current_track}/{progress.total_tracks}")

        current_track = self.query_one("#current-track-info", Static)
        current_track.update(f"  {progress.track_name}")

    def _update_summary(self, summary: Any) -> None:
        """Update summary display."""
        copied = self.query_one("#summary-copied", Static)
        copied.update(f"✓ Playlists copiées: {summary.total_playlists_copied}")

        skipped = self.query_one("#summary-skipped", Static)
        skipped.update(f"⚠ Playlists ignorées: {summary.total_playlists_skipped}")

        failed = self.query_one("#summary-failed", Static)
        failed.update(f"✗ Playlists échouées: {summary.total_playlists_failed}")

        tracks_copied = self.query_one("#summary-tracks-copied", Static)
        tracks_copied.update(f"Titres copiés: {summary.total_tracks_copied}")

        not_found = self.query_one("#summary-tracks-not-found", Static)
        not_found.update(f"Titres non trouvés: {summary.total_tracks_not_found}")
