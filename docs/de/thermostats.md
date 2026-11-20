# Thermostate

[English](../en/thermostats.md) | **Deutsch**

> **Erst beobachten, dann regeln.** Neue Räume starten im Beobachtungsmodus: Thermogeist zeigt
> nur, was es tun würde. Passt dir der Plan, schalte für den Raum **Regeln** ein.

## Thermostat hinzufügen

Öffne den Thermogeist-Eintrag deines Hauses und wähle **Thermostat hinzufügen**. Dafür brauchst
du mindestens einen Raum.

### Schritt 1: Raum und Gerät

| Feld | Was du einträgst |
|---|---|
| Raum | Der Raum, den dieses Thermostat beheizt. Ein Raum kann mehrere Thermostate haben. |
| Thermostat | Das Thermostat-Gerät in Home Assistant (es braucht eine Klima-Entität). |
| Heizkörper-Nennleistung | Optional. Die Leistung des Heizkörpers in W bei 75/65/20 °C laut Datenblatt oder Typenschild. |

### Schritt 2: Was macht was?

Bekannte Modelle erkennt Thermogeist und trägt vor, welche Entität was macht. Prüfe die Liste
und ändere, was nicht passt; leere Felder werden einfach nicht genutzt. Du kannst auch Entitäten
anderer Geräte wählen – manche Integrationen (z. B. Bosch Smart Home) legen Klima und
Ventilposition auf getrennte Geräte.

Um ein Thermostat später zu ändern, öffne den Thermogeist-Eintrag, such das Thermostat unter
dem Haus und klick auf sein Zahnrad (⚙).

| Rolle | Bedeutung |
|---|---|
| Klima-Entität | Pflicht. Die Klima-Entität des Thermostats. |
| Ventilstellung (lesen) | Zeigt, wie weit das Ventil offen ist – nötig für den Vergleich. |
| Ventilstellung (setzen) | Damit kann Thermogeist das Ventil direkt stellen. Ohne sie wird über den Sollwert geregelt. |
| Mindestöffnung im Gerät | Eine im Thermostat gespeicherte Rückfallebene; sie wirkt auch, wenn Home Assistant ausfällt. |
| Eingang externe Temperatur | Damit nutzt das Thermostat deinen Raumsensor statt seines eigenen. |

Bekannte Modelle bisher:

| Modell | Art | Hinweise |
|---|---|---|
| Sonoff TRVZB | Über Ventilstellung | Firmware 1.1.4 oder neuer. *Smart temperature control* ausschalten. |
| Sonoff TRV-ZBT (Gen2) | Über Ventilstellung | *Smart temperature control* ausschalten. |
| Bosch Heizkörperthermostat II (BTH-RA) | Über Ventilstellung | Keine Mindestöffnung im Gerät. Hält eine geschriebene Ventilstellung nur 15 Minuten; Thermogeist bestätigt sie alle 10 Minuten. |

Alle anderen Thermostate funktionieren **über den Sollwert**: Thermogeist sagt ihnen, welche
Temperatur sie anpeilen sollen, und das Thermostat bewegt sein Ventil selbst.

### Wie regeln

Im zweiten Schritt wählst du **Wie regeln**:

| Auswahl | Was passiert |
|---|---|
| Automatisch (Standard) | Über die Ventilstellung, wenn *Ventilstellung (setzen)* ausgefüllt ist, sonst über den Sollwert. |
| Über Ventilstellung | Thermogeist stellt das Ventil selbst: ruhig, mit Mindestöffnung und Vorsteuerung. Braucht *Ventilstellung (setzen)*. |
| Über Sollwert | Das Thermostat regelt mit seinem eigenen Regler; Thermogeist schickt nur das richtige Ziel. Geht mit jedem Thermostat, auch mit ventilgesteuerten, wenn du das lieber willst. |

**Über Sollwert, mit Eingang für externe Temperatur** (z. B. Bosch): Thermogeist schickt die
Raumtemperatur ans Thermostat und setzt das Raumziel als Sollwert. Das Thermostat regelt dann
auf die echte Raumtemperatur.

**Über Sollwert, ohne externen Eingang:** Das Thermostat misst direkt am warmen Heizkörper und
würde zu früh aufhören zu heizen. Thermogeist vergleicht seinen Messwert mit dem Raumsensor
(Mittel über 30 Minuten) und rechnet den Unterschied drauf: Raumziel 20 °C, Thermostat 2,5 K
wärmer als der Raum → Sollwert 22,5 °C. Die Anzeige am Thermostat zeigt deshalb den korrigierten
Wert. Sollwerte bleiben zwischen 5 und 30 °C, in 0,5-K-Schritten.

Grenzen von *über Sollwert*: keine Mindestöffnung und keine ruhige Ventilbewegung – wie weit das
Ventil öffnet, entscheidet der Regler im Thermostat.

## Regeln

Jeder Raum hat einen Schalter **Regeln**. Aus (Standard): nur beobachten. An: Thermogeist
schreibt auf die Thermostate des Raums – Ventilstellung oder Sollwert, je nach *Wie regeln*.

Was beim Einschalten passiert:

1. Nach einem Neustart von Home Assistant wird 90 Sekunden lang nichts geschrieben
   (*Wartet nach Neustart*).
2. Geräteeinstellungen, die fürs Regeln nötig sind, werden gesetzt – z. B. Bosch
   `operating_mode` → *manual*, beim Sonoff *smart temperature control* aus. Die vorherigen Werte
   merkt sich Thermogeist.
3. Jede Minute, über Ventilstellung: geplante Ventilstellung, Mindestöffnung (Sonoff),
   Raumtemperatur als externe Temperatur und das Raumziel als Sollwert am Thermostat, damit die
   Anzeige stimmt.
4. Über Sollwert: Raumtemperatur als externe Temperatur (wenn möglich) und der Sollwert –
   Änderungen ab 0,5 K, höchstens alle 10 Minuten. Fenster offen oder *Aus*: sofort 5 °C.

Was beim Ausschalten passiert: Alle gemerkten Geräteeinstellungen und die Ventilstellung werden
zurückgesetzt; Sollwert-Thermostate bekommen den einfachen Raum-Sollwert. Das Thermostat regelt
wieder selbst.

**Am Rad drehen** an einem geregelten Thermostat setzt den Raum-Sollwert (nach 20 Sekunden ohne
weiteres Drehen). Du siehst das im Logbuch. Bei korrigiertem Sollwert zählt der Unterschied:
Drehen von 22,5 auf 23,5 °C macht den Raum-Sollwert ein Grad höher.

**Verstellt ein Thermostat sein Ventil immer wieder selbst**, schreibt Thermogeist bis zu dreimal
pro Stunde neu, schaltet den Raum dann zurück auf Beobachten und zeigt einen Reparaturhinweis
([Häufige Fragen](faq/device_overrides_valve.md)).

Bevor du Regeln einschaltest: Stell eigene Automationen, Dashboards und Sprachassistenten vom
Thermostat auf die Klima-Entität des Raums um – sonst arbeiten zwei Regler gegeneinander.

### Wenn der Raum zu warm ist

Zwei Einstellungen am Haus bestimmen, was passiert, wenn ein Raum wärmer als sein Ziel wird: das
**Totband** (Wärmepumpe: 0,5 K) und die **Mindestöffnung Ventil** (Wärmepumpe: 40 %, vielleicht
hast du sie geändert). Beispiel: Ziel 19,5 °C, Totband 0,5 K, Mindestöffnung 30 %.

| Raum | Was Thermogeist tut | Mögliche Grenzen |
|---|---|---|
| unter 19,5 °C | Regelt normal: Vorsteuerung plus Reaktion auf die Abweichung. Das Ventil darf öffnen, langsam. | – |
| 19,5–20,0 °C (im Totband) | Etwas zu warm, aber noch im Rahmen. Die schnelle Reaktion ignoriert das; das Ventil wird nicht weiter geöffnet und darf schließen, aber nicht unter 30 %. | `hold_when_warm`, `min_opening` |
| 20,0–20,5 °C | Wie eben, aber jetzt zieht auch die schnelle Reaktion nach unten. Trotzdem nicht unter 30 %. | `hold_when_warm`, `min_opening` |
| über 20,5 °C (Totband + 0,5 K) | **Behaglichkeit geht vor:** Die Mindestöffnung gilt nicht mehr. Das Ventil darf unter 30 % schließen, langsam, Richtung dessen, was die Rechnung sagt. | `min_opening_relaxed` |
| zurück unter 20,0 °C | Erst jetzt gilt die Mindestöffnung wieder. Dazwischen bleibt der vorherige Zustand, damit sie nicht bei jedem Zehntelgrad an- und ausgeht. | `min_opening` |

**Warum:** Eine Wärmepumpe arbeitet am effizientesten, wenn durch jeden Heizkörper Wasser fließt.
Deshalb nimmt Thermogeist lieber ein halbes Grad zu viel in Kauf, als ein Ventil zu schließen.
Erst wenn es spürbar zu warm wird, hat die Behaglichkeit Vorrang. Zeigt ein Raum oft
`min_opening_relaxed`, ist sein Heizkörper bei der Mindestöffnung zu groß für ihn.

Beim Kessel ist das Totband 0,2 K und die Mindestöffnung 0 %; diese Stufe greift dort praktisch
nie.

## Vorlauftemperatur (optional)

Beim Haus (**Konfigurieren**) kannst du einen **Vorlauftemperatursensor** wählen – die
Temperatur des Wassers, das zu den Heizkörpern fließt, z. B. von deiner Wärmepumpe. Zusammen
mit der Heizkörperleistung und der Heizlast des Hauses berechnet Thermogeist dann eine gute
Start-Ventilstellung, statt sie langsam zu suchen.

Optional auch einen **Rücklauftemperatursensor** – das zurückkommende Wasser, an derselben Stelle
gemessen (z. B. Heizkreis-Rücklauf). Ohne ihn nimmt Thermogeist an, dass die Heizkörper im
Mittel 2,5 K kühler sind als der Vorlauf (5 K Spreizung). Mit ihm wird die gemessene Spreizung
genutzt (Mittel über 30 Minuten, begrenzt auf 1–10 K). Bei großer Spreizung sind die Heizkörper
kühler, und die Ventile öffnen etwas weiter. Der Haus-Rücklauf mischt alle Heizkörper, er zeigt
also den Durchschnitt, nicht einen einzelnen Heizkörper. Anlegefühler am Rücklauf genauso
kalibrieren wie den Vorlauf-Fühler.

## Den Vorlauf-Sensor wählen

Der Vorlauf ist die empfindlichste Eingabe der Vorsteuerung. Bei Wärmepumpen-Temperaturen liegen
nur wenige Kelvin zwischen Wasser und Raum, deshalb ändert **1 K Messfehler die berechnete
Heizkörperleistung um 20–30 %**. Wähle und prüfe den Fühler sorgfältig.

**Wo messen**

| Fühler | Geeignet? | Warum |
|---|---|---|
| Heizkreis-Vorlauf nach dem Pufferspeicher (dort, wo die Heizkörper ihr Wasser bekommen) | **ja – empfohlen** | Zeigt, was wirklich an den Heizkörpern ankommt. Beim Warmwasserbereiten sinkt er langsam; Thermogeist öffnet die Ventile dann etwas – der richtige Ausgleich. |
| Vorlauffühler der Wärmepumpe selbst (Ausgang der Wärmepumpe) | **nur mit Vorsicht** | Beim Warmwasserbereiten zeigt er 45–50 °C. Thermogeist würde die Heizkörper für heiß halten und die Ventile schließen, obwohl sie kühler werden. Mit Pufferspeicher kommt der WP-Vorlauf außerdem nicht direkt an den Heizkörpern an. |
| Kessel-Vorlauf ohne Puffer | ja | Dasselbe Wasser wie an den Heizkörpern. |

Hast du keinen Heizkreis-Fühler und musst den der Wärmepumpe nehmen: Beobachte die geplante
Ventilstellung beim Warmwasserbereiten. Eine spätere Version kann den Wert bei Warmwasser und
Abtauen halten, wenn du ihr die Betriebsart der Wärmepumpe gibst.

**Anlegefühler: kalibrieren**

Fühler, die außen am Rohr anliegen – auch unter der Dämmung –, messen oft **2–4 K zu wenig**,
weil sie die kühlere Umgebung mitmessen. So findest du den Versatz ohne Ausbau:

1. Warte einen Zeitraum ab, in dem die Wärmepumpe steht (kein Heizen, kein Warmwasser, kein
   Abtauen), die Heizkreispumpe aber weiterläuft – nachts oder an einem milden Nachmittag,
   30–60 Minuten.
2. Dann hat das Wasser im Puffer, in der Wärmepumpe und im Heizkreis-Vorlauf fast dieselbe
   Temperatur. Vergleiche deinen Fühler mit dem der Wärmepumpe oder des Puffers.
3. Trag die Differenz in Home Assistant als Versatz (Offset) für deinen Fühler ein.

Beispiel aus einer echten Anlage: WP-Vorlauf 28,9 °C, WP-Rücklauf 28,2 °C, Puffer 28,5 °C,
Anlegefühler Heizkreis-Vorlauf 25,6 °C → Versatz etwa +3 K.

**Gar kein Fühler?** Thermogeist funktioniert trotzdem: Ohne Vorsteuerung findet es die richtige
Ventilstellung über die langsame Korrektur, das dauert etwa einen Tag statt Stunden. Die
geplante Ventilstellung zeigt dann `feed_forward_missing: flow_temperature`.

## Was du siehst

Pro Raum:

| Entität | Bedeutung |
|---|---|
| Geplante Ventilstellung | Was Thermogeist gerade einstellen würde. Die Attribute zeigen die Anteile: *feed_forward* (aus dem Wärmebedarf), *proportional* (Reaktion auf den Temperaturunterschied), *integral* (langsame Korrektur) und *limits*, die gegriffen haben. Ist *feed_forward* leer, steht in *feed_forward_missing*, was fehlt – meist der Vorlauf-Sensor am Haus oder die Heizkörperleistung. |
| Ventilstellung *Thermostat* | Die tatsächliche Ventilstellung, wenn das Thermostat sie meldet. Leg sie in einem Verlaufsdiagramm neben die geplante. |
| Art *Thermostat* | Über Ventilstellung oder über Sollwert, mit *strategy* (deine Auswahl), Profil und Rollen als Attribute. |

### Grenzen, die du sehen kannst

| Grenze | Bedeutung |
|---|---|
| `min_opening` | Das Ventil bleibt auf der Mindestöffnung deiner Heizungsart (Wärmepumpe: 40 %). |
| `min_opening_relaxed` | Der Raum liegt mehr als Totband + 0,5 K über seinem Ziel, das Ventil darf unter die Mindestöffnung ([Wenn der Raum zu warm ist](#wenn-der-raum-zu-warm-ist)). Typisch für Heizkörper, die für den Raum zu groß sind. |
| `hold_when_warm` | Der Raum ist über seinem Ziel, deshalb wird das Ventil nicht weiter geöffnet, egal was die Rechnung sagt. |
| `rate_limit` | Das Ventil bewegt sich absichtlich langsam (Wärmepumpe: max. 10 % pro 30 Minuten). |
| `saturated` | Das Ventil ist ganz offen oder an seiner untersten erlaubten Stellung. |
| `stopped` | Zentralmodus *Aus*: 0 %. |
| `safety` | Der Raumsensor schweigt: Das Ventil geht auf die Mindestöffnung, mindestens 20 %. |

Der Sensor *Art* jedes Thermostats zeigt, was Thermogeist damit getan hat: `last_write` und `last_write_value`, `last_confirmation`, `rewrites_last_hour` und `valve_refresh_minutes`. Über Sollwert: `last_write`, `last_write_value` (der geschickte Sollwert) und `setpoint_offset` (die Korrektur auf das Raumziel).

Die geplante Ventilstellung zeigt außerdem `flow_temperature_used`, `return_temperature_used` und `spread_used`.

**Ventilstellung bestätigen alle … Minuten** (in den Einstellungen des Thermostats): Manche Thermostate verwerfen eine von außen gesetzte Ventilstellung nach einer Weile – das Bosch Heizkörperthermostat II nach 15 Minuten. Thermogeist schickt den unveränderten Wert dann in diesem Abstand erneut (eine Funknachricht, keine Motorbewegung). Vorbelegt aus dem Geräteprofil (Bosch: 10), leer = aus.
