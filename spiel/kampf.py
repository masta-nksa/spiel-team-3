"""Kampfsystem: Boxen und Angriffe.

Drei Arten von Boxen, sauber getrennt:
  Körperbox  nur die Fussfläche am Boden. Damit schieben sich Figuren auseinander
             und stossen an Kisten. Sie entscheidet nie über Treffer.
  Hurtbox    wo man eine Figur treffen kann (der ganze Körper als Quader).
  Hitbox     wo ein Angriff gerade trifft. Es gibt sie nur in der aktiven Phase eines Angriffs.

Ein Treffer ist: Hitbox des Angreifers überlappt Hurtbox des Ziels.
Weil das Spiel 2.5D ist, sind alle Boxen Quader mit x (Breite), y (Tiefe) und z (Höhe).
So trifft ein Schlag nur, wenn das Ziel auch ungefähr auf derselben Tiefe steht.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x1: float
    x2: float
    y1: float
    y2: float
    z1: float
    z2: float

    def ueberlappt(self, andere):
        return (
            self.x1 < andere.x2 and andere.x1 < self.x2
            and self.y1 < andere.y2 and andere.y1 < self.y2
            and self.z1 < andere.z2 and andere.z1 < self.z2
        )

    def schnitt_mitte(self, andere):
        """Mitte der Überlappung: dort erscheinen die Trefferfunken."""
        x = (max(self.x1, andere.x1) + min(self.x2, andere.x2)) / 2
        y = (max(self.y1, andere.y1) + min(self.y2, andere.y2)) / 2
        z = (max(self.z1, andere.z1) + min(self.z2, andere.z2)) / 2
        return x, y, z


@dataclass(frozen=True)
class Angriff:
    """Bauplan eines Angriffs. Zeiten in Sekunden, Längen in Pixel bei Skala 1.

    Ein Angriff hat drei Phasen:
      anlauf    Ausholen, noch keine Hitbox (der Gegner sieht ihn kommen)
      aktiv     die Hitbox ist da und kann treffen
      erholung  zurückziehen, verwundbar
    """
    name: str
    pose: str
    anlauf: float
    aktiv: float
    erholung: float
    schaden: int
    # Hitbox relativ zur Figur: von/bis vor der Körpermitte, von/bis über dem Fusspunkt
    vorne: tuple
    hoehe: tuple
    tiefe: float = 16  # halbe Tiefe der Hitbox in y
    rueckstoss: float = 90
    starre: float = 0.3  # so lange kann das Ziel nach dem Treffer nichts tun
    wirft_um: bool = False
    rundum: bool = False  # trifft auch hinter der Figur (Wirbeltritt)
    vorschub: float = 0  # Vorwärtstempo während Anlauf und aktiver Phase
    in_der_luft: bool = False
    folge_schlag: str = None  # Combo: dieser Angriff kommt, wenn man nach einem Treffer wieder schlägt
    folge_tritt: str = None
    kosten: int = 0  # eigene Lebenspunkte (Spezialangriff)
    ton: str = "schlag"

    @property
    def dauer(self):
        return self.anlauf + self.aktiv + self.erholung


ANGRIFFE = {a.name: a for a in [
    # --- Spieler: Schläge ---
    Angriff("schlag1", "gerade", 0.05, 0.07, 0.13, 5, (10, 50), (50, 76),
            rueckstoss=50, starre=0.32, folge_schlag="schlag2", folge_tritt="tritt_hoch"),
    Angriff("schlag2", "haken", 0.06, 0.07, 0.15, 6, (10, 52), (50, 76),
            rueckstoss=60, starre=0.34, folge_schlag="schlag3", folge_tritt="tritt_hoch", vorschub=60),
    Angriff("schlag3", "aufwaerts", 0.09, 0.09, 0.26, 11, (6, 48), (46, 96),
            rueckstoss=230, wirft_um=True, vorschub=80, ton="hart"),
    # --- Spieler: Tritte ---
    Angriff("tritt1", "tritt", 0.09, 0.09, 0.19, 8, (14, 60), (24, 58),
            rueckstoss=110, starre=0.36, folge_tritt="tritt2", folge_schlag="schlag3", ton="tritt"),
    Angriff("tritt2", "drehtritt", 0.10, 0.10, 0.27, 12, (10, 64), (40, 84),
            rueckstoss=260, wirft_um=True, vorschub=50, ton="hart"),
    Angriff("tritt_hoch", "hochtritt", 0.08, 0.10, 0.26, 12, (12, 62), (44, 92),
            rueckstoss=260, wirft_um=True, ton="hart"),
    # --- Spieler: in der Luft und Spezial ---
    Angriff("sprungtritt", "sprungtritt", 0.06, 0.40, 0.08, 11, (6, 60), (8, 50),
            rueckstoss=240, wirft_um=True, in_der_luft=True, ton="hart"),
    Angriff("sprungschlag", "sprungschlag", 0.05, 0.30, 0.08, 8, (8, 50), (40, 80),
            rueckstoss=140, starre=0.4, in_der_luft=True),
    Angriff("wirbel", "wirbel", 0.06, 0.30, 0.22, 10, (-58, 58), (24, 80),
            rueckstoss=280, wirft_um=True, rundum=True, kosten=4, ton="hart"),
    # --- Gegner: länger ausholen, damit man reagieren kann ---
    Angriff("g_schlag", "gerade", 0.30, 0.08, 0.30, 7, (10, 50), (50, 76),
            rueckstoss=70, starre=0.30, folge_schlag="g_haken"),
    Angriff("g_haken", "haken", 0.18, 0.08, 0.40, 8, (10, 52), (50, 76),
            rueckstoss=180, wirft_um=True, vorschub=40),
    Angriff("g_tritt", "tritt", 0.34, 0.10, 0.36, 9, (14, 58), (24, 58),
            rueckstoss=140, starre=0.34, ton="tritt"),
    Angriff("g_flinktritt", "hochtritt", 0.22, 0.09, 0.30, 7, (12, 60), (40, 88),
            rueckstoss=150, starre=0.32, ton="tritt"),
    Angriff("g_hammer", "hammer", 0.50, 0.12, 0.50, 15, (8, 62), (30, 100),
            rueckstoss=300, wirft_um=True, ton="hart"),
    Angriff("g_rammen", "rammen", 0.40, 0.45, 0.45, 13, (0, 52), (20, 90),
            rueckstoss=320, wirft_um=True, vorschub=430, ton="hart"),
]}

SPRUNG_ANGRIFFE = {"schlag": "sprungschlag", "tritt": "sprungtritt"}
START_ANGRIFFE = {"schlag": "schlag1", "tritt": "tritt1", "spezial": "wirbel"}
