import time

from radio import player
from radio.stations import get_stations
from radio.storage import (
    LANGUAGES,
    add_favorite,
    clamp_volume,
    load_config,
    load_favorites,
    remove_favorite,
    save_config,
)

VOLUME_STEP = 5
_service = None


def get_service():
    global _service
    if _service is None:
        _service = RadioService()
    return _service


class RadioService:
    def __init__(self):
        self.config = load_config()
        self._stations = []
        self._stations_language = ""
        self._index = 0
        self._display = None
        self._browse_mode = self.config.get("browse_mode", "all")
        self.refresh_stations()
        self._resolve_current_index()

    @property
    def display(self):
        return self._display

    def set_display(self, display):
        self._display = display

    def _refresh_display(self):
        if not self._display:
            return
        try:
            self._display.show_status(self.get_status())
        except Exception as exc:
            print(f"Display refresh: {exc}")

    def refresh_stations(self, force=False, language=None):
        self.config = load_config()
        lang = (language or self.config["language"]).strip().lower()
        self.config["language"] = lang

        self._stations = get_stations(lang, force_refresh=force)
        self._stations_language = lang

        if not self._stations:
            raise RuntimeError(f"No stations for language '{lang}'")

    def _reload_stations_if_needed(self):
        """Keep in-memory list aligned with config.json (language may change via web)."""
        lang = load_config()["language"].strip().lower()
        if lang == self._stations_language and self._stations:
            return

        self.refresh_stations(force=True, language=lang)
        self._resolve_current_index()

    def _resolve_current_index(self):
        self.config = load_config()
        uuid = self.config.get("station_uuid") or ""
        url = self.config.get("station_url") or ""

        for i, s in enumerate(self._stations):
            if uuid and s.get("stationuuid") == uuid:
                self._index = i
                self._persist_station()
                return
        for i, s in enumerate(self._stations):
            if url and s["url"] == url:
                self._index = i
                self._persist_station()
                return

        legacy = self.config.get("station_index")
        if isinstance(legacy, int) and 0 <= legacy < len(self._stations):
            self._index = legacy
        else:
            self._index = 0
        self._persist_station()

    def _persist_station(self):
        s = self.current_station()
        self.config = load_config()
        self.config["language"] = self._stations_language
        self.config["station_url"] = s["url"]
        self.config["station_uuid"] = s.get("stationuuid") or ""
        self.config.pop("station_index", None)
        save_config(self.config)

    def current_station(self):
        return self._stations[self._index]

    def play_current(self, announce=False):
        station = self.current_station()
        if announce:
            print(f"\n{'=' * 40}\nPlaying: {station['name']}\n{'=' * 40}\n")
        player.play(station["url"])
        self._persist_station()
        self._refresh_display()

    def get_browse_mode(self):
        return self.config.get("browse_mode", "all")

    def set_browse_mode(self, mode):
        mode = (mode or "all").strip().lower()
        if mode not in ("all", "favorites"):
            raise ValueError("mode must be 'all' or 'favorites'")
        self._browse_mode = mode
        self.config = load_config()
        self.config["browse_mode"] = mode
        save_config(self.config)
        self._refresh_display()

    def list_browse_stations(self, mode=None):
        mode = (mode or self._browse_mode).lower()
        if mode == "favorites":
            favs = self.list_favorites()
            return favs if favs else []
        return list(self._stations)

    def _playlist(self):
        if self._browse_mode == "favorites":
            favs = self.list_favorites()
            return favs if favs else self._stations
        return self._stations

    def _step_playlist(self, delta):
        playlist = self._playlist()
        if not playlist:
            return
        current_url = self.current_station()["url"]
        idx = 0
        for i, station in enumerate(playlist):
            if station["url"] == current_url:
                idx = i
                break
        target = playlist[(idx + delta) % len(playlist)]
        for i, station in enumerate(self._stations):
            if station["url"] == target["url"]:
                self._index = i
                self.play_current()
                return
        self.play_favorite(target["url"])

    def next(self):
        self._reload_stations_if_needed()
        if self._browse_mode == "favorites":
            self._step_playlist(1)
            return
        self._index = (self._index + 1) % len(self._stations)
        self._persist_station()
        self.play_current()

    def previous(self):
        self._reload_stations_if_needed()
        if self._browse_mode == "favorites":
            self._step_playlist(-1)
            return
        self._index = (self._index - 1) % len(self._stations)
        self._persist_station()
        self.play_current()

    def stop(self):
        self.stop_playback()

    def toggle(self):
        self.toggle_playback()

    def apply_saved_volume(self):
        player.set_volume(self.config["volume"])

    def _sync_volume(self, step):
        player.volume_up(step) if step > 0 else player.volume_down(-step)
        reported = player.get_playback_state().get("volume")
        self.config = load_config()
        if reported is not None:
            self.config["volume"] = clamp_volume(reported)
        else:
            delta = step if step > 0 else step
            self.config["volume"] = clamp_volume(self.config["volume"] + delta)
        save_config(self.config)
        self._refresh_display()
        return self.config["volume"]

    def volume_up(self, step=VOLUME_STEP):
        return self._sync_volume(step)

    def volume_down(self, step=VOLUME_STEP):
        return self._sync_volume(-step)

    def toggle_playback(self):
        player.toggle()
        self._refresh_display()

    def stop_playback(self):
        player.stop()
        self._refresh_display()

    def print_status(self):
        print(f"\nCurrent station:\n{self.current_station()['name']}")
        player.print_status()

    def add_current_favorite(self):
        add_favorite(self._stations_language, self.current_station())
        return self.current_station()

    def list_favorites(self):
        lang = self._stations_language or self.config["language"]
        return load_favorites().get(lang, [])

    def remove_favorite_by_url(self, url):
        lang = self._stations_language or self.config["language"]
        return remove_favorite(lang, url)

    def set_language(self, language):
        language = (language or "").strip().lower()
        if not language:
            raise ValueError("language is required")

        self.config = load_config()
        self.config["language"] = language
        self.config["station_url"] = ""
        self.config["station_uuid"] = ""
        self.config.pop("station_index", None)
        save_config(self.config)

        self.refresh_stations(force=True, language=language)
        self._index = 0
        self._persist_station()
        self.play_current()
        return self.get_status()

    def available_languages(self):
        return list(LANGUAGES)

    def play_favorite(self, url):
        for i, s in enumerate(self._stations):
            if s["url"] == url:
                self._index = i
                self._persist_station()
                self.play_current()
                return s
        self.config["station_url"] = url
        self.config["station_uuid"] = ""
        save_config(self.config)
        player.play(url)
        self.refresh_stations()
        self._resolve_current_index()
        return self.current_station()

    def set_sleep_timer(self, minutes):
        minutes = int(minutes)
        self.config = load_config()
        if minutes <= 0:
            self.config["sleep_until"] = 0
        else:
            self.config["sleep_until"] = time.time() + (minutes * 60)
        save_config(self.config)
        return self.get_sleep_timer()

    def clear_sleep_timer(self):
        return self.set_sleep_timer(0)

    def get_sleep_timer(self):
        self.config = load_config()
        until = float(self.config.get("sleep_until") or 0)
        remaining = max(0, int(until - time.time())) if until else 0
        return {
            "active": until > time.time(),
            "sleep_until": until,
            "remaining_seconds": remaining,
        }

    def check_sleep_timer(self):
        self.config = load_config()
        until = float(self.config.get("sleep_until") or 0)
        if until and time.time() >= until:
            self.config["sleep_until"] = 0
            save_config(self.config)
            self.stop_playback()
            return True
        return False

    def get_status(self):
        self.check_sleep_timer()
        self._reload_stations_if_needed()
        station = self.current_station()
        playback = player.get_playback_state()
        state = playback.get("state") or "stop"
        playlist = self._playlist()
        return {
            "station": station,
            "stream": {
                "title": playback.get("title") or "",
                "artist": playback.get("artist") or "",
                "state": state,
            },
            "volume": self.config["volume"],
            "mpc_volume": playback.get("volume"),
            "state": state,
            "playing": state == "play",
            "language": self._stations_language,
            "browse_mode": self._browse_mode,
            "index": self._index,
            "station_count": len(playlist),
            "sleep": self.get_sleep_timer(),
        }

    def get_metadata(self):
        self._reload_stations_if_needed()
        station = self.current_station()
        playback = player.get_playback_state()
        return {
            "station": station,
            "stream": {
                "title": playback.get("title") or "",
                "artist": playback.get("artist") or "",
                "state": playback.get("state") or "stop",
            },
            "language": self.config["language"],
            "index": self._index,
            "station_count": len(self._stations),
        }
