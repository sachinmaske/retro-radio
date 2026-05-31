"""
Phase 8 — Appliance boot flow.

Power on → network → MPD → RadioService → restore station → display → web
"""
import os
import subprocess
import time


def _log(msg):
    print(f"[appliance] {msg}")


def wait_for_network(timeout=120):
    if os.environ.get("RADIO_SKIP_NETWORK_WAIT", "") == "1":
        _log("network wait skipped")
        return True

    _log("waiting for network…")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            import socket
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                ("1.1.1.1", 53)
            )
            _log("network ready")
            return True
        except OSError:
            time.sleep(2)
    _log("network timeout — continuing anyway")
    return False


def ensure_mpd():
    if os.environ.get("RADIO_SKIP_MPD_CHECK", "") == "1":
        return True

    result = subprocess.run(
        ["mpc", "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        _log("MPD connected")
        return True

    _log("MPD not responding — try: sudo systemctl start mpd")
    return False


def run_appliance():
    """Full appliance startup (service_mode entry point)."""
    from radio import get_service
    from radio.display import attach_display, start_metadata_poll
    from radio.pi import display_status_message, setup_gpio
    from web_ui import start_web_server, web_enabled

    _log("starting")
    wait_for_network()
    ensure_mpd()

    service = get_service()
    service.apply_saved_volume()
    service.play_current(announce=True)
    _log(f"restored: {service.current_station()['name']}")

    print(display_status_message())
    setup_gpio(service)
    display = attach_display(service)
    if display:
        start_metadata_poll(service)

    if web_enabled():
        start_web_server(background=True)
    else:
        _log("web UI disabled (RADIO_WEB_ENABLED=0)")

    _log("ready")
    print("Language:", service.config["language"])
    print("Browse:", service.get_browse_mode())
    print("GPIO:", os.environ.get("RADIO_GPIO_ENABLED", "off"))
    print("Display:", os.environ.get("RADIO_DISPLAY_ENABLED", "off"))
    print("Web:", os.environ.get("RADIO_WEB_ENABLED", "1"))

    interval = int(os.environ.get("RADIO_APPLIANCE_POLL", "30"))
    while True:
        try:
            service.check_sleep_timer()
        except Exception as exc:
            _log(f"poll error: {exc}")
        time.sleep(interval)
