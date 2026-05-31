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
cp radio.env.example radio.env   # set RADIO_DISPLAY_ENABLED=1
pip install -r requirements-pi.txt
./start_radio.sh
```

Or manually:

```bash
export RADIO_DISPLAY_ENABLED=1
export RADIO_DISPLAY_TYPE=ssd1306    # I2C OLED (most common)
# export RADIO_DISPLAY_TYPE=st7735   # SPI TFT hat
export DISPLAY_I2C_ADDRESS=0x3C
python service_mode.py
```

**Test the display:**

```bash
export RADIO_DISPLAY_ENABLED=1
python -m radio.pi
```

**If the OLED stays blank:**

1. Enable I2C: `sudo raspi-config` → Interface Options → I2C
2. Install tools: `sudo apt install i2c-tools`
3. Scan bus: `i2cdetect -y 1` — you should see `3c` (try `0x3D` if not)
4. Add user to i2c group: `sudo usermod -aG i2c $USER` then log out/in
5. Confirm `requirements-pi.txt` is installed in your venv

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

| Module | Role |
|--------|------|
| `radio/service.py` | Single `RadioService` + `get_service()` |
| `radio/player.py` | mpc wrapper + playback state |
| `radio/stations.py` | Radio Browser fetch + cache |
| `radio/storage.py` | Config + favorites persistence |
| `radio/pi.py` | Optional GPIO + OLED integration |
| `web.py` | Flask app + REST API |
| `templates/`, `static/` | Web UI |

## Security

The web server binds to `0.0.0.0` with no authentication. Use only on a trusted LAN.
