
from flask import Flask, render_template, request
import requests

from transport import calculate_transport_grade
from green import calculate_green_grade
from education import calculate_education_grade

app = Flask(__name__)


def get_coordinates(address):
    url = "https://data.wien.gv.at/daten/OGDAddressService.svc/GetAddressInfo"
    params = {
        "Address": address,
        "crs": "EPSG:4326"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("features"):
            return None

        longitude, latitude = data["features"][0]["geometry"]["coordinates"][:2]
        return latitude, longitude

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        IndexError,
        TypeError
    ):
        return None


def calculate_overall_grade(profile, transport_grade, green_grade, education_grade):
    if profile == "senior":
        weights = {
            "transport": 0.45,
            "green": 0.45,
            "education": 0.10
        }
    else:
        weights = {
            "transport": 0.40,
            "green": 0.20,
            "education": 0.40
        }

    overall_grade = (
        transport_grade * weights["transport"]
        + green_grade * weights["green"]
        + education_grade * weights["education"]
    )

    return round(overall_grade, 2), weights


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/berechnen", methods=["POST"])
def berechnen():
    adresse = (request.form.get("address") or "").strip()
    profil = request.form.get("profile")

    if not adresse:
        return (
            '<h1>Bitte eine Adresse eingeben</h1>'
            '<a href="/">Zurück</a>',
            400
        )

    if profil not in ("student", "senior"):
        return (
            '<h1>Bitte ein gültiges Nutzerprofil auswählen</h1>'
            '<a href="/">Zurück</a>',
            400
        )

    coordinates = get_coordinates(adresse)

    if coordinates is None:
        return (
            '<h1>Adresse nicht gefunden</h1>'
            '<p>Bitte gib eine gültige Wiener Adresse ein.</p>'
            '<a href="/">Zurück</a>',
            400
        )

    latitude, longitude = coordinates

    try:
        oeffi_note, oeffi_punkte, oeffi_linien = calculate_transport_grade(
            latitude, longitude
        )
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return (
            '<h1>Öffi-Daten momentan nicht verfügbar</h1>'
            '<a href="/">Zurück</a>',
            503
        )

    try:
        (
            gruen_note,
            gruen_entfernung,
            gruen_anzahl,
            gruenflaechen
        ) = calculate_green_grade(latitude, longitude)
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return (
            '<h1>Grünflächen-Daten momentan nicht verfügbar</h1>'
            '<a href="/">Zurück</a>',
            503
        )

    try:
        (
            bildung_note,
            bildung_punkte,
            bildung_einrichtungen
        ) = calculate_education_grade(latitude, longitude)
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return (
            '<h1>Bildungsdaten momentan nicht verfügbar</h1>'
            '<a href="/">Zurück</a>',
            503
        )

    gesamtnote, gewichtung = calculate_overall_grade(
        profil,
        oeffi_note,
        gruen_note,
        bildung_note
    )

    return render_template(
        "result.html",
        adresse=adresse,
        profil=profil,
        latitude=latitude,
        longitude=longitude,
        gesamtnote=gesamtnote,
        gewichtung=gewichtung,
        oeffi_note=oeffi_note,
        oeffi_punkte=oeffi_punkte,
        oeffi_linien=oeffi_linien,
        gruen_note=gruen_note,
        gruen_entfernung=gruen_entfernung,
        gruen_anzahl=gruen_anzahl,
        gruenflaechen=gruenflaechen,
        bildung_note=bildung_note,
        bildung_punkte=bildung_punkte,
        bildung_einrichtungen=bildung_einrichtungen
    )


if __name__ == "__main__":
    app.run(debug=True)
