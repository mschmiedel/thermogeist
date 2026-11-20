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
| Fenster- und Türkontakte | Optional. Ist einer 30 Sekunden offen, hört der Raum auf zu heizen, bis er geschlossen ist ([Häufige Fragen](faq/window_open.md)). |
| Auslegungs-Innentemperatur | Planungswert aus der Heizlastberechnung – nicht die Temperatur, auf die du heizt. Meist 20 °C, Bäder 24 °C, beheizte Flure 15 °C. Ein Bad mit 24 °C bekommt einen größeren Anteil. |

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
| Anteil an der Heizlast | Der Anteil des Raums, geschätzt oder eingetragen. |
| Wärmeverlustkoeffizient | Watt pro Kelvin Temperaturunterschied nach draußen. |

Beim Haus siehst du zusätzlich **Heizlast ohne Raum**.

Um einen Raum zu ändern, öffne den Thermogeist-Eintrag und klick auf das Zahnrad (⚙) neben dem Raum.


## Geräte, die den Raum heizen (kommt bald)

> Geplant für eine spätere Version. Dieser Abschnitt erklärt schon vorab, welchen Faktor du wählst.

Viele Geräte machen aus ihrem Strom Wärme im Raum: Ein Gaming-PC mit 300 W ist ein kleiner
Heizkörper. Du wirst einem Raum die Leistungssensoren (W) solcher Geräte geben können;
Thermogeist zieht ihre Wärme dann von dem ab, was der Heizkörper liefern muss. Die Leistung wird
über 10 Minuten gemittelt, damit ein PC, der zwischen 80 und 400 W springt, das Ventil nicht bei
jedem Lastwechsel bewegt.

Pro Gerät sagt ein **Faktor**, wie viel der Leistung wirklich als Wärme im Raum bleibt.

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

Weiter: [Thermostate zuordnen](thermostats.md).
