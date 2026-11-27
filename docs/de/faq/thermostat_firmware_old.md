# Firmware des Thermostats zu alt

[English](../../en/faq/thermostat_firmware_old.md) | **Deutsch**

## Was du siehst

Eine Reparaturmeldung **…: bitte Firmware aktualisieren** mit der installierten und der
benötigten Version.

## Was das bedeutet

Das Geräteprofil des Thermostats nennt die älteste Firmware, mit der alles funktioniert, was
Thermogeist nutzt. Dein Thermostat meldet eine ältere. Thermogeist regelt es weiter, aber
eventuell fehlen Funktionen. Beispiel Sonoff TRVZB: Vor 1.3.0 fehlt *Temperature accuracy*, und
es heizt erst 1 K unter seinem Sollwert los, der Raum bleibt also etwas zu kühl; vor 1.1.4 kann
es gar keine Ventilstellung übernehmen.

Thermogeist liest die Version, die Home Assistant für das Gerät anzeigt (*Einstellungen →
Geräte*).

## Was du tun kannst

Aktualisiere die Firmware über deine Zigbee-Bridge (Zigbee2MQTT: Reiter *OTA*). Der Hinweis
verschwindet von selbst, sobald das Thermostat die neuere Version meldet.
