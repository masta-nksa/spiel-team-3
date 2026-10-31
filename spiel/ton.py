"""Töne, die das Spiel selbst ausrechnet (keine Audiodateien nötig).

Ein Ton ist nur eine lange Liste von Zahlen (Samples): wie weit die Lautsprecher-
membran gerade ausschlägt. Rauschen klingt nach Aufprall, eine fallende
Sinusschwingung nach dumpfem Schlag. Klappt etwas mit dem Ton nicht
(kein Lautsprecher, Browser blockiert), läuft das Spiel einfach ohne Ton weiter.
"""
import array
import math
import random

import pygame


class Ton:
    def __init__(self):
        self.klaenge = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 2, 512)
            frequenz, format_, kanaele = pygame.mixer.get_init()
            if format_ != -16:
                return
            self.frequenz = frequenz
            self.kanaele = kanaele
            zufall = random.Random(7)
            self.klaenge = {
                "schlag": self._erzeuge(0.12, 140, 60, 0.55, 0.7, zufall),
                "tritt": self._erzeuge(0.16, 110, 45, 0.5, 0.75, zufall),
                "hart": self._erzeuge(0.24, 95, 35, 0.65, 0.85, zufall),
                "wusch": self._erzeuge(0.10, 0, 0, 0.6, 0.18, zufall, rauschen_hoch=True),
                "aufprall": self._erzeuge(0.28, 70, 30, 0.7, 0.8, zufall),
                "bruch": self._erzeuge(0.30, 300, 120, 0.8, 0.6, zufall),
                "greifen": self._ton_folge([(440, 0.04), (660, 0.05)], 0.22),
                "wurf": self._erzeuge(0.14, 0, 0, 0.6, 0.25, zufall, rauschen_hoch=True),
                "knack": self._erzeuge(0.24, 220, 60, 0.7, 0.8, zufall),
                "sprung": self._ton_folge([(330, 0.05), (494, 0.05)], 0.25),
                "einsammeln": self._ton_folge([(660, 0.06), (880, 0.06), (1320, 0.08)], 0.25),
                "welle": self._ton_folge([(220, 0.12), (220, 0.12), (330, 0.25)], 0.3),
                "sieg": self._ton_folge([(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.35)], 0.3),
            }
            for klang in self.klaenge.values():
                klang.set_volume(0.5)
        except Exception:  # noqa: BLE001 - ohne Ton geht es auch
            self.klaenge = {}

    def _als_klang(self, werte):
        samples = array.array("h")
        for wert in werte:
            s = int(max(-1.0, min(1.0, wert)) * 30000)
            for _ in range(self.kanaele):
                samples.append(s)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _erzeuge(self, dauer, f_start, f_ende, rausch_anteil, lautstaerke, zufall, rauschen_hoch=False):
        """Schlaggeräusch: Sinus mit fallender Tonhöhe plus Rauschen, beides klingt schnell ab."""
        anzahl = int(self.frequenz * dauer)
        werte = []
        phase = 0.0
        letztes = 0.0
        for i in range(anzahl):
            t = i / anzahl
            huelle = (1 - t) ** 3 if not rauschen_hoch else math.sin(math.pi * t) ** 2
            f = f_start + (f_ende - f_start) * t
            phase += 2 * math.pi * f / self.frequenz
            rauschen = zufall.uniform(-1, 1)
            if not rauschen_hoch:
                letztes = letztes * 0.6 + rauschen * 0.4  # etwas dumpfer
                rauschen = letztes
            wert = (math.sin(phase) * (1 - rausch_anteil) + rauschen * rausch_anteil) * huelle
            werte.append(wert * lautstaerke)
        return self._als_klang(werte)

    def _ton_folge(self, noten, lautstaerke):
        """Kleine Melodie aus Rechteck-Tönen (klingt nach Retro-Konsole)."""
        werte = []
        for frequenz, dauer in noten:
            anzahl = int(self.frequenz * dauer)
            for i in range(anzahl):
                t = i / self.frequenz
                welle = 1.0 if math.sin(2 * math.pi * frequenz * t) > 0 else -1.0
                werte.append(welle * lautstaerke * (1 - i / anzahl) ** 0.5)
        return self._als_klang(werte)

    def spiele(self, name):
        klang = self.klaenge.get(name)
        if klang:
            try:
                klang.play()
            except Exception:  # noqa: BLE001
                pass
