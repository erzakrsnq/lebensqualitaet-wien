# WIENLEBEN – Lebensqualität in Wien

WIENLEBEN ist eine Webanwendung, die die Lebensqualität einer Wiener Adresse mit Schulnoten von **1 bis 5** bewertet.

Die Bewertung basiert auf Open Data der Stadt Wien und berücksichtigt drei Bereiche:

- Öffentliche Verkehrsmittel
- Grünflächen
- Bildungseinrichtungen

Je nach Nutzerprofil (**Studierende oder Senioren**) werden die Bereiche unterschiedlich gewichtet. Auf der Ergebnisseite wird erklärt, wie die Note berechnet wurde.

## Technologien

Python, Flask, HTML, CSS, JavaScript, Open Data Wien und Docker.

## Mit Docker starten

**Voraussetzung:** Docker muss installiert sein.

```bash
git clone https://github.com/erzakrsnq/lebensqualitaet-wien.git
cd lebensqualitaet-wien
docker build -t wienleben .
docker run --rm -p 5050:5000 wienleben
```

Anschließend im Browser öffnen:

**http://localhost:5050**

Zum Beenden **Ctrl + C** drücken.

## Fertiges Docker-Image laden

Falls die Datei `wienleben-docker.tar` vorhanden ist:

```bash
docker load -i wienleben-docker.tar
docker run --rm -p 5050:5000 wienleben
```

**Hinweis:** Für die Abfrage der Wiener Open-Data-Dienste ist eine Internetverbindung erforderlich.

**Projekt:** Innovation Lab  
**Auftraggeber:** Harald Wahl