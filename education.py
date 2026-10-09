import requests
from transport import calculate_distance


WFS_URL = "https://data.wien.gv.at/daten/geo"

EDUCATION_DATASETS = {
    "ogdwien:UNIVERSITAETOGD": {
        "category": "Universität / FH",
        "points": 4
    },
    "ogdwien:BUECHEREIOGD": {
        "category": "Bücherei",
        "points": 2
    },
    "ogdwien:SCHULEOGD": {
        "category": "Schule",
        "points": 1
    },
    "ogdwien:VOLKSHOCHSCHULEOGD": {
        "category": "Volkshochschule",
        "points": 1
    }
}


def education_distance_factor(distance):
    if distance <= 500:
        return 1.0
    elif distance <= 1000:
        return 0.75
    elif distance <= 2000:
        return 0.5
    elif distance <= 3000:
        return 0.25
    return 0.0


def get_nearby_education(latitude, longitude, radius=3000):
    lat_delta = radius / 111000
    lon_delta = radius / (111000 * 0.67)

    bbox = (
        f"{longitude - lon_delta},"
        f"{latitude - lat_delta},"
        f"{longitude + lon_delta},"
        f"{latitude + lat_delta},"
        "EPSG:4326"
    )

    facilities = {}

    with requests.Session() as session:
        for dataset, settings in EDUCATION_DATASETS.items():
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": dataset,
                "outputFormat": "application/json",
                "srsName": "EPSG:4326",
                "bbox": bbox
            }

            response = session.get(
                WFS_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            for feature in data.get("features", []):
                geometry = feature.get("geometry") or {}
                properties = feature.get("properties") or {}

                if geometry.get("type") != "Point":
                    continue

                coordinates = geometry.get("coordinates")

                if not coordinates or len(coordinates) < 2:
                    continue

                facility_longitude = coordinates[0]
                facility_latitude = coordinates[1]

                distance = calculate_distance(
                    latitude,
                    longitude,
                    facility_latitude,
                    facility_longitude
                )

                if distance > radius:
                    continue

                name = str(properties.get("NAME") or "").strip()
                address = str(properties.get("ADRESSE") or "").strip()

                if not name:
                    continue

                # Universitäten und FHs nur einmal pro Name zählen.
                if dataset == "ogdwien:UNIVERSITAETOGD":
                    unique_key = (
                        dataset,
                        name.casefold()
                    )
                else:
                    unique_key = (
                        dataset,
                        name.casefold(),
                        address.casefold()
                    )

                facility = {
                    "name": name,
                    "address": address,
                    "category": settings["category"],
                    "distance": distance,
                    "base_points": settings["points"],
                    "points": (
                        settings["points"]
                        * education_distance_factor(distance)
                    )
                }

                if (
                    unique_key not in facilities
                    or distance < facilities[unique_key]["distance"]
                ):
                    facilities[unique_key] = facility

    # Wichtig: Diese Zeile gehört zur Funktion,
    # aber NICHT in die for-Schleife.
    return sorted(
        facilities.values(),
        key=lambda facility: facility["distance"]
    )


def calculate_education_grade(latitude, longitude):
    facilities = get_nearby_education(
        latitude,
        longitude
    )

    total_points = sum(
        facility["points"]
        for facility in facilities
    )

    if total_points >= 6:
        grade = 1
    elif total_points >= 4.5:
        grade = 2
    elif total_points >= 3:
        grade = 3
    elif total_points >= 1.5:
        grade = 4
    else:
        grade = 5

    return grade, total_points, facilities