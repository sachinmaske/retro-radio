import os
import time

from radio import get_service
from radio.pi import display_status_message, setup_gpio, start_display_loop
from web import start_web_server, web_enabled

service = get_service()
service.apply_saved_volume()
service.play_current(announce=True)

print(display_status_message())
setup_gpio(service)
start_display_loop(service)

if web_enabled():
    start_web_server(background=True)
else:
    print("Web UI off (set RADIO_WEB_ENABLED=1 to enable)")

print("Retro Radio service running.")
print("Language:", service.config["language"])
print("GPIO:", os.environ.get("RADIO_GPIO_ENABLED", "off"))
print("Display:", os.environ.get("RADIO_DISPLAY_ENABLED", "off"))
print("Web:", os.environ.get("RADIO_WEB_ENABLED", "1"))

while True:
    time.sleep(60)
