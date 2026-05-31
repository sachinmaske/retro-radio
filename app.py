from stations import get_stations
from radio import Radio
from config import load_config, save_config
from player import (
    set_volume,
    status,
    toggle,
    volume_up,
    volume_down
)
from favorites import add_favorite
from favorites import load_favorites

config = load_config()
language = config["language"]
stations = get_stations(language)
radio = Radio(stations, config)
set_volume(config["volume"])
radio.play_current()

while True:

    cmd = input(
        "\n[n]ext [p]rev [t]oggle [+]volup [-]voldown [s]tatus [f]avorite current [v]iew favorites [q]uit : "
    ).lower()

    if cmd == "n":
        save_config(config)
        radio.next()

    elif cmd == "p":
        save_config(config)    
        radio.previous()

    elif cmd == "t":
        toggle()

    elif cmd == "+":
        volume_up()
        config["volume"] = min(
            100,
            config["volume"] + 5
        )
        save_config(config)

    elif cmd == "-":
        volume_down()
        config["volume"] = max(
            0,
            config["volume"] - 5
        )   
        save_config(config)

    elif cmd == "s":
        station = radio.current_station()
        print()
        print("Current station:")
        print(station["name"])
        status()

    elif cmd == "f":
        station = stations[radio.current]
        add_favorite(language, station)
        print()
        print("Added to favorites:")
        print(station["name"])

    elif cmd == "v":
        favs = load_favorites()
        print()
        for station in favs[language]:
            print(station["name"])

    elif cmd == "q":
        break
