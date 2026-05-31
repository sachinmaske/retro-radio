"""TFT/OLED display layer — Pillow render + luma or /dev/fb1 (per implementation plan)."""
import os
import struct
import threading
import time

_font_cache = {}


def _enabled(name):
    return os.environ.get(name, "").lower() in ("1", "true", "yes", "on")


def _env_bool(name, default="0"):
    return os.environ.get(name, default).lower() in ("1", "true", "yes", "on")


def _pin(key, default):
    return int(os.environ.get(key, default))


def _get_font(size):
    if size in _font_cache:
        return _font_cache[size]

    from PIL import ImageFont

    custom = os.environ.get("DISPLAY_FONT", "").strip()
    if custom and os.path.isfile(custom):
        font = ImageFont.truetype(custom, size)
        _font_cache[size] = font
        return font

    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if os.path.isfile(path):
            font = ImageFont.truetype(path, size)
            _font_cache[size] = font
            return font

    font = ImageFont.load_default()
    _font_cache[size] = font
    return font


def _line_height(font, default=12):
    if hasattr(font, "size"):
        return int(font.size) + 2
    return default


def render_status_image(status, width, height, monochrome=False):
    """Build a Pillow image for the current status."""
    from PIL import Image, ImageDraw

    if monochrome:
        img = Image.new("1", (width, height), 0)
        fill = 255
    else:
        img = Image.new("RGB", (width, height), (0, 0, 0))
        fill = (255, 255, 255)

    draw = ImageDraw.Draw(img)

    if height <= 64:
        title_size, body_size = 10, 9
    elif height <= 128:
        title_size, body_size = 11, 10
    else:
        title_size, body_size = 14, 12

    font_title = _get_font(title_size)
    font_body = _get_font(body_size)

    station = status.get("station", {})
    stream = status.get("stream", {})
    name = (station.get("name") or "Retro Radio").strip()
    line2 = (stream.get("title") or stream.get("artist") or "").strip()
    if not line2:
        line2 = station.get("country") or "-"
    footer = f"{status.get('state', '?')}  vol {status.get('volume', 0)}"

    max_chars = max(8, width // 7)
    name = name[:max_chars]
    line2 = line2[:max_chars]
    footer = footer[:max_chars]

    y = 0
    draw.text((0, y), name, font=font_title, fill=fill)
    y += _line_height(font_title, title_size + 2)
    draw.text((0, y), line2, font=font_body, fill=fill)
    y += _line_height(font_body, body_size + 2)
    draw.text((0, y), footer, font=font_body, fill=fill)

    return img


def _image_to_rgb565(img):
    img = img.convert("RGB")
    out = bytearray()
    for r, g, b in img.getdata():
        out.extend(struct.pack(">H", ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)))
    return bytes(out)


class Display:
    """Display facade used by RadioService (plan: show_status / refresh)."""

    def show_station(self, name):
        self.show_status({
            "station": {"name": name},
            "stream": {},
            "state": "play",
            "volume": 0,
        })

    def show_volume(self, volume):
        self.show_status({
            "station": {"name": ""},
            "stream": {},
            "state": "play",
            "volume": volume,
        })

    def refresh(self, service):
        self.show_status(service.get_status())

    def show_status(self, status):
        raise NotImplementedError


class ConsoleDisplay(Display):
    def show_status(self, status):
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


class LumaDisplay(Display):
    def __init__(self, device, backend):
        self.device = device
        self.backend = backend
        self.width = device.width
        self.height = device.height

    def show_status(self, status):
        img = render_status_image(
            status,
            self.width,
            self.height,
            monochrome=(self.backend == "ssd1306"),
        )
        self.device.display(img)


class FramebufferDisplay(Display):
    """Write RGB565 to Linux framebuffer (e.g. /dev/fb1 for GPIO TFT)."""

    def __init__(self, path, width, height):
        self.path = path
        self.width = width
        self.height = height

    def show_status(self, status):
        img = render_status_image(status, self.width, self.height)
        img = img.resize((self.width, self.height))
        data = _image_to_rgb565(img)
        with open(self.path, "wb") as fb:
            fb.write(data)


def _init_luma_device():
    display_type = os.environ.get("RADIO_DISPLAY_TYPE", "ssd1306").lower().strip()
    rotate = int(os.environ.get("DISPLAY_ROTATE", "0"))

    if display_type in ("st7735", "st7789"):
        from luma.core.interface.serial import spi

        serial = spi(
            port=int(os.environ.get("DISPLAY_SPI_PORT", "0")),
            device=int(os.environ.get("DISPLAY_SPI_DEVICE", "0")),
            gpio_DC=_pin("DISPLAY_GPIO_DC", 23),
            gpio_RST=_pin("DISPLAY_GPIO_RST", 24),
        )
        width = int(os.environ.get("DISPLAY_WIDTH", "128"))
        height = int(os.environ.get("DISPLAY_HEIGHT", "160"))
        bgr = _env_bool("DISPLAY_BGR", "1")

        if display_type == "st7789":
            from luma.lcd.device import st7789

            device = st7789(
                serial, width=width, height=height, rotate=rotate, bgr=bgr
            )
        else:
            from luma.lcd.device import st7735

            device = st7735(
                serial, width=width, height=height, rotate=rotate, bgr=bgr
            )
        print(f"{display_type.upper()} OK ({width}x{height})")
        return LumaDisplay(device, display_type)

    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306

    port = int(os.environ.get("DISPLAY_I2C_PORT", "1"))
    addr = int(os.environ.get("DISPLAY_I2C_ADDRESS", "0x3C"), 16)
    device = ssd1306(i2c(port=port, address=addr), rotate=rotate)
    print(f"SSD1306 OK (port {port}, {hex(addr)})")
    return LumaDisplay(device, "ssd1306")


def create_display():
    """Create Display backend from radio.env / environment."""
    if not _enabled("RADIO_DISPLAY_ENABLED"):
        return None

    fb_path = os.environ.get("DISPLAY_FB", "").strip()
    if fb_path:
        width = int(os.environ.get("DISPLAY_WIDTH", "128"))
        height = int(os.environ.get("DISPLAY_HEIGHT", "160"))
        print(f"Framebuffer display: {fb_path} ({width}x{height})")
        return FramebufferDisplay(fb_path, width, height)

    try:
        return _init_luma_device()
    except ImportError as exc:
        print(f"Display libs missing ({exc}); console fallback")
        return ConsoleDisplay()
    except Exception as exc:
        print(f"Display init failed ({exc}); console fallback")
        return ConsoleDisplay()


def attach_display(service):
    """Wire display to RadioService and show startup test pattern."""
    display = create_display()
    if not display:
        return None

    service.set_display(display)

    test = {
        "station": {"name": "Retro Radio"},
        "stream": {"title": "Starting…"},
        "state": "play",
        "volume": service.config.get("volume", 0),
    }
    try:
        display.show_status(test)
        time.sleep(1)
        display.refresh(service)
    except Exception as exc:
        print(f"Display test failed: {exc}")

    return display


def start_metadata_poll(service, interval=None):
    """Slow poll for stream title updates (buttons use instant refresh)."""
    if not _enabled("RADIO_DISPLAY_ENABLED"):
        return

    interval = interval or float(os.environ.get("RADIO_DISPLAY_INTERVAL", "8"))

    def loop():
        while True:
            try:
                if service.display:
                    service.display.refresh(service)
            except Exception as exc:
                print(f"Display poll: {exc}")
            time.sleep(interval)

    threading.Thread(target=loop, daemon=True, name="display-poll").start()
