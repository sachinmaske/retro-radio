import json
from pathlib import Path

FAVORITES_FILE = Path("favorites.json")


def load_favorites():

    if FAVORITES_FILE.exists():
        with open(FAVORITES_FILE) as f:
            return json.load(f)

    return {
        "hindi": [],
        "marathi": []
    }


def save_favorites(data):

    with open(FAVORITES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_favorite(language, station):

    data = load_favorites()

    exists = any(
        s["url"] == station["url"]
        for s in data[language]
    )

    if not exists:
        data[language].append(station)
        save_favorites(data)


def remove_favorite(language, url):

    data = load_favorites()

    data[language] = [
        s for s in data[language]
        if s["url"] != url
    ]

    save_favorites(data)
