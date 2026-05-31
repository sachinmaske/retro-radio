from flask import Flask, redirect
from radio_state import radio

app = Flask(__name__)

@app.route("/")

def home():
    station = "Unknown"
    if radio:
        station = radio.current_station()["name"]
    return f"""
    <h1>Retro Radio</h1>
    <h2>{station}</h2>
    <p>
      <a href="/prev">Previous</a>
      |
      <a href="/toggle">Play/Pause</a>
      |
      <a href="/next">Next</a>
    </p>
    """


@app.route("/next")
def next_station():
    if radio:
        radio.next()

    return redirect("/")

@app.route("/prev")
def prev_station():
    return redirect("/")

@app.route("/toggle")
def toggle_station():
    return redirect("/")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )