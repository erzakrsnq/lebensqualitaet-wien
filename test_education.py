import requests

url = "https://data.wien.gv.at/daten/geo"

datensaetze = [
    "ogdwien:UNIVERSITAETOGD",
    "ogdwien:BUECHEREIOGD",
    "ogdwien:SCHULEOGD",
    "ogdwien:VOLKSHOCHSCHULEOGD"
]

for datensatz in datensaetze:
    print("\n" + "=" * 60)
    print("DATENSATZ:", datensatz)
    print("=" * 60)

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": datensatz,
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "count": 2
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        print("Gefundene Beispiele:", len(features))

        for feature in features:
            print("\nGeometrie:")
            print(feature.get("geometry"))

            print("\nEigenschaften:")
            for key, value in feature.get("properties", {}).items():
                print(f"{key}: {value}")

            print("-" * 40)

    except (requests.RequestException, ValueError) as error:
        print("Fehler:", error)