# Temperatursensor meldet sich nicht

[English](../../en/faq/safety_sensor_stale.md) | **Deutsch**

## Was du siehst

Aktueller Grund: **Temperatursensor meldet sich nicht** (Attribute `cause`, `unavailable_minutes` oder `silent_minutes`, `limit_minutes`)

## Was es bedeutet

Thermogeist traut der Raumtemperatur nicht mehr, aus einem von zwei Gründen:

- `cause: unavailable` – Home Assistant zeigt den Sensor seit 15 Minuten als *nicht verfügbar*. So sieht eine leere Batterie oder eine verlorene Funkverbindung aus.
- `cause: silent` – der Sensor ist verfügbar, hat aber seit 6 Stunden keinen neuen Wert geschickt. Viele Sensoren melden nur, wenn sich die Temperatur ändert; eine ruhige Stunde oder zwei in einer windstillen Nacht sind normal, sechs Stunden nicht.

Das Ventil geht dann auf seine Mindestöffnung – nie ohne Grund ganz zu.

## Was du prüfen kannst

1. Batterie des Sensors leer oder schwach?
2. Ist der Sensor noch verbunden (Zigbee2MQTT / ZHA zeigen ihn als verfügbar)?
3. Wurde für den Raum der richtige Sensor gewählt? Öffne den Thermogeist-Eintrag und klick auf das Zahnrad (⚙) neben dem Raum → **Raum bearbeiten**.
4. Bei `cause: silent`: Zeigt der Sensor seit Stunden denselben Wert, obwohl sich der Raum verändert hat? Dann hängt er – neu starten oder neu koppeln.

## Was du tun kannst

- Behebe die Ursache oben. Sobald der Sensor wieder meldet, kehrt der Raum von selbst in den Normalzustand zurück.
