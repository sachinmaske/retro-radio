import subprocess


def _mpc(*args):
    return subprocess.run(
        ["mpc", *args],
        capture_output=True,
        text=True,
        check=False,
    )


def play(url):
    _mpc("clear")
    _mpc("add", url)
    _mpc("play")


def stop():
    _mpc("stop")


def toggle():
    _mpc("toggle")


def volume_up(step=5):
    _mpc("volume", f"+{step}")


def volume_down(step=5):
    _mpc("volume", f"-{step}")


def set_volume(volume):
    _mpc("volume", str(volume))


def get_volume():
    line = (_mpc("volume").stdout or "").strip()
    digits = "".join(ch for ch in line if ch.isdigit())
    return int(digits) if digits else None


def get_playback_state():
    text = (_mpc("status").stdout or "").strip()
    state, title, artist = "stop", "", ""
    lines = text.splitlines() if text else []

    if lines:
        title = lines[0].strip()
    if len(lines) > 1:
        meta = lines[1].strip().lower()
        if "[playing]" in meta:
            state = "play"
        elif "[paused]" in meta:
            state = "pause"
        if " - " in lines[1]:
            parts = lines[1].split(" - ", 1)
            artist = parts[0].strip("[] ")
            title = parts[1].strip() if len(parts) > 1 else title

    return {
        "state": state,
        "title": title,
        "artist": artist,
        "volume": get_volume(),
    }


def print_status():
    subprocess.run(["mpc"])
