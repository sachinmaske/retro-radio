import config
from player import play

class Radio:

    def __init__(self, stations, config):
        self.stations = stations
        self.config = config
        self.current = config["station_index"]

    def play_current(self):
        station = self.stations[self.current]

        print()
        print("=" * 40)
        print("Playing:", station["name"])
        print("=" * 40)
        print()

        play(station["url"])
    
    def current_station(self):
        return self.stations[self.current]

    def set_station(self, index):
        self.current = index
        self.play_current()

    def next(self):
        self.current = (self.current + 1) % len(self.stations)
        self.config["station_index"] = self.current
        self.play_current()
        config["station_index"] = self.current
        config.save_config(config)

    def previous(self):
        self.current = (self.current - 1) % len(self.stations)
        self.config["station_index"] = self.current
        self.play_current()
        config["station_index"] = self.current
        config.save_config(config)
