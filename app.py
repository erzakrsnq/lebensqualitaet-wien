
from flask import Flask, render_template, request
import requests
import re
import unicodedata

from transport import calculate_transport_grade
from green import calculate_green_grade
from education import calculate_education_grade

app = Flask(__name__)


class AddressServiceError(Exception):
    pass


def normalize_text(text):
    text = unicodedata.normalize("NFKC", str(text))
    text = text.casefold().strip()

    # Übliche Schreibvarianten vereinheitlichen
    text = text.replace("ß", "ss")
    text = re.sub(r"\s+", " ", text)

    return text


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

    except (requests.RequestException, ValueError) as error:
        raise AddressServiceError(
            "Der Adressdienst ist momentan nicht verfügbar."
        ) from error

    features = data.get("features", [])

    if not isinstance(features, list):
        raise AddressServiceError("Ungültige Antwort des Adressdienstes.")

    # Eingabe vereinheitlichen und optionale Wien-Angaben entfernen
    entered = normalize_text(address)
    entered = re.sub(r",?\s*(?:a-)?1\d{3}\s+wien$", "", entered)
    entered = re.sub(r",?\s*wien$", "", entered)
    entered = entered.strip(" ,")

    # Straße + Hausnummer verlangen
    match = re.fullmatch(r"(.+?)\s+(\d+[a-z]?)", entered)

    if not match:
        return None

    entered_street = match.group(1).strip()
    entered_number = match.group(2)

    for feature in features:
        properties = feature.get("properties", {})

        if normalize_text(properties.get("Municipality", "")) != "wien":
            continue

        returned_address = normalize_text(
            properties.get("Adresse", "")
        )

        returned_street = normalize_text(
            properties.get("StreetName", "")
        )

        # Kein ungefährer Straßenname!
        if returned_street != entered_street:
            continue

        # Hausnummer muss zur zurückgegebenen Adresse passen
        returned_match = re.search(
            r"(?<!\d)" + re.escape(entered_number) + r"(?!\d|[a-z])",
            returned_address
        )

        if not returned_match:
            continue

        try:
            longitude, latitude = feature["geometry"]["coordinates"][:2]
            return float(latitude), float(longitude)

        except (KeyError, IndexError, TypeError, ValueError):
            continue

    return None


def calculate_overall_grade(
    profile,
    transport_grade,
    green_grade,
    education_grade
):
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


def error_page(title, message, status_code):
    return (
        f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>WIENLEBEN – Hinweis</title>
            <style>
                body {{
                    margin: 0;
                    background: #f3f7f6;
                    color: #102b36;
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    padding: 20px;
                    box-sizing: border-box;
                }}
                .error-card {{
                    background: white;
                    border-radius: 20px;
                    padding: 35px;
                    max-width: 500px;
                    width: 100%;
                    text-align: center;
                }}
                h1 {{
                    color: #17684e;
                }}
                p {{
                    color: #648077;
                    line-height: 1.6;
                }}
                a {{
                    display: block;
                    margin-top: 25px;
                    background: #17684e;
                    color: white;
                    text-decoration: none;
                    border-radius: 12px;
                    padding: 15px;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <main class="error-card">
                <h1>{title}</h1>
                <p>{message}</p>
                <a href="/">← Zurück zur Startseite</a>
            </main>
        </body>
        </html>
        """,
        status_code
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/berechnen", methods=["POST"])
def berechnen():
    adresse = (request.form.get("address") or "").strip()
    profil = request.form.get("profile")

    if not adresse:
        return error_page(
            "Bitte eine Adresse eingeben",
            "Gib eine gültige Wiener Adresse ein.",
            400
        )

    if profil not in ("student", "senior"):
        return error_page(
            "Ungültiges Nutzerprofil",
            "Bitte wähle Studierende oder Senioren aus.",
            400
        )

    try:
        coordinates = get_coordinates(adresse)

    except AddressServiceError:
        return error_page(
            "Adressdienst momentan nicht verfügbar",
            "Bitte versuche es später erneut.",
            503
        )

    if coordinates is None:
        return error_page(
            "Adresse nicht gefunden",
            "Bitte gib eine gültige Wiener Straße mit Hausnummer ein, "
            "zum Beispiel Czeikestraße 2.",
            400
        )

    latitude, longitude = coordinates

    try:
        oeffi_note, oeffi_punkte, oeffi_linien = calculate_transport_grade(
            latitude, longitude
        )

    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        return error_page(
            "Öffi-Daten momentan nicht verfügbar",
            "Bitte versuche es später erneut.",
            503
        )

    try:
        (
            gruen_note,
            gruen_entfernung,
            gruen_anzahl,
            gruenflaechen
        ) = calculate_green_grade(latitude, longitude)

    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        return error_page(
            "Grünflächen-Daten momentan nicht verfügbar",
            "Bitte versuche es später erneut.",
            503
        )

    try:
        (
            bildung_note,
            bildung_punkte,
            bildung_einrichtungen
        ) = calculate_education_grade(latitude, longitude)

    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        return error_page(
            "Bildungsdaten momentan nicht verfügbar",
            "Bitte versuche es später erneut.",
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
