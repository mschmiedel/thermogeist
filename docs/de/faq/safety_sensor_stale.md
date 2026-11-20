# Temperatursensor meldet sich nicht

[English](../../en/faq/safety_sensor_stale.md) | **Deutsch**

## Was du siehst

Aktueller Grund: **Temperatursensor meldet sich nicht** (Attribute `silent_minutes`, `limit_minutes`)

## Was es bedeutet

Der Temperatursensor des Raums hat seit 60 Minuten keinen gültigen Wert geschickt. Thermogeist traut alten Werten nicht und markiert den Raum. Ab der Version, die Thermostate regelt, geht das Ventil dann auf seine Mindestöffnung – nie ohne Grund ganz zu.

## Was du prüfen kannst

1. Batterie des Sensors leer oder schwach?
2. Ist der Sensor noch verbunden (Zigbee2MQTT / ZHA zeigen ihn als verfügbar)?
3. Wurde für den Raum der richtige Sensor gewählt? Öffne den Thermogeist-Eintrag und klick auf das Zahnrad (⚙) neben dem Raum.
4. Manche Sensoren melden nur bei Änderung. Schweigt deiner absichtlich länger als eine Stunde, sag uns Bescheid – die Grenze wird einstellbar.

## Was du tun kannst

- Behebe die Ursache oben. Sobald der Sensor wieder meldet, kehrt der Raum von selbst in den Normalzustand zurück.
