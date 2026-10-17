"""Gegner mit KI als Zustandsautomat.

Ein Gegner hat zwei Zustände gleichzeitig:
  zustand  der Körper (stehen, angriff, getroffen, fallen ...), geerbt von Kaempfer
  ki       was er gerade vorhat:

    lauern      (Idle)    kurz stehen bleiben, dann ein Ziel suchen
    verfolgen   (Chase)   zum Ziel laufen und sich daneben in Position bringen
    angreifen   (Attack)  einen Angriff ausführen
    rueckzug    (Retreat) nach einem Angriff kurz Abstand nehmen
    getroffen   (Hurt)    solange der Körper wehrlos ist, denkt die KI nicht
    tot         (Dead)

Für jeden KI-Zustand gibt es eine Methode ki_<name>. Damit nicht alle Gegner
gleichzeitig auf denselben Spieler einprügeln, teilt die Szene jedem Spieler
höchstens MAX_ANGREIFER Angreifer zu (darf_angreifen). Die anderen warten
mit etwas Abstand und kreisen um das Geschehen.
"""
import math
import random

import einstellungen as e
from figuren import Kaempfer, gegen_null

GEGNER_TYPEN = {
    "schlaeger": dict(
        skin="schlaeger", hp=36, skala=1.0, tempo=(118, 78), gewicht=1.0, punkte=500,
        angriffe=[("g_schlag", 3), ("g_tritt", 2)], reichweite=44, pause=(0.55, 1.3), combo=0.35,
    ),
    "flitzer": dict(
        skin="flitzer", hp=26, skala=0.95, tempo=(178, 112), gewicht=0.85, punkte=600,
        angriffe=[("g_flinktritt", 3), ("g_schlag", 1)], reichweite=48, pause=(0.3, 0.9), combo=0.2,
    ),
    "brocken": dict(
        skin="brocken", hp=80, skala=1.28, tempo=(82, 56), gewicht=1.7, punkte=1500,
        angriffe=[("g_hammer", 2), ("g_schlag", 2)], reichweite=58, pause=(0.8, 1.6), combo=0.0,
    ),
    "boss": dict(
        skin="boss", hp=210, skala=1.18, tempo=(124, 82), gewicht=1.5, punkte=5000,
        angriffe=[("g_schlag", 3), ("g_tritt", 2), ("g_hammer", 1)], reichweite=52, pause=(0.35, 0.95),
        combo=0.5, rammen=True,
    ),
}


class Gegner(Kaempfer):
    team = "gegner"

    def __init__(self, typ, x, y):
        daten = GEGNER_TYPEN[typ]
        super().__init__(daten["skin"], x, y, daten["hp"], daten["skala"])
        self.typ = typ
        self.daten = daten
        self.tempo_x, self.tempo_y = daten["tempo"]
        self.gewicht = daten["gewicht"]
        self.punkte_wert = daten["punkte"]
        self.reichweite = daten["reichweite"] * self.skala

        self.ki = "lauern"
        self.ki_zeit = 0.0
        self.ziel = None
        self.denkpause = random.uniform(0.2, 0.6)  # bis zur nächsten Zielwahl
        self.angriffs_pause = random.uniform(0.6, 1.2)
        self.rammen_pause = 3.0
        self.reaktion = random.uniform(0.3, 0.7)
        # von der Szene gesetzt: darf ich zuschlagen und auf welcher Seite des Ziels stehe ich?
        self.darf_angreifen = False
        self.seite = 1
        self.warte_versatz = random.uniform(-50, 50)
        self.rueckzug_richtung = (0, 0)

    def ki_wechsel(self, neu):
        self.ki = neu
        self.ki_zeit = 0.0

    # --- KI ---------------------------------------------------------------------

    def steuern(self, dt, welt):
        self.ki_zeit += dt
        self.denkpause -= dt
        self.angriffs_pause -= dt
        self.rammen_pause -= dt

        if self.hp <= 0 or self.zustand == "tot":
            self.ki = "tot"
            return
        if self.zustand in ("getroffen", "fallen", "liegen", "aufstehen"):
            if self.ki != "getroffen":
                self.ki_wechsel("getroffen")
            return
        if self.zustand == "angriff":
            return  # Der Körper ist beschäftigt. Weiter geht's in ki_angreifen, wenn er fertig ist.
        getattr(self, "ki_" + self.ki)(dt, welt)

    def ki_lauern(self, dt, welt):
        self.stehen_bleiben()
        if self.ki_zeit < self.reaktion:
            return
        self.ziel = self.waehle_ziel(welt)
        if self.ziel:
            self.ki_wechsel("verfolgen")

    def ki_getroffen(self, dt, welt):
        # Der Körper kann wieder handeln: entweder zurückweichen oder kurz sammeln
        self.reaktion = random.uniform(0.15, 0.45)
        if random.random() < 0.4:
            self.starte_rueckzug()
        else:
            self.ki_wechsel("lauern")

    def ki_verfolgen(self, dt, welt):
        if self.denkpause <= 0 or self.ziel is None or not self.ziel.ist_ziel:
            self.ziel = self.waehle_ziel(welt)
            self.denkpause = random.uniform(0.8, 1.5)
        ziel = self.ziel
        if ziel is None:
            self.ki_wechsel("lauern")
            return

        dx, dy = ziel.x - self.x, ziel.y - self.y
        if self.darf_angreifen:
            ziel_x = ziel.x + self.seite * self.reichweite * 0.85
            ziel_y = ziel.y
        else:
            # warten: mit Abstand daneben stehen und langsam kreisen
            abstand = 150 + 30 * math.sin(self.anim_zeit * 0.7 + self.warte_versatz)
            ziel_x = ziel.x + self.seite * abstand
            ziel_y = ziel.y + self.warte_versatz + 25 * math.sin(self.anim_zeit * 0.9)
            ziel_x = max(welt.kamera.x + 40, min(welt.kamera.x + e.BREITE - 40, ziel_x))

        self.laufe_zu(ziel_x, ziel_y, langsam=not self.darf_angreifen)
        if dx:
            self.blick = 1 if dx > 0 else -1

        if not self.darf_angreifen or not ziel.hurtbox():
            return
        # Boss: Anlauf aus der Distanz
        if (self.daten.get("rammen") and self.rammen_pause <= 0 and abs(dy) < 16
                and 170 < abs(dx) < 420):
            self.rammen_pause = random.uniform(4, 7)
            self.blick = 1 if dx > 0 else -1
            self.ki_wechsel("angreifen")
            self.starte_angriff("g_rammen", welt)
            return
        in_reichweite = self.reichweite * 0.45 < abs(dx) < self.reichweite * 1.2 and abs(dy) < 12
        if in_reichweite and self.angriffs_pause <= 0:
            self.ki_wechsel("angreifen")
            self.starte_angriff(self.waehle_angriff(), welt)
            if random.random() < self.daten["combo"]:
                self.puffer = "schlag"  # versucht eine Combo, falls der erste Schlag sitzt
                self.puffer_zeit = 2.0

    def ki_angreifen(self, dt, welt):
        # Der Angriff ist vorbei (sonst wären wir gar nicht hier)
        lo, hi = self.daten["pause"]
        self.angriffs_pause = random.uniform(lo, hi)
        if random.random() < 0.35:
            self.starte_rueckzug()
        else:
            self.ki_wechsel("verfolgen")

    def ki_rueckzug(self, dt, welt):
        rx, ry = self.rueckzug_richtung
        self.vx = rx * self.tempo_x * 0.8
        self.vy = ry * self.tempo_y * 0.8
        self.wechsle("gehen")
        if self.ziel:
            self.blick = 1 if self.ziel.x > self.x else -1
        if self.ki_zeit > self.rueckzug_dauer:
            self.ki_wechsel("verfolgen")

    def ki_tot(self, dt, welt):
        pass

    # --- Hilfen -----------------------------------------------------------------

    def starte_rueckzug(self):
        weg = -self.blick
        self.rueckzug_richtung = (weg, random.choice((-1, 0, 1)))
        self.rueckzug_dauer = random.uniform(0.35, 0.8)
        self.ki_wechsel("rueckzug")

    def stehen_bleiben(self):
        self.vx = gegen_null(self.vx, 900, 1 / 60)
        self.vy = 0.0
        self.wechsle("stehen")

    def laufe_zu(self, zx, zy, langsam=False):
        dx, dy = zx - self.x, zy - self.y
        faktor = 0.6 if langsam else 1.0
        self.vx = 0.0 if abs(dx) < 6 else math.copysign(self.tempo_x * faktor, dx)
        self.vy = 0.0 if abs(dy) < 4 else math.copysign(self.tempo_y * faktor, dy)
        # Nahe am Ziel abbremsen, sonst zappelt er hin und her
        if abs(dx) < 20:
            self.vx *= abs(dx) / 20
        if abs(dy) < 10:
            self.vy *= abs(dy) / 10
        self.wechsle("gehen" if self.vx or self.vy else "stehen")

    def waehle_ziel(self, welt):
        """Nimmt den Spieler, der am nächsten ist, und verteilt sich auf beide Spieler."""
        kandidaten = [s for s in welt.spieler if s.ist_ziel]
        if not kandidaten:
            return None

        def kosten(spieler):
            k = abs(spieler.x - self.x) + 1.5 * abs(spieler.y - self.y)
            k += 160 * sum(1 for g in welt.gegner if g is not self and g.ziel is spieler and g.hp > 0)
            if spieler is self.ziel:
                k -= 80  # nicht dauernd das Ziel wechseln
            return k + random.uniform(0, 40)

        return min(kandidaten, key=kosten)

    def waehle_angriff(self):
        namen = [n for n, _ in self.daten["angriffe"]]
        gewichte = [g for _, g in self.daten["angriffe"]]
        return random.choices(namen, gewichte)[0]

    def nimm_treffer(self, angreifer, angriff, welt):
        # Der Boss lässt sich von leichten Schlägen nicht so leicht umwerfen
        umgeworfen = super().nimm_treffer(angreifer, angriff, welt)
        if self.typ == "boss" and not umgeworfen:
            self.starre *= 0.6
        return umgeworfen
