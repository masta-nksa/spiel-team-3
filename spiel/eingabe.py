"""Eingabe: übersetzt Tasten und Gamepad-Knöpfe in Spielaktionen.

Jeder Spieler hat ein eigenes Steuerung-Objekt. Die Figuren fragen nie direkt
"ist die Taste F gedrückt?", sondern nur "will mein Spieler nach links?" oder
"hat er Schlag gedrückt?". So kann man die Belegung ändern, ohne die Figur anzufassen.

Gamepads: Der zuerst gefundene Controller gehört Spieler 1, der zweite Spieler 2.
Massgeblich ist die Instanz-ID des Geräts (nicht der device_index, der sich beim An-/Abstecken verschiebt).
Alle Zugriffe auf Geräte sind abgesichert: ein Bluetooth-Abbruch oder der Browser darf nie abstürzen.
"""
import math
import sys

import pygame

import einstellungen as e

# Fehler, die beim Zugriff auf ein (weggeworfenes oder nicht vorhandenes) Gerät auftreten können
GERAETEFEHLER = (pygame.error, AttributeError, TypeError, ValueError, NotImplementedError, OSError)


def _controller_modul():
    """SDLs Controller-Schnittstelle (feste Knopfnamen). Gibt None zurück, wo es sie nicht gibt (z. B. Browser)."""
    try:
        from pygame._sdl2 import controller
        if not controller.get_init():
            controller.init()
        return controller
    except (ImportError, *GERAETEFEHLER):
        return None


class Pad:
    """Ein angeschlossener Controller, egal ob über die Controller- oder die Joystick-Schnittstelle.

    joy  = pygame-Joystick (liefert Instanz-ID und Name)
    ctrl = pygame-Controller oder None. Mit Controller sind die Knöpfe immer gleich benannt (A, B, X, Y ...),
           ohne Controller (Notlösung) gelten die rohen Joystick-Nummern aus einstellungen.py.
    """

    def __init__(self, joy, ctrl=None):
        self.joy = joy
        self.ctrl = ctrl
        self.instance_id = joy.get_instance_id()
        try:
            self.name = joy.get_name()
        except GERAETEFEHLER:
            self.name = "Controller"
        browser = sys.platform == "emscripten"
        self._tabelle = e.JOY_KNOEPFE_BROWSER if browser else e.JOY_KNOEPFE
        self._kreuz_knoepfe = browser
        self._stick_an = False  # Stick ausserhalb der Totzone (für das Zittern-Verhindern)
        self._dx = self._dy = 0

    def knopf(self, ereignis):
        """Name des gedrückten Knopfes ("a", "b", "x", "y", "lb", "rb", "back", "start") oder None."""
        if ereignis.type == pygame.CONTROLLERBUTTONDOWN and self.ctrl is not None:
            tabelle = e.CONTROLLER_KNOEPFE
        elif ereignis.type == pygame.JOYBUTTONDOWN and self.ctrl is None:
            tabelle = self._tabelle
        else:
            return None  # sonst käme jeder Druck doppelt an: einmal als Controller-, einmal als Joystick-Ereignis
        if getattr(ereignis, "instance_id", None) != self.instance_id:
            return None
        return tabelle.get(ereignis.button)

    def _stick(self):
        if self.ctrl is not None:
            # Controller-Achsen liefern -32768 bis 32767
            return (self.ctrl.get_axis(pygame.CONTROLLER_AXIS_LEFTX) / 32768,
                    self.ctrl.get_axis(pygame.CONTROLLER_AXIS_LEFTY) / 32768)
        return self.joy.get_axis(0), self.joy.get_axis(1)

    def _kreuz(self):
        """Steuerkreuz als (dx, dy), y positiv = nach unten."""
        if self.ctrl is not None:
            def knopf(k):
                return int(bool(self.ctrl.get_button(k)))
            return (knopf(pygame.CONTROLLER_BUTTON_DPAD_RIGHT) - knopf(pygame.CONTROLLER_BUTTON_DPAD_LEFT),
                    knopf(pygame.CONTROLLER_BUTTON_DPAD_DOWN) - knopf(pygame.CONTROLLER_BUTTON_DPAD_UP))
        if self.joy.get_numhats() > 0:
            hx, hy = self.joy.get_hat(0)
            return hx, -hy
        if self._kreuz_knoepfe:
            def knopf(name):
                return int(bool(self.joy.get_button(e.JOY_KREUZ_BROWSER[name])))
            return knopf("rechts") - knopf("links"), knopf("runter") - knopf("hoch")
        return 0, 0

    def _achse(self, wert, alt):
        """-1, 0 oder 1. Wer schon in einer Richtung ist, braucht weniger Ausschlag, um dort zu bleiben."""
        schwelle = e.STICK_ACHSE_AUS if alt * wert > 0 else e.STICK_ACHSE_EIN
        if abs(wert) > schwelle:
            return 1 if wert > 0 else -1
        return 0

    def richtung(self):
        """(dx, dy) mit -1, 0, 1. Stick mit Totzone und Hysterese, Diagonalen, Steuerkreuz hat Vorrang."""
        ax, ay = self._stick()
        laenge = math.hypot(ax, ay)
        if laenge >= (e.STICK_AUS if self._stick_an else e.STICK_EIN):
            self._stick_an = True
            self._dx = self._achse(ax / laenge, self._dx)
            self._dy = self._achse(ay / laenge, self._dy)
        else:
            self._stick_an = False
            self._dx = self._dy = 0
        kx, ky = self._kreuz()
        return kx or self._dx, ky or self._dy

    def rumble(self, staerke):
        """Kurzes Rütteln, staerke = (tief, hoch, Millisekunden). Nicht jedes Gerät kann das, dann passiert nichts."""
        try:
            quelle = self.ctrl if self.ctrl is not None else self.joy
            quelle.rumble(staerke[0], staerke[1], staerke[2])
        except GERAETEFEHLER:
            pass


class Steuerung:
    def __init__(self, nummer, tasten):
        self.nummer = nummer
        self.tasten = tasten
        self.gamepad = None  # Pad oder None

    def _gedrueckt(self, gedrueckt, aktion):
        return any(gedrueckt[taste] for taste in self.tasten[aktion])

    def richtung(self):
        """Gibt (dx, dy) mit Werten -1, 0 oder 1 zurück."""
        gedrueckt = pygame.key.get_pressed()
        dx = self._gedrueckt(gedrueckt, "rechts") - self._gedrueckt(gedrueckt, "links")
        dy = self._gedrueckt(gedrueckt, "runter") - self._gedrueckt(gedrueckt, "hoch")

        if self.gamepad is not None:
            try:
                px, py = self.gamepad.richtung()
                dx, dy = px or dx, py or dy
            except GERAETEFEHLER:
                self.gamepad = None  # Gerät ist weg; ein späteres Gamepad-Ereignis vergibt den Platz neu
        return dx, dy

    def knopf(self, ereignis):
        """Knopfname ("a", "start" ...), wenn das Ereignis vom Gamepad dieses Spielers kommt, sonst None."""
        if self.gamepad is None:
            return None
        return self.gamepad.knopf(ereignis)

    def aktion(self, ereignis):
        """Welche Aktion löst dieses Ereignis aus? "schlag", "tritt", "sprung", "spezial" oder None."""
        if ereignis.type == pygame.KEYDOWN:
            for name in ("schlag", "tritt", "sprung", "spezial"):
                if ereignis.key in self.tasten[name]:
                    return name
        else:
            return e.GAMEPAD_AKTIONEN.get(self.knopf(ereignis))
        return None

    def tastenname(self, aktion):
        """Beschriftung für Hinweise: der Gamepad-Knopf, wenn ein Controller verbunden ist, sonst die Taste."""
        if self.gamepad is not None:
            return e.GAMEPAD_HINWEIS[aktion]
        return pygame.key.name(self.tasten[aktion][0]).upper()

    def rumble(self, staerke):
        if self.gamepad is not None:
            self.gamepad.rumble(staerke)


def gamepads_suchen(steuerungen):
    """Verteilt angeschlossene Controller auf freie Plätze: der erste gefundene an Spieler 1, der zweite an Spieler 2.

    Wird beim Start und nach jedem An-/Abstecken aufgerufen. Bekannte Geräte (gleiche Instanz-ID) werden
    nicht doppelt vergeben, und sind alle Plätze belegt, wird gar nichts geöffnet.
    """
    if all(s.gamepad is not None for s in steuerungen):
        return
    try:
        anzahl = pygame.joystick.get_count()
    except GERAETEFEHLER:
        return  # Joystick-Teil nicht verfügbar
    for index in range(anzahl):
        frei = next((s for s in steuerungen if s.gamepad is None), None)
        if frei is None:
            return
        try:
            pad = _pad_oeffnen(index)
        except GERAETEFEHLER:
            continue
        if any(s.gamepad is not None and s.gamepad.instance_id == pad.instance_id for s in steuerungen):
            continue
        frei.gamepad = pad


def _pad_oeffnen(index):
    ctrl = joy = None
    modul = _controller_modul()
    if modul is not None:
        try:
            if modul.is_controller(index):
                ctrl = modul.Controller(index)
                joy = ctrl.as_joystick()
        except GERAETEFEHLER:
            ctrl = joy = None
    if joy is None:
        joy = pygame.joystick.Joystick(index)
    return Pad(joy, ctrl)


def gamepad_ereignis(steuerungen, ereignis):
    """Controller wurde an- oder abgesteckt. Gibt die Nummer des Spielers zurück, der sein Gamepad verloren hat (sonst None)."""
    if ereignis.type == pygame.JOYDEVICEADDED:
        gamepads_suchen(steuerungen)
        return None
    verloren = None
    if ereignis.type == pygame.JOYDEVICEREMOVED:
        for steuerung in steuerungen:
            if steuerung.gamepad is not None and steuerung.gamepad.instance_id == ereignis.instance_id:
                steuerung.gamepad = None
                verloren = steuerung.nummer
        gamepads_suchen(steuerungen)  # ein überzähliger Controller rückt auf den freien Platz nach
    return verloren
