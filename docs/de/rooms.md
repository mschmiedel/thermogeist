# Räume

[English](../en/rooms.md) | **Deutsch**

> Räume regeln noch keine Thermostate. Sie zeigen, was jeder Raum braucht und warum – die
> Grundlage für die nächsten Versionen.

## Raum hinzufügen

Öffne den Thermogeist-Eintrag deines Hauses und wähle **Raum hinzufügen**.

### Schritt 1: Grundangaben

| Feld | Was du einträgst |
|---|---|
| Name | z. B. „Wohnzimmer“. |
| Bereich | Optional. Das Raumgerät wird diesem Home-Assistant-Bereich zugeordnet. |
| Raumtemperatursensor | Ein Sensor im Raum, möglichst nicht am Heizkörper und nicht in direkter Sonne. |
| Anteil an der Heizlast | *Aus Größe und Lage schätzen* (die meisten) oder *Ich kenne den Anteil* (wenn du eine raumweise Heizlastberechnung hast). |
| Fenster- und Türkontakte | Optional. Ist einer 30 Sekunden offen, hört der Raum auf zu heizen, bis alle 10 Sekunden zu sind; beide Zeiten lassen sich ändern ([Häufige Fragen](faq/window_open.md)). |
| Auslegungs-Innentemperatur | Planungswert aus der Heizlastberechnung – nicht die Temperatur, auf die du heizt. Meist 20 °C, Bäder 24 °C, beheizte Flure 15 °C. Ein Bad mit 24 °C bekommt einen größeren Anteil. |
| Geräte, die den Raum heizen | Optional. Leistungssensoren (W) von Geräten im Raum, siehe [unten](#geräte-die-den-raum-heizen). |

### Schritt 2a: Größe und Lage (Schätzung)

Grobe Werte reichen – Thermogeist lernt das echte Verhalten später.

| Feld | Was du einträgst |
|---|---|
| Grundfläche | In m². Galerien und Lufträume zählen ihre Grundfläche einmal. |
| Raumhöhe | Bei Dachschräge: die höchste Stelle. |
| Niedrigste Stelle unter der Dachschräge | Nur bei Dachschräge. Thermogeist rechnet mit dem Mittel aus niedrigster und höchster Stelle. |
| Außenwände | Wände nach draußen. Ein Eckraum hat meist 2, ein innenliegender Flur 0. |
| Über / unter dem Raum | Beheizter Raum, unbeheizter Raum (Dachboden, Keller), Dach oder Erdreich. |

**So funktioniert die Schätzung:** Ein typischer Raum – 2,5 m hoch, zwei Außenwände, darüber und
darunter beheizt – bekommt genau seinen Anteil an der Wohnfläche: 20 m² in einem Haus mit
160 m² = 12,5 %. Höhere Decken, mehr Außenwände, ein Dach darüber oder Erdreich darunter
erhöhen den Anteil, innenliegende und niedrige Räume mit Dachschräge bekommen weniger.

### Schritt 2b: bekannter Anteil

Trag die Heizlast des Raums geteilt durch die Heizlast des Hauses in Prozent ein. Zusammen mit
den anderen Räumen und dem Anteil außerhalb von Thermogeist darf das 100 % nicht übersteigen.

**Dielen, Flure, Treppenhäuser:** Ohne Thermostat einfach weglassen – ihr Anteil erscheint dann
beim Haus als „Heizlast ohne Raum“. Mit Thermostat als normalen Raum anlegen; wenige Außenwände
ergeben einen kleinen Anteil.

## Was du pro Raum siehst

| Entität | Bedeutung |
|---|---|
| Klima (heißt wie der Raum) | Raumtemperatur und die Zieltemperatur, die du einstellst (5–30 °C). Für Dashboards und Sprachassistenten. |
| Aktueller Grund | Warum der Raum sein aktuelles Ziel anstrebt. Jeder Grund hat eine [FAQ-Seite](faq/README.md). |
| Zieltemperatur | Was der Raum gerade wirklich anstrebt – z. B. 7 °C bei Frostschutz. |
| Wärmebedarf | Watt, die der Raum gerade braucht, um sein Ziel zu halten (braucht eine Heizlast beim Haus). |
| Geschätzte Heizleistung | Nur mit Thermostaten: Watt, die die Heizkörper gerade abgeben, aus Nennleistung, Vorlauf, Raumtemperatur und Ventilstellung – zum Vergleich mit dem Wärmebedarf ([so wird geschätzt](entities.md#geschätzte-heizleistung)). |
| Anteil an der Heizlast | Der Anteil des Raums, geschätzt oder eingetragen. |
| Wärmeverlustkoeffizient | Watt pro Kelvin Temperaturunterschied nach draußen. |
| Fenster | Nur mit Fensterkontakten: an, solange einer offen ist. Attribute: die Kontakte, `heating_paused`, `frost_guard` und die geltenden Zeiten. Unter **Konfiguration**: *Fenster: schließen nach*, *Fenster: wieder heizen nach* (Wert vom Haus, bis du ihn änderst, Attribut `source`) und *Fenster: Zeiten auf Haus zurücksetzen*. |
| Heizkörpergröße | Nur mit Thermostaten: Schaffen die Heizkörper den Sollwert am kältesten Auslegungstag? *Viel größer als nötig*, *passend*, *knapp*, *zu klein* oder *noch nicht bewertbar*, mit den Zahlen als Attribute ([FAQ](faq/radiator_sizing.md)). |
| Wärme aus Geräten | Nur mit Wärmequellen: Watt, die die Geräte an den Raum abgeben (nach Faktor, Mittel über 10 Minuten). Attribute: der geltende Faktor pro Gerät und die Faktor-Sensoren. |

Beim Haus siehst du zusätzlich **Heizlast ohne Raum** und **Abdeckung durch Räume**: wie viel
der Heizlast deine Räume (und der Anteil außerhalb von Thermogeist) abdecken, mit dem fehlenden
Anteil und der Wohnfläche, die noch in keinem Raum steckt, als Attribute. **Wärmebedarf der
Räume** und **Wärmezufuhr der Räume** zeigen, was deine Räume gerade brauchen und bekommen, in
Watt – anders als die **Heizlast**, der feste Planungswert für den kältesten Tag. Mit Vor- und
Rücklaufsensor zeigt das Haus außerdem **Vorlauftemperatur**, **Rücklauftemperatur** und
**Spreizung** – die gemittelten Werte, mit denen die Regelung rechnet – und **Vorlauf am
Auslegungstag** aus der Heizkurve, die Thermogeist lernt ([FAQ](faq/radiator_sizing.md)).

Um einen Raum zu ändern, öffne den Thermogeist-Eintrag, klick auf das Zahnrad (⚙) neben dem Raum
und wähle **Raum bearbeiten**. Im selben Menü fügst du die Thermostate des Raums hinzu, änderst
oder entfernst sie.


## Geräte, die den Raum heizen

Viele Geräte machen aus ihrem Strom Wärme im Raum: Ein Gaming-PC mit 300 W ist ein kleiner
Heizkörper. Wähl ihre Leistungssensoren (W) im ersten Schritt des Raums; Thermogeist zieht ihre
Wärme dann von dem ab, was der Heizkörper liefern muss. Geht ein Gerät aus, übernimmt der
Heizkörper innerhalb von Minuten. Die geplante Ventilstellung zeigt `heat_from_devices_w` und
`demand_covered_by_devices_pct`. Die Leistung wird
über 10 Minuten gemittelt, damit ein PC, der zwischen 80 und 400 W springt, das Ventil nicht bei
jedem Lastwechsel bewegt.

In einem extra Schritt gibst du pro Gerät einen **Faktor** an: wie viel der Leistung wirklich als
Wärme im Raum bleibt.

**100 % – alles bleibt im Raum** (Standard)

| Gerät | Warum |
|---|---|
| PC, Gaming-PC, Laptop, Server, NAS, Netzwerkgeräte | Elektronik macht aus dem ganzen Strom Wärme. |
| Fernseher, Monitor, Spielkonsole, Audio | Genauso. |
| Licht | Praktisch alles, auch das Licht selbst wird am Ende zu Wärme. |
| Kühlschrank, Gefriertruhe | Die Wärme kommt hinten raus – in den Raum. |
| Wärmepumpentrockner | Arbeitet mit geschlossener Luft, die Wärme bleibt im Raum. |
| Föhn, Heizlüfter, elektrischer Handtuchheizkörper, Infrarotheizung | Wärme ist ihr Zweck. |
| Aquarium (Heizstab, Pumpe, Licht) | Das Wasser gibt die Wärme an den Raum weiter. |

**Weniger als 100 % – ein Teil der Wärme verlässt den Raum**

| Gerät | Faktor etwa | Warum |
|---|---|---|
| Ablufttrockner | 10–20 % | Warme, feuchte Luft wird nach draußen geblasen. |
| Waschmaschine | 10–20 % | Der Strom heizt vor allem Wasser, und das läuft in den Abfluss. |
| Spülmaschine | 20–40 % | Wie die Waschmaschine; die Trocknungsphase gibt etwas Wärme ab. |
| Herd mit Abluft-Dunstabzug | etwa 50 % | Ein Teil der Wärme geht mit der Abluft hinaus. |
| Durchlauferhitzer, Boiler | fast 0 % | Das Warmwasser fließt in den Abfluss. |
| Zwischenstecker mit Mehrfachdose, Geräte stehen woanders | so viel, wie davon im Raum steht | Der Sensor misst mehr, als im Raum ankommt. |
| PoE-Switch, der Außenkameras versorgt | der Anteil des Switches | Den Rest verbrauchen die Kameras draußen. |

**Mehr als 100 %:** Ein Luftentfeuchter mit Kompressor gibt seinen Strom plus die Wärme der
kondensierten Feuchte ab – etwa 150 %. Wähle trotzdem 100 %: Zu wenig Wärme anzunehmen ist
harmlos, die langsame Korrektur gleicht es aus.

**Klimaanlage, die heizt (Luft-Luft-Wärmepumpe):** Sie holt Wärme von draußen und gibt ihren
Strom mal ihren **COP** in den Raum ab, typisch das 3- bis 4-Fache. Der Faktor ist dann
COP × 100 %, erlaubt sind bis 500 %. Den COP kennst du meist nicht, aber auf dem EU-Energielabel
steht der **SCOP** für den Heizbetrieb (mittlere Heizperiode). Nimm etwas weniger, z. B. 400 % bei
einem SCOP von 4,6 – an kalten Tagen ist der COP niedriger. Kühlt die Anlage, ist sie keine Heizung:
Ein Template als Leistungssensor, das im Kühlbetrieb 0 W meldet, verhindert, dass sie mitzählt.

**Faktor aus einem Sensor:** Optional wählst du pro Gerät neben der Zahl einen *Faktor-Sensor*
in %. Solange er verfügbar ist, hat er Vorrang; fällt er aus, gilt wieder die Zahl. Thermogeist
begrenzt ihn auf 0–500 %. Damit kann ein Template den COP mit der Außentemperatur mitgehen lassen.
Eine grobe Schätzung für Split-Klimaanlagen: `COP = 0,45 · T_warm / (T_warm − T_kalt)` in Kelvin,
mit `T_warm` = Raum + 15 K und `T_kalt` = außen − 6 K. Das ergibt etwa 4,2 bei 9 °C draußen und
2,6 bei −10 °C. Die Entity-IDs im Beispiel sind Platzhalter:

```yaml
template:
  - sensor:
      - name: "Klimaanlage Wohnzimmer Faktor"
        unit_of_measurement: "%"
        state: >
          {% set innen = states('sensor.wohnzimmer_temperatur') | float(21) %}
          {% set aussen = states('sensor.aussentemperatur') | float(5) %}
          {% set warm = innen + 15 + 273.15 %}
          {% set kalt = aussen - 6 + 273.15 %}
          {% set cop = 0.45 * warm / (warm - kalt) %}
          {{ (([1, cop, 5] | sort)[1] * 100) | round(0) }}
```

Der Sensor **Wärme aus Geräten** zeigt im Attribut `sources` den Faktor, der gerade gilt, und in
`factor_entities` die gewählten Faktor-Sensoren.

Weiter: [Thermostate zuordnen](thermostats.md).
