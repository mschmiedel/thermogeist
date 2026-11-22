<p align="center"><img src="brand/logo.png" alt="Thermogeist" width="480"></p>

# Thermogeist

[English](README.md) | **Deutsch**

> **Status: Alpha, im täglichen Einsatz.** Haus und Räume beschreiben, Thermostate hinzufügen,
> sehen, was Thermogeist tun würde (Beobachten), und Raum für Raum das Regeln einschalten – über
> Ventilstellung oder über Sollwert. Zwischen den Versionen kann sich noch einiges ändern.
> Los geht's mit [Erste Schritte](docs/de/getting-started.md).

Ruhige, nachvollziehbare Heizkörperregelung für Home Assistant – für das ganze Haus, nicht nur
Ventil für Ventil.

## Warum

Smarte Heizkörperthermostate verhalten sich meist wie Einzelgeräte. Sie kennen dein Haus nicht,
regeln nervös, und wenn sie abschalten, erfährst du selten warum. Thermogeist ergänzt die
fehlende Ebene:

- **Es kennt dein Haus und deine Räume.** Heizlast, Anteil jedes Raums und Heizkörpergröße
  ergeben ein Modell dessen, was jeder Raum braucht – und Thermogeist lernt im normalen Betrieb,
  wie viel der Raum wirklich braucht.
- **Wärmepumpenfreundlich.** Ventile behalten eine Mindestöffnung und bewegen sich langsam,
  statt zuzuknallen; ein Neustart oder ein Fenster lässt sie nie springen.
- **Erklärt sich immer.** Jeder Grund – Fenster, Frostschutz, ein stummer Sensor – ist in Home
  Assistant sichtbar, mit einer Hilfeseite.
- **Einfach einzurichten.** Ein paar Fragen statt langer Formulare; Thermostate werden erkannt
  und gleich beim Anlegen eines Raums hinzugefügt.

## Was es heute kann

- **Raumregelung** über die Ventilstellung (Sonoff TRVZB, Bosch Heizkörperthermostat II) oder
  über den Sollwert (jedes Thermostat mit Klima-Entität), mit einer ruhigen Regelung, die aus dem
  Wärmebedarf vorausplant.
- **Fenster:** Das Heizen pausiert 30 s, nachdem ein Kontakt aufgeht, und geht beim Schließen
  sofort weiter; eigene Fensterfunktionen und Zeitpläne der Thermostate können deine
  Raum-Sollwerte nicht verstellen.
- **Lernen:** Jeder Raum lernt aus ruhigen Stunden, wie viel seines berechneten Bedarfs er
  wirklich braucht, getrennt nach Tag und Nacht.
- **Wärme aus Geräten:** Ein Gaming-PC oder eine heizende Klimaanlage zählt mit, mit einem Faktor
  pro Gerät (auch aus einem Sensor, z. B. einem COP-Template).
- **Diagnose:** Heizkörpergröße pro Raum (zu klein, passend, viel größer als nötig), geschätzte
  Heizleistung, Wärmebedarf und Heizleistung aller Räume am Haus, eine aus dem Vorlauf-Sensor gelernte Heizkurve – oder zwei eingegebene
  Punkte, wenn es keinen Sensor gibt.
- **Zuverlässig mit echten Geräten:** Einstellungen, die ein Firmware-Update zurücksetzt, werden
  wieder gesetzt; stumme Sensoren und veraltete Werte werden erkannt.

Geplant: Zeitpläne, Verbindungen zwischen Räumen (offene Türen), smarte Kindersicherung – siehe [`spec/roadmap.md`](spec/roadmap.md).

## Unterstützte Geräte

| Gerät | Anbindung | Wie | Getestet |
|---|---|---|---|
| Sonoff TRVZB | Zigbee2MQTT | Ventilstellung, Raumsensor wird ans Thermostat geschickt | ja |
| Bosch Heizkörperthermostat II (BTH-RA) | Zigbee2MQTT | Ventilstellung | ja |
| Sonoff TRV-ZBT (Gen 2) | Zigbee2MQTT | Ventilstellung | Profil, nicht getestet |
| Andere Zigbee2MQTT-Thermostate | Zigbee2MQTT + MQTT-Integration | Rollen aus Zigbee2MQTT erkannt | erkannt, nicht getestet |
| Jedes Thermostat mit `climate`-Entität (z. B. Bosch Smart Home) | Home Assistant | Sollwert – mit Grenzen, siehe [Thermostate](docs/de/thermostats.md) | ja |

## Installation

**HACS (benutzerdefiniertes Repository):** HACS → ⋮ → *Benutzerdefinierte Repositories* →
`https://github.com/mschmiedel/thermogeist` hinzufügen, Kategorie *Integration*. Solange
Thermogeist Alpha ist, für das Repository *Beta-Versionen anzeigen* einschalten. Dann
installieren, Home Assistant neu starten und die Integration hinzufügen.

**Von Hand:** `thermogeist.zip` aus dem neuesten
[Release](https://github.com/mschmiedel/thermogeist/releases) herunterladen, nach
`config/custom_components/thermogeist/` entpacken und Home Assistant neu starten.

Benötigt Home Assistant 2026.10 oder neuer.

## Dokumentation

- [Erste Schritte](docs/de/getting-started.md) – installieren und dein Haus beschreiben
- [Räume](docs/de/rooms.md) und [Thermostate](docs/de/thermostats.md) – mit Ablauf-Diagrammen
- [Alle Entitäten](docs/de/entities.md) – was jeder Wert bedeutet und wann er da ist
- [Häufige Fragen](docs/de/faq/README.md) – jeder Grund, den ein Raum anzeigen kann

Die Produktspezifikation (Englisch) liegt in [`spec/`](spec/).

## Lizenz

[MIT](LICENSE). Projekte und Quellen, auf denen Thermogeist aufbaut, stehen in
[CREDITS.md](CREDITS.md).
