"""Erzeugt alle Grafiken (SVG) und Klänge (WAV) für Astro-Abwehr."""
import hashlib
import io
import math
import random
import struct
import wave

# ================================================================ Pixel-Schrift
GLYPHS = r"""
A .###. #...# #...# ##### #...# #...# #...#
B ####. #...# #...# ####. #...# #...# ####.
C .###. #...# #.... #.... #.... #...# .###.
D ####. #...# #...# #...# #...# #...# ####.
E ##### #.... #.... ####. #.... #.... #####
F ##### #.... #.... ####. #.... #.... #....
G .###. #...# #.... #.### #...# #...# .####
H #...# #...# #...# ##### #...# #...# #...#
I .###. ..#.. ..#.. ..#.. ..#.. ..#.. .###.
J ..### ...#. ...#. ...#. ...#. #..#. .##..
K #...# #..#. #.#.. ##... #.#.. #..#. #...#
L #.... #.... #.... #.... #.... #.... #####
M #...# ##.## #.#.# #.#.# #...# #...# #...#
N #...# #...# ##..# #.#.# #..## #...# #...#
O .###. #...# #...# #...# #...# #...# .###.
P ####. #...# #...# ####. #.... #.... #....
Q .###. #...# #...# #...# #.#.# #..#. .##.#
R ####. #...# #...# ####. #.#.. #..#. #...#
S .#### #.... #.... .###. ....# ....# ####.
T ##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..
U #...# #...# #...# #...# #...# #...# .###.
V #...# #...# #...# #...# #...# .#.#. ..#..
W #...# #...# #...# #.#.# #.#.# #.#.# .#.#.
X #...# #...# .#.#. ..#.. .#.#. #...# #...#
Y #...# #...# .#.#. ..#.. ..#.. ..#.. ..#..
Z ##### ....# ...#. ..#.. .#... #.... #####
Ä .#.#. ..... .###. #...# ##### #...# #...#
Ö .#.#. ..... .###. #...# #...# #...# .###.
Ü .#.#. ..... #...# #...# #...# #...# .###.
0 .###. #...# #..## #.#.# ##..# #...# .###.
1 ..#.. .##.. ..#.. ..#.. ..#.. ..#.. .###.
2 .###. #...# ....# ...#. ..#.. .#... #####
3 ##### ...#. ..#.. ...#. ....# #...# .###.
4 ...#. ..##. .#.#. #..#. ##### ...#. ...#.
5 ##### #.... ####. ....# ....# #...# .###.
6 ..##. .#... #.... ####. #...# #...# .###.
7 ##### ....# ...#. ..#.. .#... .#... .#...
8 .###. #...# #...# .###. #...# #...# .###.
9 .###. #...# #...# .#### ....# ...#. .##..
_ ..... ..... ..... ..... ..... ..... .....
. ..... ..... ..... ..... ..... .##.. .##..
: ..... .##.. .##.. ..... .##.. .##.. .....
! ..#.. ..#.. ..#.. ..#.. ..#.. ..... ..#..
- ..... ..... ..... .###. ..... ..... .....
/ ..... ....# ...#. ..#.. .#... #.... .....
= ..... ..... ##### ..... ##### ..... .....
+ ..... ..#.. ..#.. ##### ..#.. ..#.. .....
? .###. #...# ....# ...#. ..#.. ..... ..#..
, ..... ..... ..... ..... .##.. ..#.. .#...
( ...#. ..#.. .#... .#... .#... ..#.. ...#.
) .#... ..#.. ...#. ...#. ...#. ..#.. .#...
"""

FONT = {}
for _line in GLYPHS.strip().split("\n"):
    _k, *_rows = _line.split()
    assert len(_rows) == 7 and all(len(r) == 5 for r in _rows), _k
    FONT[" " if _k == "_" else _k] = "".join(_rows)


def text_width(text, p):
    return len(text) * 6 * p - p


def pixel_text(text, x0, y0, p, fill, shadow=None, sh=None):
    """Zeichnet Text aus Rechtecken. Gibt SVG-Elemente zurück."""
    text = text.upper()
    out = []
    layers = []
    if shadow:
        d = sh if sh is not None else max(1, p / 2)
        layers.append((d, shadow))
    layers.append((0, fill))
    for off, col in layers:
        parts = []
        for ci, ch in enumerate(text):
            g = FONT[ch]
            gx = x0 + ci * 6 * p
            for r in range(7):
                row = g[r * 5:(r + 1) * 5]
                c = 0
                while c < 5:
                    if row[c] == "#":
                        s = c
                        while c < 5 and row[c] == "#":
                            c += 1
                        parts.append("M%g %gh%gv%gh%gz" % (gx + s * p + off, y0 + r * p + off,
                                                          (c - s) * p, p, -(c - s) * p))
                    else:
                        c += 1
        if parts:
            op = ""
            if len(col) == 9 and col.startswith("#"):
                col, op = col[:7], ' fill-opacity="%.2f"' % (int(col[7:], 16) / 255)
            out.append('<path d="%s" fill="%s"%s/>' % ("".join(parts), col, op))
    return "".join(out)


def svg(w, h, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="%g" height="%g" '
            'viewBox="0 0 %g %g">%s</svg>' % (w, h, w, h, body))


def lin_grad(gid, c1, c2, y1=0, y2=1):
    return ('<linearGradient id="%s" x1="0" y1="%g" x2="0" y2="%g"><stop offset="0" stop-color="%s"/>'
            '<stop offset="1" stop-color="%s"/></linearGradient>' % (gid, y1, y2, c1, c2))


# ================================================================ Figuren
def ship(flame, shield):
    fl = 62 if flame == 2 else 56
    body = (
        '<path d="M26 49 L32 %d L38 49 Z" fill="#ff8a00"/>' % fl +
        '<path d="M29 49 L32 %d L35 49 Z" fill="#fff3a0"/>' % (fl - 5) +
        '<path d="M32 7 L38 23 L52 37 L53 46 L40 44 L38 49 L26 49 L24 44 L11 46 L12 37 L26 23 Z" '
        'fill="#cfd9e8" stroke="#34405a" stroke-width="1.6" stroke-linejoin="round"/>'
        '<path d="M32 8 L36 22 L36 47 L28 47 L28 22 Z" fill="#f4f7fb"/>'
        '<path d="M17 40 L25 34 L25 42 Z M47 40 L39 34 L39 42 Z" fill="#8196b8"/>'
        '<rect x="11" y="36" width="3" height="10" rx="1" fill="#ff4b5c"/>'
        '<rect x="50" y="36" width="3" height="10" rx="1" fill="#ff4b5c"/>'
        '<ellipse cx="32" cy="27" rx="3.6" ry="6.8" fill="#3cc8ff" stroke="#0d5c85"/>'
        '<ellipse cx="31" cy="25" rx="1.2" ry="2.5" fill="#dff6ff"/>'
    )
    if shield:
        body += ('<circle cx="32" cy="32" r="30" fill="#4fd8ff" fill-opacity="0.18" stroke="#8ff0ff" '
                 'stroke-width="2.2" stroke-opacity="0.9"/>'
                 '<path d="M14 18 A24 24 0 0 1 30 8" fill="none" stroke="#ffffff" stroke-width="2" '
                 'stroke-linecap="round" stroke-opacity="0.7"/>')
    return svg(64, 64, body)


def laser():
    return svg(28, 8, '<rect x="0" y="0" width="28" height="8" rx="4" fill="#27e3ff" fill-opacity="0.45"/>'
                      '<rect x="2" y="2" width="24" height="4" rx="2" fill="#bdfaff"/>')


def asteroid(seed):
    rng = random.Random(seed)
    pts = []
    n = 11
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.15, 0.15)
        r = rng.uniform(22, 30)
        pts.append((32 + r * math.cos(a), 32 + r * math.sin(a)))
    poly = " ".join("%.1f,%.1f" % p for p in pts)
    hi = " ".join("%.1f,%.1f" % (32 + (x - 32) * 0.78 - 2, 32 + (y - 32) * 0.78 - 2) for x, y in pts)
    body = ('<polygon points="%s" fill="#7d736a" stroke="#3f3832" stroke-width="2.2" stroke-linejoin="round"/>'
            '<polygon points="%s" fill="#968b80"/>' % (poly, hi))
    for _ in range(4):
        cx, cy, r = rng.uniform(20, 44), rng.uniform(20, 44), rng.uniform(3, 6.5)
        body += ('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#6a6158"/>'
                 '<path d="M%.1f %.1f a%.1f %.1f 0 0 0 %.1f 0" fill="none" stroke="#b3a89c" stroke-width="1.2"/>'
                 % (cx, cy, r, cx - r, cy + 0.5, r, r, 2 * r))
    return svg(64, 64, body)


def ufo(k):
    lights = ""
    for i, x in enumerate((14, 27, 40, 53, 66)):
        col = "#ff3b3b" if (i + k) % 2 == 0 else "#ffe14d"
        lights += '<circle cx="%d" cy="29" r="3" fill="%s"/>' % (x, col)
    return svg(80, 44, (
        '<ellipse cx="40" cy="17" rx="15" ry="13" fill="#8ff7ff" fill-opacity="0.55" stroke="#2aa7b8" stroke-width="1.5"/>'
        '<circle cx="40" cy="18" r="6.5" fill="#6be36b"/>'
        '<circle cx="37.5" cy="17" r="1.6" fill="#10240f"/><circle cx="42.5" cy="17" r="1.6" fill="#10240f"/>'
        '<ellipse cx="40" cy="27" rx="38" ry="11" fill="#8f9aad" stroke="#343c4c" stroke-width="2"/>'
        '<ellipse cx="40" cy="24" rx="30" ry="5" fill="#c7cfdb"/>' + lights +
        '<path d="M26 37 L22 43 M54 37 L58 43" stroke="#343c4c" stroke-width="2.5" stroke-linecap="round"/>'))


def bullet():
    return svg(18, 18, '<circle cx="9" cy="9" r="8.5" fill="#ff3d2e" fill-opacity="0.35"/>'
                       '<circle cx="9" cy="9" r="5.2" fill="#ff7a2e"/><circle cx="9" cy="9" r="2.6" fill="#fff3c4"/>')


def boss(angry):
    hull, plate, dark = ("#6b1f2a", "#a8323f", "#2b0a10") if angry else ("#4b2a6b", "#6f40a0", "#1d0d2e")
    glow = ('<ellipse cx="100" cy="62" rx="36" ry="24" fill="#ff2a4f" fill-opacity="0.35"/>' if angry else "")
    return svg(200, 120, (
        '<path d="M12 48 L0 74 L30 82 Z M188 48 L200 74 L170 82 Z" fill="%s" stroke="%s" stroke-width="2"/>' % (plate, dark) +
        '<rect x="32" y="84" width="12" height="26" rx="2" fill="#2d2d3a"/>'
        '<rect x="156" y="84" width="12" height="26" rx="2" fill="#2d2d3a"/>'
        '<rect x="94" y="96" width="12" height="22" rx="2" fill="#2d2d3a"/>'
        '<path d="M10 50 L40 18 L160 18 L190 50 L170 86 L130 102 L70 102 L30 86 Z" fill="%s" '
        'stroke="%s" stroke-width="3" stroke-linejoin="round"/>' % (hull, dark) +
        '<path d="M50 24 L150 24 L166 44 L34 44 Z" fill="%s"/>' % plate +
        ''.join('<rect x="%d" y="30" width="10" height="5" rx="1" fill="#ff9d2e"/>' % x for x in (60, 80, 110, 130)) +
        glow +
        '<ellipse cx="100" cy="62" rx="27" ry="17" fill="#12060a" stroke="%s" stroke-width="2"/>' % ("#ffdf3a" if angry else "#b28bff") +
        '<circle cx="100" cy="62" r="11" fill="#ff2a4f"/><circle cx="100" cy="62" r="4.5" fill="#fff"/>'
        '<path d="M40 70 L60 76 M160 70 L140 76" stroke="#ff9d2e" stroke-width="3" stroke-linecap="round"/>'))


def boss_bar(k):
    body = pixel_text("BOSS", 0, 4, 3, "#ff4f6b", "#3a0a14")
    body += '<rect x="76" y="3" width="182" height="22" rx="4" fill="#220b12" stroke="#ffffff" stroke-width="2"/>'
    if k > 0:
        t = k / 20
        r, g, b = 255, int(45 + 165 * t), int(45 + 20 * t)
        body += '<rect x="80" y="7" width="%.1f" height="14" rx="2" fill="rgb(%d,%d,%d)"/>' % (174 * t, r, g, b)
        body += '<rect x="80" y="7" width="%.1f" height="5" rx="2" fill="#ffffff" fill-opacity="0.35"/>' % (174 * t)
    return svg(260, 28, body)


HEART = "M11 18 C3 12 0 9 0 5.5 C0 2.5 2.4 0 5.4 0 C7.6 0 9.6 1.3 11 3.2 C12.4 1.3 14.4 0 16.6 0 C19.6 0 22 2.5 22 5.5 C22 9 19 12 11 18 Z"


def powerup(kind):
    col = {1: "#37a9ff", 2: "#ffc21f", 3: "#3ddc6b", 4: "#ff4040"}[kind]
    body = ('<circle cx="20" cy="20" r="18.5" fill="%s" fill-opacity="0.25" stroke="%s" stroke-width="2.5"/>'
            '<circle cx="20" cy="20" r="13" fill="%s"/>'
            '<ellipse cx="15.5" cy="14" rx="5" ry="3" fill="#ffffff" fill-opacity="0.45"/>' % (col, col, col))
    if kind == 3:
        body += '<path d="%s" transform="translate(12.3 12.8) scale(0.7)" fill="#ffffff"/>' % HEART
    else:
        body += pixel_text({1: "S", 2: "3", 4: "B"}[kind], 12.5, 9.5, 3, "#ffffff", "#00000055", 1)
    return svg(40, 40, body)


def explosion(k):
    t = k / 5
    R = 16 + 40 * t
    pts = []
    for i in range(20):
        a = math.pi * i / 10
        r = R if i % 2 == 0 else R * 0.62
        pts.append("%.1f,%.1f" % (60 + r * math.cos(a), 60 + r * math.sin(a)))
    op = 1 - 0.75 * t
    body = '<polygon points="%s" fill="#ff6a1c" fill-opacity="%.2f"/>' % (" ".join(pts), op)
    body += '<circle cx="60" cy="60" r="%.1f" fill="#ffd23a" fill-opacity="%.2f"/>' % (R * 0.58 * (1 - 0.4 * t), op)
    if k < 4:
        body += '<circle cx="60" cy="60" r="%.1f" fill="#ffffff"/>' % (R * 0.3 * (1 - t))
    if k >= 2:
        body += ('<circle cx="60" cy="60" r="%.1f" fill="none" stroke="#9aa0ad" stroke-width="%.1f" '
                 'stroke-opacity="%.2f"/>' % (R * 1.02, 6 - 4 * t, 0.7 - 0.5 * t))
    return svg(120, 120, body)


def star():
    return svg(6, 6, '<circle cx="3" cy="3" r="2.2" fill="#ffffff"/>')


def digit(ch):
    return svg(22, 30, pixel_text(ch, 0, 0, 4, "#ffffff", "#1b2440", 2))


def heart():
    return svg(22, 20, '<path d="%s" fill="#ff3d5a" stroke="#6b0a1a" stroke-width="1.2"/>'
                       '<ellipse cx="6" cy="5" rx="2.5" ry="1.8" fill="#ffffff" fill-opacity="0.6"/>' % HEART)


def label(text, p, col, shadow="#1b2440"):
    w = text_width(text, p)
    return svg(w + p, 7 * p + p, pixel_text(text, 0, 0, p, col, shadow, p / 2)), (w + p) / 2, (8 * p) / 2


def hud_bar():
    body = ('<rect width="480" height="40" fill="#050a1a" fill-opacity="0.6"/>'
            '<rect y="38" width="480" height="2" fill="#35d0ff" fill-opacity="0.7"/>')
    body += pixel_text("PUNKTE", 8, 9.5, 3, "#7fe8ff", "#06283a", 1.5)
    body += pixel_text("LEVEL", 346, 9.5, 3, "#7fe8ff", "#06283a", 1.5)
    return svg(480, 40, body)


def title():
    w = 380
    body = "<defs>%s%s</defs>" % (lin_grad("tg1", "#fff27a", "#ff7b1c"), lin_grad("tg2", "#8ff7ff", "#3a7bff"))
    t1, t2, t3 = "ASTRO", "ABWEHR", "EIN WELTRAUM-ABENTEUER"
    body += pixel_text(t1, (w - text_width(t1, 10)) / 2, 0, 10, "url(#tg1)", "#3a0f4d", 4)
    body += pixel_text(t2, (w - text_width(t2, 7)) / 2, 82, 7, "url(#tg2)", "#0c1a4d", 3.5)
    body += pixel_text(t3, (w - text_width(t3, 2)) / 2, 142, 2, "#d6dcff", "#0c1a4d", 1)
    return svg(w, 157, body), w / 2, 78.5


def big_text(lines, width):
    """lines: (text, p, color, shadow, gap_after)"""
    body, y = "", 0
    for text, p, col, sh, gap in lines:
        body += pixel_text(text, (width - text_width(text, p)) / 2, y, p, col, sh, max(1, p / 2))
        y += 7 * p + gap
    return svg(width, y, body), width / 2, y / 2


def button(text, c1, c2, w=270, h=44):
    gid = "b" + hashlib.md5(text.encode()).hexdigest()[:6]
    body = "<defs>%s</defs>" % lin_grad(gid, c1, c2)
    body += ('<rect x="2" y="4" width="%d" height="%d" rx="12" fill="#000000" fill-opacity="0.35"/>'
             '<rect x="1" y="1" width="%d" height="%d" rx="12" fill="url(#%s)" stroke="#ffffff" '
             'stroke-width="2" stroke-opacity="0.85"/>'
             '<rect x="8" y="5" width="%d" height="%d" rx="8" fill="#ffffff" fill-opacity="0.18"/>'
             % (w - 2, h - 4, w - 4, h - 4, gid, w - 16, (h - 10) / 2))
    body += pixel_text(text, (w - text_width(text, 3)) / 2, (h - 21) / 2, 3, "#ffffff", "#00000066", 1.5)
    return svg(w + 2, h + 2, body), (w + 2) / 2, (h + 2) / 2


def help_panel():
    W, H = 440, 320
    body = ('<rect x="2" y="2" width="%d" height="%d" rx="16" fill="#0a1233" fill-opacity="0.96" '
            'stroke="#35d0ff" stroke-width="3"/>' % (W - 4, H - 4))

    def center(t, y, p, col):
        return pixel_text(t, (W - text_width(t, p)) / 2, y, p, col, "#000000", max(1, p / 2))

    def left(t, x, y, col="#ffffff"):
        return pixel_text(t, x, y, 2, col, "#000000", 1)

    body += center("ANLEITUNG", 16, 4, "#ffd23a")
    body += left("STEUERUNG", 28, 60, "#7fe8ff")
    body += left("PFEILE / WASD", 28, 80) + left("BEWEGEN", 250, 80, "#b8c2e6")
    body += left("LEERTASTE", 28, 98) + left("SCHIESSEN", 250, 98, "#b8c2e6")
    body += left("POWER-UPS", 28, 126, "#7fe8ff")
    icons = [(1, "SCHILD", 28, 146), (2, "3-FACH-SCHUSS", 228, 146),
             (3, "EXTRALEBEN", 28, 170), (4, "BOMBE", 228, 170)]
    for kind, name, x, y in icons:
        col = {1: "#37a9ff", 2: "#ffc21f", 3: "#3ddc6b", 4: "#ff4040"}[kind]
        body += '<circle cx="%d" cy="%d" r="9" fill="%s"/>' % (x + 9, y + 7, col)
        if kind == 3:
            body += '<path d="%s" transform="translate(%g %g) scale(0.45)" fill="#fff"/>' % (HEART, x + 4, y + 3)
        else:
            body += pixel_text({1: "S", 2: "3", 4: "B"}[kind], x + 5, y + 2.5, 1.6, "#ffffff")
        body += left(name, x + 26, y)
    body += left("GROSSE ASTEROIDEN ZERFALLEN!", 28, 204, "#ffb38a")
    body += left("UFOS SCHIESSEN ZURÜCK!", 28, 224, "#ffb38a")
    body += left("JEDES 5. LEVEL: BOSSKAMPF!", 28, 244, "#ff8aa0")
    body += center("(KLICKEN ZUM SCHLIESSEN)", 284, 2, "#8a93b8")
    return svg(W, H, body), W / 2, H / 2


def space_bg(menu):
    rng = random.Random(7 if menu else 3)
    body = "<defs>%s" % lin_grad("bg", "#0d1236" if menu else "#0b0f2e", "#020309")
    body += ('<radialGradient id="n1"><stop offset="0" stop-color="#8b2fd0" stop-opacity="%s"/>'
             '<stop offset="1" stop-color="#8b2fd0" stop-opacity="0"/></radialGradient>' % (".55" if menu else ".35"))
    body += ('<radialGradient id="n2"><stop offset="0" stop-color="#16a8b0" stop-opacity="%s"/>'
             '<stop offset="1" stop-color="#16a8b0" stop-opacity="0"/></radialGradient>' % (".45" if menu else ".28"))
    body += ('<radialGradient id="pl" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="#ffb46b"/>'
             '<stop offset="0.6" stop-color="#b8522a"/><stop offset="1" stop-color="#3a1208"/></radialGradient>')
    body += ('<radialGradient id="pl2" cx="0.35" cy="0.3" r="0.8"><stop offset="0" stop-color="#9ee7ff"/>'
             '<stop offset="0.6" stop-color="#2d6fb8"/><stop offset="1" stop-color="#0a1a3a"/></radialGradient>')
    body += "</defs>"
    body += '<rect width="480" height="360" fill="url(#bg)"/>'
    body += '<ellipse cx="120" cy="90" rx="190" ry="120" fill="url(#n1)"/>'
    body += '<ellipse cx="380" cy="260" rx="210" ry="130" fill="url(#n2)"/>'
    for _ in range(90):
        body += '<circle cx="%.1f" cy="%.1f" r="%.2f" fill="#ffffff" fill-opacity="%.2f"/>' % (
            rng.uniform(0, 480), rng.uniform(0, 360), rng.uniform(0.4, 1.3), rng.uniform(0.25, 0.9))
    if menu:
        body += '<circle cx="70" cy="320" r="95" fill="url(#pl2)"/>'
        body += ('<ellipse cx="70" cy="320" rx="150" ry="26" fill="none" stroke="#c9e9ff" stroke-width="5" '
                 'stroke-opacity="0.55" transform="rotate(-14 70 320)"/>')
        body += '<circle cx="420" cy="60" r="22" fill="url(#pl)"/>'
    else:
        body += '<circle cx="455" cy="345" r="75" fill="url(#pl)"/>'
    return svg(480, 360, body)


# ================================================================ Klänge
RATE = 22050


def _wav(samples):
    buf = io.BytesIO()
    w = wave.open(buf, "wb")
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32000)) for s in samples))
    w.close()
    return buf.getvalue(), len(samples)


def _osc(kind, ph):
    ph %= 1.0
    if kind == "square":
        return 1.0 if ph < 0.5 else -1.0
    if kind == "tri":
        return 4 * ph - 1 if ph < 0.5 else 3 - 4 * ph
    if kind == "saw":
        return 2 * ph - 1
    return math.sin(2 * math.pi * ph)


def sweep(f0, f1, dur, kind="square", vol=0.4, curve=1.0):
    n = int(RATE * dur)
    out, ph = [], 0.0
    for i in range(n):
        t = i / n
        f = f0 + (f1 - f0) * t ** curve
        ph += f / RATE
        env = (1 - t) ** 1.5 * min(1, i / 60)
        out.append(_osc(kind, ph) * vol * env)
    return out


def noise(dur, vol=0.6, lp=0.2, decay=2.0, seed=1):
    rng = random.Random(seed)
    n = int(RATE * dur)
    out, y = [], 0.0
    for i in range(n):
        t = i / n
        y += lp * (rng.uniform(-1, 1) - y)
        out.append(y * vol * (1 - t) ** decay * 3)
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    return [sum(t[i] for t in tracks if i < len(t)) for i in range(n)]


def notes(seq, kind="square", vol=0.3, gap=0.0):
    out = []
    for f, d in seq:
        n = int(RATE * d)
        ph = 0.0
        for i in range(n):
            ph += f / RATE
            env = min(1, i / 80) * (1 - i / n) ** 0.6 if f else 0
            out.append(_osc(kind, ph) * vol * env if f else 0)
        out += [0.0] * int(RATE * gap)
    return out


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


def music():
    bpm = 132
    e = 60 / bpm / 2  # Achtelnote
    chords = [(57, [69, 72, 76]), (53, [65, 69, 72]), (48, [67, 72, 76]), (55, [67, 71, 74])]
    melody = [76, 0, 79, 76, 74, 72, 74, 76, 72, 0, 74, 72, 69, 0, 72, 74,
              76, 79, 81, 79, 76, 74, 72, 74, 71, 0, 74, 76, 74, 71, 67, 0]
    total = int(RATE * e * 32)
    out = [0.0] * total
    for bar, (root, arp) in enumerate(chords):
        for s in range(8):
            start = int(RATE * e * (bar * 8 + s))
            f = midi(root - 12 if s % 2 == 0 else root)
            n = int(RATE * e * 0.9)
            ph = 0.0
            for i in range(n):
                ph += f / RATE
                out[start + i] += _osc("tri", ph) * 0.32 * (1 - i / n) ** 0.4
            for h in range(2):
                st2 = start + int(RATE * e / 2 * h)
                f2 = midi(arp[(s * 2 + h) % 3] + 12)
                n2 = int(RATE * e / 2 * 0.7)
                ph = 0.0
                for i in range(n2):
                    ph += f2 / RATE
                    if st2 + i < total:
                        out[st2 + i] += _osc("square", ph) * 0.045 * (1 - i / n2)
    for s, m in enumerate(melody):
        if not m:
            continue
        start = int(RATE * e * s)
        f = midi(m)
        n = int(RATE * e * 0.95)
        ph = 0.0
        for i in range(n):
            ph += f / RATE * (1 + 0.004 * math.sin(i / RATE * 30))
            out[start + i] += _osc("square", ph) * 0.09 * min(1, i / 100) * (1 - i / n) ** 0.5
    # Hi-Hat
    rng = random.Random(4)
    for s in range(32):
        start = int(RATE * e * s)
        for i in range(int(RATE * 0.03)):
            out[start + i] += rng.uniform(-1, 1) * 0.05 * (1 - i / (RATE * 0.03)) ** 3
    # Kick
    for s in range(0, 32, 4):
        start = int(RATE * e * s)
        ph = 0.0
        n = int(RATE * 0.12)
        for i in range(n):
            ph += (110 - 70 * i / n) / RATE
            out[start + i] += math.sin(2 * math.pi * ph) * 0.35 * (1 - i / n)
    return out


def sounds():
    s = {}
    s["Laser"] = _wav(sweep(1500, 350, 0.14, "square", 0.22, 0.6))
    s["Explosion"] = _wav(mix(noise(0.38, 0.55, 0.25, 1.8, 2), sweep(140, 40, 0.3, "sine", 0.45)))
    s["Grosse Explosion"] = _wav(mix(noise(0.9, 0.6, 0.12, 1.5, 5), sweep(90, 30, 0.8, "sine", 0.5)))
    s["Treffer"] = _wav(mix(noise(0.45, 0.4, 0.1, 1.2, 9), sweep(300, 60, 0.45, "saw", 0.3)))
    s["Klonk"] = _wav(sweep(420, 260, 0.08, "tri", 0.45))
    s["PowerUp"] = _wav(notes([(midi(72), .06), (midi(76), .06), (midi(79), .06), (midi(84), .14)], "square", 0.22))
    s["UFO-Schuss"] = _wav(sweep(500, 1100, 0.13, "saw", 0.18))
    s["Boss-Schuss"] = _wav(sweep(260, 120, 0.16, "square", 0.2))
    s["Level geschafft"] = _wav(notes([(midi(67), .1), (midi(72), .1), (midi(76), .1), (midi(79), .1),
                                      (0, .05), (midi(76), .1), (midi(79), .4)], "square", 0.22))
    s["Game Over"] = _wav(notes([(midi(67), .25), (midi(64), .25), (midi(60), .25), (midi(55), .7)], "tri", 0.4, 0.03))
    alarm = []
    for _ in range(3):
        alarm += sweep(500, 900, 0.3, "square", 0.18, 1.0)[:int(RATE * 0.3)]
    s["Alarm"] = _wav(alarm)
    s["Klick"] = _wav(sweep(900, 700, 0.05, "square", 0.2))
    s["Schild weg"] = _wav(sweep(1200, 200, 0.3, "tri", 0.35, 0.5))
    s["Musik"] = _wav(music())
    return s
