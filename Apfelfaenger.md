# Apfelfänger 🍎

Ein kleines Fangspiel für **Scratch 3**: 3 Figuren, 8 Skripte, 1 eigener Block.

## Öffnen

1. **[Apfelfaenger.sb3](Apfelfaenger.sb3)** herunterladen.
2. Auf [scratch.mit.edu](https://scratch.mit.edu) → **Entwickeln** → **Datei** → **Von deinem Computer hochladen**.
3. Auf die **grüne Flagge** klicken.

## Spielregeln

| Apfel | Wahrscheinlichkeit | Gefangen | Verpasst |
|---|---|---|---|
| 🍎 Roter Apfel | 70 % | +1 Punkt | **−1 Leben** |
| 🟡 Goldapfel | 10 % | +5 Punkte | nichts |
| 🟤 Fauler Apfel (mit Wurm) | 20 % | **−1 Leben** | nichts |

- Steuerung: **Pfeiltasten ← →** oder **A / D**
- Du startest mit **3 Leben**.
- Alle 10 Punkte werden die Äpfel **schneller** und kommen **häufiger**.
- Der **Rekord** bleibt erhalten, solange das Projekt geöffnet ist.

## Aufbau

### Variablen (für alle Figuren)

| Variable | Bedeutung |
|---|---|
| `Punkte` | aktueller Punktestand |
| `Leben` | verbleibende Leben |
| `Rekord` | bester Punktestand |
| `Tempo` | Fallgeschwindigkeit (Pixel pro Bild) |

Die Figur **Apfel** hat zusätzlich `Zufall` (nur für diese Figur), damit jeder Klon seine eigene Zufallszahl hat.

### Bühne

```
Wenn grüne Flagge angeklickt
  wechsle zu Bühnenbild [Obstgarten]
  setze Punkte auf 0
  setze Leben auf 3
  setze Tempo auf 3
  wiederhole bis <Leben < 1>
    setze Tempo auf (3 + (Punkte / 10))
  sende [Game Over] an alle

Wenn ich [Game Over] empfange
  wechsle zu Bühnenbild [Game Over]
  falls <Punkte > Rekord> dann
    setze Rekord auf Punkte
  spiele Klang [Game Over] ganz
  stoppe [alles]
```

### Korb

```
Wenn grüne Flagge angeklickt
  gehe zu x: 0 y: -140
  zeige dich
  gehe zu vorderster Ebene
  sage [Fang die Äpfel! Steuern mit ← →] für 2 Sekunden
  wiederhole fortlaufend
    falls <Taste [Pfeil nach links] gedrückt? oder Taste [a] gedrückt?> dann
      ändere x um -10
    falls <Taste [Pfeil nach rechts] gedrückt? oder Taste [d] gedrückt?> dann
      ändere x um 10
    falls <x-Position > 200> dann
      setze x auf 200
    falls <x-Position < -200> dann
      setze x auf -200

Wenn ich [Game Over] empfange
  verstecke dich
```

### Apfel

```
Wenn grüne Flagge angeklickt
  verstecke dich
  warte 2 Sekunden
  wiederhole fortlaufend
    erzeuge Klon von [mir selbst]
    warte ((Zufallszahl von 20 bis 40) / Tempo) Sekunden

Wenn ich als Klon entstehe
  gehe zu x: (Zufallszahl von -220 bis 220) y: 190
  setze Richtung auf (Zufallszahl von 70 bis 110)
  setze Zufall auf (Zufallszahl von 1 bis 10)
  falls <Zufall = 10> dann
    wechsle zu Kostüm [Goldapfel]
  sonst
    falls <Zufall > 7> dann
      wechsle zu Kostüm [Faulapfel]
    sonst
      wechsle zu Kostüm [Apfel]
  zeige dich
  wiederhole bis <y-Position < -170>
    ändere y um (-1 * Tempo)
    falls <wird [Korb] berührt?> dann
      gefangen
      lösche diesen Klon
  falls <(Kostüm [Name]) = Apfel> dann
    ändere Leben um -1
    spiele Klang [Autsch] ganz
  lösche diesen Klon

Definiere gefangen
  falls <(Kostüm [Name]) = Faulapfel> dann
    ändere Leben um -1
    spiele Klang [Autsch]
  sonst
    falls <(Kostüm [Name]) = Goldapfel> dann
      ändere Punkte um 5
      spiele Klang [Bonus]
    sonst
      ändere Punkte um 1
      spiele Klang [Plopp]

Wenn ich [Game Over] empfange
  lösche diesen Klon
```

## Informatik-Konzepte (gut für die Präsentation)

1. **Ereignisse & Nachrichten:** `Game Over` wird von der Bühne gesendet; Korb und Äpfel reagieren darauf. Die Figuren kennen sich nicht direkt.
2. **Klone:** Es gibt nur *eine* Apfel-Figur. Das Original ist unsichtbar und erzeugt ständig Kopien.
3. **Lokale Variable:** `Zufall` gilt „nur für diese Figur“ – jeder Klon hat seinen eigenen Wert.
4. **Zufall & Wahrscheinlichkeit:** Zahl 1–10 → 7 von 10 normal, 2 von 10 faul, 1 von 10 Gold.
5. **Verzweigungen:** verschachtelte `falls … sonst`-Blöcke.
6. **Schleifen:** `wiederhole fortlaufend` (Steuerung) vs. `wiederhole bis` (mit Abbruchbedingung).
7. **Eigener Block:** `gefangen` bündelt die Punkte-Logik, das Klon-Skript bleibt übersichtlich.
8. **Schwierigkeitskurve:** `Tempo = 3 + Punkte / 10` steuert gleichzeitig Fallgeschwindigkeit und Abstand zwischen den Äpfeln.

## Ideen zum Erweitern

- Countdown-Modus: 60 Sekunden mit der Variable `Stoppuhr`
- Herz-Apfel, der ein Leben zurückgibt
- Der Korb wird mit steigendem Tempo kleiner
- Eigene Kostüme im Malprogramm zeichnen

## Neu erzeugen

```bash
python3 generator/apfel.py
```
