from config import load_config, save_config
from stations import get_stations
from player import play

def current_station():

    config = load_config()

    stations = get_stations(
        config["language"]
    )

    return stations[
        config["station_index"]
    ]

def next_station():

    config = load_config()

    stations = get_stations(
        config["language"]
    )

    config["station_index"] = (
        config["station_index"] + 1
    ) % len(stations)

    save_config(config)

    play(
        stations[
            config["station_index"]
        ]["url"]
    )

def previous_station():
    
    config = load_config()

    stations = get_stations(
        config["language"]
    )

    config["station_index"] = (
        config["station_index"] - 1
    ) % len(stations)

    save_config(config)

    play(
        stations[
            config["station_index"]
        ]["url"]
    )

def volume_up():
    config = load_config()
    config["volume"] = min(config["volume"] + 1, 100)
    save_config(config)

def volume_down():
    config = load_config()
    config["volume"] = max(config["volume"] - 1, 0)
    save_config(config)
