import requests

def get_stations(language="hindi", limit=50):
    url = f"https://de1.api.radio-browser.info/json/stations/bylanguage/{language}"

    response = requests.get(url, timeout=10)
    stations = response.json()

    result = []

    for station in stations:
        if station.get("url"):
            result.append({
                "name": station["name"],
                "url": station["url"]
            })

    return result[:limit]
