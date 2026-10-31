"""Objekte im Level: Requisiten (Kisten, Fässer, Laternen) und Gegenstände zum Aufheben.

Requisiten stehen auf der Strasse wie Figuren. Sie haben eine Körperbox
(man läuft nicht durch sie hindurch) und werden ebenfalls nach ihrem Fusspunkt
sortiert gezeichnet: Wer hinter einer Laterne steht, wird von ihr verdeckt.
Zerbrechliche Requisiten haben zusätzlich eine Hurtbox und lassen beim Zerbrechen
etwas fallen.
"""
import functools
import math
import random

import pygame

import einstellungen as e
import grafik
from kampf import Box


class Objekt:
    team = "objekt"
    breite = 40  # Körperbox
    tiefe = 10
    hoehe = 40  # wer höher springt, fliegt drüber
    blockiert = True
    zerstoerbar = False
    max_hp = 1
    quelle = None  # Name für die Waffen-Drops (siehe waffen.CHANCEN)

    def __init__(self, x, y):
        self.x, self.y, self.z = float(x), float(y), 0.0
        self.hp = self.max_hp
        self.wackel = 0.0
        self.entfernen = False
        self.zeit = random.random() * 5

    @property
    def sortier_y(self):
        return self.y

    @property
    def ist_ziel(self):
        return False

    def koerperbox(self):
        if not self.blockiert:
            return None
        return (self.x - self.breite / 2, self.x + self.breite / 2, self.y - self.tiefe, self.y + self.tiefe)

    def hurtbox(self):
        if not self.zerstoerbar:
            return None
        return Box(self.x - self.breite / 2, self.x + self.breite / 2,
                   self.y - self.tiefe - 6, self.y + self.tiefe + 6, 0, self.hoehe)

    def nimm_treffer(self, angreifer, angriff, welt):
        self.hp -= 1
        self.wackel = 0.25
        welt.effekte.splitter(self.x, self.y, self.hoehe * 0.6, self.splitter_farben(), 5)
        if self.hp <= 0:
            self.entfernen = True
            welt.ton.spiele("bruch")
            welt.effekte.splitter(self.x, self.y, self.hoehe * 0.5, self.splitter_farben(), 16)
            beute = self.beute()
            if beute:
                welt.objekte.append(beute(self.x, self.y))
            if self.quelle:
                welt.waffen.wuerfle(self.quelle, self.x + 18, self.y, welt)
        return False

    def splitter_farben(self):
        return [(150, 100, 50)]

    def beute(self):
        return None

    def update(self, dt, welt):
        self.zeit += dt
        self.wackel = max(0.0, self.wackel - dt)

    def bild_pos(self, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y)
        if self.wackel > 0:
            sx += math.sin(self.wackel * 80) * 3
        return round(sx), round(sy)

    def zeichne_boden(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y)
        grafik.zeichne_schatten(flaeche, sx + 4, sy + 2, self.breite * 1.3)

    def zeichnen(self, flaeche, kamera):
        pass


class Kiste(Objekt):
    breite, tiefe, hoehe = 46, 12, 44
    zerstoerbar = True
    quelle = "kiste"
    max_hp = 3

    def splitter_farben(self):
        return [(170, 115, 60), (130, 85, 40), (200, 150, 90)]

    def beute(self):
        return random.choices([Huhn, Apfel, Geld], [3, 3, 3])[0]

    def zeichnen(self, flaeche, kamera):
        sx, sy = self.bild_pos(kamera)
        b, h = self.breite, self.hoehe
        vorne = pygame.Rect(sx - b // 2, sy - h + 8, b, h)
        oben = [(vorne.left, vorne.top), (vorne.right, vorne.top), (vorne.right - 6, vorne.top - 12), (vorne.left + 6, vorne.top - 12)]
        pygame.draw.polygon(flaeche, (196, 146, 84), oben)
        pygame.draw.polygon(flaeche, e.UMRISS, oben, 2)
        pygame.draw.rect(flaeche, (165, 112, 58), vorne)
        for i in range(1, 4):
            y = vorne.top + i * h // 4
            pygame.draw.line(flaeche, (125, 82, 40), (vorne.left, y), (vorne.right, y), 2)
        pygame.draw.line(flaeche, (120, 78, 38), vorne.topleft, vorne.bottomright, 4)
        pygame.draw.rect(flaeche, (130, 86, 42), vorne, 5)
        pygame.draw.rect(flaeche, e.UMRISS, vorne, 2)
        if self.hp < self.max_hp:
            pygame.draw.line(flaeche, e.UMRISS, (sx - 4, vorne.top + 6), (sx + 6, vorne.top + 20), 2)


class Fass(Objekt):
    breite, tiefe, hoehe = 32, 10, 50
    zerstoerbar = True
    quelle = "fass"
    max_hp = 3

    def __init__(self, x, y):
        super().__init__(x, y)
        self.farbe = random.choice([(40, 90, 170), (170, 50, 40), (60, 120, 70)])

    def splitter_farben(self):
        return [self.farbe, grafik.dunkler(self.farbe), (60, 60, 60)]

    def beute(self):
        return random.choice([Geld, Huhn])

    def zeichnen(self, flaeche, kamera):
        sx, sy = self.bild_pos(kamera)
        b, h = self.breite, self.hoehe
        koerper = pygame.Rect(sx - b // 2, sy - h + 6, b, h)
        pygame.draw.rect(flaeche, self.farbe, koerper)
        pygame.draw.rect(flaeche, grafik.heller(self.farbe, 0.25), (koerper.left + 5, koerper.top, 6, h))
        pygame.draw.rect(flaeche, grafik.dunkler(self.farbe), (koerper.right - 8, koerper.top, 8, h))
        for anteil in (0.2, 0.75):
            y = koerper.top + int(h * anteil)
            pygame.draw.line(flaeche, grafik.dunkler(self.farbe, 0.55), (koerper.left, y), (koerper.right, y), 3)
        pygame.draw.ellipse(flaeche, grafik.dunkler(self.farbe, 0.6), (koerper.left, koerper.bottom - 6, b, 12))
        pygame.draw.rect(flaeche, e.UMRISS, koerper, 2)
        deckel = pygame.Rect(koerper.left, koerper.top - 6, b, 12)
        pygame.draw.ellipse(flaeche, grafik.heller(self.farbe, 0.15), deckel)
        pygame.draw.ellipse(flaeche, e.UMRISS, deckel, 2)
        pygame.draw.circle(flaeche, grafik.dunkler(self.farbe, 0.5), (sx + 6, koerper.top), 3)


class Muelltonne(Objekt):
    breite, tiefe, hoehe = 34, 10, 46
    zerstoerbar = True
    quelle = "tonne"
    max_hp = 2

    def splitter_farben(self):
        return [(150, 155, 160), (110, 115, 120), (90, 140, 70)]

    def beute(self):
        return random.choice([Apfel, Apfel, None])

    def zeichnen(self, flaeche, kamera):
        sx, sy = self.bild_pos(kamera)
        b, h = self.breite, self.hoehe
        koerper = [(sx - b // 2, sy - h + 10), (sx + b // 2, sy - h + 10), (sx + b // 2 - 4, sy + 6), (sx - b // 2 + 4, sy + 6)]
        pygame.draw.polygon(flaeche, (140, 146, 152), koerper)
        for i in range(-2, 3):
            x = sx + i * 6
            pygame.draw.line(flaeche, (110, 115, 122), (x, sy - h + 14), (x, sy + 3), 2)
        pygame.draw.polygon(flaeche, e.UMRISS, koerper, 2)
        deckel = pygame.Rect(sx - b // 2 - 3, sy - h + 2, b + 6, 12)
        pygame.draw.ellipse(flaeche, (165, 170, 176), deckel)
        pygame.draw.ellipse(flaeche, e.UMRISS, deckel, 2)
        pygame.draw.rect(flaeche, e.UMRISS, (sx - 5, sy - h - 1, 10, 4))


@functools.cache
def lichtschein():
    """Weicher Lichtkegel, wird mit BLEND_ADD aufaddiert (hellt auf, statt zu überdecken)."""
    bild = pygame.Surface((160, 160))
    for r in range(80, 0, -4):
        wert = int(46 * (1 - r / 80) ** 1.5)
        pygame.draw.circle(bild, (wert, int(wert * 0.85), int(wert * 0.5)), (80, 80), r)
    return bild


class Laterne(Objekt):
    """Hohe Strassenlaterne. Sie verdeckt Figuren, die dahinter stehen (Y-Sorting!)."""
    breite, tiefe, hoehe = 12, 5, 230
    blockiert = True

    def zeichne_boden(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y)
        grafik.zeichne_schatten(flaeche, sx, sy + 1, 26)
        flaeche.blit(lichtschein(), (sx + 6, sy - 90), special_flags=pygame.BLEND_ADD)

    def zeichnen(self, flaeche, kamera):
        sx, sy = self.bild_pos(kamera)
        oben = sy - self.hoehe
        pygame.draw.rect(flaeche, (40, 44, 56), (sx - 7, sy - 16, 14, 18), border_radius=3)
        pygame.draw.rect(flaeche, (52, 58, 72), (sx - 3, oben, 7, self.hoehe - 14))
        pygame.draw.line(flaeche, (80, 88, 104), (sx - 1, oben), (sx - 1, sy - 16), 2)
        pygame.draw.lines(flaeche, (52, 58, 72), False, [(sx, oben + 4), (sx + 14, oben - 8), (sx + 40, oben - 8)], 5)
        kopf = [(sx + 28, oben - 12), (sx + 56, oben - 12), (sx + 50, oben - 2), (sx + 34, oben - 2)]
        pygame.draw.polygon(flaeche, (40, 44, 56), kopf)
        pygame.draw.ellipse(flaeche, (255, 236, 160), (sx + 34, oben - 5, 16, 6))
        flaeche.blit(lichtschein(), (sx - 38, oben - 70), special_flags=pygame.BLEND_ADD)


# --- Gegenstände zum Aufheben ------------------------------------------------------

class Gegenstand(Objekt):
    blockiert = False
    breite, tiefe, hoehe = 24, 8, 16
    lebensdauer = 14.0

    def update(self, dt, welt):
        super().update(dt, welt)
        if self.zeit > self.lebensdauer:
            self.entfernen = True

    def beruehrt(self, spieler):
        return abs(spieler.x - self.x) < 26 and abs(spieler.y - self.y) < 16 and spieler.z < 10

    def aufheben(self, spieler, welt):
        self.entfernen = True
        welt.ton.spiele("einsammeln")

    def zeichne_boden(self, flaeche, kamera):
        sx, sy = kamera.zu_bild(self.x, self.y)
        grafik.zeichne_schatten(flaeche, sx, sy + 2, 26)

    def zeichnen(self, flaeche, kamera):
        if self.zeit > self.lebensdauer - 3 and int(self.zeit * 10) % 2:
            return  # blinkt kurz bevor es verschwindet
        sx, sy = kamera.zu_bild(self.x, self.y)
        self.bild(flaeche, sx, sy - 6 - 3 * abs(math.sin(self.zeit * 4)))

    def bild(self, flaeche, sx, sy):
        pass


class Huhn(Gegenstand):
    heilung = 40

    def __init__(self, x, y):
        super().__init__(x, y)
        self.zeit = 0.0

    def aufheben(self, spieler, welt):
        super().aufheben(spieler, welt)
        spieler.hp = min(spieler.max_hp, spieler.hp + self.heilung)
        welt.effekte.text(self.x, self.y, 70, f"+{self.heilung} HP", e.GRUEN)

    def bild(self, flaeche, sx, sy):
        pygame.draw.ellipse(flaeche, (235, 235, 240), (sx - 18, sy - 4, 36, 12))
        pygame.draw.ellipse(flaeche, e.UMRISS, (sx - 18, sy - 4, 36, 12), 2)
        pygame.draw.ellipse(flaeche, (190, 110, 45), (sx - 13, sy - 14, 22, 16))
        pygame.draw.ellipse(flaeche, e.UMRISS, (sx - 13, sy - 14, 22, 16), 2)
        pygame.draw.line(flaeche, (250, 245, 230), (sx + 6, sy - 6), (sx + 15, sy - 11), 4)
        pygame.draw.circle(flaeche, (250, 245, 230), (sx + 16, sy - 12), 3)
        pygame.draw.ellipse(flaeche, (225, 150, 80), (sx - 9, sy - 12, 9, 5))


class Apfel(Gegenstand):
    heilung = 15

    def __init__(self, x, y):
        super().__init__(x, y)
        self.zeit = 0.0

    def aufheben(self, spieler, welt):
        super().aufheben(spieler, welt)
        spieler.hp = min(spieler.max_hp, spieler.hp + self.heilung)
        welt.effekte.text(self.x, self.y, 70, f"+{self.heilung} HP", e.GRUEN)

    def bild(self, flaeche, sx, sy):
        pygame.draw.circle(flaeche, (215, 35, 40), (sx, sy - 6), 9)
        pygame.draw.circle(flaeche, e.UMRISS, (sx, sy - 6), 9, 2)
        pygame.draw.circle(flaeche, (255, 140, 140), (sx - 3, sy - 9), 2)
        pygame.draw.line(flaeche, (90, 60, 30), (sx, sy - 14), (sx + 1, sy - 19), 2)
        pygame.draw.ellipse(flaeche, (70, 180, 70), (sx + 2, sy - 20, 9, 5))


class Geld(Gegenstand):
    wert = 1000

    def __init__(self, x, y):
        super().__init__(x, y)
        self.zeit = 0.0

    def aufheben(self, spieler, welt):
        super().aufheben(spieler, welt)
        spieler.punkte += self.wert
        welt.effekte.text(self.x, self.y, 70, f"+{self.wert}", e.GELB)

    def bild(self, flaeche, sx, sy):
        for i, (dx, dy) in enumerate(((-8, 0), (6, 0), (-1, -5), (0, -10))):
            rahmen = pygame.Rect(sx + dx - 9, sy + dy - 5, 18, 8)
            pygame.draw.ellipse(flaeche, (200, 160, 40), rahmen.move(0, 2))
            pygame.draw.ellipse(flaeche, (255, 215, 70), rahmen)
            pygame.draw.ellipse(flaeche, e.UMRISS, rahmen, 1)
        glanz = int(abs(math.sin(self.zeit * 3)) * 255)
        pygame.draw.circle(flaeche, (255, 255, glanz), (sx + 3, sy - 14), 2)


REQUISITEN = {"kiste": Kiste, "fass": Fass, "tonne": Muelltonne, "laterne": Laterne}
