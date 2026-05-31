# Retro Radio

Internet radio for Raspberry Pi (or Linux) using [MPD](https://www.musicpd.org/), [mpc](https://www.musicpd.org/clients/), and the [Radio Browser](https://www.radio-browser.info/) API.

## Requirements

- Python 3.10+
- `mpd` and `mpc`
- Network access

```bash
sudo apt install mpd mpc python3-venv
sudo systemctl enable --now mpd
```

## Install

```bash
cd retro-radio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For Raspberry Pi GPIO + OLED support, install the optional hardware stack:

```bash
pip install -r requirements-pi.txt
```

Edit `config.json`:

```json
{
  "language": "marathi",
  "station_url": "",
  "station_uuid": "",
  "volume": 70
}
```

On first run, the current station is resolved from `station_uuid`, then `station_url`, then legacy `station_index`, then defaults to the first cached station.

## Local testing (Mac / Linux)

GPIO and OLED are Pi-only. On a laptop, disable them and use MPD for audio.

### 1. Install MPD + mpc

**macOS (Homebrew):**

```bash
brew install mpd mpc
./scripts/setup_mpd_mac.sh   # creates ~/.mpd/mpd.conf and starts mpd
mpc status                   # should connect (not "Connection refused")
```

If you see **Connection refused**, MPD is not running. Run the setup script again or:

```bash
mpd
mpc status
```

Auto-start on login (after setup):

```bash
brew services start mpd
```

**Debian / Ubuntu:**

```bash
sudo apt install mpd mpc
sudo systemctl start mpd
```

### 2. Python environment

```bash
cd retro-radio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Local `radio.env` (no Pi hardware)

```bash
cp radio.env.example radio.env
```

Ensure these are **off** on a Mac:

```bash
RADIO_WEB_ENABLED=1
RADIO_GPIO_ENABLED=0
RADIO_DISPLAY_ENABLED=0
```

### 4. Run tests

**Full stack (same as Pi — radio + web):**

```bash
python service_mode.py
# open http://127.0.0.1:5000/
```

**Web + API only:**

```bash
python web.py
curl http://127.0.0.1:5000/api/status
```

**CLI:**

```bash
python app.py
```

**Station list / config (no audio):**

```bash
python -c "from radio.stations import get_stations; print(len(get_stations('marathi')), 'stations')"
```

**Display self-test (console fallback on Mac):**

```bash
RADIO_DISPLAY_ENABLED=1 python -m radio.pi
```

## Change language

**Config file** — edit `config.json` and restart:

```json
{ "language": "hindi", ... }
```

**CLI** — press `l`, enter a language (e.g. `hindi`, `marathi`, `english`).

**Web UI** — use the Language dropdown and click Apply.

**API** — `POST /api/language` with JSON `{"language": "tamil"}`.

Changing language reloads the station list and starts the first station in that language.

## Run modes

### CLI

```bash
python app.py
```

Keys: `n`/`p` next/prev, `t` toggle, `x` stop, `+`/`-` volume, `s` status, `f` favorite, `v` list favorites, `r` refresh station list, `q` quit.

### Default service (radio + web + optional GPIO/display)

The normal Pi setup starts playback, web UI, and optional hardware in **one process**:

```bash
cp radio.env.example radio.env   # optional: tune display/GPIO/web port
./start_radio.sh
# or
python service_mode.py
```

Then open **`http://<pi-ip>:5000/`** on your phone or laptop.

Web is **on by default** (`RADIO_WEB_ENABLED=1`). To disable:

```bash
export RADIO_WEB_ENABLED=0
python service_mode.py
```

Environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `RADIO_WEB_ENABLED` | `1` | Start web UI with service |
| `RADIO_WEB_HOST` | `0.0.0.0` | Listen address |
| `RADIO_WEB_PORT` | `5000` | HTTP port |

### Web UI only (no auto-play service)

```bash
python web.py
```

Use this for development on a Mac/PC without MPD service mode.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/status` | Full status (station, stream, volume, state) |
| GET | `/api/metadata` | Station + stream metadata |
| POST | `/api/next`, `/api/prev` | Change station |
| POST | `/api/toggle`, `/api/stop` | Playback control |
| POST | `/api/volume/up`, `/api/volume/down` | Volume |
| GET/POST/DELETE | `/api/favorites` | List / add current / remove (`?url=`) |
| POST | `/api/favorites/play` | JSON body `{ "url": "..." }` |
| POST | `/api/refresh-stations` | Force refresh Radio Browser cache |
| GET | `/api/languages` | Suggested language list + current |
| POST | `/api/language` | JSON `{"language": "hindi"}` — switch language |

Legacy redirects: `/next`, `/prev`, `/volumeup`, `/volumedown`.

## Station cache

Lists are cached under `stations_cache/<language>.json` (24h TTL).

```bash
REFRESH_STATIONS=1 python app.py   # force API refresh on start
STATION_CACHE_TTL=3600 python web.py   # 1 hour TTL
```

## Raspberry Pi hardware

### GPIO buttons

```bash
export RADIO_GPIO_ENABLED=1
# Optional pins (BCM): GPIO_NEXT=17 GPIO_PREV=27 GPIO_TOGGLE=22
# GPIO_VOL_UP=23 GPIO_VOL_DOWN=24
python service_mode.py
```

### OLED / TFT display

The physical display only runs with **`service_mode.py`** (not `app.py` or `web.py`).

```bash
cp radio.env.example radio.env
pip install -r requirements-pi.txt
./start_radio.sh
```

**SPI TFT (ST7735 128×160)** — typical 1.8" Pi hat:

```bash
RADIO_DISPLAY_ENABLED=1
RADIO_DISPLAY_TYPE=st7735
DISPLAY_BGR=1
DISPLAY_WIDTH=128
DISPLAY_HEIGHT=160
```

**I2C OLED (SSD1306 128×64)**:

```bash
RADIO_DISPLAY_TYPE=ssd1306
DISPLAY_I2C_ADDRESS=0x3C
```

**Test the display:**

```bash
export RADIO_DISPLAY_ENABLED=1
export RADIO_DISPLAY_TYPE=st7735
export DISPLAY_BGR=1
python -m radio.pi
```

You should see a bordered **“Retro Radio / Display OK”** screen, then sample text.

**If the TFT lights up but text is blank:**

1. Set `RADIO_DISPLAY_TYPE=st7735` (not `ssd1306` if you have a SPI TFT).
2. Set `DISPLAY_BGR=1` (most boards need this).
3. Try `DISPLAY_ROTATE=90` or `180` if text is off-screen.
4. Install fonts: `sudo apt install fonts-dejavu-core`
5. Or set `DISPLAY_FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`

**If the OLED stays blank:** enable I2C (`raspi-config`), run `i2cdetect -y 1` (expect `3c`).

Without hardware or on failure, output goes to the console as `[display] ...` lines.

## systemd example

```ini
[Unit]
Description=Retro Radio
After=network-online.target mpd.service

[Service]
User=radio
WorkingDirectory=/home/radio/retro-radio
Environment=RADIO_GPIO_ENABLED=1
Environment=RADIO_DISPLAY_ENABLED=1
EnvironmentFile=-/home/radio/retro-radio/radio.env
ExecStart=/home/radio/retro-radio/.venv/bin/python service_mode.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Project layout

| Layer | Path | Role |
|-------|------|------|
| Core | `radio/service.py` | `RadioService` — all playback logic |
| MPD | `radio/player.py` | mpc wrapper |
| Display | `radio/display.py` | TFT/OLED framebuffer |
| Appliance | `radio/appliance.py` | Pi boot flow (Phase 8) |
| GPIO | `radio/pi.py` | Physical buttons |
| Web UI | `web_ui/` | Control UI + `/api/*` (separate layer) |
| Entry | `service_mode.py` | Run appliance on Pi |
| Entry | `web.py` | Web-only dev server |

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for the full plan mapping.

## Security

The web server binds to `0.0.0.0` with no authentication. Use only on a trusted LAN.
