from flask import Blueprint, jsonify, redirect, request, url_for

from radio import get_service

api = Blueprint("api", __name__)


def svc():
    return get_service()


@api.route("/status")
def status():
    service = svc()
    service.check_sleep_timer()
    return jsonify(service.get_status())


@api.route("/metadata")
def metadata():
    return jsonify(svc().get_metadata())


@api.route("/next", methods=["POST", "GET"])
def next_station():
    svc().next()
    return jsonify(svc().get_status())


@api.route("/prev", methods=["POST", "GET"])
def prev_station():
    svc().previous()
    return jsonify(svc().get_status())


@api.route("/toggle", methods=["POST"])
def toggle():
    svc().toggle_playback()
    return jsonify(svc().get_status())


@api.route("/stop", methods=["POST"])
def stop():
    svc().stop_playback()
    return jsonify(svc().get_status())


@api.route("/volume/up", methods=["POST", "GET"])
def volume_up():
    svc().volume_up()
    return jsonify(svc().get_status())


@api.route("/volume/down", methods=["POST", "GET"])
def volume_down():
    svc().volume_down()
    return jsonify(svc().get_status())


@api.route("/favorites", methods=["GET", "POST", "DELETE"])
def favorites():
    service = svc()
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


@api.route("/favorites/play", methods=["POST"])
def favorites_play():
    data = request.get_json(silent=True) or {}
    url = data.get("url") or request.args.get("url", "")
    if not url:
        return jsonify({"error": "url required"}), 400
    station = svc().play_favorite(url)
    return jsonify(svc().get_status() | {"played": station})


@api.route("/stations")
def stations_list():
    service = svc()
    mode = request.args.get("mode", service.get_browse_mode())
    return jsonify({
        "mode": mode,
        "stations": service.list_browse_stations(mode),
    })


@api.route("/browse-mode", methods=["POST"])
def browse_mode():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode") or request.args.get("mode", "all")
    try:
        service = svc()
        service.set_browse_mode(mode)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({
        "mode": service.get_browse_mode(),
        "status": service.get_status(),
    })


@api.route("/refresh-stations", methods=["POST"])
def refresh_stations():
    service = svc()
    service.refresh_stations(force=True)
    service._resolve_current_index()
    return jsonify(service.get_status())


@api.route("/languages", methods=["GET"])
def languages():
    service = svc()
    return jsonify({
        "current": service.config["language"],
        "languages": service.available_languages(),
    })


@api.route("/language", methods=["POST"])
def set_language():
    data = request.get_json(silent=True) or {}
    language = (data.get("language") or request.args.get("language", "")).strip()
    if not language:
        return jsonify({"error": "language required"}), 400
    try:
        status = svc().set_language(language)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify(status)


@api.route("/sleep-timer", methods=["GET", "POST", "DELETE"])
def sleep_timer():
    service = svc()
    if request.method == "GET":
        return jsonify(service.get_sleep_timer())

    if request.method == "DELETE":
        service.clear_sleep_timer()
        return jsonify(service.get_sleep_timer())

    data = request.get_json(silent=True) or {}
    minutes = data.get("minutes", request.args.get("minutes", 0))
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return jsonify({"error": "minutes must be an integer"}), 400
    return jsonify(service.set_sleep_timer(minutes))


ui = Blueprint("ui", __name__)


@ui.route("/")
def home():
    from flask import render_template
    return render_template("index.html")


@ui.route("/next")
def legacy_next():
    svc().next()
    return redirect(url_for("ui.home"))


@ui.route("/prev")
def legacy_prev():
    svc().previous()
    return redirect(url_for("ui.home"))


@ui.route("/volumeup")
def legacy_volume_up():
    svc().volume_up()
    return redirect(url_for("ui.home"))


@ui.route("/volumedown")
def legacy_volume_down():
    svc().volume_down()
    return redirect(url_for("ui.home"))
