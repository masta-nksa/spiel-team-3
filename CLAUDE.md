# Doppelfaust – Hinweise für Claude

2.5D-Beat-'em-up (Python, pygame-ce 2.5.8) für 1–2 Personen, läuft lokal und im Browser (pygbag, GitHub Pages).
**Lies zuerst `docs/PROJEKTSTAND.md`**: Dort stehen Stand, Architektur, getroffene Entscheidungen, offene Vorschläge
(Waffen Stufe 2/3, feinere Grafik, Kämpferwahl) und die nächsten Schritte.

## Arbeitsregeln der Person
- Sprache: Deutsch (Chat, Kommentare, Bezeichner, Commit-Nachrichten). Bezeichner im Code nicht ins Englische umbenennen.
- Fertige Features werden direkt in `main` gemergt (fast-forward), die Person testet online unter
  https://masta-nksa.github.io/spiel-team-3/. Keinen Pull Request erstellen, ausser sie verlangt es.
- Bei grösseren Features zuerst einen Vorschlag/ein Konzept als Liste vorlegen und auf Antworten warten, dann umsetzen.
- Keine Binärdateien, Screenshots, `spiel/build/` oder `__pycache__` committen (Screenshots nur ins Scratchpad).

## Prüfen vor dem Merge
- `python3 -m pyflakes spiel/*.py` ohne Meldung.
- Headless spielen: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`, Szenen per Skript aktualisieren, Bot-Läufe (1 und 2 Spieler,
  mehrere Zufallswerte) bis zum Levelende ohne Absturz oder Softlock.
- Browser-Build: `python -m pygbag --build spiel`, danach `spiel/build/` wieder löschen.
- Im Browser nur Bilder als `.png`, Töne als `.ogg`, keine blockierenden Schleifen (`await asyncio.sleep(0)` in der Spielschleife).
