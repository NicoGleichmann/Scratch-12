#!/usr/bin/env python3
"""Baut das kleine Scratch-Spiel "Apfelfänger" als .sb3-Datei.

Aufruf:  python3 generator/apfel.py   ->  Apfelfaenger.sb3
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import assets as A  # noqa: E402
from scratch import *  # noqa: E402,F401,F403

P = Project()
S = P.stage


def kostuemname():
    return Blk("looks_costumenumbername", fields={"NUMBER_NAME": "name"})


def sage(text, sek):
    return Blk("looks_sayforsecs", inputs={"MESSAGE": text, "SECS": sek})


# ============================================================== Grafiken


def apfel(c1, c2, extra=""):
    return A.svg(44, 48, (
        '<defs><radialGradient id="g" cx="0.35" cy="0.35" r="0.75">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></radialGradient></defs>'
        '<path d="M22 12 C10 4 1 14 3 27 C5 40 14 47 22 43 C30 47 39 40 41 27 C43 14 34 4 22 12 Z" '
        'fill="url(#g)" stroke="#3a1a0a" stroke-width="1.5"/>'
        '<path d="M22 12 Q23 5 26 2" stroke="#5a3a1a" stroke-width="3" fill="none" stroke-linecap="round"/>'
        '<path d="M25 7 Q33 0 39 5 Q32 11 25 7 Z" fill="#4caf50" stroke="#2e7d32"/>'
        '<ellipse cx="13" cy="20" rx="4" ry="6" fill="#fff" fill-opacity="0.45"/>%s' % (c1, c2, extra)))


APFEL = apfel("#ff6b6b", "#b71c1c")
GOLD = apfel("#fff59d", "#f9a825",
             '<path d="M36 36 l2 -5 l2 5 l5 2 l-5 2 l-2 5 l-2 -5 l-5 -2 Z" fill="#fff"/>'
             '<path d="M6 8 l1 -3 l1 3 l3 1 l-3 1 l-1 3 l-1 -3 l-3 -1 Z" fill="#fff"/>')
FAUL = apfel("#a1887f", "#4e342e",
             '<circle cx="28" cy="28" r="4" fill="#3e2723"/><circle cx="15" cy="34" r="3" fill="#3e2723"/>'
             '<circle cx="31" cy="18" r="2" fill="#3e2723"/>'
             '<path d="M28 28 q5 -2 7 2 q2 4 6 2" stroke="#f48fb1" stroke-width="3" fill="none" '
             'stroke-linecap="round"/>')

korb_streifen = "".join(
    '<path d="M%d 22 L%d 52" stroke="#6d4c1f" stroke-width="2"/>' % (14 + i * 12, 18 + i * 10)
    for i in range(8))
KORB = A.svg(110, 56, (
    '<path d="M4 20 L106 20 L94 54 L16 54 Z" fill="#c8913a" stroke="#6d4c1f" stroke-width="2"/>'
    '%s<path d="M8 33 L102 33 M12 44 L98 44" stroke="#8d6327" stroke-width="3"/>'
    '<rect x="1" y="14" width="108" height="9" rx="4" fill="#a0692a" stroke="#6d4c1f" stroke-width="2"/>'
    % korb_streifen))


def hintergrund(game_over):
    baeume = ""
    for x, y, r in ((40, 200, 55), (445, 190, 60), (-5, 240, 45), (490, 245, 40)):
        baeume += ('<rect x="%d" y="%d" width="16" height="90" fill="#6d4c41"/>'
                   '<circle cx="%d" cy="%d" r="%d" fill="#388e3c"/>'
                   '<circle cx="%d" cy="%d" r="4" fill="#e53935"/><circle cx="%d" cy="%d" r="4" fill="#e53935"/>'
                   % (x - 8, y, x, y, r, x - 15, y + 10, x + 20, y - 12))
    body = (
        '<defs>%s</defs><rect width="480" height="360" fill="url(#h)"/>'
        '<circle cx="400" cy="60" r="32" fill="#fff176"/>'
        '<ellipse cx="120" cy="330" rx="260" ry="90" fill="#9ccc65"/>'
        '<ellipse cx="400" cy="340" rx="240" ry="80" fill="#8bc34a"/>%s'
        '<rect y="320" width="480" height="40" fill="#689f38"/>'
        % (A.lin_grad("h", "#81d4fa", "#e1f5fe"), baeume))
    if game_over:
        body += '<rect width="480" height="360" fill="#000" fill-opacity="0.55"/>'
        body += A.pixel_text("GAME OVER", 240 - A.text_width("GAME OVER", 6) / 2, 120, 6,
                             "#ff5252", shadow="#000")
        t = "GRÜNE FLAGGE = NOCHMAL"
        body += A.pixel_text(t, 240 - A.text_width(t, 3) / 2, 200, 3, "#ffffff", shadow="#000")
    return A.svg(480, 360, body)


# ============================================================== Bühne
S.var("Punkte", 0)
S.var("Leben", 3)
S.var("Rekord", 0)
S.var("Tempo", 3)
P.costume(S, "Obstgarten", hintergrund(False), 240, 180)
P.costume(S, "Game Over", hintergrund(True), 240, 180)
P.sound(S, "Game Over", *A._wav(A.notes(
    [(A.midi(67), .25), (A.midi(64), .25), (A.midi(60), .25), (A.midi(55), .7)], "tri", 0.4, 0.03)))

S.script(
    on_flag(),
    backdrop("Obstgarten"),
    setv("Punkte", 0), setv("Leben", 3), setv("Tempo", 3),
    until(lt(v("Leben"), 1),
          setv("Tempo", add(3, div(v("Punkte"), 10)))),
    broadcast("Game Over"),
    comment="Spielablauf: Werte zurücksetzen. Solange noch Leben da sind, wird das Tempo "
            "aus den Punkten berechnet (alle 10 Punkte +1). Sind alle Leben weg, "
            "wird die Nachricht 'Game Over' gesendet.")

S.script(
    on_msg("Game Over"),
    backdrop("Game Over"),
    if_(gt(v("Punkte"), v("Rekord")), setv("Rekord", v("Punkte"))),
    play_wait("Game Over"),
    stop("all"),
    comment="Spielende: Game-Over-Bild zeigen, Rekord aktualisieren, Melodie abspielen, "
            "dann alles stoppen.")

# ============================================================== Korb
korb = P.sprite("Korb", x=0, y=-140, visible=True, rotationStyle="don't rotate")
P.costume(korb, "Korb", KORB, 55, 28)

korb.script(
    on_flag(),
    goto_xy(0, -140), show(), front(),
    sage("Fang die Äpfel! Steuern mit ← →", 2),
    forever(
        if_(or_(key("left arrow"), key("a")), chx(-10)),
        if_(or_(key("right arrow"), key("d")), chx(10)),
        if_(gt(xpos(), 200), setx(200)),
        if_(lt(xpos(), -200), setx(-200))),
    comment="Steuerung: Pfeiltasten (oder A/D) bewegen den Korb nach links und rechts. "
            "Die beiden letzten Wenn-Blöcke halten ihn am Bildschirmrand fest.")

korb.script(on_msg("Game Over"), hide())

# ============================================================== Apfel
ap = P.sprite("Apfel", x=0, y=190, visible=False)
ap.var("Zufall", 0)
P.costume(ap, "Apfel", APFEL, 22, 26)
P.costume(ap, "Goldapfel", GOLD, 22, 26)
P.costume(ap, "Faulapfel", FAUL, 22, 26)
P.sound(ap, "Plopp", *A._wav(A.sweep(500, 1100, 0.09, "sine", 0.5)))
P.sound(ap, "Bonus", *A._wav(A.notes(
    [(A.midi(72), .06), (A.midi(76), .06), (A.midi(79), .06), (A.midi(84), .14)], "square", 0.22)))
P.sound(ap, "Autsch", *A._wav(A.sweep(380, 110, 0.3, "saw", 0.3)))

ap.script(
    on_flag(),
    hide(),
    wait(2),
    forever(
        clone(),
        wait(div(rnd(20, 40), v("Tempo")))),
    comment="Apfel-Fabrik: Das Original bleibt unsichtbar und erzeugt immer wieder Klone. "
            "Je höher das Tempo, desto kürzer die Pause zwischen zwei Äpfeln.")

ap.script(
    on_clone(),
    goto_xy(rnd(-220, 220), 190),
    point(rnd(70, 110)),
    setv("Zufall", rnd(1, 10)),
    ifelse(eq(v("Zufall"), 10),
           [costume("Goldapfel")],
           [ifelse(gt(v("Zufall"), 7), [costume("Faulapfel")], [costume("Apfel")])]),
    show(),
    until(lt(ypos(), -170),
          chy(mul(-1, v("Tempo"))),
          if_(touching("Korb"),
              call("gefangen"),
              delete_clone())),
    if_(eq(kostuemname(), "Apfel"),
        chg("Leben", -1),
        play_wait("Autsch")),
    delete_clone(),
    comment="Jeder Klon ist ein fallender Apfel. Zufall 1-7 = normaler Apfel (70 %), "
            "8-9 = fauler Apfel (20 %), 10 = Goldapfel (10 %). "
            "Fällt ein normaler Apfel auf den Boden, kostet das ein Leben.")

ap.proc("gefangen", [], [
    ifelse(eq(kostuemname(), "Faulapfel"),
           [chg("Leben", -1), play("Autsch")],
           [ifelse(eq(kostuemname(), "Goldapfel"),
                   [chg("Punkte", 5), play("Bonus")],
                   [chg("Punkte", 1), play("Plopp")])]),
], comment="Eigener Block: Was passiert, wenn der Korb einen Apfel fängt? "
           "Normal = +1 Punkt, Gold = +5 Punkte, faul = -1 Leben.")

ap.script(on_msg("Game Over"), delete_clone())

# ============================================================== Speichern
P.var_monitor("Punkte", 5, 5)
P.var_monitor("Leben", 5, 32)
P.var_monitor("Rekord", 5, 59)

ziel = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Apfelfaenger.sb3")
P.save(ziel, agent="Apfelfaenger Generator")
print("gespeichert:", ziel)
