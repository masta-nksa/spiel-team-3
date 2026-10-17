"""Skins: Aussehen aller Figuren. Gezeichnet wird alles in grafik.py, hier stehen nur die Daten.

  haut, haare, oberteil, hose, schuhe   Farben
  frisur        "kurz", "zopf", "irokese", "glatze", "stachel"
  aermel        Oberarme in der Farbe des Oberteils (Jacke) statt Haut
  oberteil      None = nackter Oberkörper (dann ist weste die Farbe der Weste)
  stirnband     Farbe des Stirnbands oder None. Die Bänder flattern immer nach hinten
                und zeigen so die Blickrichtung.
  dicke         Faktor für die Dicke von Armen, Beinen und Rumpf
  extras        "bart", "brille", "kette", "handschuhe"
"""

SKINS = {
    # --- Spieler ---
    "p1": dict(
        name="KAI", haut=(238, 196, 156), haare=(52, 36, 26), frisur="kurz",
        oberteil=(40, 105, 225), aermel=False, hose=(28, 44, 108), schuhe=(235, 235, 240),
        gurt=(18, 18, 28), stirnband=(110, 200, 255), dicke=1.0, extras=("handschuhe",),
        handschuhe=(90, 175, 255),
    ),
    "p2": dict(
        name="RIA", haut=(244, 204, 170), haare=(235, 175, 55), frisur="zopf",
        oberteil=(215, 45, 50), aermel=False, hose=(105, 22, 30), schuhe=(240, 230, 225),
        gurt=(30, 16, 18), stirnband=(255, 150, 110), dicke=0.95, extras=("handschuhe",),
        handschuhe=(255, 110, 100),
    ),
    # --- Gegner: alle in Grüntönen, aber gut unterscheidbar ---
    "schlaeger": dict(
        name="SCHLÄGER", haut=(205, 152, 112), haare=(25, 22, 20), frisur="kurz",
        oberteil=(55, 140, 65), aermel=True, hose=(46, 58, 44), schuhe=(40, 30, 25),
        gurt=(25, 25, 20), stirnband=None, dicke=1.0, extras=(),
    ),
    "flitzer": dict(
        name="FLITZER", haut=(226, 178, 140), haare=(80, 235, 110), frisur="irokese",
        oberteil=(130, 225, 120), aermel=False, hose=(30, 95, 62), schuhe=(240, 240, 60),
        gurt=(20, 60, 30), stirnband=None, dicke=0.9, extras=(),
    ),
    "brocken": dict(
        name="BROCKEN", haut=(180, 128, 92), haare=(30, 22, 18), frisur="glatze",
        oberteil=None, weste=(26, 92, 44), aermel=False, hose=(34, 48, 36), schuhe=(30, 26, 22),
        gurt=(70, 50, 20), stirnband=None, dicke=1.35, extras=("bart",),
    ),
    "boss": dict(
        name="BOSS GRANIT", haut=(196, 142, 104), haare=(20, 20, 24), frisur="stachel",
        oberteil=(16, 74, 40), aermel=True, hose=(18, 30, 24), schuhe=(15, 15, 15),
        gurt=(220, 185, 60), stirnband=None, dicke=1.25, extras=("brille", "kette"),
    ),
}
