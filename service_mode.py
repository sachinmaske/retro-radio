import os
import time

from radio import get_service
from radio.pi import setup_gpio, start_display_loop

service = get_service()
service.apply_saved_volume()
service.play_current(announce=True)

gpio_handles = setup_gpio(service)
display_thread = start_display_loop(service)

print("Retro Radio service running.")
print("GPIO:", os.environ.get("RADIO_GPIO_ENABLED", "off"))
print("Display:", os.environ.get("RADIO_DISPLAY_ENABLED", "off"))

while True:
    time.sleep(60)
