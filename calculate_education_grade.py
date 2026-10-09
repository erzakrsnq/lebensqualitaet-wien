from education import calculate_education_grade

# Teststandort: Karlsplatz, Wien
latitude = 48.2008
longitude = 16.3695

print("Bildungsanalyse für Karlsplatz, Wien")
print("-" * 50)

grade, points, facilities = calculate_education_grade(
    latitude,
    longitude
)

print(f"Schulnote: {grade}")
print(f"Gesamtpunkte: {points:.2f}")
print(f"Gefundene Bildungseinrichtungen: {len(facilities)}")

print("\nDie 10 nächstgelegenen Einrichtungen:\n")

for facility in facilities[:10]:
    print(f"Name: {facility['name']}")
    print(f"Kategorie: {facility['category']}")
    print(f"Entfernung: {facility['distance']:.0f} m")
    print(f"Punkte: {facility['points']:.2f}")
    print("-" * 40)