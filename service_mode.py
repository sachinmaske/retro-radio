# service_mode.py
from config import load_config
from stations import get_stations
from radio import Radio
from player import set_volume

config = load_config()

stations = get_stations(config["language"])

radio = Radio(stations, config)

set_volume(config["volume"])

radio.play_current()

while True:
    import time
    time.sleep(60)