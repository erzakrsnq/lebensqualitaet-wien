
import requests

url = "https://data.wien.gv.at/daten/geo"

params = {
    "service": "WFS",
    "version": "2.0.0",
    "request": "GetFeature",
    "typeNames": "ogdwien:OEFFGRUENLINGOGD",
    "outputFormat": "application/json",
    "srsName": "EPSG:4326",
    "count": 3
}

try:
    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()

    print("Anzahl geladener Grünflächen:", len(data.get("features", [])))

    for feature in data.get("features", []):
        print("\n--------------------")
        print("Eigenschaften:", feature.get("properties"))
        print("Geometrie-Typ:", feature.get("geometry", {}).get("type"))
        print("Koordinaten:", str(feature.get("geometry", {}).get("coordinates"))[:300])

except requests.RequestException as error:
    print("Fehler beim Abrufen:", error)
except ValueError:
    print("Antwort ist kein gültiges JSON.")
    print(response.text[:500])

