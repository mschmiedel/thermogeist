# Fenster offen

[English](../../en/faq/window_open.md) | **Deutsch**

## Was du siehst

Aktueller Grund: **Fenster offen** (Attribute `open_minutes` und `frost_guard`, solange der
Frostschutz heizt). Der Sensor **Fenster** des Raums zeigt die Kontakte und ob das Heizen
pausiert.

## Was es bedeutet

Ein Fenster- oder Türkontakt des Raums ist seit mindestens *Fenster: schließen nach* offen
(Standard 30 Sekunden). Der Raum hält nur Frostschutz (7 °C) und schließt, wenn er geregelt wird,
das Ventil sofort; Thermostate über Sollwert bekommen 5 °C.

**Frostschutz:** Fällt der Raum trotz offenem Fenster unter 7 °C, heizt Thermogeist wieder auf
7 °C (Attribut `frost_guard: on`, Logbuch-Eintrag). Über 8 °C geht das Ventil wieder zu.

## Was du prüfen kannst

1. Ist wirklich ein Fenster oder eine Tür offen?
2. Meldet der Kontakt richtig (Batterie, Lage des Magneten)?

## Was du tun kannst

- Fenster schließen. Nach *Fenster: wieder heizen nach* (Standard 10 Sekunden) kehrt der Raum zu
  seinem Sollwert zurück, das Ventil dorthin, wo es vorher stand. Die Wartezeit überbrückt das
  Umstellen von „ganz offen“ auf „gekippt“.
- Die Zeiten änderst du am Haus (Bereich **Konfiguration** des Haus-Geräts) oder pro Raum
  (Bereich **Konfiguration** des Raum-Geräts). *Fenster: Zeiten auf Haus zurücksetzen* am Raum
  lässt ihn wieder dem Haus folgen.
