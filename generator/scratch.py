"""Kleine DSL, um Scratch-3-Projekte (.sb3) aus Python heraus zu bauen.

Ein Skript wird als Liste von Blk-Objekten beschrieben. Beim Speichern werden
daraus die Block-Dictionaries erzeugt, die Scratch in project.json erwartet.
"""
import hashlib
import json
import zipfile

# ---------------------------------------------------------------- Grundtypen


class Blk:
    def __init__(self, op, inputs=None, fields=None, mutation=None):
        self.op = op
        self.inputs = inputs or {}
        self.fields = fields or {}
        self.mutation = mutation


class Menu:
    """Schatten-Menü (z.B. Kostümauswahl, Taste, Figur)."""

    def __init__(self, op, field, value, default=None):
        self.op, self.field, self.value, self.default = op, field, value, default


class Bc:
    def __init__(self, name):
        self.name = name


class Var:
    def __init__(self, name):
        self.name = name


class Lst:
    def __init__(self, name):
        self.name = name


def _hid(*parts):
    return hashlib.md5("|".join(parts).encode()).hexdigest()[:16]


BOOL_OPS = {
    "operator_gt", "operator_lt", "operator_equals", "operator_and", "operator_or",
    "operator_not", "operator_contains", "sensing_touchingobject", "sensing_keypressed",
    "sensing_mousedown", "data_listcontainsitem",
}
TEXT_SLOTS = {"MESSAGE", "STRING", "STRING1", "STRING2", "QUESTION", "OPERAND1", "OPERAND2"}


def _fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if v.is_integer():
            return str(int(v))
        return repr(v)
    return str(v)


# ---------------------------------------------------------------- Ziele


class Target:
    def __init__(self, name, is_stage=False, **props):
        self.name = name
        self.is_stage = is_stage
        self.vars = {}
        self.lists = {}
        self.scripts = []  # (Liste von Blöcken, Kommentar)
        self.procs = {}  # proccode -> (argnamen, argids, warp)
        self.costumes = []
        self.sounds = []
        self.props = dict(x=0, y=0, size=100, direction=90, visible=False,
                          rotationStyle="all around", draggable=False, currentCostume=0)
        self.props.update(props)

    # Deklarationen -------------------------------------------------------
    def var(self, name, value=0):
        self.vars[name] = (_hid("var", self.name, name), value)

    def lst(self, name, items=None):
        self.lists[name] = (_hid("list", self.name, name), list(items or []))

    def script(self, *blocks, comment=None):
        self.scripts.append((list(blocks), comment))

    def proc(self, proccode, argnames, body, warp=True, comment=None):
        ids = [_hid("arg", self.name, proccode, a) for a in argnames]
        self.procs[proccode] = (list(argnames), ids, warp)
        self.scripts.append((("PROC", proccode, list(body)), comment))


class Project:
    def __init__(self):
        self.stage = Target("Stage", is_stage=True)
        self.sprites = []
        self.files = {}
        self.broadcasts = {}
        self.monitors = []
        self._n = 0

    def sprite(self, name, **props):
        t = Target(name, **props)
        self.sprites.append(t)
        return t

    # Assets --------------------------------------------------------------
    def costume(self, target, name, svg, cx, cy):
        data = svg.encode("utf-8")
        md5 = hashlib.md5(data).hexdigest()
        self.files[md5 + ".svg"] = data
        target.costumes.append({
            "assetId": md5, "name": name, "bitmapResolution": 1, "md5ext": md5 + ".svg",
            "dataFormat": "svg", "rotationCenterX": cx, "rotationCenterY": cy,
        })

    def sound(self, target, name, wav, count, rate=22050):
        md5 = hashlib.md5(wav).hexdigest()
        self.files[md5 + ".wav"] = wav
        target.sounds.append({
            "assetId": md5, "name": name, "dataFormat": "wav", "format": "", "rate": rate,
            "sampleCount": count, "md5ext": md5 + ".wav",
        })

    # Serialisierung --------------------------------------------------------
    def _newid(self):
        self._n += 1
        return "blk%05d" % self._n

    def _var_id(self, t, name):
        if name in t.vars:
            return t.vars[name][0]
        if name in self.stage.vars:
            return self.stage.vars[name][0]
        raise KeyError("Variable '%s' in '%s' unbekannt" % (name, t.name))

    def _list_id(self, t, name):
        if name in t.lists:
            return t.lists[name][0]
        if name in self.stage.lists:
            return self.stage.lists[name][0]
        raise KeyError("Liste '%s' in '%s' unbekannt" % (name, t.name))

    def _bc_id(self, name):
        if name not in self.broadcasts:
            self.broadcasts[name] = _hid("bc", name)
        return self.broadcasts[name]

    def _field(self, t, v):
        if isinstance(v, Var):
            return [v.name, self._var_id(t, v.name)]
        if isinstance(v, Lst):
            return [v.name, self._list_id(t, v.name)]
        if isinstance(v, Bc):
            return [v.name, self._bc_id(v.name)]
        if isinstance(v, list):
            return v
        return [v, None]

    def _shadow(self, t, blocks, op, field, value, parent):
        sid = self._newid()
        blocks[sid] = {"opcode": op, "next": None, "parent": parent, "inputs": {},
                       "fields": {field: [value, None]}, "shadow": True, "topLevel": False}
        return sid

    def _input(self, t, blocks, op, name, v, parent):
        if isinstance(v, list):
            return [2, self._stack(t, blocks, v, parent)]
        if isinstance(v, Bc):
            return [1, [11, v.name, self._bc_id(v.name)]]
        if isinstance(v, Menu):
            if isinstance(v.value, Blk):
                default = v.default
                if default is None:
                    default = t.costumes[0]["name"] if v.op == "looks_costume" else ""
                sid = self._shadow(t, blocks, v.op, v.field, default, parent)
                rid = self._block(t, blocks, v.value, parent)
                return [3, rid, sid]
            return [1, self._shadow(t, blocks, v.op, v.field, v.value, parent)]
        is_bool = name == "CONDITION" or (op == "operator_not" and name == "OPERAND") or \
            op in ("operator_and", "operator_or")
        is_text = name in TEXT_SLOTS or op == "procedures_call" or \
            (op == "data_setvariableto" and name == "VALUE") or name == "ITEM"
        if isinstance(v, Blk):
            rid = self._block(t, blocks, v, parent)
            if is_bool:
                if v.op not in BOOL_OPS:
                    raise ValueError("Kein Wahrheitswert in %s.%s" % (op, name))
                return [2, rid]
            return [3, rid, [10, ""] if is_text else [4, ""]]
        if is_bool:
            raise ValueError("Literal in Bool-Slot %s.%s" % (op, name))
        return [1, [10 if is_text else 4, _fmt(v)]]

    def _block(self, t, blocks, b, parent):
        bid = self._newid()
        obj = {"opcode": b.op, "next": None, "parent": parent, "inputs": {}, "fields": {},
               "shadow": False, "topLevel": False}
        blocks[bid] = obj
        for k, v in b.fields.items():
            obj["fields"][k] = self._field(t, v)
        if b.op == "procedures_call":
            code = b.mutation
            if code not in t.procs:
                raise KeyError("Eigener Block '%s' in '%s' fehlt" % (code, t.name))
            names, ids, warp = t.procs[code]
            if len(b.inputs) != len(ids):
                raise ValueError("Falsche Argumentzahl für '%s'" % code)
            for i, aid in enumerate(ids):
                obj["inputs"][aid] = self._input(t, blocks, b.op, aid, b.inputs[i], bid)
            obj["mutation"] = {"tagName": "mutation", "children": [], "proccode": code,
                               "argumentids": json.dumps(ids), "warp": "true" if warp else "false"}
            return bid
        for k, v in b.inputs.items():
            if isinstance(v, list) and not v:
                continue
            obj["inputs"][k] = self._input(t, blocks, b.op, k, v, bid)
        if b.mutation:
            obj["mutation"] = b.mutation
        return bid

    def _stack(self, t, blocks, stmts, parent):
        first = prev = None
        for s in stmts:
            bid = self._block(t, blocks, s, prev or parent)
            if prev:
                blocks[prev]["next"] = bid
            else:
                first = bid
            prev = bid
        return first

    def _proc_def(self, t, blocks, code, body):
        names, ids, warp = t.procs[code]
        def_id, proto_id = self._newid(), self._newid()
        blocks[def_id] = {"opcode": "procedures_definition", "next": None, "parent": None,
                          "inputs": {"custom_block": [1, proto_id]}, "fields": {},
                          "shadow": False, "topLevel": True}
        proto_inputs = {}
        for aid, nm in zip(ids, names):
            rid = self._newid()
            blocks[rid] = {"opcode": "argument_reporter_string_number", "next": None,
                           "parent": proto_id, "inputs": {}, "fields": {"VALUE": [nm, None]},
                           "shadow": True, "topLevel": False}
            proto_inputs[aid] = [1, rid]
        blocks[proto_id] = {
            "opcode": "procedures_prototype", "next": None, "parent": def_id,
            "inputs": proto_inputs, "fields": {}, "shadow": True, "topLevel": False,
            "mutation": {"tagName": "mutation", "children": [], "proccode": code,
                         "argumentids": json.dumps(ids), "argumentnames": json.dumps(names),
                         "argumentdefaults": json.dumps([""] * len(names)),
                         "warp": "true" if warp else "false"}}
        blocks[def_id]["next"] = self._stack(t, blocks, body, def_id)
        return def_id

    def _target_json(self, t, layer):
        blocks, comments = {}, {}
        y = 0
        for body, comment in t.scripts:
            if isinstance(body, tuple):
                first = self._proc_def(t, blocks, body[1], body[2])
                size = _count(body[2]) + 1
            else:
                first = self._stack(t, blocks, body, None)
                blocks[first]["topLevel"] = True
                size = _count(body)
            blocks[first]["x"], blocks[first]["y"] = 440, y
            height = size * 48 + 90
            if comment:
                cid = "kom" + first
                blocks[first]["comment"] = cid
                lines = sum(len(line) // 40 + 1 for line in comment.split("\n"))
                ch = max(105, lines * 22 + 55)
                comments[cid] = {"blockId": first, "x": 0, "y": y, "width": 400,
                                 "height": ch, "minimized": False, "text": comment}
                height = max(height, ch + 60)
            y += height
        obj = {
            "isStage": t.is_stage, "name": t.name,
            "variables": {vid: [n, val] for n, (vid, val) in t.vars.items()},
            "lists": {lid: [n, items] for n, (lid, items) in t.lists.items()},
            "broadcasts": {}, "blocks": blocks, "comments": comments,
            "currentCostume": t.props["currentCostume"], "costumes": t.costumes,
            "sounds": t.sounds, "volume": 100, "layerOrder": layer,
        }
        if t.is_stage:
            obj.update({"tempo": 60, "videoTransparency": 50, "videoState": "on",
                        "textToSpeechLanguage": None})
        else:
            for k in ("visible", "x", "y", "size", "direction", "draggable", "rotationStyle"):
                obj[k] = t.props[k]
        return obj

    def save(self, path, agent="Astro-Abwehr Generator"):
        targets = [self._target_json(s, i + 1) for i, s in enumerate(self.sprites)]
        stage = self._target_json(self.stage, 0)
        stage["broadcasts"] = {bid: n for n, bid in self.broadcasts.items()}
        project = {"targets": [stage] + targets, "monitors": self.monitors,
                   "extensions": [], "meta": {"semver": "3.0.0", "vm": "0.2.0",
                                              "agent": agent}}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("project.json", json.dumps(project, ensure_ascii=False))
            for name, data in self.files.items():
                z.writestr(name, data)
        return project

    def var_monitor(self, name, x, y, mode="default"):
        self.monitors.append({
            "id": self._var_id(self.stage, name), "mode": mode, "opcode": "data_variable",
            "params": {"VARIABLE": name}, "spriteName": None, "value": 0, "width": 0,
            "height": 0, "x": x, "y": y, "visible": True, "sliderMin": 0, "sliderMax": 100,
            "isDiscrete": True})

    def list_monitor(self, name, x, y, w, h):
        self.monitors.append({
            "id": self._list_id(self.stage, name), "mode": "list", "opcode": "data_listcontents",
            "params": {"LIST": name}, "spriteName": None, "value": [], "width": w, "height": h,
            "x": x, "y": y, "visible": False})


def _count(stmts):
    n = 0
    for s in stmts:
        n += 1
        for v in s.inputs.values():
            if isinstance(v, list):
                n += _count(v) + 1
    return n


# ---------------------------------------------------------------- Blöcke
# Ereignisse
def on_flag(): return Blk("event_whenflagclicked")
def on_msg(m): return Blk("event_whenbroadcastreceived", fields={"BROADCAST_OPTION": Bc(m)})
def on_clone(): return Blk("control_start_as_clone")
def on_click(): return Blk("event_whenthisspriteclicked")
def on_key(k): return Blk("event_whenkeypressed", fields={"KEY_OPTION": k})
def broadcast(m): return Blk("event_broadcast", inputs={"BROADCAST_INPUT": Bc(m)})
def broadcast_wait(m): return Blk("event_broadcastandwait", inputs={"BROADCAST_INPUT": Bc(m)})


# Steuerung
def wait(t): return Blk("control_wait", inputs={"DURATION": t})
def forever(*b): return Blk("control_forever", inputs={"SUBSTACK": list(b)})
def repeat(n, *b): return Blk("control_repeat", inputs={"TIMES": n, "SUBSTACK": list(b)})
def until(c, *b): return Blk("control_repeat_until", inputs={"CONDITION": c, "SUBSTACK": list(b)})
def if_(c, *b): return Blk("control_if", inputs={"CONDITION": c, "SUBSTACK": list(b)})
def wait_until(c): return Blk("control_wait_until", inputs={"CONDITION": c})
def delete_clone(): return Blk("control_delete_this_clone")


def ifelse(c, a, b):
    return Blk("control_if_else", inputs={"CONDITION": c, "SUBSTACK": list(a), "SUBSTACK2": list(b)})


def clone(t="_myself_"):
    return Blk("control_create_clone_of",
               inputs={"CLONE_OPTION": Menu("control_create_clone_of_menu", "CLONE_OPTION", t)})


def stop(opt):
    return Blk("control_stop", fields={"STOP_OPTION": opt},
               mutation={"tagName": "mutation", "children": [],
                         "hasnext": "true" if opt == "other scripts in sprite" else "false"})


# Operatoren
def _op(op, a, b, n1="NUM1", n2="NUM2"): return Blk(op, inputs={n1: a, n2: b})
def add(a, b): return _op("operator_add", a, b)
def sub(a, b): return _op("operator_subtract", a, b)
def mul(a, b): return _op("operator_multiply", a, b)
def div(a, b): return _op("operator_divide", a, b)
def mod(a, b): return _op("operator_mod", a, b)
def rnd(a, b): return _op("operator_random", a, b, "FROM", "TO")
def gt(a, b): return _op("operator_gt", a, b, "OPERAND1", "OPERAND2")
def lt(a, b): return _op("operator_lt", a, b, "OPERAND1", "OPERAND2")
def eq(a, b): return _op("operator_equals", a, b, "OPERAND1", "OPERAND2")
def join(a, b): return _op("operator_join", a, b, "STRING1", "STRING2")
def letter(i, s): return _op("operator_letter_of", i, s, "LETTER", "STRING")
def length(s): return Blk("operator_length", inputs={"STRING": s})
def not_(a): return Blk("operator_not", inputs={"OPERAND": a})
def round_(x): return Blk("operator_round", inputs={"NUM": x})
def mathop(f, x): return Blk("operator_mathop", inputs={"NUM": x}, fields={"OPERATOR": f})
def sin(x): return mathop("sin", x)
def floor(x): return mathop("floor", x)


def and_(*c):
    r = c[0]
    for x in c[1:]:
        r = _op("operator_and", r, x, "OPERAND1", "OPERAND2")
    return r


def or_(*c):
    r = c[0]
    for x in c[1:]:
        r = _op("operator_or", r, x, "OPERAND1", "OPERAND2")
    return r


# Variablen und Listen
def v(name): return Blk("data_variable", fields={"VARIABLE": Var(name)})
def setv(name, val): return Blk("data_setvariableto", inputs={"VALUE": val}, fields={"VARIABLE": Var(name)})
def chg(name, val): return Blk("data_changevariableby", inputs={"VALUE": val}, fields={"VARIABLE": Var(name)})
def push(l, x): return Blk("data_addtolist", inputs={"ITEM": x}, fields={"LIST": Lst(l)})
def item(i, l): return Blk("data_itemoflist", inputs={"INDEX": i}, fields={"LIST": Lst(l)})
def delete(i, l): return Blk("data_deleteoflist", inputs={"INDEX": i}, fields={"LIST": Lst(l)})
def clear(l): return Blk("data_deletealloflist", fields={"LIST": Lst(l)})
def llen(l): return Blk("data_lengthoflist", fields={"LIST": Lst(l)})
def insert(i, l, x): return Blk("data_insertatlist", inputs={"INDEX": i, "ITEM": x}, fields={"LIST": Lst(l)})
def show_list(l): return Blk("data_showlist", fields={"LIST": Lst(l)})
def hide_list(l): return Blk("data_hidelist", fields={"LIST": Lst(l)})


# Bewegung
def goto_xy(x, y): return Blk("motion_gotoxy", inputs={"X": x, "Y": y})
def setx(x): return Blk("motion_setx", inputs={"X": x})
def sety(y): return Blk("motion_sety", inputs={"Y": y})
def chx(d): return Blk("motion_changexby", inputs={"DX": d})
def chy(d): return Blk("motion_changeyby", inputs={"DY": d})
def move(n): return Blk("motion_movesteps", inputs={"STEPS": n})
def turn(d): return Blk("motion_turnright", inputs={"DEGREES": d})
def point(d): return Blk("motion_pointindirection", inputs={"DIRECTION": d})
def xpos(): return Blk("motion_xposition")
def ypos(): return Blk("motion_yposition")
def direction(): return Blk("motion_direction")


def point_to(s):
    return Blk("motion_pointtowards",
               inputs={"TOWARDS": Menu("motion_pointtowards_menu", "TOWARDS", s)})


# Aussehen
def costume(c): return Blk("looks_switchcostumeto", inputs={"COSTUME": Menu("looks_costume", "COSTUME", c)})
def next_costume(): return Blk("looks_nextcostume")
def backdrop(b): return Blk("looks_switchbackdropto", inputs={"BACKDROP": Menu("looks_backdrops", "BACKDROP", b)})
def size(n): return Blk("looks_setsizeto", inputs={"SIZE": n})
def size_r(): return Blk("looks_size")
def effect(e, val): return Blk("looks_seteffectto", inputs={"VALUE": val}, fields={"EFFECT": e})
def cheffect(e, val): return Blk("looks_changeeffectby", inputs={"CHANGE": val}, fields={"EFFECT": e})
def clearfx(): return Blk("looks_cleargraphiceffects")
def show(): return Blk("looks_show")
def hide(): return Blk("looks_hide")
def front(): return Blk("looks_gotofrontback", fields={"FRONT_BACK": "front"})
def back(): return Blk("looks_gotofrontback", fields={"FRONT_BACK": "back"})


# Klang
def play(s): return Blk("sound_play", inputs={"SOUND_MENU": Menu("sound_sounds_menu", "SOUND_MENU", s)})
def play_wait(s): return Blk("sound_playuntildone", inputs={"SOUND_MENU": Menu("sound_sounds_menu", "SOUND_MENU", s)})
def stop_sounds(): return Blk("sound_stopallsounds")


# Fühlen
def touching(o):
    return Blk("sensing_touchingobject",
               inputs={"TOUCHINGOBJECTMENU": Menu("sensing_touchingobjectmenu", "TOUCHINGOBJECTMENU", o)})


def key(k): return Blk("sensing_keypressed", inputs={"KEY_OPTION": Menu("sensing_keyoptions", "KEY_OPTION", k)})
def ask(q): return Blk("sensing_askandwait", inputs={"QUESTION": q})
def answer(): return Blk("sensing_answer")


# Eigene Blöcke
def arg(n): return Blk("argument_reporter_string_number", fields={"VALUE": [n, None]})
def call(code, *args): return Blk("procedures_call", inputs=dict(enumerate(args)), mutation=code)
