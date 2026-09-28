# Astro-Abwehr 🚀

Ein Weltraum-Shooter für **Scratch 3** mit 17 Figuren, rund 1.350 Blöcken,
Bosskampf, Power-ups und einer Top-5-Bestenliste.

## Öffnen

1. **[Astro-Abwehr.sb3](Astro-Abwehr.sb3)** herunterladen.
2. Auf [scratch.mit.edu](https://scratch.mit.edu) → **Entwickeln** → **Datei** → **Von deinem Computer hochladen**.
3. Auf die **grüne Flagge** klicken.

## Spielen

| Taste | Aktion |
|---|---|
| Pfeiltasten / WASD | Raumschiff bewegen |
| Leertaste | Schießen (gedrückt halten), im Menü: Spiel starten |
| Maus | Menü-Knöpfe |

- **Asteroiden:** Kleine brauchen 1 Treffer. Große halten mehr aus und **zerfallen in zwei Bruchstücke**.
- **UFOs** (ab Level 2) fliegen in Wellenlinien und **zielen auf dich**.
- **Jedes 5. Level: Bosskampf.** Unter 50 % Leben wird der Boss wütend, schneller und schießt Kugelfächer.
- **Power-ups:** 🔵 S = Schild, 🟡 3 = Dreifachschuss (10 s), 🟢 ♥ = Extraleben, 🔴 B = Bombe (räumt den Bildschirm)
- **Schwierigkeit:** Leicht (5 Leben, langsamer), Normal (3 Leben), Schwer (2 Leben, 30 % schneller)
- Nach dem Game Over trägst du dich mit genug Punkten in die **Bestenliste** ein.

## Aufbau des Projekts

### Figuren

| Figur | Aufgabe |
|---|---|
| **Bühne** | Spielsteuerung (Level-Ablauf, Gegner-Spawns), Musik, Game Over, Bestenliste |
| **Spieler** | Steuerung mit Trägheit, Schießen, Schild, Treffer-Behandlung |
| **Laser** | Schüsse des Spielers (Klone) |
| **Asteroid** | Gegner (Klone), zerfällt, lässt Power-ups fallen |
| **UFO** | Gegner mit Sinus-Flugbahn, schießt gezielt |
| **Boss** | Endgegner mit zwei Phasen |
| **Gegnerschuss** | Kugeln von UFO und Boss |
| **PowerUp** | 4 Power-up-Typen |
| **Explosion** | Animation aus 6 Kostümen |
| **Ziffern** | Zeichnet Zahlen und Herzen per Klon-„Stempel“ (ohne Malstift) |
| **Bossbalken** | Lebensbalken des Bosses (21 Kostüme) |
| **Sterne** | 45 Klone für den Parallax-Sternenhimmel |
| **HUD, Anzeige, Knöpfe, Hilfe** | Oberfläche: Leiste, Titel, Banner, Menü, Anleitung |

### Nachrichten (Kommunikation zwischen Figuren)

`Menü` → `Spielstart` → `Spieler Start` / `Level Banner` / `Boss Warnung` → `Boss Start` →
`Spieler getroffen` → `Game Over` → `Game Over Anzeige` → `Nochmal anbieten`.
Außerdem: `HUD`, `Bombe`, `PowerUp eingesammelt`, `Bossbalken zeigen`, `Banner weg`, `Hilfe zeigen`.

## Informatik-Konzepte im Projekt

Jedes wichtige Skript hat im Editor einen **gelben Kommentar**, der es erklärt.

1. **Zustandsautomat:** Die Variable `Status` (`menü`, `spiel`, `boss`, `gameover`) steuert, was gerade passiert. Jede Figur richtet sich danach.
2. **Klone mit lokalen Variablen:** Jeder Asteroid hat eigene Werte für `HP`, `VX`, `VY` usw. („nur für diese Figur“). Klone **erben** diese Werte. Daran erkennt ein Bruchstück mit `Typ = 3`, dass es aus einem großen Asteroiden entstanden ist.
3. **Warteschlange (FIFO):** Soll ein Laser, eine Explosion oder ein Power-up entstehen, kommen x, y und ein dritter Wert **hinten** in eine Liste. Der neue Klon nimmt sich die **vorderen** drei Einträge. So überschreiben sich die Daten nicht, auch wenn im selben Moment mehrere Objekte entstehen.
4. **Eigene Blöcke ohne Bildschirmaktualisierung:** z. B. `Steuerung`, `Schießen`, `Zerstören`. Das macht den Code übersichtlich und schnell.
5. **Physik mit Trägheit:** Tasten ändern die Geschwindigkeit, nicht die Position. Reibung: `vx = vx · 0,86` pro Bild.
6. **Trigonometrie:** UFO-Flugbahn, schwebender Titel und pulsierende Power-ups nutzen `sin`.
7. **Modulo:** Flammen-Animation (`abgerundet(Animation / 3) mod 2`), Blinken beim Unverwundbarsein (`Unverwundbar mod 6`), Durchschalten des Modus (`(Modus mod 3) + 1`), Boss alle 5 Level (`Level mod 5 = 0`).
8. **Sortiertes Einfügen (Insertion Sort):** Neue Einträge werden an der richtigen Stelle in die absteigend sortierte Bestenliste eingefügt. Namen und Punkte liegen in zwei **parallelen Listen**.
9. **Treffer-Sperre gegen Doppeltreffer:** Nach einem Treffer ist ein Gegner 3 Bilder lang unverwundbar. Der Laser wartet genau ein Bild (`warte 0`), bevor er verschwindet. So wird jeder Treffer genau einmal gezählt.
10. **Zentrale Treffer-Behandlung:** Gegner senden nur `Spieler getroffen`. Ob Schild, Lebensverlust oder Game Over folgt, entscheidet allein die Figur Spieler.

## Ideen für eigene Erweiterungen

- Neuer Gegnertyp, z. B. ein Kamikaze-Jäger, der mit `drehe dich zu Spieler` angreift
- Weiteres Power-up, z. B. Zeitlupe über die Variable `Tempo`
- Ein zweiter Boss mit anderem Angriffsmuster ab Level 10
- Kombo-System: Mehrere Abschüsse kurz hintereinander geben Bonuspunkte

## Wie die Datei entstanden ist

Die `.sb3`-Datei wird vom Python-Skript in [`generator/`](generator/) erzeugt.
Es beschreibt alle Blöcke, zeichnet die Grafiken als SVG und erzeugt die Sounds als WAV.
Neu bauen:

```bash
python3 generator/spiel.py
```
