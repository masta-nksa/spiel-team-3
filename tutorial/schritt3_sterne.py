# Schritt 3: Viele Sterne, ein Zeitgeber und Kollisionen
# Starten: python tutorial/schritt3_sterne.py  (oder im Ordner tutorial: python schritt3_sterne.py)
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


class Stern(pygame.sprite.Sprite):
    """Fällt von oben herunter und verschwindet unten."""

    def __init__(self, x, tempo):
        super().__init__()
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        ecken = []
        for i in range(10):  # 10 Ecken: abwechselnd aussen und innen
            radius = 14 if i % 2 == 0 else 6
            winkel = math.pi / 5 * i - math.pi / 2
            ecken.append((14 + radius * math.cos(winkel), 14 + radius * math.sin(winkel)))
        pygame.draw.polygon(self.image, (255, 210, 60), ecken)
        self.rect = self.image.get_rect(midbottom=(x, 0))
        self.y = float(self.rect.y)
        self.tempo = tempo

    def update(self, dt):
        self.y += self.tempo * dt
        self.rect.y = round(self.y)
        if self.rect.top > HOEHE:
            self.kill()  # aus der Gruppe entfernen, sonst sammeln sich unsichtbare Sterne an


async def main():
    pygame.init()
    flaeche = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption("Schritt 3: Sterne")
    uhr = pygame.time.Clock()
    schrift = pygame.font.Font(None, 32)

    spieler = Spieler()
    sterne = pygame.sprite.Group()  # eine Gruppe für beliebig viele Sterne
    punkte = 0
    bis_zum_naechsten = 0.0  # Zeitgeber in Sekunden
    laeuft = True

    while laeuft:
        dt = min(uhr.tick(60) / 1000, 0.05)

        for ereignis in pygame.event.get():
            if ereignis.type == pygame.QUIT:
                laeuft = False

        spieler.update(dt)
        sterne.update(dt)  # ruft update(dt) bei jedem Stern in der Gruppe auf

        # Zeitgeber: herunterzählen, bei 0 einen neuen Stern machen und neu starten
        bis_zum_naechsten -= dt
        if bis_zum_naechsten <= 0:
            sterne.add(Stern(random.randint(20, BREITE - 20), 180))
            bis_zum_naechsten = 0.8

        # Kollision: alle Sterne, die den Spieler berühren (dokill=True entfernt sie gleich)
        gefangen = pygame.sprite.spritecollide(spieler, sterne, dokill=True)
        punkte += len(gefangen)

        flaeche.fill((18, 22, 40))
        sterne.draw(flaeche)
        flaeche.blit(spieler.image, spieler.rect)
        flaeche.blit(schrift.render(f"Punkte: {punkte}", True, (235, 235, 245)), (20, 15))
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
