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

## Run modes

### CLI

```bash
python app.py
```

Keys: `n`/`p` next/prev, `t` toggle, `x` stop, `+`/`-` volume, `s` status, `f` favorite, `v` list favorites, `r` refresh station list, `q` quit.

### Web UI

```bash
python web.py
```

Open `http://<host>:5000/` — retro-styled UI with live status polling, volume, favorites, and stream metadata.

### Headless service

```bash
python service_mode.py
# or
RETRO_RADIO_DIR="$(pwd)" ./start_radio.sh
```

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

### TFT / OLED display

```bash
export RADIO_DISPLAY_ENABLED=1
export DISPLAY_I2C_ADDRESS=0x3C
export RADIO_DISPLAY_INTERVAL=2
python service_mode.py
```

Without hardware, the display falls back to console logging.

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
