"""Posen für die Figuren: Jede Pose ist eine Sammlung von Gelenkwinkeln.

Winkel in Grad, gemessen von "gerade nach unten". Positiv heisst: nach vorne
(in Blickrichtung). Ein Arm mit 90 Grad zeigt also waagrecht nach vorne.

  neigung   Oberkörper (positiv = nach vorne gebeugt)
  tief      Hüfte wird um so viele Pixel abgesenkt (in die Knie gehen)
  kopf      Kopf zusätzlich neigen
  vs, ve    vorderer Arm: Schulter und Ellbogen (Ellbogen beugt den Unterarm nach vorne/oben)
  hs, he    hinterer Arm
  vh, vk    vorderes Bein: Hüfte und Knie (Knie beugt den Unterschenkel nach hinten)
  hh, hk    hinteres Bein
  drehung   die ganze Figur kippen (nach hinten fallen = negativ)
  umdrehen  > 0.5: Figur schaut kurz in die andere Richtung (Wirbeltritt)

Animation entsteht, indem man zwischen zwei Posen mischt (interpoliert).
"""
import math

GRUND = dict(
    neigung=6, tief=2, kopf=0,
    vs=28, ve=110, hs=12, he=120,
    vh=12, vk=10, hh=-12, hk=12,
    drehung=0, umdrehen=0,
)


def pose(**aenderungen):
    neu = dict(GRUND)
    neu.update(aenderungen)
    return neu


def mische(a, b, anteil):
    return {k: a[k] + (b[k] - a[k]) * anteil for k in a}


def weich(t):
    """Ease-in-out: langsam los, schnell in der Mitte, langsam am Ende."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# --- Bewegungsposen (t = laufende Zeit in Sekunden) ------------------------------

def stehen(t):
    atem = math.sin(t * 3.2)
    return pose(tief=2 + 1.5 * atem, vs=28 + 3 * atem, hs=12 + 3 * atem, ve=110 - 3 * atem)


def gehen(t):
    w = math.sin(t * 11)
    return pose(
        neigung=9, tief=2 + 2 * abs(math.cos(t * 11)),
        vh=24 * w, vk=12 + 28 * max(0.0, -w),
        hh=-24 * w, hk=12 + 28 * max(0.0, w),
        vs=30 - 12 * w, hs=14 + 12 * w,
    )


def springen(t):
    return pose(neigung=12, vh=55, vk=85, hh=-5, hk=75, vs=55, ve=70, hs=-35, he=60)


GETROFFEN = pose(neigung=-24, kopf=-18, vs=-30, ve=45, hs=-55, he=30, vh=16, vk=22, hh=-20, hk=10)
LIEGEN = pose(neigung=0, kopf=-10, tief=0, vs=-150, ve=10, hs=-170, he=20, vh=8, vk=20, hh=-6, hk=4, drehung=-90)
AUFSTEHEN = pose(tief=22, neigung=38, vh=50, vk=95, hh=-15, hk=80, vs=55, ve=40, hs=20, he=60)
JUBELN = pose(neigung=-4, kopf=-12, vs=165, ve=15, hs=150, he=25, vh=10, hh=-10)


def getroffen(t):
    wackeln = math.sin(t * 40) * 4
    return pose(**{**GETROFFEN, "neigung": GETROFFEN["neigung"] + wackeln})


def fallen(t):
    """t = 0 (gerade getroffen) bis 1 (am Boden)."""
    return {**GETROFFEN, "drehung": -25 - 60 * weich(t), "vh": 40, "vk": 50, "hh": 10, "hk": 30}


def liegen(t):
    return dict(LIEGEN)


def aufstehen(t):
    """t = 0 (liegt noch) bis 1 (steht)."""
    if t < 0.5:
        return mische(LIEGEN, AUFSTEHEN, weich(t * 2))
    return mische(AUFSTEHEN, GRUND, weich(t * 2 - 1))


def jubeln(t):
    hops = abs(math.sin(t * 6))
    return pose(**{**JUBELN, "tief": 6 * hops, "vs": 165 - 20 * hops})


# --- Angriffsposen: Ausholen und Treffen -------------------------------------------

ANGRIFFSPOSEN = {
    # Gerade mit der vorderen Faust
    "gerade": (
        pose(vs=12, ve=135, neigung=2),
        pose(vs=90, ve=0, neigung=16, hs=6, he=125, vh=20, hh=-22),
    ),
    # Haken mit der hinteren Faust
    "haken": (
        pose(hs=-15, he=110, neigung=-4, vs=30, ve=120),
        pose(hs=92, he=4, vs=18, ve=125, neigung=24, vh=26, vk=16, hh=-26, hk=18),
    ),
    # Aufwärtshaken
    "aufwaerts": (
        pose(tief=12, vs=-15, ve=95, neigung=16, vk=35, hk=35, vh=22, hh=-20),
        pose(vs=150, ve=22, neigung=-8, kopf=-12, tief=-3, vh=8, hh=-14),
    ),
    # Tritt nach vorne (Bauchhöhe)
    "tritt": (
        pose(vh=60, vk=105, neigung=-4, vs=10, ve=120),
        pose(vh=92, vk=0, neigung=-18, hh=-6, hk=12, vs=0, ve=120, hs=-20, he=90),
    ),
    # Hoher Tritt
    "hochtritt": (
        pose(vh=70, vk=115, neigung=-8, vs=10, ve=120),
        pose(vh=122, vk=0, neigung=-34, hh=-8, hk=10, vs=-25, ve=80, hs=40, he=70),
    ),
    # Drehtritt (Roundhouse): kurzes Wegdrehen, dann hoher Tritt
    "drehtritt": (
        pose(vh=40, vk=90, neigung=10, umdrehen=1, vs=-20, hs=40),
        pose(vh=112, vk=4, neigung=-30, hh=-6, hk=10, vs=-30, ve=70, hs=50, he=60),
    ),
    "sprungtritt": (
        pose(vh=45, vk=95, hh=-25, hk=95, vs=40, ve=70, hs=-30, he=70),
        pose(vh=96, vk=0, hh=12, hk=115, neigung=-22, vs=-35, ve=60, hs=40, he=80),
    ),
    "sprungschlag": (
        pose(vh=50, vk=85, hh=-5, hk=75, vs=-30, ve=100, neigung=0),
        pose(vh=40, vk=80, hh=-10, hk=60, vs=112, ve=10, neigung=14, hs=-20),
    ),
    # Wirbeltritt: dreht sich einmal ganz herum (siehe wirbel_pose)
    "wirbel": (
        pose(vh=40, vk=60, tief=8, neigung=10),
        pose(vh=95, vk=0, hh=-10, hk=10, neigung=-24, vs=-40, ve=40, hs=60, he=40),
    ),
    # Hammerschlag von oben (Brocken)
    "hammer": (
        pose(vs=175, ve=30, hs=165, he=30, neigung=-16, kopf=-10, tief=-2),
        pose(vs=80, ve=10, hs=70, he=15, neigung=30, tief=10, vh=30, vk=30, hh=-30, hk=20),
    ),
    # Schulterangriff (Boss)
    "rammen": (
        pose(tief=10, neigung=20, vs=-20, ve=90, hs=-30, he=90, vk=40, hk=40),
        pose(neigung=42, tief=6, vs=70, ve=80, hs=50, he=70, vh=40, vk=30, hh=-42, hk=25),
    ),
}


def angriffs_pose(name, t, ende_anlauf, ende_aktiv):
    """t = Fortschritt 0..1 durch den ganzen Angriff.

    Im Anlauf: Grundstellung -> Ausholen -> Treffen,
    in der aktiven Phase: Treffpose halten,
    in der Erholung: zurück zur Grundstellung.
    """
    aushol, treffer = ANGRIFFSPOSEN[name]
    if t < ende_anlauf:
        f = t / ende_anlauf
        if f < 0.65:
            ergebnis = mische(GRUND, aushol, weich(f / 0.65))
        else:
            ergebnis = mische(aushol, treffer, weich((f - 0.65) / 0.35))
    elif t < ende_aktiv:
        ergebnis = dict(treffer)
    else:
        f = (t - ende_aktiv) / max(0.0001, 1 - ende_aktiv)
        ergebnis = mische(treffer, GRUND, weich(f))

    if name == "wirbel":
        # Einmal ganz herum: in der Mitte der Drehung schaut die Figur nach hinten
        dreh = (t - ende_anlauf) / max(0.0001, ende_aktiv - ende_anlauf)
        ergebnis["umdrehen"] = 1 if 0.25 < dreh < 0.75 else 0
    elif name == "drehtritt":
        ergebnis["umdrehen"] = 1 if t < ende_anlauf * 0.8 else 0
    return ergebnis
