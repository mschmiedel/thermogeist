# Gelernter Bedarf

[English](../../en/faq/learned_demand.md) | **Deutsch**

## Was du siehst

Raum-Sensor **Gelernter Bedarf** in %, mit den Attributen `state` (`learning` / `settled`),
`quiet_hours`, `days`, `day_pct`, `night_pct` und `spread_pct`.

## Was es bedeutet

Aus deinen Angaben – Heizlast, Anteil des Raums, Heizkörperleistung – rechnet Thermogeist aus,
wie viel Wärme ein Raum braucht. Echte Räume weichen davon ab. Thermogeist beobachtet deshalb
**ruhige Stunden** im normalen Betrieb: Fenster zu (auch in der Stunde davor), der Raum stabil
am Ziel, die Ventilstellung bekannt. In so einer Stunde ist die Wärme, die der Raum aus
Heizkörpern und Geräten bekommen hat, genau das, was er verloren hat.

*Gelernter Bedarf* ist das Ergebnis: **Der Raum braucht etwa diesen Anteil dessen, was seine
Angaben erwarten lassen.** 100 % heißt, die Angaben passen. 50 % heißt, die halbe Wärme reicht.

- Du musst nichts tun: kein leerer oder abgeschlossener Raum, kein Testlauf.
- Es braucht mindestens 24 ruhige Stunden an 3 Tagen, meist 3–5 Nächte. Bis dahin steht der
  Zustand auf `learning`.
- Es zählt der Median der letzten 21 Tage. Ein Abend mit Besuch oder Backofen ändert also
  nichts.
- Unterscheiden sich Tag und Nacht deutlich (mehr als 25 %), bekommt jede Zeit ihren eigenen
  Wert (`day_pct`, `night_pct`): Ein Schlafzimmer mit Schlafenden braucht nachts weniger, ein
  sonniger Raum tagsüber.
- Sobald er gilt, plant Thermogeist das Ventil damit. Die Änderung kommt langsam am Ventil an,
  wie jede andere. Große Änderungen stehen im Logbuch.

## Warum ein Raum weit von 100 % weg ist

| Gelernter Bedarf | Typische Ursachen |
|---|---|
| deutlich unter 100 % | Heizkörper größer oder stärker als eingetragen (hohe Voreinstellung), Anteil an der Heizlast zu hoch angesetzt, Sonne, Menschen, Geräte ohne Leistungssensor, warmer Nachbarraum |
| deutlich über 100 % | Heizkörper schwächer als eingetragen (Voreinstellung zu niedrig, Luft, verdeckt), Anteil zu niedrig angesetzt, kalter Nachbarraum oder Treppenhaus |

Das ist kein Fehler. Wirkt ein Wert unplausibel, prüf die Angaben des Raums.

## Grenzen

Thermostate, die ihre Ventilstellung spät melden (Bosch Smart Home), machen die Beobachtungen
ungenau; `spread_pct` ist dann größer, und es dauert länger, bis der Wert steht.

## Was du tun kannst

- Nichts. Zum Neuanfang (z. B. nach einer Sanierung) am Raum **Lernen: neu beginnen**
  drücken. Ändern sich die Heizlast-Angaben des Raums oder seine Thermostate, lernt er von selbst
  neu.
