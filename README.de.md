<p align="center"><img src="brand/logo-light.svg" alt="Thermogeist" width="480"></p>

# Thermogeist

[English](README.md) | **Deutsch**

> **Status: frühe Entwicklung.** Du kannst Haus und Räume beschreiben, das Regeln der Thermostate folgt.
> Los geht's mit [Erste Schritte](docs/de/getting-started.md).

Ruhige, nachvollziehbare Heizkörperregelung für Home Assistant – für das ganze Haus, nicht nur
Ventil für Ventil.

## Warum

Smarte Heizkörperthermostate verhalten sich meist wie Einzelgeräte. Sie kennen dein Haus nicht,
regeln nervös, und wenn sie abschalten, erfährst du selten warum. Diese Integration ergänzt die
fehlende Ebene:

- **Ein Ort für das ganze Haus.** Heizungsart, Zeitpläne, Fensterregeln und Gruppen stellst du
  einmal ein, und jeder Raum übernimmt sie.
- **Sie kennt deine Räume.** Gib die Heizlast des Hauses und den Anteil jedes Raums an, optional
  die Heizkörpergröße. Daraus regelt sie gleichmäßig und sagt dir, ob ein Heizkörper zu groß oder
  zu klein ist.
- **Wärmepumpenfreundlich.** Ein eigener Wärmepumpenmodus hält die Ventile offen und bewegt sie
  sanft, statt sie zuzuknallen.
- **Erklärt sich immer.** Jedes Drosseln, Abschalten oder Überschreiben kommt mit einem
  verständlichen Grund, den du in Home Assistant siehst.
- **Zeigt, ob sie noch lernt.** Kein Rätselraten mehr, ob das Thermostat schon eingeschwungen ist.

## Unterstützte Geräte (geplant)

| Gerät | Anbindung | Hinweise |
|---|---|---|
| Sonoff TRVZB | Zigbee2MQTT | Hauptziel, direkte Ventilsteuerung |
| Bosch Heizkörperthermostat II | Zigbee2MQTT | Direkte Ventilsteuerung, keine Mindestöffnung im Gerät |
| Beliebige `climate`-Entität | Home Assistant | Grundunterstützung über den Sollwert |

## Dokumentation

Die Nutzer-Doku liegt in [`docs/de/`](docs/de/). Die Produktspezifikation (Englisch) liegt in
[`spec/`](spec/).

## Lizenz

[MIT](LICENSE). Projekte, die dieses inspiriert haben, stehen in [CREDITS.md](CREDITS.md).
