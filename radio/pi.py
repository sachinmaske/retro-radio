"""Raspberry Pi GPIO and display — optional, lazy-loaded to save RAM."""
import os
import sys
import threading
import time


def _enabled(name):
    return os.environ.get(name, "").lower() in ("1", "true", "yes", "on")


def display_status_message():
    if not _enabled("RADIO_DISPLAY_ENABLED"):
        return (
            "Display OFF — set RADIO_DISPLAY_ENABLED=1 and run service_mode.py "
            "(not app.py or web.py)"
        )
    return "Display enabled — initializing OLED/TFT..."


def _pin(key, default):
    return int(os.environ.get(key, default))


def setup_gpio(service):
    if not _enabled("RADIO_GPIO_ENABLED"):
        return []

    try:
        from gpiozero import Button
    except ImportError as exc:
        print(f"WARNING: GPIO unavailable ({exc})")
        print("  pip install -r requirements-pi.txt")
        print("  Or disable buttons: RADIO_GPIO_ENABLED=0 in radio.env")
        return []

    buttons = []
    mapping = [
        ("GPIO_NEXT", 17, service.next),
        ("GPIO_PREV", 27, service.previous),
        ("GPIO_TOGGLE", 22, service.toggle_playback),
        ("GPIO_VOL_UP", 23, service.volume_up),
        ("GPIO_VOL_DOWN", 24, service.volume_down),
    ]
    for env_key, default_pin, handler in mapping:
        btn = Button(_pin(env_key, default_pin), bounce_time=0.3)
        btn.when_pressed = handler
        buttons.append(btn)

    print(f"GPIO ready ({len(buttons)} buttons)")
    return buttons


def init_display():
    """Return (device, backend, error). backend: ssd1306 | st7735 | console | none."""
    if not _enabled("RADIO_DISPLAY_ENABLED"):
        return None, "none", "RADIO_DISPLAY_ENABLED is not set"

    display_type = os.environ.get("RADIO_DISPLAY_TYPE", "ssd1306").lower().strip()

    try:
        if display_type == "st7735":
            from luma.core.interface.serial import spi
            from luma.lcd.device import st7735

            serial = spi(
                port=int(os.environ.get("DISPLAY_SPI_PORT", "0")),
                device=int(os.environ.get("DISPLAY_SPI_DEVICE", "0")),
                gpio_DC=_pin("DISPLAY_GPIO_DC", 23),
                gpio_RST=_pin("DISPLAY_GPIO_RST", 24),
            )
            width = int(os.environ.get("DISPLAY_WIDTH", "128"))
            height = int(os.environ.get("DISPLAY_HEIGHT", "160"))
            device = st7735(serial, width=width, height=height)
            print(f"ST7735 display OK ({width}x{height})")
            return device, "st7735", None

        # default: I2C SSD1306 128x64
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306

        port = int(os.environ.get("DISPLAY_I2C_PORT", "1"))
        addr = int(os.environ.get("DISPLAY_I2C_ADDRESS", "0x3C"), 16)
        device = ssd1306(i2c(port=port, address=addr))
        print(f"SSD1306 OLED OK (I2C port {port}, address {hex(addr)})")
        return device, "ssd1306", None

    except ImportError as exc:
        return None, "console", (
            f"Missing display libraries: {exc}. "
            "On the Pi run: pip install -r requirements-pi.txt"
        )
    except Exception as exc:
        return None, "console", (
            f"Hardware init failed: {exc}. "
            "Check wiring, enable I2C/SPI (raspi-config), run: i2cdetect -y 1"
        )


def _render_console(status):
    s = status.get("station", {})
    stream = status.get("stream", {})
    print(
        "[display]",
        s.get("name", "?"),
        "|",
        stream.get("title") or status.get("state"),
        "| vol",
        status.get("volume"),
    )


def _render_device(device, backend, status):
    from PIL import Image, ImageDraw

    width, height = device.width, device.height
    mode = "RGB" if backend == "st7735" else "1"
    fill = "white" if backend == "st7735" else 255

    img = Image.new(mode, (width, height))
    draw = ImageDraw.Draw(img)
    s = status.get("station", {})
    stream = status.get("stream", {})
    draw.text((0, 0), (s.get("name") or "?")[:21], fill=fill)
    line2 = (stream.get("title") or stream.get("artist") or "")[:21]
    draw.text((0, 14), line2 or "-", fill=fill)
    draw.text(
        (0, 28),
        f"{status.get('state', '?')} vol {status.get('volume', 0)}",
        fill=fill,
    )
    device.display(img)


def start_display_loop(service):
    if not _enabled("RADIO_DISPLAY_ENABLED"):
        return None

    device, backend, error = init_display()
    if error:
        print(f"WARNING: {error}")
        print("Falling back to console display output.")
        backend = "console"

    def loop():
        interval = float(os.environ.get("RADIO_DISPLAY_INTERVAL", "3"))
        while True:
            try:
                status = service.get_status()
                if backend in ("ssd1306", "st7735") and device:
                    _render_device(device, backend, status)
                else:
                    _render_console(status)
            except Exception as exc:
                print(f"Display error: {exc}")
            time.sleep(interval)

    thread = threading.Thread(target=loop, daemon=True, name="radio-display")
    thread.start()
    return thread


def run_self_test():
    print(display_status_message())
    device, backend, error = init_display()
    if error:
        print(error)
    if backend == "none":
        print("\nTo enable:")
        print("  export RADIO_DISPLAY_ENABLED=1")
        print("  pip install -r requirements-pi.txt")
        print("  sudo raspi-config  # Interface Options -> I2C (for SSD1306)")
        print("  i2cdetect -y 1     # should show 3c for typical OLED")
        return 1

    fake_status = {
        "station": {"name": "Retro Radio Test"},
        "stream": {"title": "Display OK"},
        "state": "play",
        "volume": 42,
    }
    if backend in ("ssd1306", "st7735") and device:
        _render_device(device, backend, fake_status)
        print("Wrote test pattern to physical display.")
    else:
        _render_console(fake_status)
    return 0


if __name__ == "__main__":
    sys.exit(run_self_test())
