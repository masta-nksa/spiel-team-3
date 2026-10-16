# Startpunkt des Spiels. Lokal starten mit: python spiel/main.py
# pygbag (Browser-Version) verlangt, dass diese Datei main.py heisst
# und dass die Spielschleife mit asyncio läuft.
import asyncio
import os
import sys

import pygame

import einstellungen as e
from szenen import MenueSzene

if sys.platform != "emscripten":
    # Lokal: im Ordner dieser Datei arbeiten, damit "assets/..." immer gefunden wird,
    # egal von wo aus das Spiel gestartet wird. Im Browser ist das schon so.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Spiel:
    """Hält das Fenster offen und gibt jedes Bild an die aktuelle Szene weiter.

    Zu jedem Zeitpunkt ist genau eine Szene aktiv (Menü, Spiel oder Game Over).
    Das ist ein Zustandsautomat: Die Szene entscheidet selbst, wann sie zu welcher
    anderen Szene wechselt.
    """

    def __init__(self):
        pygame.init()
        self.flaeche = pygame.display.set_mode((e.BREITE, e.HOEHE))
        pygame.display.set_caption(e.TITEL)
        self.uhr = pygame.time.Clock()
        self.laeuft = True
        self.rekord = 0
        self.szene = MenueSzene(self)

    def wechsle_zu(self, szene):
        self.szene = szene

    def beenden(self):
        self.laeuft = False

    async def laufen(self):
        while self.laeuft:
            # Delta-Time: Sekunden seit dem letzten Bild. Wer Bewegungen damit multipliziert,
            # hat auf jedem Gerät gleich schnelle Figuren, egal wie viele Bilder pro Sekunde es schafft.
            dt = min(self.uhr.tick(e.FPS) / 1000, e.MAX_DT)

            for ereignis in pygame.event.get():
                if ereignis.type == pygame.QUIT:
                    self.beenden()
                else:
                    self.szene.ereignis(ereignis)

            self.szene.aktualisieren(dt)
            self.szene.zeichnen(self.flaeche)
            pygame.display.flip()

            # Gibt dem Browser kurz die Kontrolle zurück. Ohne diese Zeile friert die Seite ein.
            await asyncio.sleep(0)

        pygame.quit()


async def main():
    spiel = Spiel()
    await spiel.laufen()


asyncio.run(main())
