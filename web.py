from flask import Flask, redirect

from radio_controller import RadioController
from player import (
    volume_up,
    volume_down
)

app = Flask(__name__)

radio = RadioController()

@app.route("/")
def home():

    station = radio.current_station()

    return f"""
    <h1>Retro Radio</h1>

    <h2>{station['name']}</h2>

    <p>
      <a href="/prev">Previous</a>
      |
      <a href="/next">Next</a>
      |
      <a href="/volumeup">Vol+</a>
      |
      <a href="/volumedown">Vol-</a>
    </p>
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)