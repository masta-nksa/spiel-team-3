"""Das Level: Hintergrund, Requisiten und Gegnerwellen.

Hintergrund in drei Ebenen (Parallax):
  himmel  steht still
  ferne   Skyline, scrollt langsamer als die Strasse (wirkt weit weg)
  nah     Häuser, Gehsteig und Strasse, scrollt mit der Kamera

Alle Ebenen werden beim Start einmal mit pygame.draw in grosse Bilder gemalt
(mit festem Zufalls-Startwert, darum sieht das Level jedes Mal gleich aus).
Danach wird pro Bild nur noch der sichtbare Ausschnitt kopiert. Das ist schnell.

Gegnerwellen: Erreicht die Kamera die Stelle einer Welle, bleibt sie stehen
(Kamera.sperre). Die Gegner kommen von links und rechts ins Bild. Sind alle
besiegt, geht es weiter ("GO!").
"""
import random

import pygame

import einstellungen as e
import grafik
from gegner import Gegner
from objekte import REQUISITEN

LEVEL_BREITE = 5400
PARALLAX = 0.35
HAUS_UNTEN = 300  # hier beginnt der Gehsteig
BORDSTEIN = 352  # hier beginnt die Fahrbahn
TRANSPARENT = (255, 0, 255)  # diese Farbe wird beim Kopieren ausgelassen (Colorkey)

ZONEN = [(0, 1900, "altstadt"), (1900, 3700, "industrie"), (3700, LEVEL_BREITE, "hafen")]


class Welle:
    def __init__(self, kamera_x, gegner, extra=(), gleichzeitig=3, titel=None):
        self.kamera_x = kamera_x  # hier bleibt die Kamera stehen
        self.gegner = list(gegner)
        self.extra = list(extra)  # kommen nur dazu, wenn zwei Spieler spielen
        self.gleichzeitig = gleichzeitig
        self.titel = titel


WELLEN = [
    Welle(420, ["schlaeger", "schlaeger", "schlaeger"], ["schlaeger"], 3),
    Welle(1350, ["schlaeger", "flitzer", "schlaeger", "flitzer"], ["schlaeger", "flitzer"], 3),
    Welle(2350, ["brocken", "schlaeger", "flitzer", "schlaeger"], ["flitzer", "schlaeger"], 3),
    Welle(3300, ["flitzer", "schlaeger", "brocken", "flitzer", "schlaeger"], ["brocken", "flitzer"], 4),
    Welle(LEVEL_BREITE - e.BREITE, ["boss", "schlaeger", "flitzer", "schlaeger"], ["brocken", "flitzer"], 3,
          titel="BOSS: GRANIT"),
]

# (Art, x, y) – y ist der Fusspunkt
REQUISITEN_PLAN = [
    ("laterne", 300, 330), ("kiste", 760, 360), ("tonne", 1000, 340),
    ("laterne", 1120, 330), ("fass", 1560, 470), ("kiste", 1700, 345),
    ("laterne", 1950, 330), ("fass", 2500, 350), ("fass", 2540, 372), ("kiste", 2900, 480),
    ("laterne", 2780, 330), ("tonne", 3100, 342), ("kiste", 3500, 355), ("laterne", 3620, 330),
    ("fass", 3950, 470), ("kiste", 4200, 350), ("kiste", 4246, 350), ("laterne", 4480, 330),
    ("fass", 5000, 360), ("laterne", 5300, 330),
]


class Wellensteuerung:
    """Startet die Wellen der Reihe nach und lässt Gegner nachrücken."""

    def __init__(self, wellen):
        self.wellen = wellen
        self.index = 0
        self.aktiv = None
        self.warteschlange = []
        self.bis_naechster = 0.0
        self.seite = 1
        self.fertig = False

    @property
    def nummer(self):
        return self.index + 1

    def update(self, dt, welt):
        if self.fertig:
            return
        if self.aktiv is None:
            if self.index >= len(self.wellen):
                self.fertig = True
                return
            welle = self.wellen[self.index]
            if welt.kamera.x >= welle.kamera_x - 4:
                self.starte(welle, welt)
            return

        self.bis_naechster -= dt
        lebende = [g for g in welt.gegner if g.hp > 0]
        if self.warteschlange and len(lebende) < self.aktiv.gleichzeitig and self.bis_naechster <= 0:
            self.erscheinen(self.warteschlange.pop(0), welt)
            self.bis_naechster = random.uniform(0.6, 1.4)
        if not self.warteschlange and not lebende:
            # Welle geschafft
            welt.kamera.sperre = None
            self.aktiv = None
            self.index += 1
            if self.index >= len(self.wellen):
                self.fertig = True
            else:
                welt.zeige_go()

    def starte(self, welle, welt):
        self.aktiv = welle
        welt.kamera.sperre = welle.kamera_x
        self.warteschlange = list(welle.gegner)
        if welt.zwei_spieler:
            # die Extras mischen sich unter die anderen
            for i, typ in enumerate(welle.extra):
                self.warteschlange.insert(min(len(self.warteschlange), 2 + i * 2), typ)
        self.bis_naechster = 0.5
        welt.zeige_banner(welle.titel or f"WELLE {self.nummer}")
        welt.ton.spiele("welle")

    def erscheinen(self, typ, welt):
        if typ == "boss":
            seite = 1
        else:
            seite = self.seite if random.random() < 0.7 else -self.seite
            self.seite = -self.seite
        x = welt.kamera.x - 60 if seite < 0 else welt.kamera.x + e.BREITE + 60
        y = random.uniform(e.BODEN_OBEN + 15, e.BODEN_UNTEN - 15)
        gegner = Gegner(typ, x, y)
        gegner.blick = -seite
        welt.gegner.append(gegner)


class Level:
    def __init__(self):
        self.breite = LEVEL_BREITE
        zufall = random.Random(1987)
        self.himmel = male_himmel(zufall)
        self.ferne = male_skyline(zufall)
        self.nah = male_strasse(zufall)

    def zeige_hintergrund(self, flaeche, kamera):
        flaeche.blit(self.himmel, (0, 0))
        fern_x = int(kamera.x * PARALLAX)
        flaeche.blit(self.ferne, (0, 0), pygame.Rect(fern_x, 0, e.BREITE, self.ferne.get_height()))
        flaeche.blit(self.nah, (round(kamera.wackel_x), round(kamera.wackel_y)),
                     pygame.Rect(int(kamera.x), 0, e.BREITE, e.HOEHE))

    def requisiten(self):
        return [REQUISITEN[art](x, y) for art, x, y in REQUISITEN_PLAN]


def zone_bei(x):
    for start, ende, name in ZONEN:
        if start <= x < ende:
            return name
    return ZONEN[-1][2]


# --- Hintergrund malen -----------------------------------------------------------

def male_himmel(zufall):
    bild = pygame.Surface((e.BREITE, e.HOEHE))
    oben, unten = (16, 12, 38), (150, 62, 82)
    for y in range(e.HOEHE):
        f = min(1.0, y / 300)
        farbe = tuple(int(a + (b - a) * f ** 1.6) for a, b in zip(oben, unten))
        pygame.draw.line(bild, farbe, (0, y), (e.BREITE, y))
    for _ in range(90):
        x, y = zufall.randrange(e.BREITE), zufall.randrange(200)
        hell = zufall.randint(120, 255)
        bild.set_at((x, y), (hell, hell, hell))
    pygame.draw.circle(bild, (250, 240, 210), (780, 70), 30)
    pygame.draw.circle(bild, (232, 220, 190), (770, 62), 6)
    pygame.draw.circle(bild, (232, 220, 190), (790, 82), 4)
    return bild.convert() if pygame.display.get_surface() else bild


def mit_colorkey(bild):
    if pygame.display.get_surface():
        bild = bild.convert()
    bild.set_colorkey(TRANSPARENT, pygame.RLEACCEL)
    return bild


def male_skyline(zufall):
    breite = int(e.BREITE + (LEVEL_BREITE - e.BREITE) * PARALLAX) + 4
    bild = pygame.Surface((breite, HAUS_UNTEN))
    bild.fill(TRANSPARENT)
    # zwei Reihen: hinten dunkler und höher
    for reihe, (farbe, hoehe_min, hoehe_max, fenster) in enumerate(
            [((44, 30, 70), 120, 230, (90, 80, 120)), ((30, 22, 52), 70, 160, (200, 170, 90))]):
        x = -20
        while x < breite:
            b = zufall.randint(50, 120)
            h = zufall.randint(hoehe_min, hoehe_max)
            zone = zone_bei(x / PARALLAX)
            oben = HAUS_UNTEN - h
            if zone == "industrie" and reihe == 1 and zufall.random() < 0.4:
                # Fabrik mit Schornstein
                pygame.draw.rect(bild, farbe, (x, HAUS_UNTEN - 60, b, 60))
                pygame.draw.rect(bild, farbe, (x + b // 3, oben, 14, h))
                pygame.draw.rect(bild, (180, 40, 40), (x + b // 3, oben + 6, 14, 5))
            elif zone == "hafen" and reihe == 0 and zufall.random() < 0.35:
                # Hafenkran
                pygame.draw.rect(bild, farbe, (x + 20, oben, 10, h))
                pygame.draw.line(bild, farbe, (x - 30, oben + 8), (x + 110, oben + 8), 6)
                pygame.draw.line(bild, farbe, (x + 25, oben - 20), (x + 100, oben + 8), 2)
                pygame.draw.line(bild, farbe, (x + 25, oben - 20), (x - 30, oben + 8), 2)
                pygame.draw.line(bild, farbe, (x + 90, oben + 8), (x + 90, oben + 60), 1)
            else:
                pygame.draw.rect(bild, farbe, (x, oben, b, h))
                if zufall.random() < 0.3:
                    pygame.draw.rect(bild, farbe, (x + b // 2 - 2, oben - 25, 3, 25))
                for fy in range(oben + 8, HAUS_UNTEN - 8, 12):
                    for fx in range(x + 6, x + b - 6, 10):
                        if zufall.random() < 0.28:
                            pygame.draw.rect(bild, fenster, (fx, fy, 4, 5))
            x += b + zufall.randint(-10, 15)
    return mit_colorkey(bild)


GRAFFITI = ["ZACK!", "BOOM", "KAI+RIA", "WUMMS", "NKSA", "PAFF", "2P"]
SCHILDER = ["PIZZA", "BAR", "ARCADE", "KEBAB", "KIOSK", "HOTEL", "DISCO"]
NEON = [(255, 80, 180), (80, 230, 255), (255, 220, 60), (120, 255, 120)]


def male_graffiti(bild, zufall, x, y):
    wort = zufall.choice(GRAFFITI)
    farbe = zufall.choice([(255, 90, 160), (90, 220, 255), (255, 210, 60), (140, 255, 120), (200, 120, 255)])
    schrift = grafik.text_bild(wort, zufall.randint(34, 48), farbe, True)
    schrift = pygame.transform.rotate(schrift, zufall.uniform(-10, 10))
    bild.blit(schrift, schrift.get_rect(center=(x, y)))


def male_altstadt_haus(bild, zufall, x, breite):
    hoehe = zufall.randint(170, 290)
    oben = HAUS_UNTEN - hoehe
    wand = zufall.choice([(120, 62, 52), (96, 70, 60), (78, 76, 98), (112, 92, 64), (70, 84, 80)])
    pygame.draw.rect(bild, wand, (x, oben, breite, hoehe))
    # Backsteine andeuten
    for y in range(oben + 4, HAUS_UNTEN, 8):
        versatz = 0 if (y // 8) % 2 else 9
        for bx in range(x + versatz, x + breite, 18):
            pygame.draw.line(bild, grafik.dunkler(wand, 0.85), (bx, y), (bx, y + 7))
        pygame.draw.line(bild, grafik.dunkler(wand, 0.85), (x, y), (x + breite, y))
    pygame.draw.rect(bild, grafik.dunkler(wand, 0.6), (x - 4, oben - 8, breite + 8, 10))
    # Fenster
    for fy in range(oben + 22, HAUS_UNTEN - 110, 52):
        for fx in range(x + 18, x + breite - 40, 54):
            hell = zufall.random() < 0.45
            glas = (255, 214, 120) if hell else (36, 40, 66)
            pygame.draw.rect(bild, (40, 30, 30), (fx - 3, fy - 3, 34, 42))
            pygame.draw.rect(bild, glas, (fx, fy, 28, 36))
            pygame.draw.line(bild, (40, 30, 30), (fx + 14, fy), (fx + 14, fy + 36), 2)
            pygame.draw.line(bild, (40, 30, 30), (fx, fy + 18), (fx + 28, fy + 18), 2)
            pygame.draw.rect(bild, grafik.dunkler(wand, 0.7), (fx - 5, fy + 38, 38, 4))
    # Erdgeschoss: Laden oder Tür
    if zufall.random() < 0.6:
        laden = pygame.Rect(x + 14, HAUS_UNTEN - 88, breite - 28, 88)
        pygame.draw.rect(bild, (30, 34, 50), laden)
        pygame.draw.rect(bild, (70, 110, 130), laden.inflate(-12, -30).move(0, 8))
        markise = zufall.choice([(200, 50, 50), (40, 120, 200), (60, 150, 80), (220, 160, 40)])
        for i, sx in enumerate(range(laden.left - 6, laden.right + 6, 16)):
            farbe = markise if i % 2 == 0 else (235, 230, 220)
            pygame.draw.polygon(bild, farbe, [(sx, laden.top - 20), (sx + 16, laden.top - 20),
                                              (sx + 20, laden.top), (sx + 4, laden.top)])
        neon = zufall.choice(NEON)
        schild = grafik.text_bild(zufall.choice(SCHILDER), 30, neon, True)
        bild.blit(schild, schild.get_rect(midbottom=(laden.centerx, laden.top - 24)))
    else:
        tuer = pygame.Rect(x + breite // 2 - 20, HAUS_UNTEN - 70, 40, 70)
        pygame.draw.rect(bild, (60, 40, 30), tuer)
        pygame.draw.rect(bild, (30, 20, 16), tuer, 3)
        pygame.draw.circle(bild, (220, 190, 80), (tuer.right - 9, tuer.centery), 3)
        pygame.draw.rect(bild, (90, 90, 100), (tuer.left - 6, HAUS_UNTEN - 6, 52, 6))
        if zufall.random() < 0.7:
            male_graffiti(bild, zufall, x + zufall.randint(30, breite - 30), HAUS_UNTEN - zufall.randint(25, 45))
    pygame.draw.line(bild, grafik.dunkler(wand, 0.5), (x, oben), (x, HAUS_UNTEN), 2)


def male_industrie(bild, zufall, x, breite):
    if zufall.random() < 0.4:
        # Maschendrahtzaun: dahinter sieht man die Skyline
        # (auf eine eigene Fläche gemalt, damit die schrägen Drähte nicht über den Rand ragen)
        zaun = pygame.Surface((breite, 162))
        zaun.fill(TRANSPARENT)
        oben = 12
        for d in range(-150, breite + 150, 14):
            pygame.draw.line(zaun, (120, 126, 132), (d, oben), (d + 150, 162), 1)
            pygame.draw.line(zaun, (120, 126, 132), (d + 150, oben), (d, 162), 1)
        for px in range(0, breite, 60):
            pygame.draw.rect(zaun, (70, 74, 80), (px, oben - 6, 6, 156))
        pygame.draw.line(zaun, (90, 94, 100), (0, oben), (breite, oben), 3)
        for px in range(0, breite, 10):  # Stacheldraht
            pygame.draw.line(zaun, (150, 150, 160), (px, oben - 10), (px + 6, oben - 4), 1)
        zaun.set_colorkey(TRANSPARENT)
        bild.blit(zaun, (x, HAUS_UNTEN - 162))
        return
    hoehe = zufall.randint(190, 240)
    oben = HAUS_UNTEN - hoehe
    wand = zufall.choice([(84, 98, 92), (110, 104, 84), (76, 86, 104)])
    pygame.draw.rect(bild, wand, (x, oben, breite, hoehe))
    for wx in range(x, x + breite, 10):
        pygame.draw.line(bild, grafik.heller(wand, 0.12), (wx, oben), (wx, HAUS_UNTEN), 2)
        pygame.draw.line(bild, grafik.dunkler(wand, 0.8), (wx + 5, oben), (wx + 5, HAUS_UNTEN), 1)
    pygame.draw.rect(bild, grafik.dunkler(wand, 0.6), (x, oben, breite, 8))
    # Rohre
    pygame.draw.rect(bild, (130, 70, 40), (x, oben + 40, breite, 10))
    pygame.draw.rect(bild, (90, 50, 30), (x, oben + 48, breite, 3))
    # Warnschild und Tor
    tor = pygame.Rect(x + breite // 2 - 50, HAUS_UNTEN - 110, 100, 110)
    pygame.draw.rect(bild, (60, 64, 70), tor)
    for y in range(tor.top + 6, tor.bottom, 9):
        pygame.draw.line(bild, (44, 46, 52), (tor.left, y), (tor.right, y), 2)
    for i in range(0, 100, 20):
        pygame.draw.polygon(bild, (230, 190, 40) if (i // 20) % 2 == 0 else (30, 30, 30),
                            [(tor.left + i, tor.top - 10), (tor.left + i + 20, tor.top - 10),
                             (tor.left + i + 10, tor.top), (tor.left + i - 10, tor.top)])
    pygame.draw.polygon(bild, (240, 200, 40), [(x + 30, HAUS_UNTEN - 120), (x + 52, HAUS_UNTEN - 82), (x + 8, HAUS_UNTEN - 82)])
    grafik_text = grafik.text_bild("!", 30, (20, 20, 20), False)
    bild.blit(grafik_text, grafik_text.get_rect(center=(x + 30, HAUS_UNTEN - 94)))
    if zufall.random() < 0.6:
        male_graffiti(bild, zufall, x + breite - 70, HAUS_UNTEN - 50)


def male_hafen(bild, zufall, x, breite, letztes):
    if letztes:
        # Am Ende: das grosse Lagerhaus des Bosses
        oben = HAUS_UNTEN - 280
        pygame.draw.rect(bild, (70, 40, 36), (x, oben, breite, 280))
        for y in range(oben, HAUS_UNTEN, 10):
            pygame.draw.line(bild, (58, 32, 30), (x, y), (x + breite, y))
        tor = pygame.Rect(x + 60, HAUS_UNTEN - 170, breite - 120, 170)
        pygame.draw.rect(bild, (90, 96, 104), tor)
        for y in range(tor.top, tor.bottom, 8):
            pygame.draw.line(bild, (64, 68, 76), (tor.left, y), (tor.right, y), 2)
        pygame.draw.rect(bild, (30, 30, 34), tor, 6)
        schild = grafik.text_bild("LAGER 7", 46, (255, 220, 80), True)
        bild.blit(schild, schild.get_rect(center=(x + breite // 2, oben + 80)))
        return
    if zufall.random() < 0.55:
        # Container-Stapel
        unten = HAUS_UNTEN
        for stock in range(zufall.randint(1, 3)):
            farbe = zufall.choice([(170, 60, 40), (40, 100, 160), (60, 130, 70), (190, 140, 40), (110, 110, 120)])
            rahmen = pygame.Rect(x + zufall.randint(0, 20), unten - 70, breite - 30, 70)
            pygame.draw.rect(bild, farbe, rahmen)
            for cx in range(rahmen.left + 6, rahmen.right - 4, 9):
                pygame.draw.line(bild, grafik.dunkler(farbe, 0.75), (cx, rahmen.top + 4), (cx, rahmen.bottom - 4), 2)
            pygame.draw.rect(bild, grafik.dunkler(farbe, 0.55), rahmen, 3)
            unten -= 70
        return
    oben = HAUS_UNTEN - 210
    wand = (60, 70, 90)
    pygame.draw.rect(bild, wand, (x, oben, breite, 210))
    for wx in range(x, x + breite, 12):
        pygame.draw.line(bild, (50, 58, 76), (wx, oben), (wx, HAUS_UNTEN), 2)
    tor = pygame.Rect(x + 20, HAUS_UNTEN - 130, breite - 40, 130)
    pygame.draw.rect(bild, (100, 104, 110), tor)
    for y in range(tor.top, tor.bottom, 8):
        pygame.draw.line(bild, (74, 78, 86), (tor.left, y), (tor.right, y), 2)
    nummer = grafik.text_bild(str(zufall.randint(1, 6)), 40, (240, 240, 240), True)
    bild.blit(nummer, nummer.get_rect(center=(x + breite // 2, oben + 36)))


def male_strasse(zufall):
    bild = pygame.Surface((LEVEL_BREITE, e.HOEHE))
    bild.fill(TRANSPARENT)

    # Häuserzeile
    x = 0
    while x < LEVEL_BREITE:
        zone = zone_bei(x)
        if zone == "hafen" and x >= LEVEL_BREITE - 700:
            male_hafen(bild, zufall, x, LEVEL_BREITE - x, True)
            break
        breite = zufall.randint(190, 320)
        if zone == "altstadt":
            male_altstadt_haus(bild, zufall, x, breite)
        elif zone == "industrie":
            male_industrie(bild, zufall, x, breite)
        else:
            male_hafen(bild, zufall, x, breite, False)
        x += breite

    # Gehsteig
    for x in range(0, LEVEL_BREITE, 4):
        zone = zone_bei(x)
        farbe = {"altstadt": (120, 116, 124), "industrie": (110, 108, 100), "hafen": (104, 108, 116)}[zone]
        pygame.draw.line(bild, farbe, (x, HAUS_UNTEN), (x, BORDSTEIN), 4)
    for x in range(0, LEVEL_BREITE, 48):
        pygame.draw.line(bild, (88, 86, 94), (x, HAUS_UNTEN), (x - 18, BORDSTEIN), 2)
    pygame.draw.line(bild, (80, 78, 86), (0, HAUS_UNTEN + 26), (LEVEL_BREITE, HAUS_UNTEN + 26), 1)
    pygame.draw.rect(bild, (60, 58, 66), (0, HAUS_UNTEN, LEVEL_BREITE, 4))
    # Bordstein
    pygame.draw.rect(bild, (150, 148, 156), (0, BORDSTEIN, LEVEL_BREITE, 6))
    pygame.draw.rect(bild, (70, 68, 76), (0, BORDSTEIN + 6, LEVEL_BREITE, 4))

    # Fahrbahn
    oben = BORDSTEIN + 10
    for x in range(0, LEVEL_BREITE, 4):
        zone = zone_bei(x)
        farbe = {"altstadt": (52, 50, 62), "industrie": (60, 56, 54), "hafen": (64, 66, 72)}[zone]
        pygame.draw.line(bild, farbe, (x, oben), (x, e.HOEHE), 4)
    for _ in range(4000):
        px, py = zufall.randrange(LEVEL_BREITE), zufall.randrange(oben, e.HOEHE)
        hell = zufall.randint(40, 90)
        bild.set_at((px, py), (hell, hell, hell + 6))
    # Mittelstreifen und Details
    for x in range(0, LEVEL_BREITE, 120):
        farbe = (230, 220, 200) if zone_bei(x) != "hafen" else (230, 190, 50)
        pygame.draw.polygon(bild, farbe, [(x, 446), (x + 64, 446), (x + 60, 452), (x - 4, 452)])
    for x in range(0, LEVEL_BREITE, 1400):
        # Fussgängerstreifen
        for i in range(6):
            sx = x + 600 + i * 34
            pygame.draw.polygon(bild, (210, 210, 205), [(sx, oben + 6), (sx + 18, oben + 6), (sx + 4, e.HOEHE), (sx - 14, e.HOEHE)])
    for _ in range(14):
        # Pfützen und Gullydeckel
        px, py = zufall.randrange(200, LEVEL_BREITE - 200), zufall.randrange(oben + 30, e.HOEHE - 20)
        if zufall.random() < 0.5:
            pygame.draw.ellipse(bild, (74, 84, 110), (px, py, zufall.randint(40, 90), zufall.randint(10, 18)))
        else:
            pygame.draw.ellipse(bild, (40, 40, 46), (px, py, 44, 16))
            pygame.draw.ellipse(bild, (70, 70, 78), (px, py, 44, 16), 2)
            for i in range(1, 4):
                pygame.draw.line(bild, (70, 70, 78), (px + i * 11, py + 3), (px + i * 11, py + 13), 1)
    return mit_colorkey(bild)
