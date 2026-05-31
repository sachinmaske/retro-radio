# Implementation plan status

## Architecture (segregated)

```text
                    RadioService  (radio/service.py)
                              |
        -------------------------------------------
        |                    |                    |
      MPD                 Display              Web UI
  radio/player.py    radio/display.py      web_ui/
  radio/pi.py         radio/appliance.py   ├── app.py
                                           ├── routes.py
                                           ├── templates/
                                           └── static/
```

| Layer | Package | Role |
|-------|---------|------|
| Core | `radio/service.py` | Station nav, volume, config, favorites |
| Audio | `radio/player.py` | MPD / mpc |
| Display | `radio/display.py` | TFT/OLED + `/dev/fb1` |
| GPIO | `radio/pi.py` | Physical buttons |
| Appliance | `radio/appliance.py` | Phase 8 boot flow |
| Web | `web_ui/` | Control UI + REST API |

## Phase checklist

| Phase | Status |
|-------|--------|
| 1 RadioService | Done |
| 2 station_url persistence | Done |
| 3 Display layer | Done — `radio/display.py` |
| 4 Live display refresh | Done — on every control change |
| 5 Status API | Done — `/api/status` |
| 6 Favorites | Done — per language + browse mode |
| 7 GPIO | Done |
| 8 Appliance mode | Done — `radio/appliance.py`, `deploy/retro-radio.service` |
| 9 Nice-to-have | Done — logos, sleep timer, mobile UI, favorites-only mode |

## Entry points

| Command | Use |
|---------|-----|
| `python service_mode.py` | **Appliance** (Pi): network → MPD → play → display → web |
| `python web.py` | Web/API only |
| `python app.py` | Terminal CLI |

## Phase 8 — Appliance on Pi

```bash
cp radio.env.example radio.env
pip install -r requirements.txt -r requirements-pi.txt
sudo cp deploy/retro-radio.service /etc/systemd/system/
sudo systemctl enable --now retro-radio
```

Or manually: `./start_radio.sh`

## Phase 9 — Web features

- Station logo (favicon from Radio Browser)
- Sleep timer — `POST /api/sleep-timer` `{"minutes": 30}`
- Browse modes — **All stations** / **Favorites only** (next/prev respect mode)
- Mobile-friendly touch targets (`48px`), safe areas

## API (web_ui)

| Method | Path |
|--------|------|
| GET | `/api/status` |
| POST | `/api/next`, `/api/prev`, `/api/toggle` |
| POST | `/api/volume/up`, `/api/volume/down` |
| GET/POST/DELETE | `/api/favorites` |
| POST | `/api/browse-mode` `{"mode":"favorites"}` |
| GET/POST/DELETE | `/api/sleep-timer` |
| POST | `/api/language` |
