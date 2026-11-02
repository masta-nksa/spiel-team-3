# Doppelfaust – Projektstand und Übergabe

Stand: 2026-11-02. Dieses Dokument fasst zusammen, was gebaut ist, was entschieden wurde und was als Nächstes ansteht,
damit ein neuer Chat (oder ein Fork) ohne den alten Verlauf weiterarbeiten kann.

## 1. Was das Projekt ist
- Repo `masta-nksa/spiel-team-3`, Spiel «Doppelfaust» im Ordner `spiel/`. `main` = veröffentlichter Stand (GitHub Pages, Build
  bei jedem Push auf `main` über `.github/workflows/online-stellen.yml`, etwa 1 Minute).
- Alle Grafiken und Töne entstehen im Code (pygame.draw, berechnete Töne). Es gibt keine Bilddateien.
- Der Ordner `tutorial/` stammt aus der Vorlage und bleibt unverändert.
- Entwicklungsbranch der Sitzung: `claude/admiring-dirac-01n8ty` (war nach jedem Merge identisch mit `main`).

## 2. Was schon in `main` ist
1. **Grundspiel:** 2-Spieler-Koop an einer Tastatur, Kai (blau) und Ria (rot); getrennte HUDs; scrollende Kamera, die beide
   Spieler hält; 2.5D (x, Tiefe y, Höhe z) mit Y-Sorting; Hurtbox, Hitbox und Körperbox getrennt; Combos; Gegner-KI als
   Zustandsautomat; vier Gegnertypen (Schläger, Flitzer, Brocken, Boss Granit); Level mit Parallax (Altstadt, Industrie, Hafen),
   fünf Gegnerwellen; Pause, F1-Debugansicht, Game-Over- und Siegbildschirm.
2. **Controller (Commit 24cb870):** zwei Xbox-Controller, Controller 1 = 1P, Controller 2 = 2P, Tastatur läuft parallel.
3. **Waffen Stufe 1 (Commit 9be7e9b):** Greifen/Werfen, Baseballschläger, Kiste/Fass/Mülltonne werfen, Drops, HUD-Anzeige.

## 3. Steuerung
| | 1P | 2P | Xbox-Controller |
|---|---|---|---|
| Bewegen | WASD | Pfeiltasten | linker Stick / Steuerkreuz |
| Schlag | F | K, Ziffernblock 1 | X, LB |
| Tritt | G | L, Ziffernblock 2 | B |
| Sprung | Leertaste | O, Ziffernblock 0 | A |
| Spezial (Wirbeltritt) | F+G oder R | K+L oder I | Y |
| Greifen/Werfen | E | J, Ziffernblock-Punkt | RB |
| Pause | Esc | Esc | Start |
Menü: Enter/F/A/Start startet; 2P schaltet mit K (oder A/X/Y auf Controller 2) um; Esc = Pause, in der Pause Esc/B/Back zurück zum Menü.
Controller-Details: `eingabe.py` (Klasse `Pad`, nutzt SDLs Controller-Schnittstelle, Joystick-Nummern als Notlösung, Browser-Tabelle),
alle Belegungen in `einstellungen.py`. **Nur mit gefälschten Controllern getestet, nicht mit echter Hardware.**

## 4. Architektur (Dateien in `spiel/`)
| Datei | Inhalt |
|---|---|
| `main.py` | Startpunkt, Klasse `Spiel` (Schleife, Steuerungen, Ton, fertig gemaltes Level, Rekord, Debug-Schalter) |
| `einstellungen.py` | alle festen Werte: Grösse, Spielfeld, Kampf, Spieler, Waffen, Tasten, Controller, Farben |
| `szenen.py` | `MenueSzene`, `SpielSzene` (= die «Welt»: Kampfauflösung, Y-Sorting, Wellen, Drops), `ErgebnisSzene` |
| `figuren.py` | `Kaempfer` (Basis: Zustandsautomat per Methoden `_stehen`, `_angriff` …, Physik, Boxen) und `Spieler` |
| `gegner.py` | `Gegner` mit KI-Zuständen (lauern, verfolgen, angreifen, rückzug …), `GEGNER_TYPEN`, Umweg um Hindernisse |
| `kampf.py` | `Box` (Quader), `Angriff` (Anlauf/aktiv/Erholung, Schaden, Rückstoss …), `ANGRIFFE` |
| `posen.py` | Posen als Gelenkwinkel, Mischen/Interpolieren, `ANGRIFFSPOSEN` |
| `grafik.py` | `zeichne_figur` (Skelett → Kapseln), Schatten, Text, Portrait |
| `skins.py` | Aussehen: `p1` Kai, `p2` Ria, `schlaeger`, `flitzer`, `brocken`, `boss` |
| `level.py` | Hintergrund (Himmel, Skyline, Strasse), Requisitenplan, Wellen (`WELLEN`, `Wellensteuerung`) |
| `objekte.py` | Kiste, Fass, Mülltonne, Laterne, Gegenstände (Huhn, Apfel, Geld) |
| `waffen.py` | Waffen, Wurfobjekte, Geschosse, `Waffenverteiler` (Drop-Logik) |
| `kamera.py`, `hud.py`, `effekte.py`, `eingabe.py`, `ton.py` | wie benannt |
Koordinaten: Bildschirm = (x − Kamera.x, y − z). Fusspunkt y bestimmt Zeichenreihenfolge. Schwerkraft nur auf z.

## 5. Waffen Stufe 1 (gebaut)
- Schläger: 10 Treffer Haltbarkeit (pro Treffer, Fehlschläge kosten nichts), Schlag = 2er-Combo (12/18, zweiter wirft um),
  Spezial = Homerun (kostet 2 Haltbarkeit), Bruch mit «KAPUTT!». Geworfen: 14 Schaden, kostet 3 Haltbarkeit.
- Kiste 18 Schaden + 1,2 s Betäubung; Fass 24 + Umwerfen; Mülltonne 12 + 1,0 s. Tragen verlangsamt, kein Springen, bei jedem
  Treffer fallen lassen.
- Drops (Chancen): Schläger 10 %, Flitzer 12 %, Brocken 30 %, Boss 0 %, Kiste 22 %, Fass 12 %, Tonne 15 %. Bremsen: höchstens so viele
  Waffen am Boden wie Spieler, 12 s Mindestabstand, halbe Chance bei Waffe in der Hand, dreifache nach 90 s ohne Drop,
  erste zerschlagene Kiste enthält immer einen Schläger. Bodenzeit 12 s (blinkt zuletzt). Stirbt ein Spieler: Waffe fällt, blinkt, verschwindet (8 s).
- Gegner benutzen keine Waffen. Kein Friendly Fire.
- Bekannte Mängel: Fass wirft den Brocken um (statt nur zu betäuben); Tritt zeigt den Schläger in der Hand.
- Neue Waffe hinzufügen: Eintrag in `ARTEN` und `WAFFEN_POOL` (`waffen.py`) und Angriffe in `kampf.py`.

## 6. Entscheidungen der Person (gelten weiter)
- Waffen: Gegner nutzen sie «irgendwann später», nicht in Stufe 1; Abnutzung pro Treffer; Drops bleiben Zufall (kein Funkeln auf Kisten);
  Waffe eines gestorbenen Spielers fällt, blinkt und verschwindet.
- Fertig = direkt in `main` mergen, Person testet online.

## 7. Offen: Waffen Stufe 2 und 3 (Vorschlag liegt vor, noch nicht freigegeben)
- Stufe 2: **Wurfsterne** (7 Schaden, 5 Stück, Spezial Dreierfächer kostet 3), **Nunchakus** (6/6/9, 30 Treffer, schnell, Wirbel),
  **Messer** (8, 12 Treffer, auch werfbar 14), **Flasche** (Wurf 8 + Betäubung 0,9 s, 1 Treffer), Nahkampfwaffen werfen (1,2-facher Schaden).
- Stufe 3: **Stahlrohr** (14, langsam, grosse Reichweite, 8 Treffer), **Skateboard** (rutscht, trifft alle auf der Bahn, 3 Würfe),
  **Schlagring** (+4 Faustschaden, 25 s), Gegner mit Waffen (erst sichtbar bewaffnete Schläger, später Aufheben).
- Balance-Test-Idee: Bot-Läufe (200) messen Waffen pro Lauf (Ziel 3–5), Siegquote mit/ohne Waffen.

## 8. Offen: Feinere Grafik (Vorschläge liegen vor, Person hat noch nicht entschieden)
Referenz der Person: gemalter Comic-/Anime-Look («River City Reborn»-Charakterbogen: Alex, Maya, Bruno, Gegner Street Thug/Punk/Clubber/Knife Guy, Boss Viktor).
Ehrlich: Gemalte Sprites sind aus Code nicht erreichbar; mit Code etwa Stand der Mockups 1–3.
| Nr | Vorschlag | Optik | Aufwand | Browser |
|---|---|---|---|---|
| 1 | Prozedural viel feiner (Polygon-Glieder, Schattierung, Falten, Haarsträhnen, Supersampling) | 2/5 | mittel–gross | live zu langsam (≈2,7 ms/Figur) |
| 2 | Gebackene Frames aus Vorschlag 1 (Atlas, Pixel-Filter, Umriss), nur noch blitten | 2–3/5 | mittel | sehr gut |
| 3 | Pixel-Art im Code (72×84, Cut-out mit handgemalten Pixelköpfen, Paletten) | 3/5 | mittel–gross | sehr gut, Stilbruch zum glatten Hintergrund |
| 4 | Import externer PNG-Sprite-Sheets (Raster + JSON, Pivot am Fusspunkt, Anker für Waffen, Rückfall auf prozedural) | 4–5/5 | klein–mittel Code, gross Kunst (~70 Frames/Figur) | gut, Dateigrösse beachten |
Empfehlung des Agenten: 1+2 jetzt (feiner, aber vorberechnet) plus Format aus 4 einbauen; 3 nur bei Retro-Wunsch.
Für alle: Figuren müssten von ≈94 px auf 130–150 px wachsen (Welt-Faktor für Boxen, Tempo, Kamera).
Offene Fragen an die Person: (1) gemalter Look über externe PNGs oder Code-Look? (2) Figuren grösser? (3) ~70 Frames/Figur ok oder
Grafik unter ~2 MB? (4) Hintergrund mitziehen?
Hitboxen hängen nur an `ANGRIFFE` und `angriffs_phase()`, nicht an der Grafik; Waffen werden an der Hand gezeichnet (Anker nötig bei Sprites).

## 9. Offen: Kämpferwahl (Konzept liegt vor, Person hat noch nicht entschieden)
Wunsch: am Anfang aus **4 Kämpfern (2 Frauen, 2 Männer)** wählen, jede Figur nur von einem Spieler (first come, first serve), leicht
unterschiedliche Eigenschaften.
| | Kai (m) | Ria (w) | Bruno (m, neu) | Mika (w, neu) |
|---|---|---|---|---|
| Rolle | Allrounder | schnelle Kombo-Kämpferin | Schwergewicht | Technikerin (lange Tritte) |
| Look | blau, kurze dunkle Haare, Stirnband | rot, blonder Zopf | gelb-orange Lederjacke, graue Kurzhaare, `dicke` 1,22 | violett, weisse Stachelhaare, weisses Stirnband |
| HP | 100 | 100 | 108 | 98 |
| Tempo x/y | 175/115 | 193/126 | 150/100 | 170/118 |
| Sprungkraft | 620 | 660 | 580 | 640 |
| Gewicht (Rückstoss-Teiler) | 1,00 | 0,92 | 1,30 | 0,95 |
| Schadensfaktor | 1,00 | 0,97 | 1,08 | 0,97 |
| Angriffstempo | 1,00 | 1,12 | 0,90 | 1,00 |
| Reichweite | 1,00 | 1,00 | 0,95 | 1,15 |
| Spezial | Wirbel (10, 4 HP) | Sturmwirbel (8, 3 HP, schneller) | Stampfer (15, 7 HP, langsam) | Kranichstoss (12, 5 HP, nach vorn) |
| Combo | 3er-Kette | 4er-Kette (Schlag 3 → Hochtritt) | nur Schlagkette | weite Tritte |
Bot-Test (60 Läufe, Einzelspieler): Siegquote Kai 21,7 %, Ria 23,3 %, Bruno 28,3 %, Mika 11,7 % (Mika evtl. HP 100/Schaden 1,00 testen).
Regressionsziel: Bruno ≤ 35 %, Ria und Mika ≥ 10 %. Der Bot misst Tempo kaum.
- Wahlbildschirm zwischen Menü und Spiel: vier Karten (216×372, Portrait, Idle-Figur, sechs Wertebalken), Cursor pro Spieler mit Fähnchen
  «1P»/«2P», bestätigte Figur wird für den anderen abgedunkelt («BELEGT»), Cursor des anderen springt weiter, beide Cursor auf derselben
  Figur erlaubt, bei gleichzeitigem Bestätigen entscheidet die Ereignisreihenfolge, Zurück gibt die Figur frei, Start sobald alle bestätigt haben.
- Spielerring/«1P»/«2P»-Schild gehört zum Spieler, nicht zur Figur; Vorschlag: 1P Ring durchgezogen, 2P doppelt (Kai ≈ 1P-Ring, Ria ≈ 2P-Ring in der Farbe).
- Technik: neue Datei `kaempfer.py` (`KaempferDaten`, `KAEMPFER`, `angriffe_fuer` mit Faktoren statt Duplikaten), `Spieler.__init__` bekommt den
  Kämpfer, `Kaempfer.starte_angriff` liest `self.angriffe`, `Spiel.wahl = {1: "kai", 2: "ria"}`, neue `KaempferwahlSzene` (eigene Datei),
  `skins.py` nur um `bruno` und `mika` ergänzen (`p1`/`p2` nicht umbenennen). Pfeile ◄ ► fehlen in der pygame-Standardschrift.
- Stufen: MVP (4 Figuren, Werte, Wahl mit Sperre, 2P steigt später automatisch mit letzter/erster freier Figur ein); Stufe 2 (eigene Spezialangriffe,
  Zufallsfeld «?», Countdown, Wahl-Overlay beim späten Einstieg); Stufe 3 (eigene Posen, Rekord pro Figur …).
- Offene Fragen an die Person (mit Empfehlung): (1) Bruno/Mika so ok? ja. (2) Einstieg von 2P mitten im Spiel: automatisch (ja) oder Overlay? (3) Unterschiede klein lassen? ja.
  (4) Ringform 1P/2P unterscheiden? ja. (5) «?» und Countdown erst Stufe 2? ja.
- Empfohlene Reihenfolge: `kaempfer.py` + zwei Skins → ~25 Zeilen in `figuren.py` → Wahlszene → Anbindung Menü/SpielSzene → Balance-Test → README.

## 10. Nächste Schritte
1. Person beantwortet die Fragen aus 8 und 9 (und gibt Waffen Stufe 2 frei oder nicht), danach die gewünschte Variante umsetzen.
2. Echte Controller testen lassen; bei Abweichungen die Tabellen in `einstellungen.py` anpassen (Knopf-Nummern).
3. Kämpferwahl und Grafik berühren dieselben Dateien (`figuren.py`, `grafik.py`, `skins.py`, `szenen.py`): nacheinander umsetzen, nicht parallel.

## 11. Arbeitsweise und Testen
- Headless-Bots: Szene mit `SpielSzene(spiel, zwei_spieler)` erzeugen, `Steuerung.richtung` überschreiben, `spieler.taste(aktion)` aufrufen,
  `aktualisieren(1/60)`/`zeichnen` in der Schleife; ein Lauf dauert ≈1,5 s Rechenzeit für ≈200 s Spielzeit. Mit mehreren Zufallswerten und
  1/2 Spielern bis zum Levelende prüfen (Softlocks fielen früher bei Hindernissen zwischen Spielern und Gegnern auf, jetzt `Gegner.umweg`).
- Browser-Test: pygbag-Build lokal servern (`python -m http.server`) und mit dem vorinstallierten Chromium (Playwright, `executablePath`
  `/opt/pw-browsers/chromium-*/chrome-linux/chrome`) öffnen; der Proxy der Umgebung verlangt, HTTPS-Ressourcen über `--proxy-server=https=…`
  zu leiten, localhost direkt.
- Screenshots der Mockups lagen im Scratchpad der Sitzung (nicht im Repo, gehen verloren); die Entscheidungsgrundlage steht oben.
