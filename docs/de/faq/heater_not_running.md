# Heizung läuft nicht

[English](../../en/faq/heater_not_running.md) | **Deutsch**

## Was du siehst

Der Binärsensor ***Heizung* läuft nicht** ist an, eine Reparaturmeldung **… läuft nicht**
erscheint, und das Logbuch sagt, dass die Heizung eingeschaltet ist, aber nicht läuft.

## Was es bedeutet

Der Schalter der Heizung ist an, aber ihr Stufen-Sensor meldet seit 3 Minuten am Stück `0`. Ein paar Sekunden bei `0` – etwa wenn du am Gerät die Stufe umschaltest – zählen nicht. Die
Wärme, die Thermogeist erwartet, kommt nicht im Raum an; solange das so ist, rechnet es keine
Wärme von dieser Heizung. Die Meldung verschwindet von selbst, sobald der Stufen-Sensor wieder
eine Stufe meldet.

## Was du prüfen kannst

- Ist die Heizung selbst eingeschaltet (eigener Schalter oder Thermostat) und die Sicherung drin?
- Läuft das Gebläse? Bei einer Sockelheizung mit Wasserthermostat wartet das Gebläse eventuell
  auf warmes Wasser.
- Passt das Template des Stufen-Sensors noch? Eine Steckdose, die ihre Leistung seltener meldet,
  oder Grenzen, die nicht mehr zur Leistung des Gebläses passen, lassen das Template `0` melden.

Nutze den Binärsensor in einer Automation, um benachrichtigt zu werden, z. B. auf dem Handy.
