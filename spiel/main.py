# Startpunkt des Spiels. Lokal starten mit: python spiel/main.py
# pygbag (Browser-Version) verlangt, dass diese Datei main.py heisst
# und dass die Spielschleife mit asyncio läuft.
import asyncio
import os
import sys

import pygame

import einstellungen as e
from eingabe import Steuerung, gamepad_ereignis, gamepads_suchen
from level import Level
from szenen import MenueSzene
from ton import Ton

# pygame-ce wird auch mit "import pygame" geladen. Ist stattdessen das alte pygame installiert,
# laufen manche Dinge anders als im Browser. Darum hier gleich abbrechen.
if not getattr(pygame, "IS_CE", False):
    sys.exit(
        "Hier ist das alte pygame installiert, die Vorlage braucht pygame-ce.\n"
        "Im Terminal eingeben, eine Zeile nach der anderen:\n"
        "  python -m pip uninstall -y pygame pygame-ce\n"
        "  python -m pip install -r requirements.txt"
    )

if sys.platform != "emscripten":
    # Lokal: im Ordner dieser Datei arbeiten, damit "assets/..." immer gefunden wird,
    # egal von wo aus das Spiel gestartet wird. Im Browser ist das schon so.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Spiel:
    """Hält das Fenster offen und gibt jedes Bild an die aktuelle Szene weiter.

    Zu jedem Zeitpunkt ist genau eine Szene aktiv (Menü, Spiel oder Ergebnis).
    Das ist ein Zustandsautomat: Die Szene entscheidet selbst, wann sie zu welcher
    anderen Szene wechselt.

    Was über mehrere Runden erhalten bleibt, liegt hier: Steuerungen, Ton,
    das fertig gemalte Level und der Rekord.
    """

    def __init__(self):
        pygame.init()
        self.flaeche = pygame.display.set_mode((e.BREITE, e.HOEHE))
        pygame.display.set_caption(e.TITEL)
        self.uhr = pygame.time.Clock()
        self.laeuft = True
        self.rekord = 0
        self.debug = False  # F1: Hitboxen anzeigen
        self.steuerungen = [Steuerung(1, e.TASTEN_P1), Steuerung(2, e.TASTEN_P2)]
        # Schon beim Start angeschlossene Controller zur Sicherheit selbst suchen (nicht auf Ereignisse verlassen)
        gamepads_suchen(self.steuerungen)
        self.ton = Ton()
        self.level = Level()  # wird nur einmal gemalt und dann für jede Runde wiederverwendet
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
                elif ereignis.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                    verloren = gamepad_ereignis(self.steuerungen, ereignis)
                    if verloren is not None:
                        self.szene.gamepad_verloren(verloren)
                elif ereignis.type in (pygame.CONTROLLERDEVICEADDED, pygame.CONTROLLERDEVICEREMOVED,
                                       pygame.CONTROLLERDEVICEREMAPPED):
                    pass  # doppelt gemeldet: die Joystick-Ereignisse genügen
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
