"""Raspberry Pi GPIO — display lives in radio.display (implementation plan)."""
import sys

from radio.display import attach_display, create_display, start_metadata_poll


def display_status_message():
    from radio.display import _enabled

    if not _enabled("RADIO_DISPLAY_ENABLED"):
        return (
            "Display OFF — set RADIO_DISPLAY_ENABLED=1 and run service_mode.py"
        )
    fb = __import__("os").environ.get("DISPLAY_FB", "")
    if fb:
        return f"Display enabled — framebuffer {fb}"
    return "Display enabled — luma SPI/I2C TFT/OLED"


def setup_gpio(service):
    import os

    if os.environ.get("RADIO_GPIO_ENABLED", "").lower() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        return []

    try:
        from gpiozero import Button
    except ImportError as exc:
        print(f"WARNING: GPIO unavailable ({exc})")
        print("  pip install -r requirements-pi.txt")
        return []

    def pin(key, default):
        return int(os.environ.get(key, default))

    mapping = [
        ("GPIO_NEXT", 17, service.next),
        ("GPIO_PREV", 27, service.previous),
        ("GPIO_TOGGLE", 22, service.toggle_playback),
        ("GPIO_VOL_UP", 23, service.volume_up),
        ("GPIO_VOL_DOWN", 24, service.volume_down),
    ]
    buttons = []
    for env_key, default_pin, handler in mapping:
        btn = Button(pin(env_key, default_pin), bounce_time=0.3)
        btn.when_pressed = handler
        buttons.append(btn)

    print(f"GPIO ready ({len(buttons)} buttons)")
    return buttons


def start_display_loop(service):
    """Attach display + optional slow poll for stream metadata."""
    display = attach_display(service)
    if display:
        start_metadata_poll(service)
    return display


def run_self_test():
    from radio import get_service

    print(display_status_message())
    service = get_service()
    display = create_display()
    if not display:
        print("Set RADIO_DISPLAY_ENABLED=1")
        return 1
    service.set_display(display)
    display.refresh(service)
    print("Display test OK")
    return 0


if __name__ == "__main__":
    sys.exit(run_self_test())
