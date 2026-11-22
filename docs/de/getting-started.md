# Erste Schritte

[English](../en/getting-started.md) | **Deutsch**

> Thermogeist steht noch am Anfang. Du kannst dein Haus und seine [Räume](rooms.md) beschreiben.
> Thermostate zuordnen und Räume regeln geht schon – siehe [Thermostate](thermostats.md).

## Installieren

**Von Hand aus dem Zip**

1. Lade `thermogeist.zip` aus dem neuesten Release herunter.
2. Entpacke es nach `config/custom_components/thermogeist/` in deinem Home Assistant.
3. Starte Home Assistant neu.

Die Installation über HACS beschreiben wir, sobald Thermogeist veröffentlicht ist.

## Dein Haus beschreiben

Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen** und suche nach
**Thermogeist**.

Die ganze Einrichtung auf einen Blick. **Blaue** Kästen sind Schritte im Dialog, **graue**
Rauten deine Antworten, **gelbe** Kästen das, was du vorher bereitlegen solltest:

```mermaid
flowchart TD
    A["Haus: Name, Heizungsart, Außensensor"] --> B{"Heizlast bekannt?"}
    B -- "ja" --> C["Heizlast und Normaußentemperatur"]
    B -- "nein" --> D
    C --> D{"Wassertemperatur gemessen?"}
    D -- "ja" --> E["Vorlauf- (und Rücklauf-)sensor"]
    D -- "nein" --> F
    E --> F["Raum anlegen: Name, Raumsensor, Anteil"]
    F --> G{"Anteil bekannt?"}
    G -- "schätzen" --> H["Größe und Lage"]
    G -- "bekannt" --> I["Anteil in %"]
    H --> J{"Thermostat hinzufügen?"}
    I --> J
    J -- "ja" --> K["Gerät und Heizkörperleistung,<br/>Rollen werden erkannt"]
    K --> J
    J -- "fertig" --> L["Raum gespeichert – Beobachten"]
    L --> M["Regeln einschalten, wenn dir die Planung passt"]

    P1["Außensensor oder Wetter-Entität"] -.-> A
    P2["Heizlastberechnung, falls vorhanden"] -.-> C
    P3["Vorlauf-/Rücklaufsensor in Home Assistant"] -.-> E
    P4["Raumtemperatursensor"] -.-> F
    P5["Datenblatt des Heizkörpers oder Größe und Typ"] -.-> K

    classDef step fill:#cfe3ff,stroke:#3b78c4,color:#000
    classDef ask fill:#e6e6e6,stroke:#777,color:#000
    classDef prep fill:#fff1b8,stroke:#c9a200,color:#000,stroke-dasharray: 4 3
    class A,C,E,F,H,I,K,L,M step
    class B,D,G,J ask
    class P1,P2,P3,P4,P5 prep
```

### Schritt 1: die drei wichtigsten Angaben

| Feld | Was du einträgst |
|---|---|
| Name | So soll das Haus heißen, z. B. „Haus“ oder „Einliegerwohnung“. |
| Heizungsart | Wärmepumpe, Kessel (Gas, Öl, Pellets, Fernwärme) oder Elektro-Direktheizung. Davon hängt ab, wie ruhig Thermogeist regelt. |
| Außentemperatur | Ein Außenthermometer, der Außenfühler deiner Wärmepumpe oder deine **Wetter-Entität** (z. B. *Forecast Home* von Met.no oder OpenWeatherMap) – fast jedes Home Assistant hat eine. Für den Anfang reicht die Wetter-Entität; ein echter Sensor ist genauer (siehe unten). |

### Schritt 2: ein paar Fragen

Deine Antworten bestimmen, was Thermogeist als Nächstes fragt – du siehst nur die Felder, die
du ausfüllen musst.

| Frage | Was folgt |
|---|---|
| Kennst du die Heizlast? | **Ja**, wenn es eine Heizlastberechnung gibt (Heizungsbauer oder Energieberater): Ein Schritt fragt Heizlast, Normaußentemperatur und, falls bekannt, den Anteil außerhalb von Thermogeist. **Nein**: nichts weiter. |
| Wird die Wassertemperatur gemessen? | **Nein**, **nur Vorlauf** oder **Vorlauf und Rücklauf**: Ein Schritt fragt nach dem einen oder den beiden Sensoren – sorgfältig wählen, siehe [Den Vorlauf-Sensor wählen](thermostats.md#den-vorlauf-sensor-wählen). |
| Beheizte Wohnfläche | Die gesamte beheizte Fläche, ohne Balkon und Terrasse. Damit schätzt Thermogeist den Anteil jedes Raums an der Heizlast: Ein Raum mit 20 m² in einem Haus mit 160 m² startet bei etwa 12,5 %. Empfohlen. |

Die Werte in den folgenden Schritten:

| Feld | Was du einträgst |
|---|---|
| Heizlast | Die Wärme, die dein Haus am kältesten Auslegungstag braucht, in kW, aus der Heizlastberechnung. |
| Normaußentemperatur | Die Außentemperatur, für die die Heizlast berechnet wurde. |
| Anteil außerhalb von Thermogeist | Teil der Heizlast in Räumen, die Thermogeist nicht regeln soll, z. B. ein Bad mit Fußbodenheizung. Nur, wenn du ihn kennst; sonst ergibt er sich aus der Wohnfläche. |
| Vorlauf-/Rücklauftemperatursensor | Das Wasser zu den Heizkörpern und zurück; mit beiden nutzt Thermogeist die gemessene Spreizung statt 5 K anzunehmen. |

In den Haus-Einstellungen sind die Antworten vorausgewählt; wer später *Nein* antwortet,
entfernt die zugehörigen Werte.

> **Tipp: ein guter Außensensor.** Direkte Sonne lässt ein Thermometer viel zu warm messen, und
> Thermogeist würde dann zu wenig heizen. Häng es in den Schatten (Nordseite, unter einen
> Dachvorsprung). Geht das nicht, nimm zwei oder mehr Sensoren an verschiedenen Hausseiten und
> fasse sie mit dem Home-Assistant-Helfer *Kombiniere den Zustand mehrerer Sensoren* zusammen,
> Typ **Minimum** – einer steht immer im Schatten. Eine Wetter-Entität hat kein Sonnenproblem,
> liefert aber regionale Modellwerte, die oft 1–3 K abweichen und etwa stündlich kommen.

> **Tipp: die Normaußentemperatur finden.** Sie hängt von deinem Wohnort ab. Suche im Web nach
> „Normaußentemperatur“ und deiner Postleitzahl. Hast du eine Heizlastberechnung, steht der
> Wert dort drin.

Du kannst mehrere Häuser anlegen, zum Beispiel eine Einliegerwohnung mit eigener Heizung.

## Was du danach siehst

Thermogeist legt ein Gerät für dein Haus an:

- **Zentralmodus** – *Automatisch*, *Aus* oder *Frostschutz* für das ganze Haus. Die Einstellung
  bleibt auch nach einem Neustart erhalten.
- **Regelwerte** – vier Werte, die du direkt auf der Geräteseite ändern kannst. Sie starten
  mit den Voreinstellungen deiner Heizungsart; das Attribut `source` zeigt `profile` oder `user`.
  **Regelwerte auf Profil zurücksetzen** holt die Voreinstellungen zurück. Wechselst du später
  die Heizungsart, bleiben deine eigenen Werte, die unveränderten folgen dem neuen Profil.
- **Diagnosewerte** – Heizungsart, Heizlast, Normaußentemperatur, Anteil außerhalb von
  Thermogeist und Heizlast ohne Raum.

Voreinstellungen je Heizungsart:

| Voreinstellung | Wärmepumpe | Kessel | Elektro-Direkt |
|---|---|---|---|
| Mindestöffnung Ventil | 40 % | 0 % | 0 % |
| Totband über dem Sollwert | 0,5 K | 0,2 K | 0,2 K |
| Max. Ventiländerung pro 30 min | 10 % | 30 % | 100 % |
| Max. Absenkung | 2 K | 4 K | 4 K |
| Fenster: schließen nach | 30 s | 30 s | 30 s |
| Fenster: wieder heizen nach | 10 s | 10 s | 10 s |

Warum so unterschiedlich? Eine Wärmepumpe arbeitet am besten, wenn das Wasser in Bewegung
bleibt. Deshalb hält Thermogeist die Ventile offen und bewegt sie langsam. Ein Kessel reagiert
schneller und kommt mit schließenden Ventilen gut zurecht.

## Einstellungen ändern

Öffne den Thermogeist-Eintrag und wähle **Konfigurieren**. Du kannst alles außer dem Namen
ändern, Thermogeist lädt danach neu.

Weiter: [Räume anlegen](rooms.md).
