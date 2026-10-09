
import math
import requests

from transport import calculate_distance


WFS_URL = "https://data.wien.gv.at/daten/geo"


def distance_to_segment(latitude, longitude, point_a, point_b):
    """
    Berechnet näherungsweise die kürzeste Entfernung
    zwischen einer Adresse und einem Liniensegment.
    Ergebnis in Metern.
    """

    # GeoJSON verwendet [Längengrad, Breitengrad]
    lon_a, lat_a = point_a[:2]
    lon_b, lat_b = point_b[:2]

    # Umrechnung in ein lokales Koordinatensystem (Meter)
    earth_radius = 6371000
    reference_lat = math.radians(latitude)

    def to_xy(lat, lon):
        x = earth_radius * math.radians(lon - longitude) * math.cos(reference_lat)
        y = earth_radius * math.radians(lat - latitude)
        return x, y

    ax, ay = to_xy(lat_a, lon_a)
    bx, by = to_xy(lat_b, lon_b)

    dx = bx - ax
    dy = by - ay

    length_squared = dx * dx + dy * dy

    if length_squared == 0:
        return math.hypot(ax, ay)

    # Nächstgelegener Punkt auf dem Liniensegment
    t = -(ax * dx + ay * dy) / length_squared
    t = max(0, min(1, t))

    closest_x = ax + t * dx
    closest_y = ay + t * dy

    return math.hypot(closest_x, closest_y)


def distance_to_geometry(latitude, longitude, geometry):

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates", [])

    if geometry_type == "LineString":
        lines = [coordinates]

    elif geometry_type == "MultiLineString":
        lines = coordinates

    elif geometry_type == "Point":
        lon, lat = coordinates[:2]
        return calculate_distance(latitude, longitude, lat, lon)

    else:
        return float("inf")

    shortest_distance = float("inf")

    for line in lines:
        if len(line) == 1:
            lon, lat = line[0][:2]
            distance = calculate_distance(latitude, longitude, lat, lon)
            shortest_distance = min(shortest_distance, distance)

        for index in range(len(line) - 1):
            distance = distance_to_segment(
                latitude,
                longitude,
                line[index],
                line[index + 1]
            )

            shortest_distance = min(shortest_distance, distance)

    return shortest_distance


def get_nearby_green_spaces(latitude, longitude, radius=1200):
    lat_delta = radius / 111000
    lon_delta = radius / (
        111000 * math.cos(math.radians(latitude))
    )

    bbox = (
        f"{longitude - lon_delta},"
        f"{latitude - lat_delta},"
        f"{longitude + lon_delta},"
        f"{latitude + lat_delta},"
        f"EPSG:4326"
    )

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "ogdwien:OEFFGRUENLINGOGD",
        "outputFormat": "application/json",
        "srsName": "EPSG:4326",
        "bbox": bbox
    }

    response = requests.get(
        WFS_URL,
        params=params,
        timeout=30
    )
    response.raise_for_status()

    data = response.json()

    green_spaces = {}

    for feature in data.get("features", []):
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}

        name = str(properties.get("TEXT13ID") or "").strip()

        if not name:
            continue

        distance = distance_to_geometry(
            latitude,
            longitude,
            geometry
        )

        if distance > radius:
            continue

        # Gleicher Name = nur eine Grünfläche.
        # Wir behalten die kürzeste Entfernung.
        if (
            name not in green_spaces
            or distance < green_spaces[name]
        ):
            green_spaces[name] = distance

    return green_spaces


def calculate_green_grade(latitude, longitude):

    green_spaces = get_nearby_green_spaces(
        latitude,
        longitude
    )

    if not green_spaces:
        return 5, None, 0, {}

    nearest_distance = min(green_spaces.values())

    if nearest_distance <= 200:
        grade = 1
    elif nearest_distance <= 400:
        grade = 2
    elif nearest_distance <= 700:
        grade = 3
    elif nearest_distance <= 1000:
        grade = 4
    else:
        grade = 5

    count_within_750m = sum(
        1
        for distance in green_spaces.values()
        if distance <= 750
    )

    # Bonus bei mindestens 3 verschiedenen Grünflächen
    if count_within_750m >= 3:
        grade = max(1, grade - 1)

    return (
        grade,
        nearest_distance,
        count_within_750m,
        green_spaces
    )


# TEST: Karlsplatz
if __name__ == "__main__":

    latitude = 48.2008
    longitude = 16.3695

    print("GRÜNFLÄCHEN-BEWERTUNG KARLSPLATZ")
    print("--------------------------------")

    try:
        grade, nearest, count, green_spaces = (
            calculate_green_grade(latitude, longitude)
        )

        print("Schulnote:", grade)

        if nearest is not None:
            print(f"Nächste Grünfläche: {nearest:.0f} m")
        else:
            print("Keine Grünfläche im Suchbereich gefunden.")

        print("Grünflächen innerhalb von 750 m:", count)

        print("\nGefundene Grünflächen:")

        for name, distance in sorted(
            green_spaces.items(),
            key=lambda item: item[1]
        )[:15]:
            print(f"{name}: {distance:.0f} m")

    except (requests.RequestException, ValueError) as error:
        print("Fehler beim Laden der Grünflächendaten:", error)
