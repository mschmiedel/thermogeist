# Heizungen mit Stufen

[English](../en/heaters.md) | **Deutsch**

Manche Heizungen werden nicht über ein Ventil geregelt, sondern geschaltet: eine smarte
Steckdose oder ein Relais vor einem Gebläsekonvektor (Sockelheizung), ein Infrarotpaneel, ein
elektrischer Handtuchheizkörper, ein Heizlüfter mit mehreren Stufen. Thermogeist regelt sie wie
Heizkörper – gleiches Raumziel, gleiche Fenster und gleicher Zentralmodus –, schaltet sie aber
ein und aus, statt ein Ventil zu bewegen.

Ein Raum hat **entweder Thermostate oder Heizungen**. Beides in einem Raum (z. B. ein Gebläse als
Verstärker an einem Heizkörper mit Ventil) ist geplant.

## Heizung hinzufügen

Raum → Zahnrad → **Heizung hinzufügen** (beim Anlegen eines Raums: *Eine Heizung hinzufügen*).

| Feld | Was eintragen |
|---|---|
| Schalter | Die Entität, die die Heizung ein- und ausschaltet (`switch` oder `input_boolean`). |
| Wärme aus | **Heizkreis**, wenn die Wärme aus dem Heizwasser kommt (Sockelheizung, Gebläsekonvektor): Ihre Leistung hängt dann wie bei einem Heizkörper von der Vorlauftemperatur ab. **Elektrisch** für Infrarot, Heizlüfter und elektrische Handtuchheizkörper: Die Leistung ist fest. |
| Anzahl Stufen | 1 für eine einfache An/Aus-Heizung. |
| Wärmeleistung pro Stufe | Ein Wert pro Stufe in W, von niedrig nach hoch, durch Kommas getrennt: `1300, 1700`. Heizkreis: die Leistung bei 75/65/20 °C aus dem Datenblatt. Elektrisch: die Leistung selbst. **Nicht** die Leistung, die das Gebläse aufnimmt – ein Gebläse mit 22 W kann 1700 W Wärme bewegen. |

Unter **Stufen und Details**:

| Feld | Was eintragen |
|---|---|
| Stufen-Sensor | Eine Entität, die sagt, welche Stufe läuft: `0` = läuft nicht, `1`, `2` … (siehe [Templates](#templates)). Bei mehr als einer Stufe nötig, außer du hast einen Stufen-Setzer. Meldet auch eine Heizung, die eingeschaltet ist, aber nicht läuft. |
| Stufen-Setzer | Eine `number` oder `input_number`, die die Stufe `1`, `2` … annimmt und dein Gerät schaltet. Ohne sie schaltet Thermogeist nur ein und aus, und die Heizung bleibt auf der Stufe, auf die sie eingestellt ist. |
| Wärmeleistung im ausgeschalteten Zustand | Wärme, die die Heizung auch ausgeschaltet abgibt, z. B. Heizwasser, das bei stehendem Gebläse durch eine Sockelheizung fließt. Aus dem Datenblatt, meist 0. |
| Exponent | Nur für den Heizkreis: wie sich die Leistung mit der Wassertemperatur ändert. Heizkörper 1,3 (Vorgabe), Gebläsekonvektoren etwa 1,0. Mit 1,0 gibt ein Gebläsekonvektor bei niedriger Vorlauftemperatur viel mehr ab als ein Heizkörper mit derselben Normleistung. |

## Wie Thermogeist schaltet

Thermogeist plant einen Anteil an der höchsten Leistung der Heizung, z. B. 60 %. Innerhalb eines
Zyklus von 20 Minuten lässt es die Heizung dann auf den beiden Stufen um diesen Anteil laufen:

- **Mit Stufen-Setzer** wählt es die niedrigsten Stufen, die den Bedarf decken: Ein kleiner
  Bedarf wechselt zwischen aus und Stufe 1, ein großer zwischen Stufe 1 und Stufe 2. Das ist
  leiser, als die höchste Stufe ein- und auszuschalten.
- **Ohne Stufen-Setzer** wechselt es zwischen aus und der Stufe, auf der die Heizung läuft (vom
  Stufen-Sensor, sonst die höchste Stufe).

Jede Stufe läuft mindestens 5 Minuten, damit Relais und Gebläse nicht jede Minute schalten. Was
ein Zyklus deshalb nicht laufen kann, kommt zum nächsten dazu, sodass auch ein kleiner Bedarf im
Mittel gedeckt wird. Ein neuer Plan gilt ab dem nächsten Zyklus; ein offenes Fenster oder der
zentrale Stopp schalten sofort aus.

Im **Beobachtungsmodus** zeigt die Heizung nur, was sie tun würde (Attribut `planned_stage`); im
**Regelbetrieb** stellt Thermogeist Schalter und Stufen-Setzer. Schaltest du das Regeln aus,
gehen beide in den Zustand von vorher zurück.

## Templates

Thermogeist kennt dein Gerät nicht. Zwei kleine Templates passen es an.

**Stufen-Sensor aus der Leistung einer smarten Steckdose** (ein Gebläse, das auf Stufe 1 etwa
11 W und auf Stufe 2 etwa 22 W aufnimmt; die Grenzen liegen zwischen den Werten):

```yaml
template:
  - sensor:
      - name: "Sockelheizung Stufe"
        state: >
          {% set w = states('sensor.sockelheizung_steckdose_leistung') | float(0) %}
          {{ 0 if w < 5 else 1 if w < 16 else 2 }}
```

**Stufen-Setzer für eine Heizung mit zwei Relais** (ein Ausgang pro Stufe):

```yaml
template:
  - number:
      - name: "Heizlüfter Stufe"
        min: 1
        max: 2
        step: 1
        state: "{{ 2 if is_state('switch.heizluefter_hoch', 'on') else 1 }}"
        set_value:
          - action: "switch.turn_{{ 'on' if value | int == 2 else 'off' }}"
            target:
              entity_id: switch.heizluefter_hoch
```

## Was du siehst

- **Stufe *Heizung*** – die Stufe, die gerade läuft. Attribute: `planned_stage`, `lower_stage`,
  `upper_stage`, `upper_share_pct` (Anteil des Zyklus auf der oberen Stufe), `cycle_started`,
  `on_since` / `off_since`, `heat_output_w`, `stage_source` (`stage_sensor`, `stage_setter` oder
  `switch`) und deine Eingaben.
- **Geplanter Wärmeanteil** am Raum – der Anteil an der höchsten Leistung der Heizungen, den
  Thermogeist plant, mit denselben Teilen wie die geplante Ventilstellung bei Heizkörpern.
- **Geschätzte Heizleistung** – die Leistung der laufenden Stufe bei den aktuellen Temperaturen.
- ***Heizung* läuft nicht** (nur mit Stufen-Sensor) – siehe [FAQ](faq/heater_not_running.md).

Die Prüfung der Heizkörpergröße entfällt für Räume mit Heizungen: Sie setzt Heizkörper mit
Ventilen voraus.
