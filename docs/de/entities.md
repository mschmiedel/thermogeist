# Alle Entitäten

[English](../en/entities.md) | **Deutsch**

Alle Entitäten, die Thermogeist anlegt, nach Gerät: das **Haus**, jeder **Raum** und die
**Thermostate** eines Raums (ihre Entitäten hängen am Raum-Gerät). Die Spalte *Wann vorhanden*
sagt, ob du die Entität überhaupt siehst; *Unbekannt, wenn* sagt, wann sie zwar da ist, aber
keinen Wert zeigt. Diagnose- und Konfigurations-Entitäten findest du auf der Geräteseite unter
*Diagnose* und *Konfiguration*.

## Haus

| Entität | Bedeutung | Wann vorhanden | Unbekannt, wenn |
|---|---|---|---|
| Zentralmodus | *Automatisch*, *Aus* oder *Frostschutz* für das ganze Haus. Bleibt über Neustarts erhalten. | immer | – |
| Heizungsart | Wärmepumpe, Kessel oder Elektro-Direktheizung – bestimmt, wie ruhig Thermogeist regelt. Diagnose. | immer | – |
| Heizlast | Die eingetragene Heizlast in kW: was das Haus am kältesten Auslegungstag braucht. Ein fester Planungswert, nicht der Bedarf von jetzt (siehe *Wärmebedarf der Räume* unten). Diagnose. | immer | keine Heizlast eingetragen |
| Normaußentemperatur | Die Außentemperatur, für die die Heizlast berechnet wurde. Diagnose. | immer | nicht eingetragen |
| Anteil außerhalb von Thermogeist | Teil der Heizlast in Räumen, die Thermogeist nicht regelt, wie eingetragen. Diagnose. | immer | – |
| Heizlast ohne Raum | Teil der Heizlast, den noch kein Raum (und kein Anteil außerhalb) abdeckt. Diagnose. | immer | – |
| Abdeckung durch Räume | 100 % minus der Teil ohne Raum. Attribute: `missing_pct`, `floor_area_not_in_rooms_m2`, `rooms`. | immer | – |
| Wärmebedarf der Räume | Watt, die deine Räume gerade brauchen, um ihr Ziel zu halten – die Summe ihres *Wärmebedarfs*. | immer | keine Heizlast am Haus |
| Geschätzte Heizleistung der Räume | Watt, die alle Heizkörper gerade abgeben – die Summe der *Geschätzten Heizleistung* der Räume. Nur Heizkörper: Vergleiche sie über die Zeit mit dem, was deine Wärmepumpe oder dein Kessel liefert (Wärmemengenzähler). | immer | kein Raum hat eine Schätzung |
| Wärme aus Geräten der Räume | Watt, die deine Geräte in die Räume abgeben – die Summe der *Wärme aus Geräten* der Räume. Getrennt gehalten, weil diese Wärme aus der Steckdose kommt, nicht aus der Heizung. | immer | kein Raum hat eine Schätzung |

Die drei Summen umfassen dieselben Räume, du kannst sie also direkt vergleichen. Ein Raum, dessen Heizkörper sich nicht schätzen lassen (keine Ventilstellung oder kein Thermostat), fehlt in allen dreien und steht im Attribut `rooms_without_estimate`; `rooms` sagt, wie viele gezählt sind. Es zählen nur Räume in Thermogeist (siehe *Abdeckung durch Räume*). Eine gemeinsame Summe aus Heizkörpern und Geräten gibt es nicht; ein Template kann beides addieren, wenn du sie brauchst.

| Entität | Bedeutung | Wann vorhanden | Unbekannt, wenn |
|---|---|---|---|
| Vorlauftemperatur | Der gemittelte Vorlauf, mit dem die Regelung rechnet (`source`: dein Sensor, oder `heating_curve`, wenn er aus der Heizkurve bei der aktuellen Außentemperatur kommt). | Vorlauf-Sensor gewählt oder Heizkurve eingegeben | der Sensor liefert keinen plausiblen Wert |
| Rücklauftemperatur | Der gemittelte Rücklauf. | Rücklauf-Sensor gewählt | der Sensor liefert keinen Wert |
| Spreizung | Vorlauf minus Rücklauf, begrenzt auf 1–10 K; ersetzt die angenommenen 5 K. | Vorlauf- und Rücklauf-Sensor gewählt | einer davon liefert keinen Wert |
| Vorlauf am Auslegungstag | Der Vorlauf, den deine Heizung am kältesten Auslegungstag erreicht, aus der Heizkurve, die Thermogeist lernt ([FAQ](faq/radiator_sizing.md)). Attribute: `slope_k_per_k`, `hours`, `outdoor_min_c`, `outdoor_max_c`, `confidence`. Mit eingegebener Heizkurve kommt er aus dieser Kurve (`source`: `heating_curve` und die beiden Punkte). Diagnose. | Vorlauf-Sensor gewählt oder Heizkurve eingegeben | weniger als 48 Heizstunden über mindestens 5 K Außentemperatur gelernt, oder keine Normaußentemperatur |
| Mindestöffnung Ventil | Wie weit ein Ventil beim Regeln mindestens offen bleibt, in %. Wärmepumpe 40 %: Das Wasser soll immer durch die Heizkörper fließen können, sonst schaltet die Wärmepumpe ständig ein und aus. Nur wenn ein Raum deutlich zu warm ist (mehr als Totband + 0,5 K über dem Ziel), darf das Ventil darunter ([Wenn der Raum zu warm ist](thermostats.md#wenn-der-raum-zu-warm-ist)). Kessel und Elektro: 0 %. Konfiguration. | immer | – |
| Totband | Wie viel wärmer als sein Ziel ein Raum werden darf, bevor die Regelung deswegen das Ventil zudreht, in K. Beispiel Wärmepumpe 0,5 K, Ziel 21 °C: Bis 21,5 °C bleibt das Ventil ruhig – etwas Sonne oder Kochen lässt es in Ruhe. Bleibt der Raum lange zu warm, nimmt die langsame Korrektur trotzdem nach und nach zurück. Unter dem Ziel gibt es kein Totband: Ist es zu kalt, reagiert die Regelung sofort. Konfiguration. | immer | – |
| Max. Ventiländerung pro 30 min | Wie weit sich ein Ventil in 30 Minuten höchstens bewegt, in Prozentpunkten. Wärmepumpe 10: von 40 % auf 70 % dauert mindestens anderthalb Stunden. So ändert sich der Wasserdurchfluss nur langsam, und die Wärmepumpe läuft gleichmäßig. Ausnahmen: Nach einem geschlossenen Fenster oder einer Sicherheitsabschaltung geht es sofort zurück auf den Plan, und ein zu warmer Raum wird nie weiter geöffnet. Konfiguration. | immer | – |
| Max. Absenkung | Für Zeitpläne und *Abwesend*: um wie viel Kelvin ein Raum dann höchstens kühler werden darf. Wärmepumpe 2 K, weil tiefes Absenken beim Wiederaufheizen mehr kostet, als es spart. **Wirkt noch nicht** – Zeitpläne sind geplant. Konfiguration. | immer | – |
| Fenster: schließen nach, Fenster: wieder heizen nach | Hauswerte für alle Räume mit Fensterkontakten, in Sekunden. Konfiguration. | immer | – |
| Regelwerte auf Profil zurücksetzen | Taste: alle Regelwerte zurück auf die Vorgaben der Heizungsart. Konfiguration. | immer | – |

Die vier Regelwerte gelten für alle Räume des Hauses und starten mit den Vorgaben deiner
Heizungsart ([Tabelle](getting-started.md#was-du-danach-siehst)). Das Attribut `source` zeigt
`profile` (Vorgabe) oder `user` (von dir geändert). Meist musst du nichts ändern.

## Raum

| Entität | Bedeutung | Wann vorhanden | Unbekannt, wenn |
|---|---|---|---|
| Klima (heißt wie der Raum) | Raumtemperatur und der Sollwert, den du einstellst (5–30 °C). Für Dashboards und Sprachassistenten. | immer | – (Temperatur unbekannt, solange der Raumsensor keinen Wert hat) |
| Regeln | Schalter: aus = Thermogeist beobachtet nur, an = es schreibt auf die Thermostate. Attribut `can_control`. | immer | nicht verfügbar, solange der Raum kein Thermostat hat |
| Aktueller Grund | Warum der Raum sein aktuelles Ziel hat, mit einer [FAQ-Seite](faq/README.md) je Grund. Attribute: `severity`, `since`, `faq` und die Zahlen zum Grund. | immer | – |
| Zieltemperatur | Was der Raum gerade anstrebt, z. B. 7 °C bei offenem Fenster. | immer | der Raum soll nicht heizen (Zentralmodus *Aus*) |
| Wärmebedarf | Watt, die der Raum gerade braucht, um sein Ziel zu halten: Wärmeverlustkoeffizient × (Ziel − außen). | immer | keine Heizlast oder Normaußentemperatur am Haus, oder keine Außentemperatur |
| Geschätzte Heizleistung | Watt, die die Heizkörper gerade abgeben – zum Vergleich neben dem *Wärmebedarf* ([Details unten](#geschätzte-heizleistung)). Attribute: `max_output_w`, `radiators`, `valve_characteristic`, `missing`. | Raum hat Thermostate | siehe `missing`: ein Thermostat ohne Nennleistung oder Ventilstellung, kein Vorlauf oder keine Raumtemperatur |
| Anteil an der Heizlast | Der Anteil des Raums, geschätzt oder eingetragen. Attribute: `source` (`estimated` / `known`), `scaled_down`. Diagnose. | immer | – |
| Wärmeverlustkoeffizient | Watt pro Kelvin Unterschied nach draußen. Diagnose. | immer | keine Heizlast oder Normaußentemperatur am Haus |
| Wärme aus Geräten | Watt, die deine Geräte in den Raum abgeben, nach Faktoren, über 10 Minuten gemittelt ([Räume](rooms.md#geräte-die-den-raum-heizen)). Attribute: `sources`, `factor_entities`. | Wärmequellen gewählt | – |
| Geplante Ventilstellung | Was Thermogeist stellen würde (Beobachten) oder stellt (Regeln). Attribute: `mode` (`observe` / `control`), `feed_forward`, `feed_forward_missing`, `proportional`, `integral`, `limits` und die verwendeten Temperaturen ([Thermostate](thermostats.md#was-du-siehst)). | Raum hat Thermostate | direkt nach dem Start, vor dem ersten Plan |
| Heizkörpergröße | Schaffen die Heizkörper den Sollwert am Auslegungstag? Attribute mit den Zahlen ([FAQ](faq/radiator_sizing.md)). Diagnose. | Raum hat Thermostate | – (zeigt *Noch nicht bewertbar* mit `missing`) |
| Gelernter Bedarf | Wie viel der Wärme, die seine Angaben erwarten lassen, der Raum wirklich braucht, gelernt aus ruhigen Stunden ([FAQ](faq/learned_demand.md)). Plant das Ventil mit, sobald `settled`. Attribute: `state`, `quiet_hours`, `days`, `day_pct`, `night_pct`, `spread_pct`. | Raum hat Thermostate | noch `learning` (weniger als 24 ruhige Stunden an 3 Tagen) |
| Lernen: neu beginnen | Taste: Der Raum vergisst das Gelernte und beginnt neu. Konfiguration. | Raum hat Thermostate | – |
| Fenster | An, solange ein Kontakt des Raums offen ist. Attribute: `contacts`, `heating_paused`, `frost_guard`, `close_after_s`, `resume_after_s`. | Fensterkontakte gewählt | – |
| Fenster: schließen nach, Fenster: wieder heizen nach | Die eigenen Fensterzeiten des Raums; Hauswert, bis du sie änderst (Attribut `source`). Konfiguration. | Fensterkontakte gewählt | – |
| Fenster: Zeiten auf Haus zurücksetzen | Taste: der Raum folgt wieder den Fensterzeiten des Hauses. Konfiguration. | Fensterkontakte gewählt | – |

## Thermostat

Nach dem Thermostat benannt, am Raum-Gerät.

| Entität | Bedeutung | Wann vorhanden | Unbekannt, wenn |
|---|---|---|---|
| Art *Thermostat* | Über Ventilstellung oder über Sollwert. Attribute: `strategy`, `profile`, `radiator_output_w`, `roles` und was Thermogeist zuletzt geschrieben hat (`last_write`, `last_write_value`, `last_confirmation`, `rewrites_last_hour`; über Sollwert `setpoint_offset`). Diagnose. | immer | – |
| Ventilstellung *Thermostat* | Wo das Ventil wirklich steht – zum Vergleich mit der geplanten ([warum sie abweichen kann](thermostats.md#geplante-und-tatsächliche-ventilstellung)). `source: reported`, wenn das Thermostat sie meldet; `source: derived` bei Sonoff-Thermostaten: die gesetzte Stellung, solange das Thermostat heizt, die Mindestöffnung, solange es ruht (`hvac_action`). | die Rolle *Ventilstellung (lesen)* ist ausgefüllt, oder ein Sonoff mit Ventilstellung (setzen) und Mindestöffnung | das Thermostat meldet nichts, oder ein Sonoff meldet weder Heizen noch Ruhen |

## Geschätzte Heizleistung

Thermogeist schätzt für jedes Thermostat mit Nennleistung in zwei Schritten:

1. **Ganz offen** (`max_output_w`): die Nennleistung, umgerechnet auf die aktuellen
   Temperaturen mit der Norm-Formel für Heizkörper (EN 442): Nennleistung × ((Vorlauf −
   Spreizung/2 − Raum) / 49,8 K)^1,3. Ohne Rücklauf-Sensor wird eine Spreizung von 5 K
   angenommen. Stimmt die Nennleistung, ist diese Zahl recht belastbar.
2. **Bei der aktuellen Ventilstellung:** Unter 10 % fließt praktisch kein Wasser. Darüber steigt
   die Leistung schnell, weil ein Heizkörper schon mit halbem Durchfluss den größten Teil seiner
   Wärme abgibt. Thermogeist nimmt an: Leistung = ganz offen × √((Ventil − 10 %) / 90 %). Mit
   derselben Kurve, nur andersherum, plant es das Ventil. Dein Ventil kann sich anders verhalten,
   deshalb steht in `valve_characteristic` `assumed` (angenommen).

| Ventil | Anteil der vollen Leistung |
|---|---|
| 10 % oder weniger | 0 % |
| 20 % | 33 % |
| 40 % | 58 % |
| 55 % | 71 % |
| 75 % | 85 % |
| 100 % | 100 % |

Beispiel: Nennleistung 700 W, Vorlauf 40 °C, Raum 19,5 °C, kein Rücklauf-Sensor → ganz offen
etwa 186 W. Bei 39 % Ventil schätzt Thermogeist etwa 106 W.

**Welche Ventilstellung:** die, die das Thermostat meldet (`valve_source: reported`), bei Sonoff-Thermostaten die ermittelte (`derived`, siehe *Ventilstellung*). Meldet es
keine und stellt Thermogeist das Ventil selbst, die geplante (`planned`). Ein Thermostat über
Sollwert ohne gemeldetes Ventil hat keine Stellung, die Thermogeist nutzen könnte: Die Schätzung
des Raums ist dann unbekannt, `max_output_w` zeigt aber trotzdem, was die Heizkörper könnten.

**So liest du sie:** Bleibt die geschätzte Leistung bei ganz offenem Ventil deutlich unter dem
Wärmebedarf, ist der Heizkörper für den aktuellen Vorlauf zu klein – siehe *Heizkörpergröße*.
Liegt sie weit darüber und der Raum wird trotzdem nicht warm, ist die Nennleistung vielleicht zu
hoch angegeben oder der Heizkörper bekommt zu wenig Wasser. Geräte, die den Raum heizen (*Wärme
aus Geräten*), sind nicht enthalten: Der Heizkörper muss nur den Rest liefern.
