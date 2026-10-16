# Schritt 2: Die erste Klasse, der Spieler
# Starten: python tutorial/schritt2_spieler.py  (oder im Ordner tutorial: python schritt2_spieler.py)
import asyncio

import pygame

BREITE = 800
HOEHE = 450


class Spieler(pygame.sprite.Sprite):
    """Die Schale unten. Sie kennt ihre Daten (Bild, Position) und ihr Verhalten (update)."""

    GESCHWINDIGKEIT = 420  # Pixel pro Sekunde

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((80, 18), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (80, 160, 255), self.image.get_rect(), border_radius=8)
        self.rect = self.image.get_rect(midbottom=(BREITE / 2, HOEHE - 20))
        self.x = float(self.rect.centerx)

    def update(self, dt):
        schritt = self.GESCHWINDIGKEIT * dt

        if pygame.mouse.get_pressed()[0]:
            # Maus gedrückt (oder Finger auf dem Handy): zur Maus fahren, aber nicht darüber hinaus
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

        # Am Rand stehen bleiben
        halbe_breite = self.rect.width / 2
        self.x = max(halbe_breite, min(BREITE - halbe_breite, self.x))
        self.rect.centerx = round(self.x)


async def main():
    pygame.init()
    flaeche = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption("Schritt 2: Spieler")
    uhr = pygame.time.Clock()

    spieler = Spieler()  # ein Objekt der Klasse Spieler
    laeuft = True

    while laeuft:
        dt = min(uhr.tick(60) / 1000, 0.05)

        for ereignis in pygame.event.get():
            if ereignis.type == pygame.QUIT:
                laeuft = False

        spieler.update(dt)

        flaeche.fill((18, 22, 40))
        flaeche.blit(spieler.image, spieler.rect)  # Bild an die Stelle von rect kopieren
        pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
