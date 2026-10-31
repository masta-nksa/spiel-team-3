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

# --- Waffen und Wurfobjekte (siehe waffen.py) -----------------------------------
WAFFE_BODEN_ZEIT = 12.0  # so lange liegt eine Waffe am Boden (die letzten 3 s blinkt sie)
WAFFE_TOD_ZEIT = 8.0  # Waffe eines gestorbenen Spielers: blinkt die ganze Zeit
GREIF_REICHWEITE = (34, 18)  # |dx|, |dy| zum Aufheben einer Waffe
DROP_MINDESTABSTAND = 12.0  # Sekunden zwischen zwei Waffen-Drops
DROP_PITY_ZEIT = 90.0  # so lange ohne Drop, dann steigt die Chance
DROP_PITY_FAKTOR = 3.0

# --- Tastenbelegung -----------------------------------------------------------
# Mehrere Tasten pro Aktion sind möglich. Schlag + Tritt gleichzeitig = Spezialangriff, "greifen" hebt auf und wirft.
TASTEN_P1 = {
    "links": (pygame.K_a,),
    "rechts": (pygame.K_d,),
    "hoch": (pygame.K_w,),
    "runter": (pygame.K_s,),
    "schlag": (pygame.K_f,),
    "tritt": (pygame.K_g,),
    "sprung": (pygame.K_SPACE,),
    "spezial": (pygame.K_r,),
    "greifen": (pygame.K_e,),
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
    "greifen": (pygame.K_j, pygame.K_KP_PERIOD),
}
# --- Gamepad (Xbox) -----------------------------------------------------------
# Controller 1 gehört Spieler 1, Controller 2 Spieler 2. Die Tastatur geht immer parallel.
# Belegung: linker Stick / Steuerkreuz = Bewegen, X = Schlag, B = Tritt, A = Sprung, Y = Spezial,
#           LB = Schlag, RB = Greifen/Werfen, Start = Pause, Back = Pause: zurück zum Menü.
# Alles, was mit Knopf-Nummern zu tun hat, steht hier an einer Stelle.
GAMEPAD_AKTIONEN = {"x": "schlag", "lb": "schlag", "b": "tritt", "rb": "greifen", "a": "sprung", "y": "spezial"}
# Welcher Knopf steht beim Hinweis "... drücken"? (LB ist nur Zweitbelegung von Schlag)
GAMEPAD_HINWEIS = {"schlag": "X", "tritt": "B", "sprung": "A", "spezial": "Y", "greifen": "RB"}

# Normalfall: SDL kennt den Controller (bei Xbox-Controllern immer). Dann kommen CONTROLLERBUTTONDOWN-Ereignisse mit
# festen Namen, egal ob USB, Bluetooth, XInput oder HIDAPI. Das ist die sichere Variante.
CONTROLLER_KNOEPFE = {
    pygame.CONTROLLER_BUTTON_A: "a",
    pygame.CONTROLLER_BUTTON_B: "b",
    pygame.CONTROLLER_BUTTON_X: "x",
    pygame.CONTROLLER_BUTTON_Y: "y",
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "lb",
    pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "rb",
    pygame.CONTROLLER_BUTTON_BACK: "back",
    pygame.CONTROLLER_BUTTON_START: "start",
}
# Notlösung (z. B. im Browser, wo es die Controller-Schnittstelle nicht gibt): rohe Joystick-Nummern.
# Windows (XInput/WGI) und Linux (xpad): A=0 B=1 X=2 Y=3 LB=4 RB=5 Back=6 Start=7, Stick = Achse 0/1, Kreuz = Hat 0.
JOY_KNOEPFE = {0: "a", 1: "b", 2: "x", 3: "y", 4: "lb", 5: "rb", 6: "back", 7: "start"}
# Browser (Gamepad-API "standard"): Back=8, Start=9, das Steuerkreuz sind die Knöpfe 12-15.
JOY_KNOEPFE_BROWSER = {0: "a", 1: "b", 2: "x", 3: "y", 4: "lb", 5: "rb", 8: "back", 9: "start"}
JOY_KREUZ_BROWSER = {"hoch": 12, "runter": 13, "links": 14, "rechts": 15}

STICK_EIN = 0.5  # ab so viel Ausschlag (Länge des Sticks) zählt eine Richtung ...
STICK_AUS = 0.35  # ... und erst darunter hört sie wieder auf. Der Abstand verhindert Zittern.
STICK_ACHSE_EIN = 0.42  # Anteil einer Achse am Ausschlag, ab dem sie zählt (Diagonalen)
STICK_ACHSE_AUS = 0.30
RUMBLE_TREFFER = (0.35, 0.35, 120)  # tiefer Motor, hoher Motor, Millisekunden
RUMBLE_UMGEWORFEN = (0.8, 0.6, 260)

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
