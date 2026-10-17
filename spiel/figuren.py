"""Kämpfer: gemeinsame Basisklasse für Spieler und Gegner, dazu die Spielerfigur.

Jeder Kämpfer ist ein Zustandsautomat. Der Zustand bestimmt, was die Figur
gerade kann und welche Pose gezeichnet wird:

  stehen / gehen   frei steuerbar
  springen         in der Luft, Sprungangriff möglich
  angriff          ein Angriff läuft (Anlauf -> aktiv -> Erholung)
  getroffen        kurz wehrlos nach einem Treffer (Trefferstarre)
  fallen           umgeworfen, fliegt durch die Luft
  liegen           am Boden, unverwundbar
  aufstehen        steht wieder auf
  tot              blinkt und verschwindet (Gegner) oder steigt neu ein (Spieler)

Für jeden Zustand gibt es eine Methode mit Unterstrich, z. B. _fallen. update ruft
die passende Methode über ihren Namen auf. Wer einen neuen Zustand will, schreibt
einfach eine neue Methode.
"""
import random

import einstellungen as e
import grafik
import posen
from kampf import ANGRIFFE, SPRUNG_ANGRIFFE, START_ANGRIFFE, Box
from skins import SKINS


def gegen_null(wert, abbau, dt):
    """Zieht eine Geschwindigkeit gleichmässig Richtung 0 (Reibung)."""
    if wert > 0:
        return max(0.0, wert - abbau * dt)
    return min(0.0, wert + abbau * dt)


class Kaempfer:
    team = ""

    def __init__(self, skin, x, y, max_hp, skala=1.0):
        self.skin = SKINS[skin]
        self.name = self.skin["name"]
        self.x, self.y, self.z = float(x), float(y), 0.0
        self.vx = self.vy = self.vz = 0.0
        self.blick = 1
        self.skala = skala
        self.max_hp = self.hp = max_hp
        self.gewicht = 1.0  # schwere Figuren fliegen weniger weit

        self.zustand = "stehen"
        self.zustand_zeit = 0.0
        self.anim_zeit = random.random() * 3

        self.angriff = None
        self.angriff_zeit = 0.0
        self.getroffene = set()  # wer von diesem Angriff schon getroffen wurde (jeder nur einmal)
        self.angriff_traf = False
        self.puffer = None  # gedrückte, aber noch nicht ausgeführte Aktion
        self.puffer_zeit = 0.0

        self.starre = 0.0
        self.unverwundbar = 0.0
        self.blitz = 0.0
        self.abgeprallt = False
        self.treffer_serie = 0  # Treffer hintereinander, ohne sich zu erholen
        self.letzter_angreifer = None
        self.entfernen = False

        self.breite = 30 * skala  # Hurtbox-Breite
        self.hoehe = grafik.FIGUR_HOEHE * skala  # Hurtbox-Höhe
        self.fuss_breite = 24 * skala  # Körperbox (nur Fussfläche)

    # --- Abfragen ---------------------------------------------------------------

    @property
    def sortier_y(self):
        """Nach diesem Wert wird gezeichnet (Y-Sorting): wer weiter vorne steht, kommt später."""
        return self.y

    @property
    def kann_handeln(self):
        return self.zustand in ("stehen", "gehen")

    @property
    def ist_ziel(self):
        """Kann man diese Figur gerade angreifen?"""
        return self.hp > 0 and self.zustand not in ("tot",) and not self.entfernen

    def angriffs_phase(self):
        a, t = self.angriff, self.angriff_zeit
        if t < a.anlauf:
            return "anlauf"
        if t < a.anlauf + a.aktiv:
            return "aktiv"
        return "erholung"

    # --- Boxen ------------------------------------------------------------------

    def koerperbox(self):
        """Fussfläche (x1, x2, y1, y2) zum Wegschieben. Liegende und Fliegende schieben nicht."""
        if self.zustand in ("fallen", "liegen", "tot") or self.z > 30:
            return None
        h = self.fuss_breite / 2
        return (self.x - h, self.x + h, self.y - 5, self.y + 5)

    def hurtbox(self):
        if self.zustand in ("fallen", "liegen", "aufstehen", "tot") or self.unverwundbar > 0:
            return None
        h = self.breite / 2
        return Box(self.x - h, self.x + h, self.y - 10, self.y + 10, self.z, self.z + self.hoehe)

    def hitbox(self):
        if self.zustand != "angriff" or self.angriffs_phase() != "aktiv":
            return None
        a, s = self.angriff, self.skala
        von, bis = a.vorne[0] * s, a.vorne[1] * s
        if a.rundum or self.blick > 0:
            x1, x2 = self.x + von, self.x + bis
        else:
            x1, x2 = self.x - bis, self.x - von
        return Box(x1, x2, self.y - a.tiefe, self.y + a.tiefe, self.z + a.hoehe[0] * s, self.z + a.hoehe[1] * s)

    # --- Zustände wechseln ------------------------------------------------------

    def wechsle(self, zustand):
        if zustand != self.zustand:
            self.zustand = zustand
            self.zustand_zeit = 0.0
        if zustand != "angriff":
            self.angriff = None

    def starte_angriff(self, name, welt):
        a = ANGRIFFE[name]
        if a.kosten:
            self.hp = max(1, self.hp - a.kosten)
        self.zustand = "angriff"
        self.zustand_zeit = 0.0
        self.angriff = a
        self.angriff_zeit = 0.0
        self.getroffene = set()
        self.angriff_traf = False
        self.puffer = None
        if not a.in_der_luft:
            self.vx = self.vy = 0.0
        welt.ton.spiele("wusch")

    def nimm_treffer(self, angreifer, angriff, welt):
        """Gibt True zurück, wenn die Figur umgeworfen wurde."""
        self.hp = max(0, self.hp - angriff.schaden)
        self.blitz = 0.12
        self.letzter_angreifer = angreifer
        self.puffer = None
        richtung = angreifer.blick
        if angriff.rundum:
            richtung = 1 if self.x >= angreifer.x else -1
        self.blick = -richtung  # dreht sich zum Angreifer
        stoss = angriff.rueckstoss / self.gewicht
        # Wer schon wehrlos ist und weiter getroffen wird, fällt irgendwann um.
        # So kann niemand endlos in der Trefferstarre gehalten werden.
        self.treffer_serie = self.treffer_serie + 1 if self.zustand == "getroffen" else 1

        if angriff.wirft_um or self.hp <= 0 or self.z > 0 or self.treffer_serie >= 4:
            self.wechsle("fallen")
            self.abgeprallt = False
            self.vx = richtung * max(stoss, 150)
            self.vy = 0.0
            self.vz = 420 / self.gewicht ** 0.5
            return True
        self.wechsle("getroffen")
        self.starre = angriff.starre
        self.vx = richtung * stoss
        self.vy = 0.0
        return False

    def treffer_gelandet(self, ziel, angriff, welt):
        """Wird aufgerufen, wenn der eigene Angriff etwas trifft."""
        self.angriff_traf = True

    def landen(self, welt):
        self.z = 0.0
        self.vz = 0.0
        self.vx = self.vy = 0.0
        welt.effekte.staub(self.x, self.y, 3)
        self.wechsle("stehen")

    # --- Update -----------------------------------------------------------------

    def update(self, dt, welt):
        self.anim_zeit += dt
        self.zustand_zeit += dt
        self.unverwundbar = max(0.0, self.unverwundbar - dt)
        self.blitz = max(0.0, self.blitz - dt)
        if self.puffer:
            self.puffer_zeit -= dt
            if self.puffer_zeit <= 0:
                self.puffer = None

        self.steuern(dt, welt)
        getattr(self, "_" + self.zustand)(dt, welt)
        self.physik(dt, welt)

    def steuern(self, dt, welt):
        """Spieler lesen hier die Eingabe, Gegner denken hier nach (KI)."""

    def _stehen(self, dt, welt):
        pass

    def _gehen(self, dt, welt):
        pass

    def _springen(self, dt, welt):
        if self.z <= 0 and self.vz <= 0 and self.zustand_zeit > 0.05:
            self.landen(welt)

    def _angriff(self, dt, welt):
        a = self.angriff
        self.angriff_zeit += dt
        if a.in_der_luft:
            if self.z <= 0 and self.vz <= 0 and self.zustand_zeit > 0.05:
                self.landen(welt)
            return

        phase = self.angriffs_phase()
        self.vx = a.vorschub * self.blick if phase == "aktiv" else 0.0

        # Combo: Wer getroffen hat und schon wieder gedrückt hat, darf die Erholung abbrechen
        if phase == "erholung" and self.angriff_traf and self.puffer in ("schlag", "tritt"):
            folge = a.folge_schlag if self.puffer == "schlag" else a.folge_tritt
            if folge:
                self.starte_angriff(folge, welt)
                return
        if self.angriff_zeit >= a.dauer:
            self.wechsle("stehen")

    def _getroffen(self, dt, welt):
        self.vx = gegen_null(self.vx, 500, dt)
        self.starre -= dt
        if self.starre <= 0:
            self.wechsle("stehen")

    def _fallen(self, dt, welt):
        if self.z <= 0 and self.vz <= 0 and self.zustand_zeit > 0.05:
            self.z = 0.0
            if not self.abgeprallt:
                # einmal kurz aufprallen
                self.abgeprallt = True
                self.vz = 170
                self.vx *= 0.45
                welt.effekte.staub(self.x, self.y, 6)
                welt.ton.spiele("aufprall")
                welt.wackeln(4 * self.gewicht)
            else:
                self.vx = self.vz = 0.0
                self.wechsle("liegen")

    def _liegen(self, dt, welt):
        if self.hp <= 0:
            if self.zustand_zeit > 0.5:
                self.wechsle("tot")
        elif self.zustand_zeit > 0.85:
            self.wechsle("aufstehen")

    def _aufstehen(self, dt, welt):
        if self.zustand_zeit > 0.4:
            self.wechsle("stehen")
            self.unverwundbar = 0.45

    def _tot(self, dt, welt):
        if self.zustand_zeit > 1.3:
            self.entfernen = True

    def _jubeln(self, dt, welt):
        pass

    def grenzen_x(self, welt):
        return -120, welt.level.breite + 120

    def physik(self, dt, welt):
        if self.z > 0 or self.vz > 0:
            self.vz -= e.SCHWERKRAFT * dt
            self.z = max(0.0, self.z + self.vz * dt)
        elif self.zustand not in ("fallen",):
            self.vz = 0.0

        self.x += self.vx * dt
        self.y += self.vy * dt
        links, rechts = self.grenzen_x(welt)
        self.x = max(links, min(rechts, self.x))
        self.y = max(e.BODEN_OBEN, min(e.BODEN_UNTEN, self.y))

        # Kisten, Fässer und Laternen sind im Weg
        meine = self.koerperbox()
        if meine is None:
            return
        for objekt in welt.objekte:
            andere = objekt.koerperbox()
            if andere is None or self.z > objekt.hoehe:
                continue
            x1, x2, y1, y2 = meine
            ox1, ox2, oy1, oy2 = andere
            if x1 < ox2 and ox1 < x2 and y1 < oy2 and oy1 < y2:
                # auf dem kürzesten Weg hinausschieben
                wege = [(ox2 - x1, 0), (ox1 - x2, 0), (0, oy2 - y1), (0, oy1 - y2)]
                dx, dy = min(wege, key=lambda w: abs(w[0]) + abs(w[1]))
                self.x += dx
                self.y += dy
                meine = self.koerperbox()

    # --- Zeichnen ---------------------------------------------------------------

    def aktuelle_pose(self):
        z = self.zustand
        if z == "angriff":
            a = self.angriff
            t = self.angriff_zeit / a.dauer
            if t >= 1 and self.z > 0:
                return posen.springen(0)
            return posen.angriffs_pose(a.pose, min(1.0, t), a.anlauf / a.dauer, (a.anlauf + a.aktiv) / a.dauer)
        if z == "gehen":
            return posen.gehen(self.anim_zeit)
        if z == "springen":
            return posen.springen(self.zustand_zeit)
        if z == "getroffen":
            return posen.getroffen(self.zustand_zeit)
        if z == "fallen":
            return posen.fallen(min(1.0, self.zustand_zeit / 0.45))
        if z in ("liegen", "tot"):
            return posen.liegen(0)
        if z == "aufstehen":
            return posen.aufstehen(self.zustand_zeit / 0.4)
        if z == "jubeln":
            return posen.jubeln(self.anim_zeit)
        return posen.stehen(self.anim_zeit)

    def unsichtbar_blinkend(self):
        if self.zustand == "tot":
            return int(self.zustand_zeit * 14) % 2 == 1
        return self.unverwundbar > 0.5 and int(self.anim_zeit * 16) % 2 == 1

    def zeichne_boden(self, flaeche, kamera):
        """Schatten: immer am Boden, auch wenn die Figur springt. So sieht man die Tiefe."""
        sx, sy = kamera.zu_bild(self.x, self.y, 0)
        breite = 46 * self.skala / (1 + self.z / 160)
        if self.zustand in ("liegen", "tot"):
            breite *= 2.1
        grafik.zeichne_schatten(flaeche, sx, sy, breite)

    def zeichnen(self, flaeche, kamera):
        if self.unsichtbar_blinkend():
            return
        sx, sy = kamera.zu_bild(self.x, self.y, self.z)
        if self.blitz > 0:
            sx += random.choice((-2, 2))  # zittert beim Treffer
        grafik.zeichne_figur(flaeche, self.skin, self.aktuelle_pose(), sx, sy, self.blick,
                             self.skala, weiss=self.blitz > 0.06, zeit=self.anim_zeit)


class Spieler(Kaempfer):
    team = "spieler"

    def __init__(self, nummer, steuerung, x, y):
        super().__init__("p1" if nummer == 1 else "p2", x, y, e.SPIELER_HP)
        self.nummer = nummer
        self.steuerung = steuerung
        self.farbe = e.SPIELER_FARBEN[nummer]
        self.leben = e.SPIELER_EXTRALEBEN
        self.punkte = 0
        self.combo = 0
        self.combo_zeit = 0.0
        self.beste_combo = 0
        self.ausgeschieden = False
        self.seit_taste = {}  # Aktion -> Sekunden seit dem letzten Drücken

    @property
    def ist_ziel(self):
        return super().ist_ziel and not self.ausgeschieden

    def grenzen_x(self, welt):
        # Spieler bleiben immer im Bild: die Kamera hält beide zusammen
        return welt.kamera.x + 22, welt.kamera.x + e.BREITE - 22

    def taste(self, aktion):
        """Wird von der Szene für jede gedrückte Aktionstaste aufgerufen."""
        andere = {"schlag": "tritt", "tritt": "schlag"}.get(aktion)
        if andere and self.seit_taste.get(andere, 9) < 0.09:
            aktion = "spezial"  # Schlag + Tritt gleichzeitig
            # Ein Angriff, der gerade erst anläuft, wird zum Spezialangriff
            if self.zustand == "angriff" and self.angriff.name in ("schlag1", "tritt1") and self.angriff_zeit < 0.1:
                self.wechsle("stehen")
        self.seit_taste[aktion] = 0.0
        self.puffer = aktion
        self.puffer_zeit = 0.25

    def steuern(self, dt, welt):
        for aktion in self.seit_taste:
            self.seit_taste[aktion] += dt
        if self.combo_zeit > 0:
            self.combo_zeit -= dt
            if self.combo_zeit <= 0:
                self.combo = 0

        dx, dy = self.steuerung.richtung()
        if self.kann_handeln:
            if self.puffer:
                aktion = self.puffer
                self.puffer = None
                if dx:
                    self.blick = dx
                if aktion == "sprung":
                    self.vz = e.SPRUNGKRAFT
                    self.vx = dx * e.SPIELER_TEMPO_X * 1.15
                    self.vy = dy * e.SPIELER_TEMPO_Y * 0.8
                    self.wechsle("springen")
                    welt.ton.spiele("sprung")
                elif aktion == "spezial" and self.hp <= ANGRIFFE["wirbel"].kosten + 1:
                    self.starte_angriff("schlag1", welt)  # zu schwach für den Wirbel
                else:
                    self.starte_angriff(START_ANGRIFFE[aktion], welt)
                return
            self.vx = dx * e.SPIELER_TEMPO_X
            self.vy = dy * e.SPIELER_TEMPO_Y
            if dx:
                self.blick = dx
            self.wechsle("gehen" if dx or dy else "stehen")
        elif self.zustand == "springen" and self.puffer in SPRUNG_ANGRIFFE:
            self.starte_angriff(SPRUNG_ANGRIFFE[self.puffer], welt)

    def treffer_gelandet(self, ziel, angriff, welt):
        super().treffer_gelandet(ziel, angriff, welt)
        if ziel.team != "gegner":
            return
        self.combo += 1
        self.combo_zeit = e.COMBO_ZEIT
        self.beste_combo = max(self.beste_combo, self.combo)
        self.punkte += angriff.schaden * 10 + (self.combo - 1) * 5

    def _tot(self, dt, welt):
        if self.zustand_zeit < 1.6:
            return
        if self.leben > 0:
            self.leben -= 1
            self.einsteigen(welt)
        else:
            self.ausgeschieden = True

    def einsteigen(self, welt):
        """Fällt von oben ins Bild, kurz unverwundbar."""
        anteil = 0.3 if self.nummer == 1 else 0.6
        self.x = welt.kamera.x + e.BREITE * anteil
        self.y = (e.BODEN_OBEN + e.BODEN_UNTEN) / 2 + (self.nummer - 1.5) * 40
        self.z = 330
        self.vx = self.vy = self.vz = 0.0
        self.hp = self.max_hp
        self.unverwundbar = 2.5
        self.blick = 1
        self.wechsle("springen")
        self.ausgeschieden = False

    def zeichne_boden(self, flaeche, kamera):
        super().zeichne_boden(flaeche, kamera)
        if self.zustand not in ("liegen", "tot", "fallen"):
            sx, sy = kamera.zu_bild(self.x, self.y, 0)
            grafik.zeichne_spielerring(flaeche, sx, sy, 50, self.farbe, self.blick)

    def zeichnen(self, flaeche, kamera):
        super().zeichnen(flaeche, kamera)
        if self.zustand not in ("liegen", "tot") and not self.unsichtbar_blinkend():
            sx, sy = kamera.zu_bild(self.x, self.y, self.z)
            grafik.text(flaeche, f"{self.nummer}P", 20, (sx, sy - self.hoehe - 14), self.farbe)
