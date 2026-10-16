import functools
import random

import pygame

import einstellungen as e
from figuren import Spieler, Stein, Stern


@functools.cache
def schrift(groesse):
    # Schriften nur einmal pro Grösse laden, nicht in jedem Bild neu.
    return pygame.font.Font(None, groesse)


def text_zeichnen(flaeche, text, groesse, mitte, farbe=e.TEXT):
    bild = schrift(groesse).render(text, True, farbe)
    flaeche.blit(bild, bild.get_rect(center=mitte))


def ist_weiter(ereignis):
    """Leertaste, Enter, Mausklick oder Antippen."""
    if ereignis.type == pygame.KEYDOWN:
        return ereignis.key in (pygame.K_SPACE, pygame.K_RETURN)
    return ereignis.type == pygame.MOUSEBUTTONDOWN


class Szene:
    """Bauplan für alle Szenen. Jede Szene überschreibt die Methoden, die sie braucht."""

    def __init__(self, spiel):
        self.spiel = spiel

    def ereignis(self, ereignis):
        """Wird für jede Taste, jeden Klick usw. einmal aufgerufen."""

    def aktualisieren(self, dt):
        """Spiellogik: Bewegen, Kollisionen, Zeitgeber. dt = Sekunden seit dem letzten Bild."""

    def zeichnen(self, flaeche):
        """Nur zeichnen, hier nichts am Spielzustand ändern."""


class MenueSzene(Szene):
    def ereignis(self, ereignis):
        if ist_weiter(ereignis):
            self.spiel.wechsle_zu(SpielSzene(self.spiel))

    def zeichnen(self, flaeche):
        flaeche.fill(e.HINTERGRUND)
        text_zeichnen(flaeche, e.TITEL, 72, (e.BREITE / 2, e.HOEHE / 2 - 50), e.GELB)
        text_zeichnen(flaeche, "Sterne fangen, Steinen ausweichen", 32, (e.BREITE / 2, e.HOEHE / 2 + 10))
        text_zeichnen(flaeche, "Leertaste oder Klick zum Starten", 28, (e.BREITE / 2, e.HOEHE / 2 + 60), e.GRAU)


class SpielSzene(Szene):
    def __init__(self, spiel):
        super().__init__(spiel)
        self.spieler = Spieler()
        self.fallende = pygame.sprite.Group()
        self.punkte = 0
        self.zeit = 0.0  # Sekunden seit Spielbeginn
        self.bis_zum_naechsten = 0.0  # Zeitgeber: Sekunden bis zum nächsten fallenden Objekt

    def ereignis(self, ereignis):
        if ereignis.type == pygame.KEYDOWN and ereignis.key == pygame.K_ESCAPE:
            self.spiel.wechsle_zu(MenueSzene(self.spiel))

    def aktualisieren(self, dt):
        self.zeit += dt
        self.spieler.update(dt)
        self.fallende.update(dt)

        # Zeitgeber mit dt statt mit Bildern zählen: läuft auf jedem Gerät gleich schnell.
        self.bis_zum_naechsten -= dt
        if self.bis_zum_naechsten <= 0:
            self.neues_objekt()
            self.bis_zum_naechsten = max(0.25, 0.9 - self.zeit * 0.01)

        # Polymorphie: Die Szene weiss nicht, ob sie einen Stern oder einen Stein gefangen hat.
        # Jedes Objekt weiss selbst, was beim Fangen passiert.
        for objekt in pygame.sprite.spritecollide(self.spieler, self.fallende, dokill=True):
            objekt.beim_fangen(self)

    def neues_objekt(self):
        x = random.randint(20, e.BREITE - 20)
        tempo = 160 + self.zeit * 6  # wird mit der Zeit schneller
        art = Stein if random.random() < 0.3 else Stern
        self.fallende.add(art(x, tempo))

    def verloren(self):
        self.spiel.rekord = max(self.spiel.rekord, self.punkte)
        self.spiel.wechsle_zu(GameOverSzene(self.spiel, self.punkte))

    def zeichnen(self, flaeche):
        flaeche.fill(e.HINTERGRUND)
        self.fallende.draw(flaeche)
        flaeche.blit(self.spieler.image, self.spieler.rect)
        text_zeichnen(flaeche, f"Punkte: {self.punkte}", 32, (80, 25))


class GameOverSzene(Szene):
    SPERRZEIT = 0.7  # Sekunden, damit man nicht aus Versehen sofort neu startet

    def __init__(self, spiel, punkte):
        super().__init__(spiel)
        self.punkte = punkte
        self.wartezeit = self.SPERRZEIT

    def ereignis(self, ereignis):
        if self.wartezeit <= 0 and ist_weiter(ereignis):
            self.spiel.wechsle_zu(SpielSzene(self.spiel))

    def aktualisieren(self, dt):
        self.wartezeit -= dt

    def zeichnen(self, flaeche):
        flaeche.fill(e.HINTERGRUND)
        text_zeichnen(flaeche, "Game Over", 72, (e.BREITE / 2, e.HOEHE / 2 - 50), e.GELB)
        text_zeichnen(flaeche, f"Punkte: {self.punkte}   Rekord: {self.spiel.rekord}", 36, (e.BREITE / 2, e.HOEHE / 2 + 10))
        if self.wartezeit <= 0:
            text_zeichnen(flaeche, "Leertaste oder Klick: nochmal", 28, (e.BREITE / 2, e.HOEHE / 2 + 60), e.GRAU)
