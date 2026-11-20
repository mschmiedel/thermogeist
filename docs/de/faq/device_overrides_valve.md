# Thermostat regelt selbst

[English](../../en/faq/device_overrides_valve.md) | **Deutsch**

## Was du siehst

Ein Reparaturhinweis **… regelt immer wieder selbst**, und der Schalter Regeln des Raums ist aus.

## Was es bedeutet

Thermogeist hat die Ventilstellung mehrmals geschrieben, aber das Thermostat hat sie jedes Mal zurückgestellt – seine eigene Regelung ist noch aktiv. Damit es kein endloses Hin und Her gibt, hat Thermogeist das Regeln für den Raum ausgeschaltet.

## Was du prüfen kannst

1. Bosch Heizkörperthermostat II: Steht `operating_mode` noch auf *manual*? Thermogeist setzt das beim Start des Regelns; ein Zeitplan oder die Bosch-App können es zurückstellen.
2. Ist eine eingebaute Regelung (z. B. Sonoff *smart temperature control*) wieder eingeschaltet?
3. Schreiben Automationen oder andere Integrationen auf das Thermostat?

## Was du tun kannst

- Ursache beheben, dann **Regeln** für den Raum wieder einschalten.
- Passiert es immer wieder, lässt sich das Thermostat nicht direkt regeln – sag uns dein Modell, damit sein Profil verbessert werden kann.
