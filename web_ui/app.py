import os
import threading

from flask import Flask

from web_ui.routes import api, ui


def web_enabled():
    value = os.environ.get("RADIO_WEB_ENABLED", "1").lower()
    return value not in ("0", "false", "no", "off")


def create_app():
    root = os.path.dirname(os.path.abspath(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(root, "templates"),
        static_folder=os.path.join(root, "static"),
    )
    app.register_blueprint(ui)
    app.register_blueprint(api, url_prefix="/api")
    return app


def start_web_server(background=True):
    host = os.environ.get("RADIO_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("RADIO_WEB_PORT", "5000"))
    app = create_app()

    def run():
        app.run(host=host, port=port, threaded=True, use_reloader=False)

    if background:
        thread = threading.Thread(target=run, daemon=True, name="radio-web")
        thread.start()
        print(f"Web UI: http://{host}:{port}/")
        return thread

    print(f"Web UI: http://{host}:{port}/")
    run()
    return None
