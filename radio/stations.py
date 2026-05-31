import json
import os
import time
from pathlib import Path

import requests

from radio.storage import ROOT

API_BASE = "https://de1.api.radio-browser.info/json"
CACHE_DIR = ROOT / "stations_cache"
CACHE_TTL = int(os.environ.get("STATION_CACHE_TTL", "86400"))
DEFAULT_LIMIT = int(os.environ.get("STATION_LIMIT", "25"))


def _normalize(raw):
    return {
        "name": raw.get("name") or "Unknown",
        "url": raw["url"],
        "stationuuid": raw.get("stationuuid") or "",
        "country": raw.get("country") or "",
        "codec": raw.get("codec") or "",
        "bitrate": raw.get("bitrate") or 0,
    }


def _cache_path(language):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{language}.json"


def _read_cache(language):
    path = _cache_path(language)
    if not path.exists():
        return None
    with open(path) as f:
        payload = json.load(f)
    if time.time() - payload.get("fetched_at", 0) > CACHE_TTL:
        return None
    return payload.get("stations")


def _write_cache(language, stations):
    with open(_cache_path(language), "w") as f:
        json.dump(
            {"language": language, "fetched_at": time.time(), "stations": stations},
            f,
        )


def _fetch_api(language, limit):
    url = f"{API_BASE}/stations/bylanguage/{language}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    stations = []
    for row in response.json():
        if row.get("url"):
            stations.append(_normalize(row))
    return stations[:limit]


def get_stations(language="hindi", limit=None, force_refresh=False):
    limit = limit or DEFAULT_LIMIT
    if force_refresh or os.environ.get("REFRESH_STATIONS") == "1":
        stations = _fetch_api(language, limit)
        _write_cache(language, stations)
        return stations

    cached = _read_cache(language)
    if cached is not None:
        return cached[:limit]

    stations = _fetch_api(language, limit)
    _write_cache(language, stations)
    return stations
