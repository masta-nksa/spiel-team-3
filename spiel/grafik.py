"""Prozedurale Grafik: Alle Figuren werden jedes Bild neu aus einfachen Formen gezeichnet.

Eine Figur ist ein Skelett aus Gelenken (Hüfte, Knie, Schulter, Ellbogen ...).
Die Pose (siehe posen.py) legt die Winkel fest, daraus rechnet zeichne_figur die
Gelenkpunkte aus und zeichnet Arme und Beine als abgerundete "Kapseln".
Gezeichnet wird von hinten nach vorne: hinteres Bein, hinterer Arm, Rumpf,
vorderes Bein, Kopf, vorderer Arm. Hintere Gliedmassen sind etwas dunkler, das gibt Tiefe.

Gerechnet wird in einem lokalen Koordinatensystem: Ursprung am Fusspunkt, +x zeigt
in Blickrichtung, y nach unten. Erst ganz am Schluss wird gespiegelt (Blickrichtung),
gekippt (Fallen, Liegen) und auf den Bildschirm verschoben.
"""
import functools
import math

import pygame

import einstellungen as e

# Längen der Körperteile in Pixel bei Skala 1 (eine Figur ist dann gut 90 Pixel gross)
L_OBERSCHENKEL = 21
L_UNTERSCHENKEL = 21
L_RUMPF = 30
L_HALS = 3
R_KOPF = 10
L_OBERARM = 15
L_UNTERARM = 15
L_FUSS = 9
FIGUR_HOEHE = L_OBERSCHENKEL + L_UNTERSCHENKEL + L_RUMPF + L_HALS + 2 * R_KOPF

sin, cos, rad = math.sin, math.cos, math.radians


def dunkler(farbe, faktor=0.74):
    return tuple(int(c * faktor) for c in farbe)


def heller(farbe, anteil=0.35):
    return tuple(int(c + (255 - c) * anteil) for c in farbe)


def kapsel(flaeche, a, b, r1, farbe, umriss=e.UMRISS, r2=None):
    """Abgerundeter Balken von a nach b (Radius r1 bei a, r2 bei b) mit Umriss."""
    if r2 is None:
        r2 = r1
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    laenge = math.hypot(dx, dy)
    for zusatz, f in ((1.6, umriss), (0, farbe)):
        ra, rb = r1 + zusatz, r2 + zusatz
        if laenge > 0.5:
            nx, ny = -dy / laenge, dx / laenge
            pygame.draw.polygon(flaeche, f, [
                (ax + nx * ra, ay + ny * ra), (bx + nx * rb, by + ny * rb),
                (bx - nx * rb, by - ny * rb), (ax - nx * ra, ay - ny * ra),
            ])
        pygame.draw.circle(flaeche, f, a, ra)
        pygame.draw.circle(flaeche, f, b, rb)


def zeichne_figur(flaeche, skin, p, fx, fy, blick, skala=1.0, weiss=False, zeit=0.0, halte=None):
    """Zeichnet eine Figur mit Fusspunkt (fx, fy) in der Pose p.

    blick: 1 = schaut nach rechts, -1 = nach links
    weiss: Figur blitzt weiss auf (gerade getroffen)
    halte: Funktion, die zuletzt (vor allem anderen) etwas in die Hand zeichnet. Sie bekommt
           (Fläche, vordere Hand, vorderer Ellbogen, hintere Hand, hinterer Ellbogen, Skala) in Bildkoordinaten.
    """
    if p["umdrehen"] > 0.5:
        blick = -blick
    s = skala
    d = skin["dicke"] * s

    if weiss:
        def F(_farbe):
            return (255, 255, 255)
        U = (210, 210, 225)
    else:
        def F(farbe):
            return farbe
        U = e.UMRISS

    # --- Skelett ausrechnen (lokal) ---
    huefte = (0.0, -(L_OBERSCHENKEL + L_UNTERSCHENKEL) * s + p["tief"] * s)
    n = rad(p["neigung"])
    hals = (huefte[0] + sin(n) * L_RUMPF * s, huefte[1] - cos(n) * L_RUMPF * s)
    schulter = (huefte[0] + (hals[0] - huefte[0]) * 0.86, huefte[1] + (hals[1] - huefte[1]) * 0.86)
    kw = n + rad(p["kopf"])
    kopf = (hals[0] + sin(kw) * (L_HALS + R_KOPF) * s, hals[1] - cos(kw) * (L_HALS + R_KOPF) * s)

    def glied(start, w1, l1, w2, l2):
        a1, a2 = rad(w1), rad(w2)
        mitte = (start[0] + sin(a1) * l1 * s, start[1] + cos(a1) * l1 * s)
        ende = (mitte[0] + sin(a2) * l2 * s, mitte[1] + cos(a2) * l2 * s)
        return mitte, ende

    huefte_h = (huefte[0] - 2 * s, huefte[1])
    schulter_h = (schulter[0] - 3 * s, schulter[1])
    knie_v, fuss_v = glied(huefte, p["vh"], L_OBERSCHENKEL, p["vh"] - p["vk"], L_UNTERSCHENKEL)
    knie_h, fuss_h = glied(huefte_h, p["hh"], L_OBERSCHENKEL, p["hh"] - p["hk"], L_UNTERSCHENKEL)
    ellb_v, hand_v = glied(schulter, p["vs"], L_OBERARM, p["vs"] + p["ve"], L_UNTERARM)
    ellb_h, hand_h = glied(schulter_h, p["hs"], L_OBERARM, p["hs"] + p["he"], L_UNTERARM)

    # Steht die Figur, kommt der tiefste Fuss genau auf den Boden
    dreh = rad(p["drehung"])
    boden = 0.0
    if abs(p["drehung"]) < 1:
        boden = -max(fuss_v[1], fuss_h[1]) - 3 * d

    cd, sd = cos(dreh), sin(dreh)
    versatz = -sd * 40 * s  # liegende Figuren liegen um ihre Mitte herum
    heben = abs(sd) * 7 * s

    def P(punkt):
        lx, ly = punkt[0], punkt[1] + boden
        rx = lx * cd - ly * sd + versatz
        ry = lx * sd + ly * cd - heben
        return (fx + blick * rx, fy + ry)

    # --- Farben ---
    haut = skin["haut"]
    hose = skin["hose"]
    oberteil = skin["oberteil"]
    handschuh = skin.get("handschuhe", haut)

    def bein(h, knie, fuss, w_unterschenkel, dunkel):
        f = dunkler if dunkel else (lambda c: c)
        kapsel(flaeche, P(h), P(knie), 5.2 * d, F(f(hose)), U, 4.6 * d)
        kapsel(flaeche, P(knie), P(fuss), 4.6 * d, F(f(hose)), U, 4.0 * d)
        a = rad(w_unterschenkel)
        richtung = (cos(a), -sin(a))  # Fuss zeigt nach vorne
        ferse = (fuss[0] - richtung[0] * 2 * s, fuss[1] - richtung[1] * 2 * s)
        spitze = (fuss[0] + richtung[0] * L_FUSS * s, fuss[1] + richtung[1] * L_FUSS * s)
        kapsel(flaeche, P(ferse), P(spitze), 3.4 * d, F(f(skin["schuhe"])), U)

    def arm(sch, ellb, hand, dunkel):
        f = dunkler if dunkel else (lambda c: c)
        farbe_oa = oberteil if (skin["aermel"] and oberteil) else haut
        kapsel(flaeche, P(sch), P(ellb), 4.2 * d, F(f(farbe_oa)), U, 3.8 * d)
        kapsel(flaeche, P(ellb), P(hand), 3.7 * d, F(f(haut)), U, 3.4 * d)
        if "handschuhe" in skin["extras"]:
            kapsel(flaeche, P(hand), P(hand), 5.0 * d, F(f(handschuh)), U)
        else:
            kapsel(flaeche, P(hand), P(hand), 4.4 * d, F(f(haut)), U)

    def rumpf():
        tx, ty = hals[0] - huefte[0], hals[1] - huefte[1]
        laenge = math.hypot(tx, ty) or 1
        nx, ny = -ty / laenge, tx / laenge  # zeigt nach vorne (Brust)
        farbe = oberteil if oberteil else skin.get("weste", haut)
        kapsel(flaeche, P(huefte), P(schulter), 7.4 * d, F(farbe), U, 9.6 * d)
        if not oberteil:
            # offene Weste: vorne sieht man die Brust
            a = (huefte[0] + nx * 4 * d, huefte[1] + ny * 4 * d)
            b = (schulter[0] + nx * 4.5 * d, schulter[1] + ny * 4.5 * d)
            kapsel(flaeche, P(a), P(b), 3.6 * d, F(haut), F(haut), 5.2 * d)
        elif not weiss:
            # Lichtkante vorne am Oberteil
            a = (huefte[0] + nx * 4.5 * d, huefte[1] + ny * 4.5 * d - 2 * s)
            b = (schulter[0] + nx * 5.5 * d, schulter[1] + ny * 5.5 * d)
            pygame.draw.line(flaeche, heller(farbe, 0.3), P(a), P(b), max(1, int(2.5 * s)))
        # Gürtel
        g1 = (huefte[0] + nx * 7.6 * d - tx / laenge * 2, huefte[1] + ny * 7.6 * d - ty / laenge * 2)
        g2 = (huefte[0] - nx * 7.6 * d - tx / laenge * 2, huefte[1] - ny * 7.6 * d - ty / laenge * 2)
        pygame.draw.line(flaeche, F(skin["gurt"]), P(g1), P(g2), max(2, int(3.5 * s)))
        if "kette" in skin["extras"] and not weiss:
            for i in range(5):
                f = 0.2 + i * 0.16
                kx = hals[0] + nx * (2 + i * 1.6) * d - (hals[0] - schulter[0]) * f * 3
                ky = hals[1] + ny * (2 + i * 1.6) * d - (hals[1] - schulter[1]) * f * 3
                pygame.draw.circle(flaeche, (240, 200, 70), P((kx, ky)), max(1.5, 1.8 * s))

    def kopf_zeichnen():
        r = R_KOPF * s * (1 + (skin["dicke"] - 1) * 0.3)

        def kp(theta, faktor):
            """Punkt am Kopf: theta in Grad ab "oben", positiv = nach vorne; faktor = Anteil vom Radius."""
            a = kw + rad(theta)
            return (kopf[0] + sin(a) * r * faktor, kopf[1] - cos(a) * r * faktor)

        frisur = skin["frisur"]
        wehen = sin(zeit * 9)
        if frisur == "zopf":
            ansatz = kp(-105, 0.9)
            mitte = (ansatz[0] - 7 * s, ansatz[1] + 5 * s + wehen * 1.5 * s)
            ende = (ansatz[0] - 12 * s, ansatz[1] + 13 * s + wehen * 3 * s)
            kapsel(flaeche, P(ansatz), P(mitte), 3.6 * s, F(skin["haare"]), U, 3.2 * s)
            kapsel(flaeche, P(mitte), P(ende), 3.2 * s, F(skin["haare"]), U, 2.0 * s)
        # Hals und Kopf
        kapsel(flaeche, P(hals), P(hals), 3.6 * d, F(dunkler(haut, 0.9)), U)
        kapsel(flaeche, P(kopf), P(kopf), r, F(haut), U)

        haare = F(skin["haare"])
        if frisur in ("kurz", "zopf"):
            aussen = [kp(t, 1.1) for t in range(45, -136, -15)]
            innen = [kp(t, 0.6) for t in range(-110, 31, 20)]
            pygame.draw.polygon(flaeche, haare, [P(q) for q in aussen + innen])
        elif frisur == "stachel":
            aussen = [kp(t, 1.15 if i % 2 else 1.5) for i, t in enumerate(range(40, -141, -12))]
            innen = [kp(t, 0.65) for t in range(-120, 31, 30)]
            pygame.draw.polygon(flaeche, haare, [P(q) for q in aussen + innen])
            pygame.draw.polygon(flaeche, U, [P(q) for q in aussen], 1)
        elif frisur == "irokese":
            for t in range(25, -96, -24):
                fuss1, fuss2, spitze = kp(t + 9, 0.95), kp(t - 9, 0.95), kp(t - 6, 1.75)
                pygame.draw.polygon(flaeche, haare, [P(fuss1), P(spitze), P(fuss2)])
                pygame.draw.polygon(flaeche, U, [P(fuss1), P(spitze), P(fuss2)], 1)
        elif frisur == "glatze" and not weiss:
            pygame.draw.circle(flaeche, heller(haut, 0.45), P(kp(-15, 0.55)), max(1.5, r * 0.22))

        if weiss:
            return
        # Gesicht: alles auf der Vorderseite, so sieht man sofort, wohin die Figur schaut
        pygame.draw.circle(flaeche, dunkler(haut, 0.8), P(kp(-80, 0.15)), max(1.5, r * 0.22))  # Ohr
        if "brille" in skin["extras"]:
            pygame.draw.line(flaeche, (10, 10, 12), P(kp(-70, 0.98)), P(kp(60, 0.62)), max(2, int(2 * s)))
            pygame.draw.line(flaeche, (10, 10, 12), P(kp(48, 0.62)), P(kp(88, 1.02)), max(3, int(4.4 * s)))
            pygame.draw.circle(flaeche, (120, 200, 255), P(kp(66, 0.78)), max(1, 1.1 * s))
        else:
            pygame.draw.circle(flaeche, (255, 255, 255), P(kp(66, 0.62)), max(1.5, 2.1 * s))
            pygame.draw.circle(flaeche, (20, 20, 30), P(kp(70, 0.68)), max(1, 1.3 * s))
            pygame.draw.line(flaeche, dunkler(skin["haare"], 0.8), P(kp(50, 0.72)), P(kp(80, 0.84)), max(1, int(2 * s)))
        pygame.draw.circle(flaeche, dunkler(haut, 0.88), P(kp(96, 1.0)), max(1.5, 1.9 * s))  # Nase
        pygame.draw.line(flaeche, (120, 50, 50), P(kp(122, 0.72)), P(kp(135, 0.62)), max(1, int(1.5 * s)))  # Mund
        if "bart" in skin["extras"]:
            punkte = [kp(t, 1.08) for t in range(100, 211, 22)] + [kp(150, 0.45)]
            pygame.draw.polygon(flaeche, skin["haare"], [P(q) for q in punkte])

        band = skin["stirnband"]
        if band:
            vorne, hinten = kp(32, 1.0), kp(-88, 1.0)
            pygame.draw.line(flaeche, band, P(vorne), P(hinten), max(2, int(3.5 * s)))
            # die Bänder flattern nach hinten: zweiter Richtungsanzeiger
            ende1 = (hinten[0] - 11 * s, hinten[1] + 2 * s + wehen * 2.5 * s)
            ende2 = (hinten[0] - 9 * s, hinten[1] + 7 * s - wehen * 2 * s)
            pygame.draw.line(flaeche, band, P(hinten), P(ende1), max(2, int(3 * s)))
            pygame.draw.line(flaeche, dunkler(band), P(hinten), P(ende2), max(2, int(3 * s)))

    # --- Zeichnen, von hinten nach vorne ---
    bein(huefte_h, knie_h, fuss_h, p["hh"] - p["hk"], True)
    arm(schulter_h, ellb_h, hand_h, True)
    rumpf()
    bein(huefte, knie_v, fuss_v, p["vh"] - p["vk"], False)
    kopf_zeichnen()
    arm(schulter, ellb_v, hand_v, False)
    if halte is not None:
        halte(flaeche, P(hand_v), P(ellb_v), P(hand_h), P(ellb_h), s)


# --- Schatten und Spielermarkierung ----------------------------------------------

@functools.lru_cache(maxsize=128)
def schatten_bild(breite):
    hoehe = max(4, breite // 3)
    bild = pygame.Surface((breite, hoehe), pygame.SRCALPHA)
    pygame.draw.ellipse(bild, (0, 0, 0, 100), bild.get_rect())
    return bild


def zeichne_schatten(flaeche, x, y, breite):
    bild = schatten_bild(max(6, int(breite)))
    flaeche.blit(bild, bild.get_rect(center=(round(x), round(y))))


def zeichne_spielerring(flaeche, x, y, breite, farbe, blick):
    """Farbiger Ring am Boden mit Pfeil in Blickrichtung."""
    rahmen = pygame.Rect(0, 0, int(breite), int(breite / 3))
    rahmen.center = (round(x), round(y))
    pygame.draw.ellipse(flaeche, farbe, rahmen, 2)
    spitze_x = x + blick * (breite / 2 + 9)
    basis_x = x + blick * (breite / 2 + 1)
    pygame.draw.polygon(flaeche, farbe, [(spitze_x, y), (basis_x, y - 5), (basis_x, y + 5)])


# --- Text -----------------------------------------------------------------------

@functools.cache
def schrift(groesse):
    # Schriften nur einmal pro Grösse laden, nicht in jedem Bild neu.
    return pygame.font.Font(None, groesse)


@functools.lru_cache(maxsize=512)
def text_bild(inhalt, groesse, farbe, umriss):
    vorne = schrift(groesse).render(inhalt, True, farbe)
    if not umriss:
        return vorne
    rand = max(1, groesse // 16)
    hinten = schrift(groesse).render(inhalt, True, e.UMRISS)
    bild = pygame.Surface((vorne.get_width() + 2 * rand, vorne.get_height() + 2 * rand), pygame.SRCALPHA)
    for dx in (-rand, 0, rand):
        for dy in (-rand, 0, rand):
            if dx or dy:
                bild.blit(hinten, (rand + dx, rand + dy))
    bild.blit(vorne, (rand, rand))
    return bild


def text(flaeche, inhalt, groesse, pos, farbe=e.TEXT, anker="center", umriss=True):
    bild = text_bild(str(inhalt), groesse, tuple(farbe), umriss)
    rahmen = bild.get_rect(**{anker: (round(pos[0]), round(pos[1]))})
    flaeche.blit(bild, rahmen)
    return rahmen


# --- Portrait fürs HUD ----------------------------------------------------------

def zeichne_portrait(flaeche, skin, rahmen, zeit=0.0, hintergrund=(40, 40, 60)):
    """Kopf der Figur gross im Rahmen: dieselbe Zeichenfunktion, nur vergrössert und abgeschnitten."""
    from posen import stehen
    pygame.draw.rect(flaeche, hintergrund, rahmen, border_radius=8)
    alt = flaeche.get_clip()
    flaeche.set_clip(rahmen)
    skala = rahmen.height / 30
    fuss_y = rahmen.centery + (FIGUR_HOEHE - R_KOPF - 3) * skala
    zeichne_figur(flaeche, skin, stehen(zeit), rahmen.centerx - 2 * skala, fuss_y, 1, skala, zeit=zeit)
    flaeche.set_clip(alt)
    pygame.draw.rect(flaeche, e.UMRISS, rahmen, 2, border_radius=8)
