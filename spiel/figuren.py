import math

import pygame

import einstellungen as e


class Spieler(pygame.sprite.Sprite):
    """Die Schale unten, die du mit Pfeiltasten, A/D oder Maus/Finger bewegst."""

    GESCHWINDIGKEIT = 420  # Pixel pro Sekunde

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((80, 18), pygame.SRCALPHA)
        pygame.draw.rect(self.image, e.BLAU, self.image.get_rect(), border_radius=8)
        self.rect = self.image.get_rect(midbottom=(e.BREITE / 2, e.HOEHE - 20))
        # Genaue Position als Kommazahl. rect kennt nur ganze Pixel, kleine Schritte gingen sonst verloren.
        self.x = float(self.rect.centerx)

    def update(self, dt):
        schritt = self.GESCHWINDIGKEIT * dt

        if pygame.mouse.get_pressed()[0]:
            # Maus gedrückt oder Finger auf dem Handy: zur Zeigerposition fahren, ohne darüber hinaus.
            abstand = pygame.mouse.get_pos()[0] - self.x
            self.x += max(-schritt, min(schritt, abstand))
        else:
            tasten = pygame.key.get_pressed()
            richtung = 0
            if tasten[pygame.K_LEFT] or tasten[pygame.K_a]:
                richtung -= 1
            if tasten[pygame.K_RIGHT] or tasten[pygame.K_d]:
                richtung += 1
            self.x += richtung * schritt

        halbe_breite = self.rect.width / 2
        self.x = max(halbe_breite, min(e.BREITE - halbe_breite, self.x))
        self.rect.centerx = round(self.x)


class FallendesObjekt(pygame.sprite.Sprite):
    """Gemeinsamer Bauplan für alles, was von oben herunterfällt.

    Unterklassen legen nur fest, wie sie aussehen (bild_erstellen) und was beim
    Fangen passiert (beim_fangen). Fallen und Verschwinden erben sie von hier.
    """

    def __init__(self, x, tempo):
        super().__init__()
        self.image = self.bild_erstellen()
        self.rect = self.image.get_rect(midbottom=(x, 0))
        self.y = float(self.rect.y)
        self.tempo = tempo  # Pixel pro Sekunde

    def bild_erstellen(self):
        raise NotImplementedError("Jede Unterklasse braucht ein eigenes Bild.")

    def beim_fangen(self, szene):
        raise NotImplementedError("Jede Unterklasse legt fest, was beim Fangen passiert.")

    def update(self, dt):
        self.y += self.tempo * dt
        self.rect.y = round(self.y)
        if self.rect.top > e.HOEHE:
            self.kill()  # aus allen Gruppen entfernen, sonst sammeln sich unsichtbare Objekte an


class Stern(FallendesObjekt):
    """Gibt einen Punkt."""

    def bild_erstellen(self):
        groesse = 28
        bild = pygame.Surface((groesse, groesse), pygame.SRCALPHA)
        mitte = groesse / 2
        ecken = []
        for i in range(10):
            radius = mitte if i % 2 == 0 else mitte * 0.45
            winkel = math.pi / 5 * i - math.pi / 2
            ecken.append((mitte + radius * math.cos(winkel), mitte + radius * math.sin(winkel)))
        pygame.draw.polygon(bild, e.GELB, ecken)
        return bild

    def beim_fangen(self, szene):
        szene.punkte += 1


class Stein(FallendesObjekt):
    """Beendet das Spiel."""

    def bild_erstellen(self):
        bild = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(bild, e.GRAU, bild.get_rect(), border_radius=6)
        return bild

    def beim_fangen(self, szene):
        szene.verloren()
