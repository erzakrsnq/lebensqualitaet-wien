from flask import Flask, render_template, request
import requests
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

        coordinates = data["features"][0]["geometry"]["coordinates"]

        longitude = coordinates[0]
        latitude = coordinates[1]

        return latitude, longitude

    except requests.RequestException:
        return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/berechnen", methods=["POST"])
def berechnen():
    adresse = request.form.get("address")
    profil = request.form.get("profile")

    coordinates = get_coordinates(adresse)

    if coordinates is None:
        return """
            <h1>Adresse nicht gefunden</h1>
            <p>Bitte gib eine gültige Wiener Adresse ein.</p>
            <a href="/">Zurück</a>
        """

    latitude, longitude = coordinates

    return f"""
        <h1>Adresse gefunden!</h1>
        <p>Adresse: {adresse}</p>
        <p>Profil: {profil}</p>
        <p>Breitengrad: {latitude}</p>
        <p>Längengrad: {longitude}</p>
        <a href="/">Zurück</a>
    """
if __name__ == "__main__":
    app.run(debug=True)