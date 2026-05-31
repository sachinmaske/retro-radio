from flask import Flask, redirect
from flask import jsonify
from radio_service import current_station
from radio_controller import RadioController
from player import (
    volume_up,
    volume_down
)

app = Flask(__name__)

radio = RadioController()

@app.route("/api/status")
def status():

    station = current_station()

    return jsonify({
        "station": station["name"]
    })

@app.route("/")
def home():

    station = current_station()

    return f"""
    <h1>Retro Radio</h1>

    <h2>{station['name']}</h2>

    <a href="/prev">Previous</a>
    <br><br>

    <a href="/next">Next</a>
    """

@app.route("/next")
def next_station():

    radio.next()

    return redirect("/")

@app.route("/prev")
def prev_station():

    radio.previous()

    return redirect("/")

@app.route("/volumeup")
def volume_up_route():

    volume_up()

    return redirect("/")

@app.route("/volumedown")
def volume_down_route():

    volume_down()

    return redirect("/")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )