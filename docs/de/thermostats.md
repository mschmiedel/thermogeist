# Thermostate

[English](../en/thermostats.md) | **Deutsch**

> **Beobachtungsmodus.** Thermogeist berechnet, was es mit jedem Ventil tun würde, und zeigt
> es an – es schreibt noch nichts auf deine Thermostate. Nutze diese Phase, um den Plan mit dem
> zu vergleichen, was deine Thermostate heute tun.

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
und ändere, was nicht passt; leere Felder werden einfach nicht genutzt.

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
| Bosch Heizkörperthermostat II (BTH-RA) | Über Ventilstellung | Keine Mindestöffnung im Gerät. Ob es eine geschriebene Ventilstellung hält, wird noch getestet. |

Alle anderen Thermostate funktionieren **über den Sollwert**: Thermogeist regelt sie über die
Zieltemperatur (ab der nächsten Version).

## Vorlauftemperatur (optional)

Beim Haus (**Konfigurieren**) kannst du einen **Vorlauftemperatursensor** wählen – die
Temperatur des Wassers, das zu den Heizkörpern fließt, z. B. von deiner Wärmepumpe. Zusammen
mit der Heizkörperleistung und der Heizlast des Hauses berechnet Thermogeist dann eine gute
Start-Ventilstellung, statt sie langsam zu suchen.

## Was du siehst

Pro Raum:

| Entität | Bedeutung |
|---|---|
| Geplante Ventilstellung | Was Thermogeist gerade einstellen würde. Die Attribute zeigen die Anteile: *feed_forward* (aus dem Wärmebedarf), *proportional* (Reaktion auf den Temperaturunterschied), *integral* (langsame Korrektur) und *limits*, die gegriffen haben. Ist *feed_forward* leer, steht in *feed_forward_missing*, was fehlt – meist der Vorlauf-Sensor am Haus oder die Heizkörperleistung. |
| Ventilstellung *Thermostat* | Die tatsächliche Ventilstellung, wenn das Thermostat sie meldet. Leg sie in einem Verlaufsdiagramm neben die geplante. |
| Art *Thermostat* | Über Ventilstellung oder über Sollwert, mit Profil und Rollen als Attribute. |

### Grenzen, die du sehen kannst

| Grenze | Bedeutung |
|---|---|
| `min_opening` | Das Ventil bleibt auf der Mindestöffnung deiner Heizungsart (Wärmepumpe: 40 %). |
| `min_opening_relaxed` | Der Raum ist deutlich zu warm, das Ventil darf unter die Mindestöffnung. Typisch für Heizkörper, die für den Raum zu groß sind. |
| `rate_limit` | Das Ventil bewegt sich absichtlich langsam (Wärmepumpe: max. 10 % pro 30 Minuten). |
| `saturated` | Das Ventil ist ganz offen oder an seiner untersten erlaubten Stellung. |
| `stopped` | Zentralmodus *Aus*: 0 %. |
| `safety` | Der Raumsensor schweigt: Das Ventil geht auf die Mindestöffnung, mindestens 20 %. |
