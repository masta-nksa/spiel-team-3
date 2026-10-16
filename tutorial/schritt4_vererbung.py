# Schritt 4: Vererbung (Stern und Stein) und die Runde als Klasse
# Starten: python tutorial/schritt4_vererbung.py  (oder im Ordner tutorial: python schritt4_vererbung.py)
import asyncio
import math
import random

import pygame

BREITE = 800
HOEHE = 450


class Spieler(pygame.sprite.Sprite):
    """Wie in Schritt 2."""

    GESCHWINDIGKEIT = 420

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((80, 18), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (80, 160, 255), self.image.get_rect(), border_radius=8)
        self.rect = self.image.get_rect(midbottom=(BREITE / 2, HOEHE - 20))
        self.x = float(self.rect.centerx)

    def update(self, dt):
        schritt = self.GESCHWINDIGKEIT * dt
        if pygame.mouse.get_pressed()[0]:
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
        self.x = max(halbe_breite, min(BREITE - halbe_breite, self.x))
        self.rect.centerx = round(self.x)


class FallendesObjekt(pygame.sprite.Sprite):
    """Gemeinsamer Bauplan: Das Fallen ist für alle gleich. Aussehen und Wirkung legen die Unterklassen fest."""

    def __init__(self, x, tempo):
        super().__init__()
        self.image = self.bild_erstellen()  # welche Methode hier läuft, hängt von der Unterklasse ab
        self.rect = self.image.get_rect(midbottom=(x, 0))
        self.y = float(self.rect.y)
        self.tempo = tempo

    def bild_erstellen(self):
        raise NotImplementedError("Jede Unterklasse braucht ein eigenes Bild.")

    def beim_fangen(self, szene):
        raise NotImplementedError("Jede Unterklasse legt fest, was beim Fangen passiert.")

    def update(self, dt):
        self.y += self.tempo * dt
        self.rect.y = round(self.y)
        if self.rect.top > HOEHE:
            self.kill()


class Stern(FallendesObjekt):
    def bild_erstellen(self):
        bild = pygame.Surface((28, 28), pygame.SRCALPHA)
        ecken = []
        for i in range(10):
            radius = 14 if i % 2 == 0 else 6
            winkel = math.pi / 5 * i - math.pi / 2
            ecken.append((14 + radius * math.cos(winkel), 14 + radius * math.sin(winkel)))
        pygame.draw.polygon(bild, (255, 210, 60), ecken)
        return bild

    def beim_fangen(self, szene):
        szene.punkte += 1


class Stein(FallendesObjekt):
    def bild_erstellen(self):
        bild = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(bild, (130, 130, 145), bild.get_rect(), border_radius=6)
        return bild

    def beim_fangen(self, szene):
        szene.verloren()


class SpielSzene:
    """Eine Runde: Sie hält alles zusammen, was zum Spiel gehört, und hat drei Methoden."""

    def __init__(self):
        self.spieler = Spieler()
        self.fallende = pygame.sprite.Group()
        self.punkte = 0
        self.zeit = 0.0
        self.bis_zum_naechsten = 0.0
        self.vorbei = False
        self.schrift = pygame.font.Font(None, 32)

    def verloren(self):
        self.vorbei = True

    def aktualisieren(self, dt):
        if self.vorbei:
            return
        self.zeit += dt
        self.spieler.update(dt)
        self.fallende.update(dt)

        self.bis_zum_naechsten -= dt
        if self.bis_zum_naechsten <= 0:
            x = random.randint(20, BREITE - 20)
            tempo = 160 + self.zeit * 6  # wird mit der Zeit schneller
            art = Stein if random.random() < 0.3 else Stern  # eine Klasse in einer Variablen
            self.fallende.add(art(x, tempo))
            self.bis_zum_naechsten = max(0.25, 0.9 - self.zeit * 0.01)

        # Polymorphie: Wir fragen nicht, ob es ein Stern oder ein Stein ist. Jedes Objekt weiss es selbst.
        for objekt in pygame.sprite.spritecollide(self.spieler, self.fallende, dokill=True):
            objekt.beim_fangen(self)

    def zeichnen(self, flaeche):
        flaeche.fill((18, 22, 40))
        self.fallende.draw(flaeche)
        flaeche.blit(self.spieler.image, self.spieler.rect)
        flaeche.blit(self.schrift.render(f"Punkte: {self.punkte}", True, (235, 235, 245)), (20, 15))
        if self.vorbei:
            text = self.schrift.render("Game Over, Leertaste: nochmal", True, (255, 210, 60))
            flaeche.blit(text, text.get_rect(center=(BREITE / 2, HOEHE / 2)))


async def main():
    pygame.init()
    flaeche = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption("Schritt 4: Vererbung")
    uhr = pygame.time.Clock()

    szene = SpielSzene()
    laeuft = True

    while laeuft:
        dt = min(uhr.tick(60) / 1000, 0.05)

        for ereignis in pygame.event.get():
            if ereignis.type == pygame.QUIT:
                laeuft = False
            elif ereignis.type == pygame.KEYDOWN and ereignis.key == pygame.K_SPACE and szene.vorbei:
                szene = SpielSzene()  # neue Runde: einfach ein neues Objekt

        szene.aktualisieren(dt)
        szene.zeichnen(flaeche)
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
