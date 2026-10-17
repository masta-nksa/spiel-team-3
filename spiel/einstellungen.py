# Alle festen Werte an einem Ort. Wer etwas ändern will, muss nicht im ganzen Code suchen.
import pygame

TITEL = "Doppelfaust"
BREITE = 960
HOEHE = 540
FPS = 60

# Grösster erlaubter Zeitschritt in Sekunden. Wechselt man im Browser den Tab,
# kommt sonst nach der Pause ein riesiger Sprung, und Figuren fliegen durch Wände.
MAX_DT = 0.05

# --- Spielfeld (2.5D) ---------------------------------------------------------
# Jede Figur hat drei Koordinaten:
#   x = links/rechts in der Welt
#   y = Tiefe auf der Strasse (klein = hinten, gross = vorne). Das ist auch der Fusspunkt auf dem Bild.
#   z = Höhe über dem Boden (Sprünge, Flug nach einem Treffer)
# Auf den Bildschirm kommt eine Figur bei (x - kamera, y - z).
BODEN_OBEN = 322  # hinterster Fusspunkt (am Gehsteig)
BODEN_UNTEN = 522  # vorderster Fusspunkt
SCHWERKRAFT = 1900  # Pixel pro Sekunde², zieht z nach unten

# --- Kampf --------------------------------------------------------------------
TREFFERSTOPP_LEICHT = 0.05  # Sekunden "Einfrieren" bei einem Treffer: macht Schläge spürbar
TREFFERSTOPP_SCHWER = 0.10
MAX_ANGREIFER = 2  # so viele Gegner dürfen gleichzeitig auf denselben Spieler losgehen
COMBO_ZEIT = 1.2  # Sekunden, bis der Trefferzähler wieder auf 0 fällt

# --- Spieler ------------------------------------------------------------------
SPIELER_HP = 100
SPIELER_EXTRALEBEN = 2
SPIELER_TEMPO_X = 175  # Pixel pro Sekunde
SPIELER_TEMPO_Y = 115  # in die Tiefe langsamer, das wirkt räumlicher
SPRUNGKRAFT = 620

# --- Tastenbelegung -----------------------------------------------------------
# Mehrere Tasten pro Aktion sind möglich. Schlag + Tritt gleichzeitig = Spezialangriff.
TASTEN_P1 = {
    "links": (pygame.K_a,),
    "rechts": (pygame.K_d,),
    "hoch": (pygame.K_w,),
    "runter": (pygame.K_s,),
    "schlag": (pygame.K_f,),
    "tritt": (pygame.K_g,),
    "sprung": (pygame.K_SPACE,),
    "spezial": (pygame.K_r,),
}
TASTEN_P2 = {
    "links": (pygame.K_LEFT,),
    "rechts": (pygame.K_RIGHT,),
    "hoch": (pygame.K_UP,),
    "runter": (pygame.K_DOWN,),
    "schlag": (pygame.K_k, pygame.K_KP1),
    "tritt": (pygame.K_l, pygame.K_KP2),
    "sprung": (pygame.K_o, pygame.K_KP0),
    "spezial": (pygame.K_i, pygame.K_KP3),
}
# Gamepad (Xbox-Belegung): X = Schlag, B = Tritt, A = Sprung, Y = Spezial
GAMEPAD_KNOEPFE = {2: "schlag", 1: "tritt", 0: "sprung", 3: "spezial"}

# --- Farben als (Rot, Grün, Blau) -----------------------------------------------
HINTERGRUND = (14, 12, 28)
TEXT = (240, 238, 245)
GELB = (255, 210, 60)
ORANGE = (255, 140, 40)
ROT = (230, 50, 50)
GRUEN = (90, 210, 100)
GRAU = (140, 140, 155)
DUNKEL = (20, 18, 30)
UMRISS = (22, 18, 30)
SPIELER_FARBEN = {1: (70, 150, 255), 2: (255, 80, 80)}
