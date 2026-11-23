# Thermostat nicht kalibriert

[English](../../en/faq/thermostat_not_calibrated.md) | **Deutsch**

## Was du siehst

Eine Reparaturmeldung **… ist nicht kalibriert**, und die Ventilstellung des Thermostats zeigt *unbekannt*.

## Was es bedeutet

Das Thermostat meldet selbst, dass es seine Kalibrierung verloren hat: Es weiß nicht mehr, wo sein Ventil offen und wo es zu ist. Das passiert z. B. nach einem Firmware-Update. Dann bewegt es sein Ventil nicht mehr – meist bleibt es ganz offen in der Montageposition –, nimmt aber weiter jeden Wert an, den Thermogeist schreibt, und meldet ihn zurück. Deshalb zeigt Thermogeist die Ventilstellung als unbekannt statt einer falschen Zahl.

Thermogeist meldet es erst, wenn es 10 Minuten anhält: Eine normale Kalibrierung nach dem Montieren durchläuft dieselben Werte in etwa einer Minute.

## Was du tun kannst

- **Sonoff TRVZB:** Drück kurz die Taste am Thermostat; es kalibriert sich neu. Ist die Kindersicherung an? Dann zuerst **Kindersicherung: 30 Min. aus** für den Raum drücken.
- **Bosch Heizkörperthermostat II:** Starte die Kalibrierung in Zigbee2MQTT oder am Gerät, wie in der Anleitung beschrieben.

Die Meldung verschwindet von selbst, sobald das Thermostat meldet, dass es wieder kalibriert ist.
