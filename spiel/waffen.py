"""Waffen und Wurfobjekte: Baseballschläger, Kisten, Fässer und Mülltonnen zum Tragen und Werfen.

Die Taste "greifen" hebt auf (Waffe vom Boden, Kiste/Fass/Tonne von der Strasse) und wirft.

  Trageding        was ein Spieler in den Händen hält (Art + Rest-Haltbarkeit)
  WaffeAmBoden     eine Waffe, die herumliegt (Gegenstand, wird aber nur auf Tastendruck aufgehoben)
  Geschoss         etwas Geworfenes im Flug. Es ist ein Objekt in welt.objekte und hat eine Hitbox,
                   darum findet das normale Treffersystem (SpielSzene.kampf) es von selbst
  Waffenverteiler  würfelt, wann Gegner und Requisiten eine Waffe fallen lassen (mit Schutz vor zu vielen)

Schwere Dinge (Kiste, Fass, Tonne) bremsen beim Tragen, man lässt sie bei jedem Treffer fallen,
und sie zerbrechen beim Wurf. Der Schläger nutzt sich bei jedem Treffer ab und bricht irgendwann.
"""
import math
import random

import pygame

import einstellungen as e
import grafik
from kampf import Angriff, Box
from objekte import Fass, Gegenstand, Kiste, Muelltonne, Objekt

HOLZ = (178, 126, 68)

# Daten aller Dinge, die man tragen kann.
#   wurf   Angriff des fliegenden Dings (Schaden, Betäubung = starre, Umwerfen ...)
#   v      Wurfgeschwindigkeit (vorwärts, hoch) in Pixel pro Sekunde
ARTEN = {
    "schlaeger": dict(
        name="SCHLÄGER", schwer=False, haltbarkeit=10, farbe=HOLZ, wurf_kosten=3, v=(480, 120),
        wurf=Angriff("wurf_schlaeger", "wurf", 0, 0, 0, 14, (0, 0), (0, 0), rueckstoss=200, starre=0.6, ton="hart"),
    ),
    "kiste": dict(
        name="KISTE", schwer=True, tempo=0.75, farbe=(170, 115, 60), klasse=Kiste, v=(430, 200),
        wurf=Angriff("wurf_kiste", "wurf", 0, 0, 0, 18, (0, 0), (0, 0), rueckstoss=140, starre=1.2, ton="hart"),
    ),
    "fass": dict(
        name="FASS", schwer=True, tempo=0.65, farbe=(40, 90, 170), klasse=Fass, v=(340, 140),
        wurf=Angriff("wurf_fass", "wurf", 0, 0, 0, 24, (0, 0), (0, 0), rueckstoss=300, wirft_um=True, ton="hart"),
    ),
    "tonne": dict(
        name="TONNE", schwer=True, tempo=0.75, farbe=(150, 155, 160), klasse=Muelltonne, v=(400, 180),
        wurf=Angriff("wurf_tonne", "wurf", 0, 0, 0, 12, (0, 0), (0, 0), rueckstoss=120, starre=1.0, ton="hart"),
    ),
}
ART_VON_KLASSE = {d["klasse"]: art for art, d in ARTEN.items() if "klasse" in d}

# Chance, dass beim Besiegen / Zerbrechen eine Waffe herauskommt (Quelle = Gegnertyp oder Requisit)
CHANCEN = {
    "schlaeger": 0.10, "flitzer": 0.12, "brocken": 0.30, "boss": 0.0,
    "kiste": 0.22, "fass": 0.12, "tonne": 0.15,
}
# Welche Waffe kommt heraus? (Stufe 1: nur der Schläger, weitere Waffen kommen hier einfach dazu.)
WAFFEN_POOL = {"schlaeger": 1}


class _FixKamera:
    """Tut so, als stünde die Kamera so, dass ein Requisit genau an einer Bildschirmstelle gezeichnet wird."""

    def __init__(self):
        self.px = self.py = 0

    def zu_bild(self, x, y, z=0.0):
        return (self.px, self.py)


_FIX = _FixKamera()


def zeichne_requisit(flaeche, prop, sx, sy):
    """Zeichnet eine Kiste, ein Fass oder eine Tonne mit dem Fusspunkt bei (sx, sy)."""
    _FIX.px, _FIX.py = sx, sy
    prop.wackel = 0.0
    prop.zeichnen(flaeche, _FIX)


def zeichne_schlaeger(flaeche, griff, spitze, s=1.0, anteil=1.0):
    """Baseballschläger von griff nach spitze. Unter 30 % Haltbarkeit hat er Risse."""
    gx, gy = griff
    sx, sy = spitze
    laenge = math.hypot(sx - gx, sy - gy) or 1.0
    ux, uy = (sx - gx) / laenge, (sy - gy) / laenge
    grafik.kapsel(flaeche, griff, spitze, 2.0 * s, HOLZ, e.UMRISS, 4.6 * s)
    # helle Kante auf der dicken Seite und dunkles Griffband
    pygame.draw.line(flaeche, grafik.heller(HOLZ, 0.35),
                     (gx + ux * laenge * 0.55, gy + uy * laenge * 0.55), (gx + ux * laenge * 0.9, gy + uy * laenge * 0.9),
                     max(1, int(2 * s)))
    pygame.draw.line(flaeche, (50, 40, 44),
                     (gx + ux * laenge * 0.04, gy + uy * laenge * 0.04), (gx + ux * laenge * 0.28, gy + uy * laenge * 0.28),
                     max(2, int(3.4 * s)))
    pygame.draw.circle(flaeche, grafik.dunkler(HOLZ, 0.7), (round(gx), round(gy)), max(2, int(3.2 * s)))
    if anteil < 0.3:
        for f in (0.62, 0.78):
            mx, my = gx + ux * laenge * f, gy + uy * laenge * f
            pygame.draw.line(flaeche, e.UMRISS, (mx - uy * 4 * s, my + ux * 4 * s), (mx + uy * 2 * s, my - ux * 2 * s), 2)


def zeichne_symbol(flaeche, art, rahmen):
    """Kleines Bild der Waffe fürs HUD."""
    if ARTEN[art]["schwer"]:
        pygame.draw.rect(flaeche, ARTEN[art]["farbe"], rahmen.inflate(-8, 0))
        pygame.draw.rect(flaeche, e.UMRISS, rahmen.inflate(-8, 0), 2)
    else:
        zeichne_schlaeger(flaeche, (rahmen.left + 3, rahmen.bottom - 3), (rahmen.right - 3, rahmen.top + 3), 0.6)


class Trageding:
    """Was ein Spieler gerade in den Händen hält."""

    def __init__(self, art, rest=None, prop=None):
        self.art = art
        self.daten = ARTEN[art]
        self.prop = prop  # bei Kiste, Fass, Tonne: das echte Objekt, damit es heil wieder hingestellt werden kann
        self.maximum = self.daten.get("haltbarkeit", 1)
        self.rest = self.maximum if rest is None else rest

    @property
    def schwer(self):
        return self.daten["schwer"]

    @property
    def name(self):
        return self.daten["name"]

    @property
    def anteil(self):
        return max(0.0, self.rest / self.maximum)

    def zeichne_in_hand(self, flaeche, hand_v, ellb_v, hand_h, ellb_h, s):
        if self.schwer:
            # über dem Kopf, zwischen beiden Händen
            mx, my = (hand_v[0] + hand_h[0]) / 2, (hand_v[1] + hand_h[1]) / 2
            zeichne_requisit(flaeche, self.prop, round(mx), round(my - 2))
            return
        dx, dy = hand_v[0] - ellb_v[0], hand_v[1] - ellb_v[1]
        laenge = math.hypot(dx, dy) or 1.0
        ux, uy = dx / laenge, dy / laenge
        griff = (hand_v[0] - ux * 8 * s, hand_v[1] - uy * 8 * s)
        spitze = (hand_v[0] + ux * 52 * s, hand_v[1] + uy * 52 * s)
        # wackelt, wenn er fast kaputt ist
        if self.anteil < 0.25:
            spitze = (spitze[0] + random.uniform(-1, 1), spitze[1] + random.uniform(-1, 1))
        zeichne_schlaeger(flaeche, griff, spitze, s, self.anteil)


class WaffeAmBoden(Gegenstand):
    """Eine Waffe, die herumliegt. Sie wird nie automatisch eingesammelt, nur mit der Greifen-Taste."""
    breite, tiefe, hoehe = 52, 8, 16

    def __init__(self, art, rest, x, y, lebensdauer=e.WAFFE_BODEN_ZEIT, blinkt=False):
        super().__init__(x, y)
        self.zeit = 0.0
        self.art = art
        self.rest = rest
        self.lebensdauer = lebensdauer
        self.blinkt = blinkt  # Waffe eines gestorbenen Spielers: blinkt die ganze Zeit
        self.z = 40.0  # kleiner Hüpfer beim Herausfallen
        self.vz = 260.0

    def beruehrt(self, spieler):
        return False

    def update(self, dt, welt):
        super().update(dt, welt)
        if self.z > 0 or self.vz > 0:
            self.vz -= e.SCHWERKRAFT * dt
            self.z = max(0.0, self.z + self.vz * dt)
            if self.z == 0.0:
                self.vz = 0.0

    def zeichne_boden(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y)
        grafik.zeichne_schatten(flaeche, sx, sy + 2, 44 / (1 + self.z / 120))

    def zeichnen(self, flaeche, kamera):
        if self.blinkt:
            if (self.zeit * 6) % 1 > 0.6:
                return
        elif self.zeit > self.lebensdauer - 3 and int(self.zeit * 10) % 2:
            return  # blinkt kurz bevor sie verschwindet
        sx, sy = kamera.zu_bild(self.x, self.y, self.z)
        anteil = self.rest / ARTEN[self.art]["haltbarkeit"]
        zeichne_schlaeger(flaeche, (sx - 24, sy - 5), (sx + 26, sy - 11), 1.0, anteil)


class Geschoss(Objekt):
    """Ein geworfenes Ding im Flug. Seine Hitbox trifft Gegner wie ein Schlag (jeden nur einmal)."""
    blockiert = False

    def __init__(self, besitzer, ding, x, y, z, blick, rest):
        super().__init__(x, y)
        self.z = float(z)
        self.besitzer = besitzer
        self.ding = ding
        self.team = besitzer.team
        self.angriff = ding.daten["wurf"]
        self.blick = blick
        self.rest = rest  # Haltbarkeit, die ein geworfener Schläger noch hat
        self.getroffene = set()
        self.gefaehrlich = True
        self.alter = 0.0
        self.drehung = 0.0
        vor, hoch = ding.daten["v"]
        self.vx, self.vy, self.vz = vor * blick, 0.0, float(hoch)
        if ding.schwer:
            self.breite, self.hoehe = ding.prop.breite, ding.prop.hoehe
        else:
            self.breite, self.hoehe = 56, 14

    # Das Treffersystem fragt Angreifer nach diesen Dingen:
    @property
    def punkte(self):
        return self.besitzer.punkte

    @punkte.setter
    def punkte(self, wert):
        self.besitzer.punkte = wert

    def hitbox(self):
        if not self.gefaehrlich:
            return None
        h = self.breite / 2
        return Box(self.x - h, self.x + h, self.y - 14, self.y + 14, self.z, self.z + self.hoehe)

    def treffer_gelandet(self, ziel, angriff, welt):
        self.besitzer.wurf_treffer(ziel, angriff)
        if self.entfernen or not self.gefaehrlich:
            return
        if self.ding.schwer:
            self.zerbrich(welt)
        else:
            # der Schläger prallt ab und fällt zu Boden
            self.gefaehrlich = False
            self.vx = -self.blick * 70
            self.vz = max(self.vz, 160)

    def zerbrich(self, welt):
        self.entfernen = True
        prop = self.ding.prop
        welt.effekte.splitter(self.x, self.y, self.z + self.hoehe / 2, prop.splitter_farben(), 14)
        welt.ton.spiele("bruch")
        welt.wackeln(3)
        beute = prop.beute()
        if beute and random.random() < 0.5:  # halb so oft wie beim Zerschlagen
            welt.objekte.append(beute(self.x_im_bild(welt), self.y))

    def x_im_bild(self, welt):
        return max(welt.kamera.x + 30, min(welt.kamera.x + e.BREITE - 30, self.x))

    def update(self, dt, welt):
        super().update(dt, welt)
        self.alter += dt
        self.vz -= e.SCHWERKRAFT * dt
        self.x += self.vx * dt
        self.y = max(e.BODEN_OBEN, min(e.BODEN_UNTEN, self.y + self.vy * dt))
        self.z += self.vz * dt
        self.drehung += dt * 16 * self.blick
        if self.z <= 0 and self.vz < 0:
            self.z = 0.0
            self.landen(welt)
        elif self.alter > 4 or not welt.kamera.ist_sichtbar(self.x, 160):
            self.entfernen = True

    def landen(self, welt):
        if self.ding.schwer:
            self.zerbrich(welt)
            return
        self.entfernen = True
        x = self.x_im_bild(welt)
        if self.rest > 0:
            welt.objekte.append(WaffeAmBoden(self.ding.art, self.rest, x, self.y, lebensdauer=10.0))
            welt.effekte.staub(x, self.y, 3)
        else:
            welt.effekte.splitter(x, self.y, 10, [HOLZ, grafik.dunkler(HOLZ)], 10)
            welt.ton.spiele("knack")

    def zeichne_boden(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y)
        grafik.zeichne_schatten(flaeche, sx, sy + 2, max(18.0, self.breite * 1.1 / (1 + self.z / 120)))

    def zeichnen(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y, self.z)
        if self.ding.schwer:
            zeichne_requisit(flaeche, self.ding.prop, round(sx), round(sy + 6))
            return
        mx, my = sx, sy - 7
        dx, dy = math.cos(self.drehung) * 28, math.sin(self.drehung) * 28
        zeichne_schlaeger(flaeche, (mx - dx, my - dy), (mx + dx, my + dy), 1.0, self.rest / self.ding.maximum)


class Waffenverteiler:
    """Entscheidet, wann eine Waffe herausfällt. Schutz gegen zu viele Waffen:

      - höchstens so viele Waffen am Boden wie Spieler
      - mindestens DROP_MINDESTABSTAND Sekunden zwischen zwei Drops
      - trägt schon jemand eine Waffe, ist die Chance halbiert
      - Pity-Timer: kam lange nichts, ist die Chance höher
      - die erste zerschlagene Kiste enthält immer einen Schläger (so lernt man das Aufheben)
    """

    def __init__(self):
        self.letzter = None  # Spielzeit des letzten Drops
        self.anzahl = 0
        self.kiste_garantiert = True

    def wuerfle(self, quelle, x, y, welt):
        """Gibt True zurück, wenn eine Waffe herausgefallen ist."""
        aktive = [s for s in welt.spieler if not s.ausgeschieden]
        if not aktive:
            return False
        if quelle == "kiste" and self.kiste_garantiert:
            self.kiste_garantiert = False
            return self.abwerfen(x, y, welt)
        chance = CHANCEN.get(quelle, 0.0)
        if chance <= 0:
            return False
        liegend = sum(1 for o in welt.objekte if isinstance(o, WaffeAmBoden) and not o.entfernen)
        if liegend >= len(aktive):
            return False
        if self.letzter is not None and welt.spielzeit - self.letzter < e.DROP_MINDESTABSTAND:
            return False
        if any(s.trage is not None and not s.trage.schwer for s in aktive):
            chance *= 0.5
        if welt.spielzeit - (self.letzter or 0.0) > e.DROP_PITY_ZEIT:
            chance *= e.DROP_PITY_FAKTOR
        if random.random() >= chance:
            return False
        return self.abwerfen(x, y, welt)

    def abwerfen(self, x, y, welt):
        art = random.choices(list(WAFFEN_POOL), list(WAFFEN_POOL.values()))[0]
        x = max(welt.kamera.x + 30, min(welt.kamera.x + e.BREITE - 30, x))
        welt.objekte.append(WaffeAmBoden(art, ARTEN[art]["haltbarkeit"], x, y))
        self.letzter = welt.spielzeit
        self.anzahl += 1
        return True
