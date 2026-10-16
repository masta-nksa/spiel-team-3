# Schritt 1: Ein Fenster und die Spielschleife
# Starten: python tutorial/schritt1_fenster.py  (oder im Ordner tutorial: python schritt1_fenster.py)
import asyncio

import pygame

BREITE = 800
HOEHE = 450


async def main():
    pygame.init()
    flaeche = pygame.display.set_mode((BREITE, HOEHE))
    pygame.display.set_caption("Schritt 1: Spielschleife")
    uhr = pygame.time.Clock()

    x = 0.0  # Position des Kreises als Kommazahl, damit auch kleine Schritte zählen
    tempo = 200  # Pixel pro Sekunde
    laeuft = True

    while laeuft:
        # Delta-Time: Sekunden seit dem letzten Bild (bei 60 Bildern pro Sekunde etwa 0.017)
        dt = min(uhr.tick(60) / 1000, 0.05)

        # 1. Eingaben lesen
        for ereignis in pygame.event.get():
            if ereignis.type == pygame.QUIT:
                laeuft = False

        # 2. Aktualisieren: Tempo mal Zeit = Weg
        x += tempo * dt
        if x > BREITE:
            x = 0

        # 3. Zeichnen: zuerst alles übermalen, dann neu zeichnen, dann anzeigen
        flaeche.fill((18, 22, 40))
        pygame.draw.circle(flaeche, (255, 210, 60), (round(x), HOEHE // 2), 20)
        pygame.display.flip()

        await asyncio.sleep(0)  # nötig für den Browser, schadet lokal nicht

    pygame.quit()


asyncio.run(main())
