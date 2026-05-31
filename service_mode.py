from radio_controller import RadioController
from player import set_volume
import time

radio = RadioController()

set_volume(
    radio.config["volume"]
)

radio.play_current()

while True:
    time.sleep(60)