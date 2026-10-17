"""Effekte: Trefferfunken, Staub, Splitter, schwebender Text.

Effekte leben nur kurz und haben keinen Einfluss auf das Spiel ("Juice").
Sie liegen in Weltkoordinaten (x, y, z) und scrollen deshalb mit der Kamera mit.
"""
import math
import random

import pygame

import einstellungen as e
import grafik


class Effekt:
    dauer = 0.3

    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.alter = 0.0

    @property
    def fertig(self):
        return self.alter >= self.dauer

    def update(self, dt):
        self.alter += dt

    def zeichnen(self, flaeche, kamera):
        pass


class Funke(Effekt):
    """Sternförmiger Blitz an der Trefferstelle."""

    def __init__(self, x, y, z, gross):
        super().__init__(x, y, z)
        self.dauer = 0.16 if not gross else 0.22
        self.groesse = 26 if gross else 17
        self.winkel = random.uniform(0, math.pi)

    def zeichnen(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y, self.z)
        f = self.alter / self.dauer
        r = self.groesse * (0.6 + 0.8 * f)
        punkte = []
        for i in range(16):
            radius = r if i % 2 == 0 else r * 0.38
            w = self.winkel + i * math.pi / 8
            punkte.append((sx + math.cos(w) * radius, sy + math.sin(w) * radius))
        farbe = (255, 250, 200) if f < 0.4 else e.GELB
        pygame.draw.polygon(flaeche, e.ORANGE, punkte)
        innen = [(sx + (px - sx) * 0.6, sy + (py - sy) * 0.6) for px, py in punkte]
        pygame.draw.polygon(flaeche, farbe, innen)


class Partikel(Effekt):
    def __init__(self, x, y, z, farbe, tempo=200, groesse=3, schwerkraft=900):
        super().__init__(x, y, z)
        winkel = random.uniform(0, math.tau)
        self.vx = math.cos(winkel) * tempo * random.uniform(0.4, 1)
        self.vy = random.uniform(-30, 30)
        self.vz = abs(math.sin(winkel)) * tempo * random.uniform(0.5, 1.2) + 60
        self.farbe = farbe
        self.groesse = groesse
        self.schwerkraft = schwerkraft
        self.dauer = random.uniform(0.35, 0.7)

    def update(self, dt):
        super().update(dt)
        self.vz -= self.schwerkraft * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        if self.z < 0:
            self.z = 0
            self.vz *= -0.4
            self.vx *= 0.6

    def zeichnen(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y, self.z)
        g = self.groesse * (1 - 0.5 * self.alter / self.dauer)
        pygame.draw.rect(flaeche, self.farbe, (sx - g / 2, sy - g / 2, g, g))


class Staub(Effekt):
    """Graue Wölkchen, die sich am Boden ausbreiten."""

    def __init__(self, x, y, richtung):
        super().__init__(x, y, 0)
        self.vx = richtung * random.uniform(30, 90)
        self.dauer = random.uniform(0.35, 0.55)
        self.groesse = random.uniform(5, 9)

    def update(self, dt):
        super().update(dt)
        self.x += self.vx * dt
        self.z += 18 * dt

    def zeichnen(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y, self.z)
        f = self.alter / self.dauer
        r = self.groesse * (0.6 + f)
        hell = int(200 - 60 * f)
        pygame.draw.circle(flaeche, (hell, hell - 8, hell - 20), (sx, sy - r * 0.5), r)


class SchwebeText(Effekt):
    def __init__(self, x, y, z, inhalt, farbe, groesse=26):
        super().__init__(x, y, z)
        self.inhalt = inhalt
        self.farbe = farbe
        self.groesse = groesse
        self.dauer = 0.9

    def update(self, dt):
        super().update(dt)
        self.z += 50 * dt

    def zeichnen(self, flaeche, kamera):
        if self.alter > self.dauer * 0.7 and int(self.alter * 20) % 2:
            return
        sx, sy = kamera.zu_bild(self.x, self.y, self.z)
        grafik.text(flaeche, self.inhalt, self.groesse, (sx, sy), self.farbe)


class Effekte:
    def __init__(self):
        self.liste = []

    def update(self, dt):
        for effekt in self.liste:
            effekt.update(dt)
        self.liste = [eff for eff in self.liste if not eff.fertig]

    def zeichnen(self, flaeche, kamera):
        for effekt in self.liste:
            effekt.zeichnen(flaeche, kamera)

    # Abkürzungen, damit der Rest des Spiels einfach "welt.effekte.funke(...)" sagen kann
    def funke(self, x, y, z, gross=False):
        self.liste.append(Funke(x, y, z, gross))
        for _ in range(6 if gross else 3):
            self.liste.append(Partikel(x, y, z, random.choice((e.GELB, (255, 255, 255), e.ORANGE)), 260, 3))

    def staub(self, x, y, anzahl=4):
        for i in range(anzahl):
            self.liste.append(Staub(x, y + random.uniform(-3, 3), -1 if i % 2 else 1))

    def splitter(self, x, y, z, farben, anzahl=12):
        for _ in range(anzahl):
            self.liste.append(Partikel(x, y, z, random.choice(farben), 300, random.randint(3, 6), 1200))

    def text(self, x, y, z, inhalt, farbe=e.GELB, groesse=26):
        self.liste.append(SchwebeText(x, y, z, inhalt, farbe, groesse))
