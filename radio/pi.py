"""Optional Raspberry Pi GPIO and OLED — lazy imports to save RAM when disabled."""
import os
import threading
import time


def _enabled(name):
    return os.environ.get(name, "").lower() in ("1", "true", "yes", "on")


def setup_gpio(service):
    if not _enabled("RADIO_GPIO_ENABLED"):
        return []

    from gpiozero import Button

    pins = {
        "GPIO_NEXT": 17,
        "GPIO_PREV": 27,
        "GPIO_TOGGLE": 22,
        "GPIO_VOL_UP": 23,
        "GPIO_VOL_DOWN": 24,
    }

    def pin(key, default):
        return int(os.environ.get(key, default))

    buttons = []

    next_btn = Button(pin("GPIO_NEXT", pins["GPIO_NEXT"]), bounce_time=0.3)
    next_btn.when_pressed = (
        service.next
    )
    buttons.append(next_btn)

    prev_btn = Button(pin("GPIO_PREV", pins["GPIO_PREV"]), bounce_time=0.3)
    prev_btn.when_pressed = (
        service.previous
    )
    buttons.append(prev_btn)

    toggle_btn = Button(pin("GPIO_TOGGLE", pins["GPIO_TOGGLE"]), bounce_time=0.3)
    toggle_btn.when_pressed = service.toggle_playback
    buttons.append(toggle_btn)

    vol_up_btn = Button(pin("GPIO_VOL_UP", pins["GPIO_VOL_UP"]), bounce_time=0.3)
    vol_up_btn.when_pressed = (
        service.volume_up
    )
    buttons.append(vol_up_btn)

    vol_down_btn = Button(pin("GPIO_VOL_DOWN", pins["GPIO_VOL_DOWN"]), bounce_time=0.3)
    vol_down_btn.when_pressed = service.volume_down
    buttons.append(vol_down_btn)

    return buttons


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


def _render_oled(device, status):
    from PIL import Image, ImageDraw

    img = Image.new("1", (device.width, device.height))
    draw = ImageDraw.Draw(img)
    s = status.get("station", {})
    stream = status.get("stream", {})
    draw.text((0, 0), (s.get("name") or "?")[:21], fill=255)
    line2 = (stream.get("title") or stream.get("artist") or "")[:21]
    draw.text((0, 12), line2 or "-", fill=255)
    draw.text(
        (0, 24),
        f"{status.get('state', '?')} vol {status.get('volume', 0)}",
        fill=255,
    )
    device.display(img)


def start_display_loop(service):
    if not _enabled("RADIO_DISPLAY_ENABLED"):
        return

    device = None
    use_oled = False

    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306

        addr = int(os.environ.get("DISPLAY_I2C_ADDRESS", "0x3C"), 16)
        device = ssd1306(i2c(port=1, address=addr))
        use_oled = True
    except Exception as exc:
        print(f"OLED unavailable ({exc}); console display only")

    def loop():
        interval = float(os.environ.get("RADIO_DISPLAY_INTERVAL", "3"))
        while True:
            try:
                status = service.get_status()
                if use_oled and device:
                    _render_oled(device, status)
                else:
                    _render_console(status)
            except Exception as exc:
                print(f"Display error: {exc}")
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True, name="radio-display").start()
