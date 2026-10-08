import requests
from collections import defaultdict

url = "https://data.wien.gv.at/daten/geo"

typen = defaultdict(list)
anzahl_gesamt = 0

try:
    for start_index in range(0, 10000, 1000):
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeNames": "ogdwien:OEFFHALTESTOGD",
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
            "count": 1000,
            "startIndex": start_index
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        features = data.get("features", [])
        anzahl_gesamt += len(features)

        for feature in features:
            properties = feature.get("properties", {})

            typ = properties.get("LTYP")
            name = properties.get("HTXT")
            linien = properties.get("HLINIEN")

            if len(typen[typ]) < 5:
                typen[typ].append((name, linien))

        print(f"Bisher geladen: {anzahl_gesamt} Haltestellen")

        if len(features) < 1000:
            break

    print("\nGefundene Verkehrstypen:\n")

    for typ, beispiele in sorted(typen.items(), key=lambda x: str(x[0])):
        print(f"LTYP = {typ}")

        for name, linien in beispiele:
            print(f"  {name} | Linien: {linien}")

        print("-" * 40)

except requests.RequestException as error:
    print("Verbindungsfehler:", error)

except ValueError:
    print("Der Server hat kein gültiges JSON zurückgegeben.")