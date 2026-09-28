#!/usr/bin/env python3
"""Baut das Scratch-Spiel "Astro-Abwehr" als .sb3-Datei.

Aufruf:  python3 generator/spiel.py   ->  Astro-Abwehr.sb3
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import assets as A  # noqa: E402
from scratch import *  # noqa: E402,F401,F403

A.SOUNDS = A.sounds()
P = Project()
S = P.stage

# ============================================================== Hilfsfunktionen


def laeuft():
    """Wahr, solange eine Runde aktiv ist (normales Level oder Bosskampf)."""
    return or_(eq(v("Status"), "spiel"), eq(v("Status"), "boss"))


def pop3(liste):
    """Entfernt die ersten drei Einträge einer Warteschlange."""
    return [delete(1, liste), delete(1, liste), delete(1, liste)]


def hover_script(t):
    t.script(on_flag(), hide(),
             forever(ifelse(touching("_mouse_"), [size(108), effect("BRIGHTNESS", 15)],
                            [size(100), effect("BRIGHTNESS", 0)])),
             comment="Hover-Effekt: Liegt der Mauszeiger auf dem Knopf, wird er etwas "
                     "größer und heller.")


EXPLOSION = "Explosion bei x: %s y: %s Größe: %s"
POWERUP = "Power-Up erzeugen bei x: %s y: %s Typ: %s"
SCHUSS = "Gegnerschuss bei x: %s y: %s Richtung: %s"


def def_explosion(t):
    t.proc(EXPLOSION, ["x", "y", "größe"], [
        push("Explosions_Daten", arg("x")),
        push("Explosions_Daten", arg("y")),
        push("Explosions_Daten", arg("größe")),
        clone("Explosion"),
    ], comment="WARTESCHLANGE (FIFO): Position und Größe werden hinten an die Liste "
               "angehängt, dann wird ein Klon der Figur 'Explosion' erzeugt. Der neue Klon "
               "nimmt sich die ersten drei Einträge wieder heraus. So können beliebig viele "
               "Explosionen im selben Moment entstehen, ohne dass sich Daten überschreiben.")


def def_powerup(t):
    t.proc(POWERUP, ["x", "y", "typ"], [
        push("PowerUp_Daten", arg("x")),
        push("PowerUp_Daten", arg("y")),
        push("PowerUp_Daten", arg("typ")),
        clone("PowerUp"),
    ], comment="Gleiches Prinzip wie bei der Explosion: Daten in die Warteschlange, "
               "dann Klon erzeugen. Typ 1 = Schild, 2 = 3-fach-Schuss, 3 = Extraleben, 4 = Bombe.")


def def_schuss(t):
    t.proc(SCHUSS, ["x", "y", "richtung"], [
        push("Schuss_Daten", arg("x")),
        push("Schuss_Daten", arg("y")),
        push("Schuss_Daten", arg("richtung")),
        clone("Gegnerschuss"),
    ], comment="Feuert einen gegnerischen Schuss über die Warteschlange 'Schuss_Daten' ab.")


# ============================================================== Bühne
for name, val in [("Punkte", 0), ("Highscore", 0), ("Leben", 3), ("Level", 1),
                  ("Status", "menü"), ("Schwierigkeit", 2), ("Tempo", 1), ("Gegner_übrig", 0),
                  ("Schild", 0), ("Dreifach", 0), ("Boss_HP", 0), ("Boss_HP_Max", 1),
                  ("UFO_Anzahl", 0), ("Spawnpause", 1), ("Position", 1), ("i", 1), ("Name", "")]:
    S.var(name, val)
for name in ["Laser_Daten", "Schuss_Daten", "Explosions_Daten", "PowerUp_Daten", "Bestenliste"]:
    S.lst(name)
S.lst("Bestenliste_Namen", ["Captain Nova", "Astro-Bot", "Kometa", "Sternchen", "Neuling"])
S.lst("Bestenliste_Punkte", [8000, 5000, 3000, 1500, 500])

QUEUES = ["Laser_Daten", "Schuss_Daten", "Explosions_Daten", "PowerUp_Daten"]

S.script(
    on_flag(),
    setv("Status", "menü"),
    *[clear(q) for q in QUEUES],
    hide_list("Bestenliste"),
    clearfx(),
    broadcast("Menü"),
    comment="START: Beim Klick auf die grüne Flagge wird der Zustand auf 'menü' gesetzt, "
            "alle Warteschlangen geleert und das Hauptmenü aufgerufen.")

S.script(
    on_flag(),
    forever(ifelse(eq(v("Status"), "gameover"), [wait(0.2)], [play_wait("Musik")])),
    comment="HINTERGRUNDMUSIK in Endlosschleife – außer im Game-Over-Bildschirm.")

S.script(
    on_msg("Menü"),
    backdrop("Menü"),
    hide_list("Bestenliste"),
    comment="Hauptmenü: Hintergrund wechseln. Die Knöpfe und der Titel reagieren selbst "
            "auf die Nachricht 'Menü'.")

S.script(
    on_key("space"),
    if_(eq(v("Status"), "menü"), play("Klick"), broadcast("Spielstart")),
    comment="Komfort: Im Menü startet auch die Leertaste das Spiel.")

S.script(
    on_msg("Spielstart"),
    setv("Status", "spiel"),
    setv("Punkte", 0), setv("Level", 1), setv("Schild", 0), setv("Dreifach", 0),
    setv("UFO_Anzahl", 0), setv("Boss_HP", 0),
    if_(eq(v("Schwierigkeit"), 1), setv("Leben", 5), setv("Tempo", 0.75)),
    if_(eq(v("Schwierigkeit"), 2), setv("Leben", 3), setv("Tempo", 1)),
    if_(eq(v("Schwierigkeit"), 3), setv("Leben", 2), setv("Tempo", 1.3)),
    *[clear(q) for q in QUEUES],
    backdrop("Weltraum"),
    hide_list("Bestenliste"),
    broadcast("HUD"),
    broadcast("Spieler Start"),
    until(eq(v("Status"), "gameover"),
          ifelse(eq(mod(v("Level"), 5), 0), [
              play("Alarm"),
              broadcast_wait("Boss Warnung"),
              if_(eq(v("Status"), "spiel"),
                  setv("Status", "boss"),
                  broadcast("Boss Start"),
                  wait_until(not_(eq(v("Status"), "boss")))),
          ], [
              broadcast_wait("Level Banner"),
              setv("Gegner_übrig", add(6, mul(v("Level"), 4))),
              until(or_(lt(v("Gegner_übrig"), 1), eq(v("Status"), "gameover")),
                    clone("Asteroid"),
                    if_(and_(gt(v("Level"), 1),
                             lt(v("UFO_Anzahl"), add(1, floor(div(v("Level"), 4)))),
                             lt(rnd(1, 100), add(12, mul(v("Level"), 2)))),
                        clone("UFO")),
                    setv("Spawnpause", sub(div(1.1, v("Tempo")), mul(v("Level"), 0.06))),
                    if_(lt(v("Spawnpause"), 0.3), setv("Spawnpause", 0.3)),
                    wait(v("Spawnpause"))),
          ]),
          if_(not_(eq(v("Status"), "gameover")),
              chg("Punkte", mul(v("Level"), 100)),
              chg("Level", 1),
              play("Level geschafft"),
              broadcast("HUD"))),
    comment="SPIELSTEUERUNG (Zustandsautomat): Setzt alle Werte je nach Schwierigkeit zurück "
            "und läuft dann Level für Level ab.\n"
            "- Normales Level: Es erscheinen Asteroiden (ab Level 2 auch UFOs), bis genug "
            "Gegner abgeschossen wurden. Je höher das Level, desto kürzer die Pause.\n"
            "- Jedes 5. Level: Bosskampf. Die Bühne wartet, bis der Boss den Status "
            "wieder auf 'spiel' setzt.\n"
            "Nach jedem Level gibt es Bonuspunkte (Level x 100).")

S.script(
    on_msg("Game Over"),
    stop_sounds(),
    play("Game Over"),
    wait(2),
    if_(gt(v("Punkte"), v("Highscore")), setv("Highscore", v("Punkte"))),
    broadcast("Game Over Anzeige"),
    wait(0.6),
    if_(gt(v("Punkte"), item(5, "Bestenliste_Punkte")),
        ask("Neuer Eintrag in der Bestenliste! Wie heißt du?"),
        setv("Name", answer()),
        if_(eq(v("Name"), ""), setv("Name", "Anonym")),
        call("In Bestenliste eintragen: %s mit %s Punkten", v("Name"), v("Punkte"))),
    call("Bestenliste anzeigen"),
    show_list("Bestenliste"),
    broadcast("Nochmal anbieten"),
    comment="GAME OVER: Highscore aktualisieren, bei genug Punkten nach dem Namen fragen "
            "und in die Top-5-Bestenliste eintragen.")

S.proc("In Bestenliste eintragen: %s mit %s Punkten", ["name", "punkte"], [
    setv("Position", 1),
    until(or_(gt(v("Position"), llen("Bestenliste_Punkte")),
              gt(arg("punkte"), item(v("Position"), "Bestenliste_Punkte"))),
          chg("Position", 1)),
    insert(v("Position"), "Bestenliste_Punkte", arg("punkte")),
    insert(v("Position"), "Bestenliste_Namen", arg("name")),
    until(lt(llen("Bestenliste_Punkte"), 6),
          delete(llen("Bestenliste_Punkte"), "Bestenliste_Punkte"),
          delete(llen("Bestenliste_Namen"), "Bestenliste_Namen")),
], comment="SORTIERTES EINFÜGEN (wie beim Insertion Sort): Wir laufen die absteigend "
           "sortierte Liste durch, bis wir einen kleineren Wert finden, und fügen dort ein. "
           "Danach wird die Liste auf 5 Einträge gekürzt. Namen und Punkte stehen in zwei "
           "parallelen Listen an derselben Position.")

S.proc("Bestenliste anzeigen", [], [
    clear("Bestenliste"),
    setv("i", 1),
    repeat(llen("Bestenliste_Namen"),
           push("Bestenliste", join(join(v("i"), ". "),
                                    join(item(v("i"), "Bestenliste_Namen"),
                                         join(": ", item(v("i"), "Bestenliste_Punkte"))))),
           chg("i", 1)),
], comment="Baut aus den beiden Listen eine lesbare Liste wie '1. Kometa: 3000'.")

S.script(
    on_msg("Bombe"),
    play("Grosse Explosion"),
    repeat(3, effect("BRIGHTNESS", 60), wait(0.05), effect("BRIGHTNESS", 0), wait(0.05)),
    comment="Bomben-Power-Up: Der Bildschirm blitzt dreimal auf.")

P.costume(S, "Menü", A.space_bg(True), 240, 180)
P.costume(S, "Weltraum", A.space_bg(False), 240, 180)

# ============================================================== Sterne (Parallax)
st = P.sprite("Sterne")
st.var("Geschw", 1)
st.script(on_flag(), hide(), repeat(45, clone()),
          comment="Erzeugt 45 Stern-Klone für einen bewegten Sternenhimmel.")
st.script(
    on_clone(),
    setv("Geschw", div(rnd(3, 30), 10)),
    goto_xy(rnd(-240, 240), rnd(-180, 180)),
    size(add(40, mul(v("Geschw"), 30))),
    effect("GHOST", sub(75, mul(v("Geschw"), 22))),
    show(), back(),
    forever(ifelse(laeuft(), [chy(mul(v("Geschw"), -1.6))], [chy(mul(v("Geschw"), -0.5))]),
            if_(lt(ypos(), -177), goto_xy(rnd(-240, 240), 180))),
    comment="PARALLAX-EFFEKT: Jeder Stern hat eine eigene Geschwindigkeit (lokale Variable). "
            "Schnelle Sterne sind größer und heller – das wirkt räumlich. Unten angekommen "
            "springt der Stern wieder nach oben.")
P.costume(st, "Stern", A.star(), 3, 3)

# ============================================================== HUD-Leiste
hud = P.sprite("HUD", x=0, y=160)
hud.script(on_flag(), hide(), goto_xy(0, 160))
hud.script(on_msg("Spielstart"), show(), front(),
           comment="Die Anzeigeleiste oben mit den Beschriftungen PUNKTE und LEVEL.")
hud.script(on_msg("Menü"), hide())
hud.script(on_msg("Game Over Anzeige"), hide())
P.costume(hud, "Leiste", A.hud_bar(), 240, 20)

# ============================================================== Asteroid
ast = P.sprite("Asteroid")
for n, val in [("Typ", 0), ("HP", 1), ("VX", 0), ("VY", 0), ("Drehung", 0), ("Sperre", 0),
               ("Punktwert", 10), ("Zählt", 0)]:
    ast.var(n, val)
def_explosion(ast)
def_powerup(ast)
ast.script(on_flag(), hide(), setv("Typ", 0),
           comment="Das Original bleibt unsichtbar. Es dient nur als Vorlage für Klone.")
ast.script(
    on_clone(),
    ifelse(eq(v("Typ"), 3), [
        setv("Typ", 1), setv("Zählt", 0), size(50), setv("HP", 1), setv("Punktwert", 10),
        setv("VX", div(rnd(-30, 30), 10)),
        setv("VY", mul(div(rnd(-35, -15), 10), v("Tempo"))),
    ], [
        goto_xy(rnd(-210, 210), 195),
        setv("Zählt", 1), setv("Sperre", 0),
        ifelse(lt(rnd(1, 100), add(30, mul(v("Level"), 3))),
               [setv("Typ", 2), size(100), setv("HP", add(3, floor(div(v("Level"), 4)))),
                setv("Punktwert", 25)],
               [setv("Typ", 1), size(55), setv("HP", 1), setv("Punktwert", 10)]),
        setv("VY", mul(-1, mul(add(div(rnd(15, 30), 10), mul(v("Level"), 0.2)), v("Tempo")))),
        setv("VX", div(rnd(-10, 10), 10)),
    ]),
    costume(rnd(1, 3)),
    setv("Drehung", rnd(-5, 5)),
    show(),
    until(or_(lt(ypos(), -175), not_(laeuft())),
          chx(v("VX")), chy(v("VY")), turn(v("Drehung")),
          if_(or_(and_(gt(xpos(), 225), gt(v("VX"), 0)), and_(lt(xpos(), -225), lt(v("VX"), 0))),
              setv("VX", mul(v("VX"), -1))),
          ifelse(gt(v("Sperre"), 0), [
              chg("Sperre", -1),
              if_(lt(v("Sperre"), 1), effect("BRIGHTNESS", 0)),
          ], [
              if_(touching("Laser"),
                  chg("HP", -1), setv("Sperre", 3), effect("BRIGHTNESS", 70),
                  ifelse(lt(v("HP"), 1), [call("Zerstören")], [play("Klonk")])),
          ]),
          if_(touching("Spieler"),
              broadcast("Spieler getroffen"),
              call(EXPLOSION, xpos(), ypos(), size_r()),
              delete_clone())),
    delete_clone(),
    comment="KLON-LOGIK: Typ 3 bedeutet 'Bruchstück eines großen Asteroiden' – er startet "
            "an der Position des zerstörten Asteroiden (Klone erben Position und lokale "
            "Variablen!). Sonst entsteht oben ein neuer Asteroid: groß (3+ Treffer, 25 Punkte) "
            "oder klein (1 Treffer, 10 Punkte).\n"
            "'Sperre' verhindert, dass ein Laser mehrfach trifft: nach einem Treffer ist der "
            "Asteroid 3 Bilder lang unverwundbar und blitzt hell auf.")
ast.proc("Zerstören", [], [
    chg("Punkte", mul(v("Punktwert"), v("Level"))),
    if_(eq(v("Zählt"), 1), chg("Gegner_übrig", -1)),
    call(EXPLOSION, xpos(), ypos(), mul(size_r(), 1.2)),
    if_(lt(rnd(1, 100), 10), call(POWERUP, xpos(), ypos(), rnd(1, 4))),
    broadcast("HUD"),
    if_(eq(v("Typ"), 2), setv("Typ", 3), repeat(2, clone())),
    delete_clone(),
], comment="Punkte vergeben (mehr in höheren Levels), Explosion zeigen, mit 10 % "
           "Wahrscheinlichkeit ein Power-Up fallen lassen. Große Asteroiden zerfallen in "
           "zwei Bruchstücke (Typ 3).")
ast.script(on_msg("Bombe"), if_(gt(v("Typ"), 0), setv("Typ", 1), call("Zerstören")),
           comment="Bombe: Jeder Asteroid-Klon (Typ > 0) wird sofort zerstört – ohne zu zerfallen.")
for i in range(3):
    P.costume(ast, "Stein%d" % (i + 1), A.asteroid(i * 17 + 5), 32, 32)
P.sound(ast, "Klonk", *A.SOUNDS["Klonk"])

# ============================================================== UFO
ufo = P.sprite("UFO", rotationStyle="don't rotate")
for n, val in [("HP", 3), ("Zeit", 0), ("Mitte", 0), ("Breite", 100), ("Sperre", 0),
               ("Schusstimer", 60)]:
    ufo.var(n, val)
def_explosion(ufo)
def_powerup(ufo)
def_schuss(ufo)
ufo.script(on_flag(), hide())
ufo.script(
    on_clone(),
    chg("UFO_Anzahl", 1),
    setv("HP", add(3, floor(div(v("Level"), 4)))),
    setv("Zeit", rnd(0, 120)), setv("Mitte", rnd(-80, 80)), setv("Breite", rnd(70, 140)),
    setv("Sperre", 0), setv("Schusstimer", rnd(40, 70)),
    goto_xy(v("Mitte"), 200), clearfx(), show(),
    until(or_(lt(v("HP"), 1), not_(laeuft())),
          chg("Zeit", 1),
          setx(add(v("Mitte"), mul(v("Breite"), sin(mul(v("Zeit"), 3))))),
          if_(gt(ypos(), 105), chy(-1.5)),
          if_(eq(mod(v("Zeit"), 8), 0), next_costume()),
          chg("Schusstimer", -1),
          if_(lt(v("Schusstimer"), 1),
              point_to("Spieler"),
              call(SCHUSS, xpos(), sub(ypos(), 14), add(direction(), rnd(-8, 8))),
              setv("Schusstimer", div(rnd(50, 90), v("Tempo"))),
              play("UFO-Schuss")),
          ifelse(gt(v("Sperre"), 0), [
              chg("Sperre", -1),
              if_(lt(v("Sperre"), 1), effect("BRIGHTNESS", 0)),
          ], [
              if_(touching("Laser"), chg("HP", -1), setv("Sperre", 3), effect("BRIGHTNESS", 70)),
          ]),
          if_(touching("Spieler"), broadcast("Spieler getroffen"), setv("HP", 0))),
    chg("UFO_Anzahl", -1),
    if_(laeuft(),
        chg("Punkte", mul(50, v("Level"))),
        chg("Gegner_übrig", -1),
        broadcast("HUD"),
        call(EXPLOSION, xpos(), ypos(), 130),
        if_(lt(rnd(1, 100), 35), call(POWERUP, xpos(), ypos(), rnd(1, 4)))),
    delete_clone(),
    comment="UFO: Fliegt eine Sinuskurve (x = Mitte + Breite * sin(Zeit)) und zielt mit "
            "'drehe dich zu Spieler' auf das Raumschiff. Die Richtung wird dann an den Schuss "
            "weitergegeben. Das UFO selbst dreht sich nicht mit (Drehtyp 'nicht drehen').")
ufo.script(on_msg("Bombe"), setv("HP", 0))
P.costume(ufo, "UFO1", A.ufo(0), 40, 24)
P.costume(ufo, "UFO2", A.ufo(1), 40, 24)
P.sound(ufo, "UFO-Schuss", *A.SOUNDS["UFO-Schuss"])

# ============================================================== Boss
boss = P.sprite("Boss", rotationStyle="don't rotate")
for n, val in [("Zeit", 0), ("Sperre", 0), ("Schusstimer", 50), ("Phase", 1), ("Winkel", 0)]:
    boss.var(n, val)
def_explosion(boss)
def_powerup(boss)
def_schuss(boss)
boss.script(on_flag(), hide())
boss.script(
    on_msg("Boss Start"),
    setv("Boss_HP_Max", add(30, mul(v("Level"), 8))),
    setv("Boss_HP", v("Boss_HP_Max")),
    setv("Phase", 1), setv("Zeit", 0), setv("Sperre", 0), setv("Schusstimer", 50),
    costume("Boss1"), clearfx(), goto_xy(0, 230), show(),
    broadcast("Bossbalken zeigen"),
    until(lt(ypos(), 66), chy(-2)),
    until(or_(lt(v("Boss_HP"), 1), not_(laeuft())),
          chg("Zeit", 1),
          setx(mul(160, sin(mul(v("Zeit"), mul(1.5, v("Phase")))))),
          sety(add(65, mul(10, sin(mul(v("Zeit"), 4))))),
          if_(and_(eq(v("Phase"), 1), lt(v("Boss_HP"), div(v("Boss_HP_Max"), 2))),
              setv("Phase", 2), costume("Boss2"), play("Alarm"), setv("Schusstimer", 15)),
          chg("Schusstimer", -1),
          if_(lt(v("Schusstimer"), 1),
              ifelse(eq(v("Phase"), 1), [
                  point_to("Spieler"),
                  setv("Winkel", sub(direction(), 15)),
                  repeat(3, call(SCHUSS, xpos(), sub(ypos(), 50), v("Winkel")), chg("Winkel", 15)),
                  setv("Schusstimer", div(50, v("Tempo"))),
              ], [
                  setv("Winkel", 120),
                  repeat(7, call(SCHUSS, xpos(), sub(ypos(), 50), v("Winkel")), chg("Winkel", 20)),
                  setv("Schusstimer", div(38, v("Tempo"))),
                  if_(eq(rnd(1, 3), 1), clone("Asteroid")),
              ]),
              play("Boss-Schuss")),
          ifelse(gt(v("Sperre"), 0), [
              chg("Sperre", -1),
              if_(lt(v("Sperre"), 1), effect("BRIGHTNESS", 0)),
          ], [
              if_(touching("Laser"), chg("Boss_HP", -1), setv("Sperre", 2), effect("BRIGHTNESS", 60)),
          ]),
          if_(touching("Spieler"), broadcast("Spieler getroffen"))),
    ifelse(laeuft(), [
        play("Grosse Explosion"),
        repeat(8, call(EXPLOSION, add(xpos(), rnd(-80, 80)), add(ypos(), rnd(-40, 40)), rnd(90, 170)),
               wait(0.12)),
        hide(),
        chg("Punkte", mul(v("Level"), 200)),
        broadcast("HUD"),
        call(POWERUP, xpos(), ypos(), 3),
        setv("Status", "spiel"),
    ], [hide()]),
    comment="BOSSKAMPF mit zwei Phasen:\n"
            "Phase 1: Der Boss schwebt hin und her und feuert eine gezielte 3er-Salve.\n"
            "Phase 2 (unter 50 % Leben): Er wird rot, schneller und schießt einen Fächer "
            "aus 7 Kugeln (Winkel 120° bis 240°). Zusätzlich fallen Asteroiden.\n"
            "Nach dem Sieg setzt der Boss den Status zurück auf 'spiel' – dadurch läuft die "
            "Spielsteuerung auf der Bühne weiter.")
P.costume(boss, "Boss1", A.boss(False), 100, 60)
P.costume(boss, "Boss2", A.boss(True), 100, 60)
P.sound(boss, "Alarm", *A.SOUNDS["Alarm"])
P.sound(boss, "Boss-Schuss", *A.SOUNDS["Boss-Schuss"])
P.sound(boss, "Grosse Explosion", *A.SOUNDS["Grosse Explosion"])

# ============================================================== Gegnerschuss
gs = P.sprite("Gegnerschuss")
gs.var("Geschw", 4)
gs.script(on_flag(), hide())
gs.script(
    on_clone(),
    goto_xy(item(1, "Schuss_Daten"), item(2, "Schuss_Daten")),
    point(item(3, "Schuss_Daten")),
    *pop3("Schuss_Daten"),
    setv("Geschw", mul(add(4, mul(v("Level"), 0.15)), v("Tempo"))),
    show(),
    until(or_(touching("_edge_"), not_(laeuft())),
          move(v("Geschw")),
          if_(touching("Spieler"), broadcast("Spieler getroffen"), delete_clone())),
    delete_clone(),
    comment="Nimmt x, y und Richtung aus der Warteschlange 'Schuss_Daten' und fliegt "
            "geradeaus, bis er den Rand oder das Raumschiff berührt.")
gs.script(on_msg("Bombe"), delete_clone())
P.costume(gs, "Kugel", A.bullet(), 9, 9)

# ============================================================== Power-Up
pu = P.sprite("PowerUp")
pu.var("Typ", 1)
pu.var("Zeit", 0)
pu.script(on_flag(), hide())
pu.script(
    on_clone(),
    goto_xy(item(1, "PowerUp_Daten"), item(2, "PowerUp_Daten")),
    setv("Typ", item(3, "PowerUp_Daten")),
    *pop3("PowerUp_Daten"),
    costume(v("Typ")), setv("Zeit", 0), size(90), show(),
    until(or_(lt(ypos(), -175), not_(laeuft())),
          chy(-1.4), chg("Zeit", 1),
          size(add(90, mul(10, sin(mul(v("Zeit"), 10))))),
          if_(touching("Spieler"),
              if_(eq(v("Typ"), 1), setv("Schild", 1)),
              if_(eq(v("Typ"), 2), setv("Dreifach", 300)),
              if_(eq(v("Typ"), 3),
                  ifelse(lt(v("Leben"), 5), [chg("Leben", 1)], [chg("Punkte", 500)])),
              if_(eq(v("Typ"), 4), broadcast("Bombe")),
              chg("Punkte", 50),
              broadcast("HUD"),
              broadcast("PowerUp eingesammelt"),
              delete_clone())),
    delete_clone(),
    comment="Power-Up fällt langsam und pulsiert (Größe folgt einer Sinuswelle). "
            "Beim Einsammeln wirkt es je nach Typ:\n1 Schild, 2 Dreifachschuss (300 Bilder "
            "= 10 Sekunden), 3 Extraleben (max. 5, sonst 500 Punkte), 4 Bombe.")
for k, n in enumerate(["Schild", "Dreifach", "Leben", "Bombe"]):
    P.costume(pu, n, A.powerup(k + 1), 20, 20)

# ============================================================== Laser
la = P.sprite("Laser")
la.script(on_flag(), hide())
la.script(
    on_clone(),
    goto_xy(item(1, "Laser_Daten"), item(2, "Laser_Daten")),
    point(item(3, "Laser_Daten")),
    *pop3("Laser_Daten"),
    show(),
    until(or_(gt(ypos(), 170), gt(xpos(), 232), lt(xpos(), -232), not_(laeuft())),
          move(15),
          if_(or_(touching("Asteroid"), touching("UFO"), touching("Boss")),
              wait(0),
              delete_clone())),
    delete_clone(),
    comment="LASERSTRAHL: Übernimmt Position und Richtung aus der Warteschlange.\n"
            "Trifft er ein Ziel, wartet er genau EIN Bild ('warte 0'), bevor er "
            "verschwindet. So hat der Gegner sicher Zeit, die Berührung zu bemerken.")
P.costume(la, "Strahl", A.laser(), 14, 4)

# ============================================================== Spieler
sp = P.sprite("Spieler")
for n, val in [("vx", 0), ("vy", 0), ("Nachladen", 0), ("Unverwundbar", 0), ("Animation", 0)]:
    sp.var(n, val)
def_explosion(sp)
sp.script(on_flag(), hide())
sp.script(on_msg("Menü"), hide())
sp.script(
    on_msg("Spieler Start"),
    goto_xy(0, -130), setv("vx", 0), setv("vy", 0), setv("Nachladen", 0),
    setv("Unverwundbar", 60), point(90), clearfx(), show(), front(),
    until(eq(v("Status"), "gameover"),
          call("Steuerung"),
          call("Schießen"),
          call("Aussehen aktualisieren")),
    comment="HAUPTSCHLEIFE DES SPIELERS: 30-mal pro Sekunde werden Steuerung, Schießen "
            "und Aussehen in eigenen Blöcken abgearbeitet. Zu Beginn ist das Schiff 2 "
            "Sekunden unverwundbar (60 Bilder).")
sp.proc("Steuerung", [], [
    if_(or_(key("right arrow"), key("d")), chg("vx", 1.3)),
    if_(or_(key("left arrow"), key("a")), chg("vx", -1.3)),
    if_(or_(key("up arrow"), key("w")), chg("vy", 1.1)),
    if_(or_(key("down arrow"), key("s")), chg("vy", -1.1)),
    setv("vx", mul(v("vx"), 0.86)),
    setv("vy", mul(v("vy"), 0.86)),
    chx(v("vx")), chy(v("vy")),
    if_(gt(xpos(), 215), setx(215), setv("vx", 0)),
    if_(lt(xpos(), -215), setx(-215), setv("vx", 0)),
    if_(gt(ypos(), 40), sety(40), setv("vy", 0)),
    if_(lt(ypos(), -155), sety(-155), setv("vy", 0)),
    point(add(90, mul(v("vx"), 2.5))),
], comment="PHYSIK MIT TRÄGHEIT: Tasten ändern nicht direkt die Position, sondern die "
           "Geschwindigkeit (vx, vy). Jedes Bild wird die Geschwindigkeit mit 0,86 "
           "multipliziert (Reibung) – so gleitet das Schiff weich aus. Beim seitlichen "
           "Fliegen neigt es sich leicht in Flugrichtung.")
sp.proc("Laser abfeuern bei x: %s y: %s Richtung: %s", ["x", "y", "richtung"], [
    push("Laser_Daten", arg("x")),
    push("Laser_Daten", arg("y")),
    push("Laser_Daten", arg("richtung")),
    clone("Laser"),
], comment="Legt die Startwerte in die Warteschlange 'Laser_Daten' und erzeugt einen Laser-Klon.")
FIRE = "Laser abfeuern bei x: %s y: %s Richtung: %s"
sp.proc("Schießen", [], [
    if_(gt(v("Nachladen"), 0), chg("Nachladen", -1)),
    if_(and_(key("space"), lt(v("Nachladen"), 1)),
        ifelse(gt(v("Dreifach"), 0), [
            call(FIRE, sub(xpos(), 14), add(ypos(), 8), -12),
            call(FIRE, xpos(), add(ypos(), 22), 0),
            call(FIRE, add(xpos(), 14), add(ypos(), 8), 12),
            setv("Nachladen", 8),
        ], [
            call(FIRE, xpos(), add(ypos(), 22), 0),
            setv("Nachladen", 6),
        ]),
        play("Laser")),
], comment="Solange die Leertaste gedrückt ist, wird gefeuert – aber nur, wenn der "
           "Nachlade-Zähler abgelaufen ist (sonst gäbe es 30 Schüsse pro Sekunde). "
           "Mit Power-Up werden drei Strahlen im Fächer abgefeuert.")
sp.proc("Aussehen aktualisieren", [], [
    chg("Animation", 1),
    ifelse(eq(v("Schild"), 1),
           [costume(join("Schild", add(mod(floor(div(v("Animation"), 3)), 2), 1)))],
           [costume(join("Schiff", add(mod(floor(div(v("Animation"), 3)), 2), 1)))]),
    ifelse(gt(v("Unverwundbar"), 0), [
        chg("Unverwundbar", -1),
        ifelse(lt(mod(v("Unverwundbar"), 6), 3), [effect("GHOST", 75)], [effect("GHOST", 0)]),
    ], [effect("GHOST", 0)]),
    if_(gt(v("Dreifach"), 0), chg("Dreifach", -1)),
], comment="Animiert die Triebwerksflamme (Kostümwechsel alle 3 Bilder), zeigt den Schild "
           "und lässt das Schiff blinken, solange es unverwundbar ist.")
sp.script(
    on_msg("Spieler getroffen"),
    if_(and_(laeuft(), lt(v("Unverwundbar"), 1)),
        ifelse(eq(v("Schild"), 1), [
            setv("Schild", 0), setv("Unverwundbar", 45), play("Schild weg"),
        ], [
            chg("Leben", -1), setv("Dreifach", 0), setv("Unverwundbar", 90),
            play("Treffer"),
            call(EXPLOSION, xpos(), ypos(), 90),
            broadcast("HUD"),
            if_(lt(v("Leben"), 1),
                setv("Status", "gameover"),
                call(EXPLOSION, xpos(), ypos(), 220),
                hide(),
                broadcast("Game Over")),
        ])),
    comment="TREFFER-BEHANDLUNG an EINER zentralen Stelle: Alle Gegner senden nur die "
            "Nachricht 'Spieler getroffen'. Hier wird entschieden, ob der Schild den Treffer "
            "abfängt oder ein Leben verloren geht. Danach ist das Schiff kurz unverwundbar.")
sp.script(on_msg("PowerUp eingesammelt"), play("PowerUp"))
P.costume(sp, "Schiff1", A.ship(1, False), 32, 32)
P.costume(sp, "Schiff2", A.ship(2, False), 32, 32)
P.costume(sp, "Schild1", A.ship(1, True), 32, 32)
P.costume(sp, "Schild2", A.ship(2, True), 32, 32)
for n in ["Laser", "Treffer", "PowerUp", "Schild weg"]:
    P.sound(sp, n, *A.SOUNDS[n])

# ============================================================== Explosion
ex = P.sprite("Explosion")
ex.script(on_flag(), hide())
ex.script(
    on_clone(),
    goto_xy(item(1, "Explosions_Daten"), item(2, "Explosions_Daten")),
    size(item(3, "Explosions_Daten")),
    *pop3("Explosions_Daten"),
    costume("Expl1"), point(rnd(0, 359)), show(), front(),
    play("Explosion"),
    repeat(5, wait(0.04), next_costume()),
    wait(0.04),
    delete_clone(),
    comment="Spielt eine Explosions-Animation aus 6 Kostümen ab und löscht sich danach.")
for k in range(6):
    P.costume(ex, "Expl%d" % (k + 1), A.explosion(k), 60, 60)
P.sound(ex, "Explosion", *A.SOUNDS["Explosion"])

# ============================================================== Bossbalken
bb = P.sprite("Bossbalken")
bb.script(on_flag(), hide())
bb.script(
    on_msg("Bossbalken zeigen"),
    goto_xy(0, 134), show(), front(),
    until(not_(eq(v("Status"), "boss")),
          costume(join("Balken", round_(div(mul(v("Boss_HP"), 20), v("Boss_HP_Max")))))),
    hide(),
    comment="Lebensbalken: 21 Kostüme (Balken0 bis Balken20). Der Anteil der restlichen "
            "Lebenspunkte wird auf 0–20 umgerechnet und das passende Kostüm gewählt.")
for k in range(21):
    P.costume(bb, "Balken%d" % k, A.boss_bar(k), 130, 14)

# ============================================================== Ziffern
zf = P.sprite("Ziffern")
for n, val in [("Gruppe", ""), ("Klon", 0), ("i", 1), ("Startx", 0), ("Abstand", 24)]:
    zf.var(n, val)
TEXT = "Zahl zeichnen: %s bei x: %s y: %s Größe: %s Gruppe: %s zentriert: %s"
zf.proc(TEXT, ["zahl", "x", "y", "größe", "gruppe", "zentriert"], [
    front(),
    setv("Gruppe", arg("gruppe")),
    setv("Klon", 1),
    size(arg("größe")),
    setv("Abstand", div(mul(24, arg("größe")), 100)),
    ifelse(eq(arg("zentriert"), 1),
           [setv("Startx", sub(arg("x"), div(mul(sub(length(arg("zahl")), 1), v("Abstand")), 2)))],
           [setv("Startx", arg("x"))]),
    setv("i", 1),
    repeat(length(arg("zahl")),
           costume(join("Z", letter(v("i"), arg("zahl")))),
           goto_xy(add(v("Startx"), mul(sub(v("i"), 1), v("Abstand"))), arg("y")),
           clone(),
           chg("i", 1)),
    setv("Klon", 0),
], comment="ZAHLEN OHNE MALSTIFT: Für jede Ziffer wird das passende Kostüm (Z0–Z9) gewählt "
           "und ein Klon an der richtigen Stelle abgesetzt – wie ein Stempel.\n"
           "Wichtig: Vor dem Klonen wird 'Klon' auf 1 und 'Gruppe' gesetzt. Klone erben "
           "diese lokalen Variablen und wissen so, dass sie Klone sind und wozu sie gehören.")
zf.proc("Herzen zeichnen", [], [
    front(),
    setv("Gruppe", "hud"), setv("Klon", 1),
    costume("Herz"), size(85),
    goto_xy(-226, 126),
    repeat(v("Leben"), clone(), chx(24)),
    setv("Klon", 0),
], comment="Ein Herz pro Leben.")
zf.script(on_flag(), hide(), setv("Klon", 0))
zf.script(on_clone(), show())
zf.script(
    on_msg("HUD"),
    ifelse(eq(v("Klon"), 1), [
        if_(eq(v("Gruppe"), "hud"), delete_clone()),
    ], [
        call(TEXT, v("Punkte"), -104, 160, 70, "hud", 0),
        call(TEXT, v("Level"), 210, 160, 70, "hud", 0),
        call("Herzen zeichnen"),
    ]),
    comment="HUD neu zeichnen: Alte HUD-Klone löschen sich selbst, das Original zeichnet "
            "Punkte, Level und Herzen neu. (Neue Klone empfangen die Nachricht nicht mehr.)")
zf.script(
    on_msg("Level Banner"),
    if_(eq(v("Klon"), 0), call(TEXT, v("Level"), 100, 20, 250, "banner", 0)))
zf.script(on_msg("Banner weg"), if_(and_(eq(v("Klon"), 1), eq(v("Gruppe"), "banner")), delete_clone()))
zf.script(on_msg("Game Over Anzeige"), if_(and_(eq(v("Klon"), 1), eq(v("Gruppe"), "hud")), delete_clone()))
zf.script(on_msg("Spielstart"), if_(and_(eq(v("Klon"), 1), eq(v("Gruppe"), "banner")), delete_clone()))
zf.script(
    on_msg("Game Over Anzeige"),
    if_(eq(v("Klon"), 0), call(TEXT, v("Punkte"), 0, 82, 130, "banner", 1)))
zf.script(
    on_msg("Menü"),
    ifelse(eq(v("Klon"), 1), [delete_clone()], [
        front(), setv("Gruppe", "banner"), setv("Klon", 1),
        costume("Rekord"), size(100), goto_xy(-52, -160), clone(),
        setv("Klon", 0),
        call(TEXT, v("Highscore"), 22, -160, 70, "banner", 0),
    ]),
    comment="Im Menü wird der bisherige Rekord unten angezeigt.")
for d in "0123456789":
    P.costume(zf, "Z" + d, A.digit(d), 10, 14)
P.costume(zf, "Herz", A.heart(), 11, 10)
svg_, cx, cy = A.label("REKORD", 3, "#ffd23a")
P.costume(zf, "Rekord", svg_, cx, cy)

# ============================================================== Anzeige (Titel/Banner)
an = P.sprite("Anzeige", visible=True, y=100)
an.var("Zeit", 0)
an.script(on_flag(), hide())
an.script(
    on_msg("Menü"),
    costume("Titel"), clearfx(), goto_xy(0, 100), show(), front(), setv("Zeit", 0),
    until(not_(eq(v("Status"), "menü")),
          chg("Zeit", 1), sety(add(100, mul(4, sin(mul(v("Zeit"), 6)))))),
    comment="Der Titel schwebt im Menü sanft auf und ab (Sinusbewegung).")
an.script(on_msg("Spielstart"), hide())
an.script(
    on_msg("Level Banner"),
    costume("Level"), goto_xy(-55, 20), effect("GHOST", 100), show(), front(),
    repeat(10, cheffect("GHOST", -10)),
    wait(1.2),
    repeat(10, cheffect("GHOST", 10)),
    hide(), clearfx(),
    broadcast("Banner weg"),
    comment="'LEVEL x' ein- und ausblenden. Die Bühne wartet mit 'sende ... und warte', "
            "bis dieses Skript fertig ist.")
an.script(
    on_msg("Boss Warnung"),
    costume("Boss"), clearfx(), goto_xy(0, 20), front(),
    repeat(5, show(), wait(0.3), hide(), wait(0.15)))
an.script(on_msg("Game Over Anzeige"), costume("GameOver"), clearfx(), goto_xy(0, 138), show(), front())
s_, cx, cy = A.title()
P.costume(an, "Titel", s_, cx, cy)
s_, cx, cy = A.big_text([("LEVEL", 8, "#7fe8ff", "#0c1a4d", 0)], 240)
P.costume(an, "Level", s_, cx, cy)
s_, cx, cy = A.big_text([("WARNUNG", 4, "#ffd23a", "#3a1a00", 14),
                         ("BOSS!", 12, "#ff3b4f", "#3a0010", 0)], 360)
P.costume(an, "Boss", s_, cx, cy)
s_, cx, cy = A.big_text([("GAME OVER", 6, "#ff4f6b", "#3a0010", 9),
                         ("DEINE PUNKTE", 2, "#d6dcff", "#0c1a4d", 0)], 340)
P.costume(an, "GameOver", s_, cx, cy)

# ============================================================== Knöpfe
kn = P.sprite("Startknopf", visible=True, y=-12)
hover_script(kn)
kn.script(on_msg("Menü"), costume("Start"), goto_xy(0, -12), show(), front())
kn.script(on_msg("Nochmal anbieten"), costume("Menü"), goto_xy(0, -152), show(), front())
kn.script(on_msg("Spielstart"), hide())
kn.script(
    on_click(),
    play("Klick"),
    ifelse(eq(v("Status"), "menü"), [hide(), broadcast("Spielstart")], [
        if_(eq(v("Status"), "gameover"), hide(), setv("Status", "menü"), broadcast("Menü")),
    ]),
    comment="Im Menü startet der Knopf das Spiel, nach Game Over führt er zurück ins Menü.")
s_, cx, cy = A.button("SPIEL STARTEN", "#39e07a", "#128a3e")
P.costume(kn, "Start", s_, cx, cy)
s_, cx, cy = A.button("ZUM MENÜ", "#a35cff", "#5a1fb0")
P.costume(kn, "Menü", s_, cx, cy)
P.sound(kn, "Klick", *A.SOUNDS["Klick"])

mk = P.sprite("Modusknopf", visible=True, y=-64, currentCostume=1)
hover_script(mk)
mk.script(on_msg("Menü"), costume(v("Schwierigkeit")), goto_xy(0, -64), show(), front())
mk.script(on_msg("Spielstart"), hide())
mk.script(
    on_click(),
    if_(eq(v("Status"), "menü"),
        setv("Schwierigkeit", add(mod(v("Schwierigkeit"), 3), 1)),
        costume(v("Schwierigkeit")),
        play("Klick")),
    comment="Schaltet reihum durch 1 → 2 → 3 → 1 (Rechnung mit Modulo). Das Kostüm zeigt "
            "den gewählten Modus.\nLeicht: 5 Leben, langsam. Normal: 3 Leben. Schwer: 2 "
            "Leben, 30 % schneller.")
for name, c1, c2 in [("LEICHT", "#5fe08a", "#1f8f4a"), ("NORMAL", "#ffc94d", "#c77a00"),
                     ("SCHWER", "#ff6b6b", "#b01f2f")]:
    s_, cx, cy = A.button("MODUS: " + name, c1, c2)
    P.costume(mk, name.capitalize(), s_, cx, cy)
P.sound(mk, "Klick", *A.SOUNDS["Klick"])

hk = P.sprite("Hilfeknopf", visible=True, y=-116)
hover_script(hk)
hk.script(on_msg("Menü"), goto_xy(0, -116), show(), front())
hk.script(on_msg("Spielstart"), hide())
hk.script(on_click(), if_(eq(v("Status"), "menü"), play("Klick"), broadcast("Hilfe zeigen")))
s_, cx, cy = A.button("ANLEITUNG", "#4db8ff", "#1f5fc2")
P.costume(hk, "Anleitung", s_, cx, cy)
P.sound(hk, "Klick", *A.SOUNDS["Klick"])

hi = P.sprite("Hilfe")
hi.script(on_flag(), hide())
hi.script(on_msg("Hilfe zeigen"), goto_xy(0, 0), show(), front())
hi.script(on_click(), hide(), play("Klick"))
hi.script(on_msg("Spielstart"), hide())
hi.script(on_msg("Menü"), hide())
s_, cx, cy = A.help_panel()
P.costume(hi, "Anleitung", s_, cx, cy)
P.sound(hi, "Klick", *A.SOUNDS["Klick"])

# ============================================================== Bühnenklänge
for n in ["Musik", "Alarm", "Level geschafft", "Game Over", "Klick", "Grosse Explosion"]:
    P.sound(S, n, *A.SOUNDS[n])

P.list_monitor("Bestenliste", 105, 124, 270, 170)

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Astro-Abwehr.sb3")
    proj = P.save(out)
    n_blocks = sum(len([b for b in t["blocks"].values() if not b["shadow"]]) for t in proj["targets"])
    print("Gespeichert: %s  (%d Figuren, %d Blöcke, %.0f KB)" % (
        os.path.normpath(out), len(proj["targets"]) - 1, n_blocks, os.path.getsize(out) / 1024))
