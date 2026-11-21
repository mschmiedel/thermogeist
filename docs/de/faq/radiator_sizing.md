# Heizkörpergröße

[English](../../en/faq/radiator_sizing.md) | **Deutsch**

## Was du siehst

Den Raumsensor **Heizkörpergröße** (im Diagnosebereich des Raums) mit einem dieser Werte und
eventuell einen Hinweis unter **Einstellungen → Reparaturen**:

| Wert | Bedeutung |
|---|---|
| Viel größer als nötig | Selbst am kältesten Auslegungstag braucht der Raum weniger als 30 % dessen, was seine Heizkörper liefern. |
| Passend | 30–90 %. |
| Knapp | 90–100 %: An den kältesten Tagen bleibt kaum Reserve. |
| Zu klein | Über 100 %, oder das Ventil stand an kalten Tagen ganz offen und der Raum wurde trotzdem nicht warm. |
| Noch nicht bewertbar | Etwas fehlt; das Attribut `missing` sagt, was. |

## So rechnet Thermogeist

1. **Bedarf am Auslegungstag:** Wärmeverlust des Raums (aus seinem Anteil an der Heizlast) mal
   dem Unterschied zwischen deinem Sollwert und der Normaußentemperatur.
2. **Vorlauf am Auslegungstag:** Thermogeist lernt deine Heizkurve. Jede Stunde, in der geheizt
   wird, merkt es sich Außen- und Vorlauftemperatur (den Median, damit Warmwasser-Spitzen nicht
   zählen). Ab 48 Stunden über mindestens 5 K Außentemperatur legt es eine Gerade durch und
   verlängert sie bis zum Auslegungstag. Der Haus-Sensor **Vorlauf am Auslegungstag** zeigt das
   Ergebnis; `confidence` sagt, wie weit die Gerade verlängert werden musste (*high* bis 5 K
   unter der kältesten gesehenen Stunde, *medium* bis 15 K, sonst *low*). Im Frühherbst dauert
   es ein paar Tage, bis die Gerade gelernt ist.
3. **Heizkörperleistung an diesem Tag** aus der Nennleistung der Thermostate des Raums (EN 442).
4. **Im Betrieb:** Eine Stunde zählt als „ganz offen in der Kälte“, wenn das Ventil mindestens
   95 % offen war, der Raum mehr als 0,5 K unter seinem Ziel lag und es draußen unter 5 °C hatte.
   Sechs solche Stunden in einer Woche bedeuten *zu klein*, egal was die Rechnung sagt. Im
   Beobachtungsmodus braucht das ein Thermostat, das seine Ventilstellung meldet.

Geräte, die den Raum heizen, zählen nicht mit: Auf sie ist am kältesten Tag kein Verlass.

Die Attribute zeigen die Zahlen: `load_pct`, `factor` (Leistung / Bedarf), `design_flow_c`,
`design_demand_w`, `design_output_w`, `full_open_hours`, `basis` (`static` = gerechnet,
`operation` = beobachtet) und `cause`.

## Zu klein

`cause: radiator_small` – die Heizkörper geben beim gelernten Vorlauf zu wenig ab.

- Stimmt die Nennleistung der Thermostate (bei 75/65/20 °C, aus dem Datenblatt)?
- Ist der Anteil des Raums an der Heizlast plausibel? Ein Raum, der zu einem Nachbarraum offen
  ist (breite Tür, offener Grundriss), bekommt Wärme von dort; leg beide als einen Raum mit allen
  Thermostaten an.
- Möglichkeiten: ein größerer oder zusätzlicher Heizkörper, eine höhere Heizkurve (kostet bei
  einer Wärmepumpe Effizienz), oder an den kältesten Tagen etwas weniger akzeptieren.

`cause: input_or_hydraulics` – laut Rechnung passt es, aber im Betrieb wird der Raum mit ganz
offenem Ventil nicht warm.

- Ist der Heizkörper verdeckt (Vorhang, Möbel, Verkleidung)?
- Ist die Voreinstellung des Ventileinsatzes zu weit zu, oder fehlt der hydraulische Abgleich?
  Ist Luft im Heizkörper?
- Ist die Nennleistung zu hoch eingetragen?

## Viel größer als nötig

- **Wärmepumpe:** kein Fehler. Ein großer Heizkörper lässt die Wärmepumpe mit niedrigem Vorlauf
  laufen, das spart Energie (Attribut `note: reserve`, kein Reparaturhinweis).
- **Kessel oder Elektro-Direkt:** Das Ventil arbeitet meist fast geschlossen, die Regelung wird
  gröber. Die Voreinstellung des Ventileinsatzes etwas zu schließen hilft.
- **Alle Räume viel größer als nötig** (`cause: flow_high`, Reparaturhinweis *Vorlauf
  wahrscheinlich höher als nötig*): Die Heizkurve steht wahrscheinlich höher, als dein Haus
  braucht. Sie schrittweise abzusenken spart Energie, besonders mit einer Wärmepumpe. Thermogeist
  ändert nichts an deiner Heizung; stell sie an der Wärmepumpe oder am Kessel um und beobachte
  die Räume ein paar Tage.

## Noch nicht bewertbar

`missing` nennt, was fehlt: `heat_load` (Heizlast und Normaußentemperatur am Haus),
`radiator_output` (Nennleistung der Thermostate), `flow_temperature` (Vorlaufsensor am Haus)
oder `heating_curve` (noch nicht genug Heizstunden gelernt – ein paar Tage warten).
