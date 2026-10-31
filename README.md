# Doppelfaust – ein 2.5D-Beat-'em-up mit pygame-ce

Ein klassisches Strassen-Prügelspiel im Stil von «Double Dragon», allein oder zu zweit an einer Tastatur.
Kai (blau) und Ria (rot) kämpfen sich durch Altstadt, Industriegebiet und Hafen bis zum Boss.
Alles ist mit [pygame-ce](https://pyga.me/) programmiert. **Es gibt keine einzige Bilddatei:** Figuren, Häuser, Kisten
und Töne entstehen im Code. Bei jedem Push baut GitHub das Spiel mit [pygbag](https://github.com/pygame-web/pygbag)
für den Browser und stellt es online.

Das Spiel läuft danach unter `https://masta-nksa.github.io/<name-des-repos>/`.

## Steuerung

| | 1P Kai (blau) | 2P Ria (rot) | Xbox-Controller |
|---|---|---|---|
| Bewegen | W A S D | Pfeiltasten | linker Stick oder Steuerkreuz |
| Schlag | F | K oder Ziffernblock 1 | X (oder LB) |
| Tritt | G | L oder Ziffernblock 2 | B (oder RB) |
| Sprung | Leertaste | O oder Ziffernblock 0 | A |
| Spezial (Wirbeltritt) | F+G gleichzeitig oder R | K+L gleichzeitig oder I | Y |

### Mit Controllern spielen

- **Zuordnung:** Der zuerst gefundene Controller steuert **1P Kai**, der zweite **2P Ria**. Ist nur einer da, gehört er 1P, und 2P bleibt auf der Tastatur. Die Tastatur funktioniert immer parallel.
- **Bluetooth (Windows):** Zuerst beide Controller im Windows-Bluetooth-Menü koppeln (Einstellungen → Bluetooth & Geräte → Gerät hinzufügen), dann das Spiel starten. Im Menü steht pro Spieler "Controller verbunden" oder "Tastatur".
- **Zwischendurch anstecken:** Ein neu verbundener Controller bekommt den freien Platz. Bricht die Verbindung ab, pausiert das Spiel, und nach dem Wiederverbinden geht es mit Start weiter.
- **Menü:** A, X oder Start startet. **2P dazu:** A auf Controller 2 (oder K), mit Start auf Controller 2 geht es gleich zu zweit los. Y/LB/RB auf Controller 1 schaltet zwischen 1P und 2P um.
- **Im Spiel:** 2P steigt mit X auf Controller 2 ein. **Start** = Pause und weiter, in der Pause **B** oder **Back** = zurück zum Menü.
- **Ergebnis:** A oder Start = zurück zum Menü.
- Bei einem Treffer rüttelt der Controller kurz (wenn er das kann).

- **Combos:** Wer trifft und sofort wieder drückt, verkettet die Angriffe:
  Schlag → Schlag → Aufwärtshaken, Schlag → Schlag → Tritt, Tritt → Drehtritt.
- **Sprungangriffe:** in der Luft Schlag oder Tritt.
- **Spezial:** trifft vorne und hinten, kostet aber 4 eigene Lebenspunkte.
- **Mitspielen:** 2P kann im Menü oder jederzeit im Spiel mit **K** (Controller 2: **X**) einsteigen.
- **Esc** Pause (nochmals Esc: zum Menü), **F1** zeigt Körper-, Hurt- und Hitboxen und den KI-Zustand der Gegner.
- Kisten, Fässer und Mülltonnen kann man zerschlagen. Darin: Hähnchen (+40 HP), Äpfel (+15 HP), Geld (+1000 Punkte).

## Lokal starten

Einmalig im Terminal von VS Code:

```bash
python -m pip install -r requirements.txt
```

Das Spiel braucht **pygame-ce**, nicht das alte **pygame**. Beide lädt man mit `import pygame`, sie vertragen sich aber nicht
im selben Python. Beim Start steht im Terminal `pygame-ce 2.5.8 (SDL …)`. Steht dort nur `pygame 2.6…`, oder bricht das
Spiel mit einem Hinweis ab, zuerst beide entfernen und dann neu installieren:

```bash
python -m pip uninstall -y pygame pygame-ce
```

```bash
python -m pip install -r requirements.txt
```

Spiel starten:

```bash
python spiel/main.py
```

Im Browser testen, bevor du pushst (dann <http://localhost:8000> öffnen, beenden mit Ctrl+C):

```bash
python -m pygbag spiel
```

## Online stellen

Commit, dann Push auf `main`. Unter **Actions** siehst du, wie das Spiel gebaut wird (etwa 1 Minute).
Ein grüner Haken heisst: Die neue Version ist online. Ein rotes Kreuz: Klick darauf und lies die Fehlermeldung.
Siehst du trotz grünem Haken noch die alte Version, hat der Browser sie zwischengespeichert (bis zu 10 Minuten):
mit `Ctrl+Shift+R` neu laden oder die Seite in einem privaten Fenster öffnen.

## Aufbau

| Datei | Inhalt |
|---|---|
| `spiel/main.py` | Startpunkt, Klasse `Spiel` mit der Spielschleife |
| `spiel/einstellungen.py` | Grösse, Tempo, Spielfeld, Tastenbelegung, Farben |
| `spiel/szenen.py` | Szenen: Menü, Spiel (die «Welt»), Ergebnis (Game Over / Sieg) |
| `spiel/figuren.py` | `Kaempfer` (Basisklasse mit Zustandsautomat und Physik) und `Spieler` |
| `spiel/gegner.py` | `Gegner` mit KI-Zustandsautomat und den vier Gegnertypen |
| `spiel/kampf.py` | `Box` (Quader für Treffer) und alle Angriffe als Daten (`Angriff`) |
| `spiel/posen.py` | Posen als Gelenkwinkel, Animation durch Mischen von Posen |
| `spiel/grafik.py` | zeichnet Figuren aus Formen (Skelett → Kapseln), Schatten, Text, Portraits |
| `spiel/skins.py` | Aussehen aller Figuren (Farben, Frisuren, Extras) |
| `spiel/level.py` | Hintergrund mit Parallax, Requisiten, Gegnerwellen |
| `spiel/objekte.py` | Kisten, Fässer, Laternen und Gegenstände zum Aufheben |
| `spiel/kamera.py` | scrollende Kamera, die beide Spieler im Bild hält |
| `spiel/hud.py` | Lebensbalken, Punkte, Combo-Zähler, Boss-Balken |
| `spiel/effekte.py` | Trefferfunken, Staub, Splitter, schwebender Text |
| `spiel/eingabe.py` | Tastatur und Gamepads (Zuordnung, Hot-Plug) → Aktionen («schlag», «tritt» …) |
| `spiel/ton.py` | Töne, die aus Sinus und Rauschen berechnet werden |
| `tutorial/` | Grundlagen-Tutorial der Vorlage (Spielschleife, Klassen, Vererbung) |
| `.github/workflows/online-stellen.yml` | baut das Spiel und stellt es online |

## Was im Code steckt

| Konzept | Wo | Worum es geht |
|---|---|---|
| 2.5D-Koordinaten | `einstellungen.py`, `Kamera.zu_bild` | x = links/rechts, y = Tiefe auf der Strasse, z = Höhe. Bildschirm: (x − Kamera, y − z) |
| Y-Sorting | `SpielSzene.zeichnen` | alles nach dem Fusspunkt `y` sortieren und von hinten nach vorne zeichnen |
| Hurtbox / Hitbox / Körperbox | `kampf.py`, `Kaempfer.hurtbox/hitbox/koerperbox` | drei getrennte Boxen: verwundbar, aktiver Angriff, Platz am Boden |
| Treffersystem | `SpielSzene.kampf`, `Kaempfer.nimm_treffer` | Hitbox ∩ Hurtbox → Schaden, Rückstoss, Trefferstarre oder Umwerfen |
| Angriffsphasen | `Angriff` (Anlauf, aktiv, Erholung) | nur in der aktiven Phase gibt es eine Hitbox |
| Combos | `Kaempfer._angriff`, `folge_schlag`/`folge_tritt` | nach einem Treffer darf man die Erholung mit dem Folgeangriff abbrechen |
| Eingabepuffer | `Spieler.taste`, `puffer` | ein zu früh gedrückter Knopf wird kurz gemerkt |
| Zustandsautomat (Körper) | `Kaempfer.update` → `_stehen`, `_fallen` … | eine Methode pro Zustand, Aufruf über den Namen |
| Zustandsautomat (KI) | `Gegner.ki_lauern`, `ki_verfolgen`, `ki_angreifen` … | Idle, Chase, Attack, Retreat, Hurt, Dead |
| Zielwahl und Angriffsplätze | `Gegner.waehle_ziel`, `SpielSzene.koordiniere_gegner` | Gegner verteilen sich auf beide Spieler, höchstens zwei schlagen gleichzeitig zu |
| Prozedurale Grafik | `grafik.zeichne_figur`, `posen.py` | Skelett aus Winkeln, Vorwärtskinematik, Interpolation zwischen Posen |
| Parallax | `Level.zeige_hintergrund` | die Skyline scrollt langsamer als die Strasse |
| Kamera | `Kamera.update` | folgt der Mitte der Spieler, nur vorwärts, bleibt bei Wellen stehen |
| Juice | `trefferstopp`, `wackeln`, `effekte.py` | Trefferstopp, Bildschirmwackeln, Funken: Treffer fühlen sich wuchtig an |
| Delta-Time | `dt` überall | Bewegung in Pixel **pro Sekunde**, damit das Spiel überall gleich schnell läuft |

## Regeln, damit es im Browser läuft

- Die Startdatei heisst `main.py`, und in der Spielschleife steht `await asyncio.sleep(0)`.
- Keine eigene `while`-Schleife, die auf etwas wartet. Warten geht über Zeitgeber in `aktualisieren`.
- Kein `input()` und kein `time.sleep()`: Beide halten das Spiel an.
- Töne nur als `.ogg`, nicht als `.wav` oder `.mp3`, Bilder als `.png`.
- Pfade relativ und mit `/`, zum Beispiel `"assets/stern.png"`.

## Ideen zum Ausbauen

- [ ] Ein neuer Gegnertyp: Eintrag in `GEGNER_TYPEN` (gegner.py) und ein Skin in `skins.py`
- [ ] Ein neuer Angriff: Eintrag in `ANGRIFFE` (kampf.py) und eine Pose in `ANGRIFFSPOSEN` (posen.py)
- [ ] Waffen zum Aufheben (Baseballschläger, Messer) als neue `Gegenstand`-Klasse
- [ ] Greifen und Werfen (wie in Double Dragon): neuer Zustand `_greifen`
- [ ] Ein zweites Level mit anderen Wellen (`WELLEN` und `REQUISITEN_PLAN` in level.py)
- [ ] Musik als `.ogg` in `spiel/assets/`
- [ ] Schwierigkeitsgrade: Tempo und Lebenspunkte der Gegner anpassen
- [ ] Touch-Steuerung fürs Handy

Zum Weiterlesen: [Game Programming Patterns](https://gameprogrammingpatterns.com/) von Robert Nystrom
(frei online, unter anderem zu Spielschleife, Zustand und Komponenten).
