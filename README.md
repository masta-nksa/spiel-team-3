# Spielvorlage: pygame-ce im Browser

Ein kleines, fertiges Spiel («Sternenfänger») als Startpunkt für dein eigenes Spiel.
Du programmierst in Python mit [pygame-ce](https://pyga.me/). Bei jedem Push baut GitHub das Spiel
mit [pygbag](https://github.com/pygame-web/pygbag) für den Browser und stellt es online.

Dein Spiel läuft danach unter `https://masta-nksa.github.io/<name-des-repos>/`, auch auf dem Handy.

## Lokal starten

Einmalig im Terminal von VS Code:

```bash
python -m pip install -r requirements.txt
```

Die Vorlage braucht **pygame-ce**, nicht das alte **pygame**. Beide lädt man mit `import pygame`, sie vertragen sich aber nicht
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

Commit, dann Push. Unter **Actions** siehst du, wie das Spiel gebaut wird (etwa 1 Minute).
Ein grüner Haken heisst: Die neue Version ist online. Ein rotes Kreuz: Klick darauf und lies die Fehlermeldung.

## Aufbau

| Datei | Inhalt |
|---|---|
| `spiel/main.py` | Startpunkt, Klasse `Spiel` mit der Spielschleife |
| `spiel/szenen.py` | Szenen: Menü, Spiel, Game Over |
| `spiel/figuren.py` | Spieler und fallende Objekte (Stern, Stein) |
| `spiel/einstellungen.py` | Grösse, Tempo, Farben |
| `spiel/assets/` | deine Bilder und Töne |
| `.github/workflows/online-stellen.yml` | baut das Spiel und stellt es online |

## Was im Code steckt

| Konzept | Wo | Worum es geht |
|---|---|---|
| Spielschleife | `Spiel.laufen` | Jedes Bild: Eingaben lesen → aktualisieren → zeichnen |
| Delta-Time | `dt` in `laufen` und `update` | Bewegung in Pixel **pro Sekunde**, damit das Spiel überall gleich schnell läuft |
| Zustandsautomat | `Szene`, `wechsle_zu` | Genau eine Szene ist aktiv und entscheidet, wann sie wechselt |
| Klassen | `Spieler`, `Stern`, `Stein` | Jede Figur kennt ihre Daten (Position, Bild) und ihr Verhalten |
| Vererbung | `FallendesObjekt` | Stern und Stein erben das Fallen, legen aber ihr Aussehen selbst fest |
| Polymorphie | `beim_fangen` | Die Szene ruft bei jedem Objekt dieselbe Methode auf, jedes reagiert anders |
| Sprites und Gruppen | `pygame.sprite.Group` | Viele Objekte gemeinsam bewegen, zeichnen und auf Kollision prüfen |
| Zeitgeber | `bis_zum_naechsten`, `wartezeit` | Zeit in Sekunden mit `dt` herunterzählen |

## Regeln, damit es im Browser läuft

- Die Startdatei heisst `main.py`, und in der Spielschleife steht `await asyncio.sleep(0)`.
- Keine eigene `while`-Schleife, die auf etwas wartet. Warten geht über Zeitgeber in `aktualisieren`.
- Kein `input()` und kein `time.sleep()`: Beide halten das Spiel an.
- Töne nur als `.ogg`, nicht als `.wav` oder `.mp3`, Bilder als `.png`.
- Pfade relativ und mit `/`, zum Beispiel `"assets/stern.png"`.

## Ideen zum Ausbauen

- [ ] Eine neue Art fallendes Objekt (zum Beispiel ein Herz, das ein Leben schenkt)
- [ ] Drei Leben statt sofort Game Over
- [ ] Eine Pause-Szene mit der Taste P
- [ ] Eigene Bilder statt Formen (`pygame.image.load`)
- [ ] Töne beim Fangen
- [ ] «Juice»: Der Bildschirm wackelt kurz bei einem Stein, Funken beim Stern (Partikel)
- [ ] Dann: dein eigenes Spiel. Die Szenen und die Spielschleife kannst du behalten.

Zum Weiterlesen: [Game Programming Patterns](https://gameprogrammingpatterns.com/) von Robert Nystrom
(frei online, unter anderem zu Spielschleife, Zustand und Komponenten).
