import json
from config import load_config, save_config
from stations import get_stations
from player import play

class RadioController:

    def __init__(self):

        self.config = load_config()

        self.stations = get_stations(
            self.config["language"]
        )

    def current_station(self):

        return self.stations[
            self.config["station_index"]
        ]

    def play_current(self):

        station = self.current_station()

        play(station["url"])

    def next(self):

        self.config["station_index"] = (
            self.config["station_index"] + 1
        ) % len(self.stations)

        save_config(self.config)

        self.play_current()

    def previous(self):

        self.config["station_index"] = (
            self.config["station_index"] - 1
        ) % len(self.stations)

        save_config(self.config)

        self.play_current()