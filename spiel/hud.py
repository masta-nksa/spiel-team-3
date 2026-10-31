"""HUD: Lebensanzeigen, Punkte und Hinweise am Bildschirmrand.

Jeder Spieler hat sein eigenes Feld (1P links, 2P rechts). Der Lebensbalken hat
eine rote "Nachlaufspur": Bei einem Treffer fällt der Balken sofort, die Spur
folgt langsam. So sieht man, wie viel ein Treffer gekostet hat.
"""
import pygame

import einstellungen as e
import grafik
import waffen

PANEL_BREITE = 320
PANEL_HOEHE = 66


def balken_farbe(anteil):
    if anteil > 0.5:
        return (90, 220, 90)
    if anteil > 0.25:
        return (250, 200, 50)
    return (240, 60, 50)


def zeichne_balken(flaeche, rahmen, anteil, spur, farbe=None):
    pygame.draw.rect(flaeche, (30, 26, 40), rahmen)
    innen = rahmen.inflate(-4, -4)
    if spur > anteil:
        pygame.draw.rect(flaeche, (200, 40, 40), (innen.left, innen.top, int(innen.width * spur), innen.height))
    if anteil > 0:
        voll = pygame.Rect(innen.left, innen.top, max(1, int(innen.width * anteil)), innen.height)
        pygame.draw.rect(flaeche, farbe or balken_farbe(anteil), voll)
        pygame.draw.line(flaeche, (255, 255, 255), voll.topleft, (voll.right - 1, voll.top), 1)
    pygame.draw.rect(flaeche, e.UMRISS, rahmen, 2)


class HUD:
    def __init__(self):
        self.spur = {}  # Kämpfer -> angezeigter Anteil der Nachlaufspur
        self.zeit = 0.0

    def update(self, dt, welt):
        self.zeit += dt
        for figur in list(welt.spieler) + list(welt.gegner):
            anteil = figur.hp / figur.max_hp
            alt = self.spur.get(figur, anteil)
            self.spur[figur] = anteil if anteil > alt else max(anteil, alt - dt * 0.6)
        # vergessene Figuren aufräumen
        lebende = set(welt.spieler) | set(welt.gegner)
        self.spur = {f: w for f, w in self.spur.items() if f in lebende}

    def zeichnen(self, flaeche, welt):
        for nummer in (1, 2):
            links = 10 if nummer == 1 else e.BREITE - PANEL_BREITE - 10
            rahmen = pygame.Rect(links, 8, PANEL_BREITE, PANEL_HOEHE)
            spieler = welt.spieler_nummer(nummer)
            if spieler is None:
                self.zeichne_beitreten(flaeche, rahmen, welt, nummer)
            else:
                self.zeichne_spieler(flaeche, rahmen, spieler)
        self.zeichne_gegner(flaeche, welt)

    def panel(self, flaeche, rahmen, farbe):
        flaeche_panel = pygame.Surface(rahmen.size, pygame.SRCALPHA)
        pygame.draw.rect(flaeche_panel, (10, 8, 20, 170), flaeche_panel.get_rect(), border_radius=10)
        flaeche.blit(flaeche_panel, rahmen)
        pygame.draw.rect(flaeche, farbe, rahmen, 2, border_radius=10)

    def zeichne_spieler(self, flaeche, rahmen, spieler):
        self.panel(flaeche, rahmen, spieler.farbe)
        bild = pygame.Rect(rahmen.left + 7, rahmen.top + 7, 52, 52)
        grafik.zeichne_portrait(flaeche, spieler.skin, bild, self.zeit, grafik.dunkler(spieler.farbe, 0.45))
        x = bild.right + 10
        grafik.text(flaeche, f"{spieler.nummer}P {spieler.name}", 24, (x, rahmen.top + 8), spieler.farbe, "topleft")
        grafik.text(flaeche, f"{spieler.punkte:07d}", 24, (rahmen.right - 10, rahmen.top + 8), e.TEXT, "topright")
        if spieler.ausgeschieden:
            if int(self.zeit * 2) % 2 == 0:
                grafik.text(flaeche, "GAME OVER", 28, (x + 100, rahmen.top + 44), e.ROT)
            return
        anteil = spieler.hp / spieler.max_hp
        zeichne_balken(flaeche, pygame.Rect(x, rahmen.top + 30, 190, 16), anteil, self.spur.get(spieler, anteil))
        # Extraleben als kleine Herzen
        for i in range(spieler.leben):
            hx, hy = x + 6 + i * 16, rahmen.top + 54
            pygame.draw.circle(flaeche, e.ROT, (hx - 3, hy - 2), 4)
            pygame.draw.circle(flaeche, e.ROT, (hx + 3, hy - 2), 4)
            pygame.draw.polygon(flaeche, e.ROT, [(hx - 7, hy - 1), (hx + 7, hy - 1), (hx, hy + 6)])
        if spieler.trage is not None:
            self.zeichne_waffe(flaeche, rahmen, spieler)
        if spieler.combo >= 2:
            grafik.text(flaeche, f"{spieler.combo} HITS!", 30, (rahmen.centerx, rahmen.bottom + 16), e.GELB)

    def zeichne_waffe(self, flaeche, rahmen, spieler):
        """Was der Spieler trägt: Symbol und bei Waffen ein Haltbarkeitsbalken (blinkt, wenn sie fast kaputt ist)."""
        ding = spieler.trage
        symbol = pygame.Rect(rahmen.left + 109, rahmen.top + 47, 28, 16)
        waffen.zeichne_symbol(flaeche, ding.art, symbol)
        if ding.schwer:
            grafik.text(flaeche, f"{ding.name}: werfen", 18, (symbol.right + 8, symbol.centery), e.TEXT, "midleft", umriss=False)
            return
        balken = pygame.Rect(symbol.right + 8, symbol.top + 3, 100, 10)
        anteil = ding.anteil
        if anteil < 0.25 and int(self.zeit * 6) % 2:
            zeichne_balken(flaeche, balken, anteil, anteil, (255, 255, 255))
        else:
            zeichne_balken(flaeche, balken, anteil, anteil)

    def zeichne_beitreten(self, flaeche, rahmen, welt, nummer):
        self.panel(flaeche, rahmen, e.GRAU)
        if int(self.zeit * 2) % 2 == 0:
            taste = welt.steuerung(nummer).tastenname("schlag")
            grafik.text(flaeche, f"{nummer}P: {taste} drücken", 30, (rahmen.centerx, rahmen.centery - 10), e.SPIELER_FARBEN[nummer])
            grafik.text(flaeche, "zum Mitspielen", 22, (rahmen.centerx, rahmen.centery + 16), e.GRAU)

    def zeichne_gegner(self, flaeche, welt):
        boss = next((g for g in welt.gegner if g.typ == "boss" and g.hp > 0), None)
        if boss:
            rahmen = pygame.Rect(e.BREITE // 2 - 220, e.HOEHE - 34, 440, 18)
            grafik.text(flaeche, boss.name, 26, (rahmen.centerx, rahmen.top - 12), (150, 255, 150))
            anteil = boss.hp / boss.max_hp
            zeichne_balken(flaeche, rahmen, anteil, self.spur.get(boss, anteil), (110, 220, 90))
        gegner = welt.zuletzt_getroffen
        if gegner is not None and gegner is not boss and welt.zuletzt_getroffen_zeit > 0:
            mitte = e.BREITE // 2
            grafik.text(flaeche, gegner.name, 22, (mitte, 18), (170, 240, 170))
            anteil = gegner.hp / gegner.max_hp
            zeichne_balken(flaeche, pygame.Rect(mitte - 90, 30, 180, 12), anteil, self.spur.get(gegner, anteil), (110, 220, 90))
        elif welt.wellen.aktiv is not None:
            grafik.text(flaeche, f"WELLE {welt.wellen.nummer}/{len(welt.wellen.wellen)}", 22, (e.BREITE // 2, 22), e.GRAU)
