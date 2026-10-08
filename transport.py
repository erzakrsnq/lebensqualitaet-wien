import requests
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371000

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    return 2 * earth_radius * math.asin(math.sqrt(a))

def get_nearby_stops(latitude, longitude, radius=1000):
    # Ungefährer Suchbereich in GPS-Koordinaten
    lat_delta = radius / 111_000
    lon_delta = radius / (111_000 * 0.67)

    bbox = (
        f"{longitude - lon_delta},"
        f"{latitude - lat_delta},"
        f"{longitude + lon_delta},"
        f"{latitude + lat_delta},"
        "EPSG:4326"
    )

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "ogdwien:OEFFHALTESTOGD",
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": "".join(bbox)
    }

    response = requests.get(
        "https://data.wien.gv.at/daten/geo",
        params=params,
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    return data.get("features", [])

def distance_factor(distance):
    if distance <= 250:
        return 1.0
    elif distance <= 500:
        return 0.75
    elif distance <= 750:
        return 0.5
    elif distance <= 1000:
        return 0.25
    return 0


def classify_line(line, stop_type):
    line = line.strip().upper()

    if not line:
        return None
    if line == "WLB":
        return "Lokalbahn", 3

    if line.startswith("U") and line[1:].isdigit():
        return "U-Bahn", 4

    if line.startswith("S") and line[1:].isdigit():
        return "S-Bahn", 3

    if line.startswith("N") and line[1:].isdigit():
        return None  # Nachtbusse vorerst nicht bewerten

    if stop_type == 1:
        # Bei Straßenbahn-Haltestellen können auch Buslinien stehen.
        if line.endswith(("A", "B")):
            return "Bus", 1
        if line == "WLB":
            return "Straßenbahn", 3
        if line.isdigit() or line in ("D", "O"):
            return "Straßenbahn", 3

    if stop_type in (2, 3):
        return "Bus", 1

    if stop_type == 9 and line == "WLB":
        return "Straßenbahn", 3

    return None


def calculate_transport_grade(latitude, longitude):
    stops = get_nearby_stops(latitude, longitude)

    # Jede Linie wird nur einmal gezählt.
    # Bei mehreren Haltestellen zählt die kürzeste Entfernung.
    lines = {}

    for stop in stops:
        geometry = stop.get("geometry") or {}
        coordinates = geometry.get("coordinates")

        if not coordinates or len(coordinates) < 2:
            continue

        stop_lon, stop_lat = coordinates[:2]

        distance = calculate_distance(
            latitude, longitude, stop_lat, stop_lon
        )

        if distance > 1000:
            continue

        properties = stop.get("properties", {})
        stop_type = properties.get("LTYP")
        line_text = properties.get("HLINIEN") or ""

        for line in line_text.split(","):
            line = line.strip().upper()
            classification = classify_line(line, stop_type)

            if classification is None:
                continue

            category, base_points = classification

            if line not in lines or distance < lines[line]["distance"]:
                lines[line] = {
                    "category": category,
                    "distance": distance,
                    "base_points": base_points
                }

    total_points = 0

    for line, details in lines.items():
        points = (
            details["base_points"]
            * distance_factor(details["distance"])
        )

        details["points"] = points
        total_points += points

    score = min(total_points, 10)

    if score >= 8:
        grade = 1
    elif score >= 6:
        grade = 2
    elif score >= 4:
        grade = 3
    elif score >= 2:
        grade = 4
    else:
        grade = 5

    return grade, score, lines

if __name__ == "__main__":
    latitude = 48.199591
    longitude = 16.370226

    grade, score, lines = calculate_transport_grade(
        latitude, longitude
    )

    print("ÖFFI-BEWERTUNG KARLSPLATZ")
    print("-------------------------")
    print(f"Anzahl unterschiedlicher Linien: {len(lines)}")
    print(f"Punkte: {score:.2f} von 10")
    print(f"Schulnote: {grade}")

    print("\nGefundene Linien:")

    for line, details in sorted(lines.items()):
        print(
            f"{line} | {details['category']} "
            f"| {details['distance']:.0f} m "
            f"| {details['points']:.2f} Punkte"
        )