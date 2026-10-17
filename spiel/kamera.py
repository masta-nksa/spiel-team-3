"""Scrollende Kamera, die beide Spieler im Bild behält.

Die Kamera schaut auf die Mitte zwischen den Spielern. Sie scrollt nur vorwärts
(wie in klassischen Beat-'em-ups) und bleibt bei einer Gegnerwelle stehen
(sperre), bis alle Gegner besiegt sind. Am Levelende ist ebenfalls Schluss.
Die Spieler selbst dürfen den Bildausschnitt nie verlassen (siehe Spieler.grenzen_x),
deshalb muss niemand auf den anderen warten, der Vordere wird einfach am Rand gebremst.
"""
import random

import einstellungen as e

RAND = 60  # so viel Platz bleibt mindestens zwischen Spieler und Bildrand


class Kamera:
    def __init__(self, level_breite):
        self.level_breite = level_breite
        self.x = 0.0
        self.links = 0.0  # weiter zurück geht es nicht mehr
        self.sperre = None  # x, an dem die Kamera stehen bleibt (Gegnerwelle)
        self.wackel_staerke = 0.0
        self.wackel_x = 0
        self.wackel_y = 0

    @property
    def rechts(self):
        ende = self.level_breite - e.BREITE
        return ende if self.sperre is None else min(ende, self.sperre)

    @property
    def ist_am_ende(self):
        return self.x >= self.level_breite - e.BREITE - 1

    def update(self, dt, spieler_x):
        ziel = self.x
        if spieler_x:
            mitte = sum(spieler_x) / len(spieler_x)
            ziel = mitte - e.BREITE / 2 + 80  # etwas Blick nach vorne, dorthin geht's
            # Niemand darf hinten aus dem Bild fallen
            ziel = min(ziel, min(spieler_x) - RAND)
        ziel = max(self.links, min(self.rechts, ziel))

        self.x += (ziel - self.x) * min(1.0, dt * 5)
        self.links = max(self.links, self.x)  # nur vorwärts scrollen

        # Bildschirmwackeln klingt schnell ab
        if self.wackel_staerke > 0.3:
            self.wackel_x = random.uniform(-1, 1) * self.wackel_staerke
            self.wackel_y = random.uniform(-1, 1) * self.wackel_staerke * 0.6
            self.wackel_staerke *= max(0.0, 1 - dt * 12)
        else:
            self.wackel_staerke = 0.0
            self.wackel_x = self.wackel_y = 0

    def wackeln(self, staerke):
        self.wackel_staerke = max(self.wackel_staerke, staerke)

    def zu_bild(self, x, y, z=0.0):
        """Weltkoordinaten -> Bildschirm. Höhe z zieht die Figur nach oben."""
        return (x - self.x + self.wackel_x, y - z + self.wackel_y)

    def ist_sichtbar(self, x, rand=100):
        return self.x - rand < x < self.x + e.BREITE + rand
