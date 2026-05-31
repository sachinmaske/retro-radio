import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.json"
FAVORITES_FILE = ROOT / "favorites.json"

DEFAULT_CONFIG = {
    "language": "marathi",
    "station_url": "",
    "station_uuid": "",
    "volume": 70,
    "browse_mode": "all",
    "sleep_until": 0,
}

# Common Radio Browser language tags; any string works via set_language().
LANGUAGES = ("hindi", "marathi", "english", "tamil", "telugu", "bengali", "kannada")
VOLUME_MIN = 0
VOLUME_MAX = 100


def clamp_volume(volume):
    return max(VOLUME_MIN, min(VOLUME_MAX, int(volume)))


def normalize_config(config):
    config = {**DEFAULT_CONFIG, **config}
    config["volume"] = clamp_volume(config.get("volume", DEFAULT_CONFIG["volume"]))
    return config


def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE) as f:
        return normalize_config(json.load(f))


def save_config(config):
    config = normalize_config(config)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_favorites():
    if not FAVORITES_FILE.exists():
        return {lang: [] for lang in LANGUAGES}
    with open(FAVORITES_FILE) as f:
        data = json.load(f)
    for lang in LANGUAGES:
        data.setdefault(lang, [])
    return data


def save_favorites(data):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_favorite(language, station):
    data = load_favorites()
    data.setdefault(language, [])
    if any(s["url"] == station["url"] for s in data[language]):
        return False
    entry = {"name": station["name"], "url": station["url"]}
    if station.get("stationuuid"):
        entry["stationuuid"] = station["stationuuid"]
    if station.get("favicon"):
        entry["favicon"] = station["favicon"]
    data[language].append(entry)
    save_favorites(data)
    return True


def remove_favorite(language, url):
    data = load_favorites()
    data.setdefault(language, [])
    before = len(data[language])
    data[language] = [s for s in data[language] if s["url"] != url]
    save_favorites(data)
    return len(data[language]) < before
