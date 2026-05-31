"""Web-only entry point. Appliance mode uses service_mode.py."""
from web_ui import start_web_server

if __name__ == "__main__":
    start_web_server(background=False)
