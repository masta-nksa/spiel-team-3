"""Szenen: Menü, Spiel, Game Over, Sieg.

Die SpielSzene ist gleichzeitig die "Welt": Figuren, Effekte und Wellen bekommen
sie als Parameter welt und fragen sie nach Kamera, Gegnern, Spielern usw.

Ablauf eines Bildes in der SpielSzene (aktualisieren):
  1. Kamera, Effekte, HUD nachführen
  2. Trefferstopp? Dann bleiben alle Figuren ein paar Hundertstel stehen.
  3. Figuren bewegen (Spieler: Eingabe, Gegner: KI)
  4. Kampf: Hitboxen gegen Hurtboxen prüfen
  5. Figuren auseinanderschieben (Körperboxen), Gegenstände einsammeln
  6. Wellen: neue Gegner, Kamera freigeben, Sieg/Niederlage
"""
import math

import pygame

import einstellungen as e
import grafik
import posen
from effekte import Effekte
from figuren import Spieler
from hud import HUD
from kamera import Kamera
from level import WELLEN, Wellensteuerung
from objekte import Gegenstand
from skins import SKINS


def ist_weiter(ereignis):
    """Enter, Leertaste, Mausklick oder Antippen."""
    if ereignis.type == pygame.KEYDOWN:
        return ereignis.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)
    return ereignis.type == pygame.MOUSEBUTTONDOWN


def irgendein_knopf(steuerungen, ereignis):
    """Name des Gamepad-Knopfes ("a", "b", "start" ...), wenn ein Ereignis von einem Controller kommt, sonst None."""
    for steuerung in steuerungen:
        knopf = steuerung.knopf(ereignis)
        if knopf:
            return knopf
    return None


def hat_gamepad(spiel):
    return any(s.gamepad is not None for s in spiel.steuerungen)


def abdunkeln(flaeche, alpha=150):
    schleier = pygame.Surface(flaeche.get_size(), pygame.SRCALPHA)
    schleier.fill((8, 6, 18, alpha))
    flaeche.blit(schleier, (0, 0))


def zeichne_titel(flaeche, inhalt, y, groesse=96, farbe=e.GELB):
    grafik.text(flaeche, inhalt, groesse, (e.BREITE / 2 + 4, y + 5), (120, 30, 40))
    grafik.text(flaeche, inhalt, groesse, (e.BREITE / 2, y), farbe)


class Szene:
    """Bauplan für alle Szenen. Jede Szene überschreibt die Methoden, die sie braucht."""

    def __init__(self, spiel):
        self.spiel = spiel

    def ereignis(self, ereignis):
        """Wird für jede Taste, jeden Klick usw. einmal aufgerufen."""

    def gamepad_verloren(self, nummer):
        """Der Controller von Spieler <nummer> wurde getrennt (z. B. Bluetooth-Abbruch)."""

    def aktualisieren(self, dt):
        """Spiellogik: Bewegen, Kollisionen, Zeitgeber. dt = Sekunden seit dem letzten Bild."""

    def zeichnen(self, flaeche):
        """Nur zeichnen, hier nichts am Spielzustand ändern."""


class MenueKamera:
    """Ganz einfache Kamera, die im Menü langsam über das Level fährt."""

    def __init__(self):
        self.x = 0.0
        self.wackel_x = self.wackel_y = 0

    def zu_bild(self, x, y, z=0.0):
        return (x - self.x, y - z)


class MenueSzene(Szene):
    def __init__(self, spiel):
        super().__init__(spiel)
        self.kamera = MenueKamera()
        self.zeit = 0.0
        self.zwei_spieler = False

    def ereignis(self, ereignis):
        p1, p2 = self.spiel.steuerungen
        k1, k2 = p1.knopf(ereignis), p2.knopf(ereignis)
        taste = ereignis.type == pygame.KEYDOWN
        # 2P ein/aus: K, A/X auf Controller 2, oder Y / LB / RB auf Controller 1
        if (taste and p2.aktion(ereignis) == "schlag") or k2 in ("a", "x", "y") or k1 in ("y", "lb", "rb"):
            self.zwei_spieler = not self.zwei_spieler
            self.spiel.ton.spiele("einsammeln")
            return
        if k2 == "start":
            self.zwei_spieler = True  # Start auf Controller 2: los, mit beiden
            self.spiel.wechsle_zu(SpielSzene(self.spiel, True))
            return
        if ist_weiter(ereignis) or (taste and p1.aktion(ereignis) == "schlag") or k1 in ("a", "x", "start"):
            self.spiel.wechsle_zu(SpielSzene(self.spiel, self.zwei_spieler))

    def aktualisieren(self, dt):
        self.zeit += dt
        self.kamera.x = (self.zeit * 40) % (self.spiel.level.breite - e.BREITE)

    def zeichnen(self, flaeche):
        self.spiel.level.zeige_hintergrund(flaeche, self.kamera)
        abdunkeln(flaeche, 120)
        zeichne_titel(flaeche, e.TITEL.upper(), 92, 110)
        grafik.text(flaeche, "Ein Beat-'em-up für eine oder zwei Personen", 30, (e.BREITE / 2, 152), e.TEXT)

        # Die beiden Helden zeigen, was sie können
        boden = 380
        takt = self.zeit % 2.0
        for nummer, x, blick in ((1, 160, 1), (2, e.BREITE - 160, -1)):
            skin = SKINS["p1" if nummer == 1 else "p2"]
            versatz = 0.0 if nummer == 1 else 1.0
            t = (takt + versatz) % 2.0
            if t < 0.5:
                pose = posen.angriffs_pose("gerade" if nummer == 1 else "hochtritt", t / 0.5, 0.3, 0.55)
            else:
                pose = posen.stehen(self.zeit)
            aktiv = nummer == 1 or self.zwei_spieler
            grafik.zeichne_schatten(flaeche, x, boden, 110)
            if aktiv:
                grafik.zeichne_spielerring(flaeche, x, boden, 120, e.SPIELER_FARBEN[nummer], blick)
            grafik.zeichne_figur(flaeche, skin, pose, x, boden, blick, 2.2, zeit=self.zeit)
            steuerung = self.spiel.steuerungen[nummer - 1]
            status = "BEREIT" if aktiv else f"{steuerung.tastenname('schlag')} drücken"
            farbe = e.SPIELER_FARBEN[nummer] if aktiv else e.GRAU
            grafik.text(flaeche, f"{nummer}P {skin['name']}", 34, (x, boden + 30), farbe)
            if steuerung.gamepad is not None:
                grafik.text(flaeche, "Controller verbunden", 20, (x, boden + 82), e.GRUEN, umriss=False)
            else:
                grafik.text(flaeche, "Tastatur", 20, (x, boden + 82), e.GRAU, umriss=False)
            if not aktiv and int(self.zeit * 2) % 2:
                continue
            grafik.text(flaeche, status, 24, (x, boden + 56), farbe)

        # Steuerung
        pad = hat_gamepad(self.spiel)
        kasten = pygame.Rect(e.BREITE / 2 - 190, 186, 380, 250 if pad else 230)
        schleier = pygame.Surface(kasten.size, pygame.SRCALPHA)
        pygame.draw.rect(schleier, (10, 8, 20, 190), schleier.get_rect(), border_radius=12)
        flaeche.blit(schleier, kasten)
        zeilen = [
            ("1P", "WASD  ·  F Schlag  ·  G Tritt", e.SPIELER_FARBEN[1]),
            ("", "Leertaste Sprung  ·  F+G Spezial", e.SPIELER_FARBEN[1]),
            ("2P", "Pfeile  ·  K Schlag  ·  L Tritt", e.SPIELER_FARBEN[2]),
            ("", "O Sprung  ·  K+L Spezial", e.SPIELER_FARBEN[2]),
            ("", "(oder Ziffernblock 1 / 2 / 0 / 3)", e.GRAU),
            ("", "Controller: X Schlag · B Tritt · A Sprung", e.GRAU),
        ]
        if pad:
            zeilen.append(("", "Y Spezial · Stick/Kreuz · Start Pause", e.GRAU))
        zeilen.append(("", "Esc Pause  ·  F1 Hitboxen zeigen", e.GRAU))
        for i, (_, zeile, farbe) in enumerate(zeilen):
            grafik.text(flaeche, zeile, 24, (kasten.centerx, kasten.top + 22 + i * 30), farbe, umriss=False)

        if int(self.zeit * 2.5) % 2 == 0:
            start = "Enter, F oder A: Start" if pad else "Enter oder F: Start"
            grafik.text(flaeche, start, 38, (e.BREITE / 2, 462), e.GELB)
        if pad:
            grafik.text(flaeche, "2P dazu: K oder A auf Controller 2  ·  Y: 1P/2P wechseln", 22, (e.BREITE / 2, 492), e.TEXT, umriss=False)
        grafik.text(flaeche, f"Rekord: {self.spiel.rekord}", 24, (e.BREITE / 2, 518), e.GRAU)


class SpielSzene(Szene):
    def __init__(self, spiel, zwei_spieler=False):
        super().__init__(spiel)
        self.level = spiel.level
        self.kamera = Kamera(self.level.breite)
        self.effekte = Effekte()
        self.ton = spiel.ton
        self.hud = HUD()
        self.spieler = []
        self.gegner = []
        self.objekte = self.level.requisiten()
        self.wellen = Wellensteuerung(WELLEN)

        self.stopp = 0.0  # Trefferstopp
        self.banner = ""
        self.banner_zeit = 0.0
        self.go_zeit = 0.0
        self.zuletzt_getroffen = None
        self.zuletzt_getroffen_zeit = 0.0
        self.pausiert = False
        self.pause_grund = ""
        self.sieg_zeit = None
        self.verloren_zeit = None
        self.spielzeit = 0.0

        self.neuer_spieler(1)
        if zwei_spieler:
            self.neuer_spieler(2)
        self.zeige_banner("LOS GEHT'S!")

    # --- Dinge, nach denen Figuren und Wellen fragen ------------------------------

    @property
    def zwei_spieler(self):
        return len(self.spieler) >= 2

    def spieler_nummer(self, nummer):
        return next((s for s in self.spieler if s.nummer == nummer), None)

    def steuerung(self, nummer):
        return self.spiel.steuerungen[nummer - 1]

    def neuer_spieler(self, nummer):
        spieler = Spieler(nummer, self.steuerung(nummer), 0, 0)
        spieler.einsteigen(self)
        spieler.z = 200
        self.spieler.append(spieler)

    def wackeln(self, staerke):
        self.kamera.wackeln(staerke)

    def trefferstopp(self, sekunden):
        self.stopp = max(self.stopp, sekunden)

    def zeige_banner(self, inhalt):
        self.banner = inhalt
        self.banner_zeit = 2.0

    def zeige_go(self):
        self.go_zeit = 5.0

    # --- Eingabe ------------------------------------------------------------------

    def ereignis(self, ereignis):
        if ereignis.type == pygame.KEYDOWN:
            if ereignis.key == pygame.K_ESCAPE:
                if self.pausiert:
                    self.spiel.wechsle_zu(MenueSzene(self.spiel))
                else:
                    self.pausiert = True
                return
            if ereignis.key == pygame.K_F1:
                self.spiel.debug = not self.spiel.debug
                return
        knopf = irgendein_knopf(self.spiel.steuerungen, ereignis)
        if knopf == "start":
            self.pausiert = not self.pausiert
            self.pause_grund = ""
            return
        if self.pausiert:
            if knopf in ("b", "back"):
                self.spiel.wechsle_zu(MenueSzene(self.spiel))
            elif knopf == "a" or ist_weiter(ereignis):
                self.pausiert = False
                self.pause_grund = ""
            return

        for nummer, steuerung in enumerate(self.spiel.steuerungen, start=1):
            aktion = steuerung.aktion(ereignis)
            if not aktion:
                continue
            spieler = self.spieler_nummer(nummer)
            if spieler is None:
                # Mitten im Spiel einsteigen
                if aktion == "schlag" and self.sieg_zeit is None and self.verloren_zeit is None:
                    self.neuer_spieler(nummer)
                    self.zeige_banner(f"{nummer}P STEIGT EIN!")
            elif not spieler.ausgeschieden:
                spieler.taste(aktion)

    def gamepad_verloren(self, nummer):
        """Controller getrennt: wer gerade mitspielt, wird automatisch pausiert, damit nichts passiert."""
        spieler = self.spieler_nummer(nummer)
        if spieler is None or spieler.ausgeschieden or self.sieg_zeit is not None or self.verloren_zeit is not None:
            return
        self.pausiert = True
        self.pause_grund = f"Controller {nummer} getrennt"

    # --- Spiellogik ---------------------------------------------------------------

    def aktualisieren(self, dt):
        if self.pausiert:
            return
        self.spielzeit += dt
        self.banner_zeit -= dt
        self.go_zeit -= dt
        self.zuletzt_getroffen_zeit -= dt
        aktive = [s for s in self.spieler if not s.ausgeschieden]
        self.kamera.update(dt, [s.x for s in aktive])
        self.effekte.update(dt)
        self.hud.update(dt, self)

        if self.stopp > 0:
            self.stopp -= dt
            return

        for spieler in aktive:
            spieler.update(dt, self)
        for gegner in self.gegner:
            gegner.update(dt, self)
        for objekt in self.objekte:
            objekt.update(dt, self)
        self.koordiniere_gegner()
        self.kampf()
        self.auseinanderschieben()
        self.einsammeln()
        self.gegner = [g for g in self.gegner if not g.entfernen]
        self.objekte = [o for o in self.objekte if not o.entfernen]
        self.wellen.update(dt, self)
        self.pruefe_ende(dt)

    def koordiniere_gegner(self):
        """Pro Spieler dürfen nur die nächsten MAX_ANGREIFER Gegner zuschlagen, von beiden Seiten."""
        for gegner in self.gegner:
            gegner.darf_angreifen = False
        for spieler in self.spieler:
            jaeger = [g for g in self.gegner if g.ziel is spieler and g.hp > 0]
            jaeger.sort(key=lambda g: abs(g.x - spieler.x) + 2 * abs(g.y - spieler.y) - (60 if g.darf_angreifen else 0))
            erste_seite = 1
            for i, gegner in enumerate(jaeger):
                eigene_seite = 1 if gegner.x >= spieler.x else -1
                gegner.darf_angreifen = i < e.MAX_ANGREIFER
                if i == 0:
                    gegner.seite = erste_seite = eigene_seite
                elif i == 1:
                    gegner.seite = -erste_seite  # der zweite kommt von der anderen Seite
                else:
                    gegner.seite = eigene_seite

    def kampf(self):
        """Hitbox gegen Hurtbox: das ganze Treffersystem in einer Methode."""
        aktive_spieler = [s for s in self.spieler if not s.ausgeschieden]
        for angreifer in aktive_spieler + self.gegner:
            hitbox = angreifer.hitbox()
            if hitbox is None:
                continue
            if angreifer.team == "spieler":
                ziele = self.gegner + [o for o in self.objekte if o.zerstoerbar]
            else:
                ziele = aktive_spieler
            for ziel in ziele:
                if ziel in angreifer.getroffene:
                    continue  # jeder Angriff trifft jedes Ziel nur einmal
                hurtbox = ziel.hurtbox()
                if hurtbox is None or not hitbox.ueberlappt(hurtbox):
                    continue
                angreifer.getroffene.add(ziel)
                angriff = angreifer.angriff
                x, y, z = hitbox.schnitt_mitte(hurtbox)
                umgeworfen = ziel.nimm_treffer(angreifer, angriff, self)
                steuerung = getattr(ziel, "steuerung", None)
                if steuerung is not None:  # getroffener Spieler: Controller rüttelt kurz
                    steuerung.rumble(e.RUMBLE_UMGEWORFEN if umgeworfen else e.RUMBLE_TREFFER)
                angreifer.treffer_gelandet(ziel, angriff, self)

                self.effekte.funke(x, y, z, gross=umgeworfen)
                self.ton.spiele(angriff.ton)
                self.trefferstopp(e.TREFFERSTOPP_SCHWER if umgeworfen else e.TREFFERSTOPP_LEICHT)
                self.wackeln(6 if umgeworfen else 2)
                if ziel.team == "gegner":
                    self.zuletzt_getroffen = ziel
                    self.zuletzt_getroffen_zeit = 2.5
                    if ziel.hp <= 0 and angreifer.team == "spieler" and not getattr(ziel, "besiegt", False):
                        ziel.besiegt = True
                        angreifer.punkte += ziel.punkte_wert
                        self.effekte.text(ziel.x, ziel.y, ziel.hoehe + 20, f"+{ziel.punkte_wert}")

    def auseinanderschieben(self):
        """Körperboxen: stehende Figuren schieben sich sanft auseinander, damit sie nicht verschmelzen."""
        figuren = [(f, f.koerperbox()) for f in self.spieler + self.gegner if not getattr(f, "ausgeschieden", False)]
        figuren = [(f, box) for f, box in figuren if box is not None]
        for i, (a, box_a) in enumerate(figuren):
            for b, box_b in figuren[i + 1:]:
                if abs(a.y - b.y) > 10:
                    continue
                ueberlappung = min(box_a[1], box_b[1]) - max(box_a[0], box_b[0])
                if ueberlappung <= 0:
                    continue
                richtung = 1 if a.x > b.x or (a.x == b.x and id(a) > id(b)) else -1
                schub = ueberlappung * 0.25
                a.x += richtung * schub
                b.x -= richtung * schub

    def einsammeln(self):
        for objekt in self.objekte:
            if not isinstance(objekt, Gegenstand) or objekt.entfernen:
                continue
            for spieler in self.spieler:
                if spieler.ausgeschieden or spieler.hp <= 0 or not objekt.beruehrt(spieler):
                    continue
                if getattr(objekt, "heilung", 0) and spieler.hp >= spieler.max_hp:
                    continue  # Essen bleibt liegen, wenn man es nicht braucht
                objekt.aufheben(spieler, self)
                break

    def pruefe_ende(self, dt):
        if self.wellen.fertig:
            if self.sieg_zeit is None:
                self.sieg_zeit = 0.0
                self.zeige_banner("GESCHAFFT!")
                self.ton.spiele("sieg")
            self.sieg_zeit += dt
            for spieler in self.spieler:
                if spieler.kann_handeln:
                    spieler.wechsle("jubeln")
                    spieler.vx = spieler.vy = 0
            if self.sieg_zeit > 4:
                self.spiel.wechsle_zu(ErgebnisSzene(self.spiel, self, gewonnen=True))
        elif all(s.ausgeschieden for s in self.spieler):
            self.verloren_zeit = (self.verloren_zeit or 0.0) + dt
            if self.verloren_zeit > 2:
                self.spiel.wechsle_zu(ErgebnisSzene(self.spiel, self, gewonnen=False))

    # --- Zeichnen -----------------------------------------------------------------

    def zeichnen(self, flaeche):
        flaeche.fill(e.DUNKEL)
        self.level.zeige_hintergrund(flaeche, self.kamera)

        sichtbar = [s for s in self.spieler if not s.ausgeschieden]
        sichtbar += [d for d in self.gegner + self.objekte if self.kamera.ist_sichtbar(d.x, 300)]
        # Zuerst alle Schatten: sie liegen am Boden und damit unter allen Figuren
        for ding in sichtbar:
            ding.zeichne_boden(flaeche, self.kamera)
        # Y-Sorting: von hinten (kleines y) nach vorne (grosses y) zeichnen
        for ding in sorted(sichtbar, key=lambda d: (d.sortier_y, d.x)):
            ding.zeichnen(flaeche, self.kamera)
        self.effekte.zeichnen(flaeche, self.kamera)

        if self.spiel.debug:
            self.zeichne_debug(flaeche, sichtbar)
        self.hud.zeichnen(flaeche, self)
        self.zeichne_hinweise(flaeche)

    def zeichne_hinweise(self, flaeche):
        if self.banner_zeit > 0:
            einflug = min(1.0, (2.0 - self.banner_zeit) * 5)
            x = e.BREITE / 2 + (1 - einflug) * e.BREITE
            grafik.text(flaeche, self.banner, 84, (x + 4, 205), (120, 30, 40))
            grafik.text(flaeche, self.banner, 84, (x, 200), e.GELB)
        if self.go_zeit > 0 and self.wellen.aktiv is None and int(self.go_zeit * 3) % 2 == 0:
            x = e.BREITE - 110 + math.sin(self.spielzeit * 10) * 8
            grafik.text(flaeche, "GO", 64, (x, 250), e.GELB)
            pygame.draw.polygon(flaeche, e.GELB, [(x + 40, 230), (x + 70, 250), (x + 40, 270)])
            pygame.draw.polygon(flaeche, e.UMRISS, [(x + 40, 230), (x + 70, 250), (x + 40, 270)], 3)
        if self.pausiert:
            abdunkeln(flaeche, 160)
            zeichne_titel(flaeche, "PAUSE", 200)
            if hat_gamepad(self.spiel):
                grafik.text(flaeche, "Enter / Start: weiter   ·   Esc / B: zum Menü", 32, (e.BREITE / 2, 290))
            else:
                grafik.text(flaeche, "Enter: weiter   ·   Esc: zum Menü", 32, (e.BREITE / 2, 290))
            if self.pause_grund:
                grafik.text(flaeche, self.pause_grund, 28, (e.BREITE / 2, 335), e.ROT)

    def zeichne_debug(self, flaeche, sichtbar):
        """F1: Körperboxen (gelb), Hurtboxen (blau) und Hitboxen (rot) anzeigen."""
        k = self.kamera
        for ding in sichtbar:
            box = ding.koerperbox()
            if box:
                x1, y1 = k.zu_bild(box[0], box[2])
                x2, y2 = k.zu_bild(box[1], box[3])
                pygame.draw.rect(flaeche, (255, 230, 0), (x1, y1, x2 - x1, y2 - y1), 1)
            for box, farbe in ((ding.hurtbox(), (60, 160, 255)), (getattr(ding, "hitbox", lambda: None)(), (255, 40, 40))):
                if box is None:
                    continue
                mitte_y = (box.y1 + box.y2) / 2
                x1, oben = k.zu_bild(box.x1, mitte_y, box.z2)
                x2, unten = k.zu_bild(box.x2, mitte_y, box.z1)
                pygame.draw.rect(flaeche, farbe, (x1, oben, x2 - x1, unten - oben), 2)
                # Tiefe der Box als Linie am Boden
                bx, by1 = k.zu_bild(box.x1, box.y1)
                _, by2 = k.zu_bild(box.x1, box.y2)
                pygame.draw.line(flaeche, farbe, (bx, by1), (bx, by2), 1)
            if hasattr(ding, "ki"):
                sx, sy = k.zu_bild(ding.x, ding.y, ding.hoehe + 30)
                farbe = e.ROT if ding.darf_angreifen else e.GRAU
                grafik.text(flaeche, f"{ding.ki} / {ding.zustand}", 18, (sx, sy), farbe)
        fps = self.spiel.uhr.get_fps()
        grafik.text(flaeche, f"FPS {fps:4.0f}  Gegner {len(self.gegner)}  Kamera {self.kamera.x:5.0f}",
                    20, (10, e.HOEHE - 12), e.TEXT, "bottomleft")


class ErgebnisSzene(Szene):
    """Game Over oder Sieg: zeigt die Punkte und den Rekord."""

    SPERRZEIT = 1.0  # Sekunden, damit man nicht aus Versehen sofort weiterdrückt

    def __init__(self, spiel, spielszene, gewonnen):
        super().__init__(spiel)
        self.gewonnen = gewonnen
        self.spieler = spielszene.spieler
        self.spielzeit = spielszene.spielzeit
        self.wartezeit = self.SPERRZEIT
        self.zeit = 0.0
        self.kamera = spielszene.kamera
        self.level = spielszene.level
        bester = max((s.punkte for s in self.spieler), default=0)
        self.neuer_rekord = bester > spiel.rekord
        spiel.rekord = max(spiel.rekord, bester)

    def ereignis(self, ereignis):
        knopf = irgendein_knopf(self.spiel.steuerungen, ereignis)
        if self.wartezeit <= 0 and (ist_weiter(ereignis) or knopf in ("a", "start")
                                    or self.spiel.steuerungen[0].aktion(ereignis) == "schlag"):
            self.spiel.wechsle_zu(MenueSzene(self.spiel))

    def aktualisieren(self, dt):
        self.wartezeit -= dt
        self.zeit += dt

    def zeichnen(self, flaeche):
        self.level.zeige_hintergrund(flaeche, self.kamera)
        abdunkeln(flaeche, 170)
        if self.gewonnen:
            zeichne_titel(flaeche, "GESCHAFFT!", 90)
            grafik.text(flaeche, "Die Strassen sind wieder sicher.", 32, (e.BREITE / 2, 150))
        else:
            zeichne_titel(flaeche, "GAME OVER", 90, farbe=e.ROT)
            grafik.text(flaeche, "Die Bande war zu stark. Nochmal?", 32, (e.BREITE / 2, 150))

        breite = len(self.spieler)
        for i, spieler in enumerate(sorted(self.spieler, key=lambda s: s.nummer)):
            x = e.BREITE / 2 + (i - (breite - 1) / 2) * 300
            boden = 350
            pose = posen.jubeln(self.zeit) if self.gewonnen else posen.liegen(0)
            grafik.zeichne_schatten(flaeche, x, boden, 90)
            grafik.zeichne_figur(flaeche, spieler.skin, pose, x, boden, 1, 1.4, zeit=self.zeit)
            grafik.text(flaeche, f"{spieler.nummer}P {spieler.name}", 32, (x, boden + 26), spieler.farbe)
            grafik.text(flaeche, f"Punkte: {spieler.punkte}", 28, (x, boden + 54))
            grafik.text(flaeche, f"Beste Combo: {spieler.beste_combo}", 24, (x, boden + 78), e.GRAU)

        minuten, sekunden = divmod(int(self.spielzeit), 60)
        zeile = f"Zeit {minuten}:{sekunden:02d}   ·   Rekord: {self.spiel.rekord}"
        if self.neuer_rekord:
            zeile += "  NEU!"
        grafik.text(flaeche, zeile, 28, (e.BREITE / 2, 468), e.GELB if self.neuer_rekord else e.TEXT)
        if self.wartezeit <= 0 and int(self.zeit * 2.5) % 2 == 0:
            hinweis = "Enter / A: zurück zum Menü" if hat_gamepad(self.spiel) else "Enter: zurück zum Menü"
            grafik.text(flaeche, hinweis, 32, (e.BREITE / 2, 505), e.GRAU)
