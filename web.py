import os
import threading

from flask import Flask, jsonify, redirect, render_template, request, url_for

from radio import get_service

app = Flask(__name__)
service = get_service()


def web_enabled():
    value = os.environ.get("RADIO_WEB_ENABLED", "1").lower()
    return value not in ("0", "false", "no", "off")


def start_web_server(background=True):
    """Start Flask. background=True runs in a daemon thread (for service_mode)."""
    host = os.environ.get("RADIO_WEB_HOST", "0.0.0.0")
    port = int(os.environ.get("RADIO_WEB_PORT", "5000"))

    def run():
        # use_reloader=False — required when not in main thread; saves RAM on Pi
        app.run(
            host=host,
            port=port,
            threaded=True,
            use_reloader=False,
        )

    if background:
        thread = threading.Thread(target=run, daemon=True, name="radio-web")
        thread.start()
        print(f"Web UI: http://{host}:{port}/")
        return thread

    print(f"Web UI: http://{host}:{port}/")
    run()
    return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify(service.get_status())


@app.route("/api/metadata")
def api_metadata():
    return jsonify(service.get_metadata())


@app.route("/api/next", methods=["POST", "GET"])
def api_next():
    service.next()
    return jsonify(service.get_status())


@app.route("/api/prev", methods=["POST", "GET"])
def api_prev():
    service.previous()
    return jsonify(service.get_status())


@app.route("/api/toggle", methods=["POST"])
def api_toggle():
    service.toggle_playback()
    return jsonify(service.get_status())


@app.route("/api/stop", methods=["POST"])
def api_stop():
    service.stop_playback()
    return jsonify(service.get_status())


@app.route("/api/volume/up", methods=["POST", "GET"])
def api_volume_up():
    service.volume_up()
    return jsonify(service.get_status())


@app.route("/api/volume/down", methods=["POST", "GET"])
def api_volume_down():
    service.volume_down()
    return jsonify(service.get_status())


@app.route("/api/favorites", methods=["GET", "POST", "DELETE"])
def api_favorites():
    if request.method == "GET":
        return jsonify({
            "language": service.config["language"],
            "favorites": service.list_favorites(),
        })

    if request.method == "POST":
        station = service.add_current_favorite()
        return jsonify({
            "added": True,
            "station": station,
            "favorites": service.list_favorites(),
        })

    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "url required"}), 400
    removed = service.remove_favorite_by_url(url)
    return jsonify({
        "removed": removed,
        "favorites": service.list_favorites(),
    })


@app.route("/api/favorites/play", methods=["POST"])
def api_favorites_play():
    data = request.get_json(silent=True) or {}
    url = data.get("url") or request.args.get("url", "")
    if not url:
        return jsonify({"error": "url required"}), 400
    station = service.play_favorite(url)
    return jsonify(service.get_status() | {"played": station})


@app.route("/api/refresh-stations", methods=["POST"])
def api_refresh_stations():
    service.refresh_stations(force=True)
    service._resolve_current_index()
    return jsonify(service.get_status())


@app.route("/api/languages", methods=["GET"])
def api_languages():
    return jsonify({
        "current": service.config["language"],
        "languages": service.available_languages(),
    })


@app.route("/api/language", methods=["POST"])
def api_set_language():
    data = request.get_json(silent=True) or {}
    language = (data.get("language") or request.args.get("language", "")).strip()
    if not language:
        return jsonify({"error": "language required"}), 400
    try:
        status = service.set_language(language)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(status)


# Legacy redirect routes
@app.route("/next")
def legacy_next():
    service.next()
    return redirect(url_for("home"))


@app.route("/prev")
def legacy_prev():
    service.previous()
    return redirect(url_for("home"))


@app.route("/volumeup")
def legacy_volume_up():
    service.volume_up()
    return redirect(url_for("home"))


@app.route("/volumedown")
def legacy_volume_down():
    service.volume_down()
    return redirect(url_for("home"))


if __name__ == "__main__":
    start_web_server(background=False)
