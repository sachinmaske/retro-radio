#!/bin/bash
# Start retro-radio in headless service mode.
# Override paths: RETRO_RADIO_DIR, RETRO_RADIO_VENV

REPO_DIR="${RETRO_RADIO_DIR:-/home/radio/retro-radio}"
VENV_NAME="${RETRO_RADIO_VENV:-.venv}"

cd "$REPO_DIR" || exit 1
# shellcheck source=/dev/null
source "$VENV_NAME/bin/activate"
python service_mode.py
