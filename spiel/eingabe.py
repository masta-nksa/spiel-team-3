"""Eingabe: übersetzt Tasten und Gamepad-Knöpfe in Spielaktionen.

Jeder Spieler hat ein eigenes Steuerung-Objekt. Die Figuren fragen nie direkt
"ist die Taste F gedrückt?", sondern nur "will mein Spieler nach links?" oder
"hat er Schlag gedrückt?". So kann man die Belegung ändern, ohne die Figur anzufassen.
"""
import pygame

import einstellungen as e

TOTZONE = 0.4  # Stick-Ausschläge darunter zählen nicht (alte Sticks zittern)


class Steuerung:
    def __init__(self, nummer, tasten):
        self.nummer = nummer
        self.tasten = tasten
        self.gamepad = None  # pygame.joystick.Joystick oder None

    def _gedrueckt(self, gedrueckt, aktion):
        return any(gedrueckt[taste] for taste in self.tasten[aktion])

    def richtung(self):
        """Gibt (dx, dy) mit Werten -1, 0 oder 1 zurück."""
        gedrueckt = pygame.key.get_pressed()
        dx = self._gedrueckt(gedrueckt, "rechts") - self._gedrueckt(gedrueckt, "links")
        dy = self._gedrueckt(gedrueckt, "runter") - self._gedrueckt(gedrueckt, "hoch")

        if self.gamepad is not None:
            try:
                ax, ay = self.gamepad.get_axis(0), self.gamepad.get_axis(1)
                if abs(ax) > TOTZONE:
                    dx = 1 if ax > 0 else -1
                if abs(ay) > TOTZONE:
                    dy = 1 if ay > 0 else -1
                if self.gamepad.get_numhats() > 0:
                    hx, hy = self.gamepad.get_hat(0)
                    dx = hx or dx
                    dy = -hy or dy
            except pygame.error:
                self.gamepad = None
        return dx, dy

    def aktion(self, ereignis):
        """Welche Aktion löst dieses Ereignis aus? "schlag", "tritt", "sprung", "spezial" oder None."""
        if ereignis.type == pygame.KEYDOWN:
            for name in ("schlag", "tritt", "sprung", "spezial"):
                if ereignis.key in self.tasten[name]:
                    return name
        elif ereignis.type == pygame.JOYBUTTONDOWN and self.gamepad is not None:
            if ereignis.instance_id == self.gamepad.get_instance_id():
                return e.GAMEPAD_KNOEPFE.get(ereignis.button)
        return None

    def tastenname(self, aktion):
        return pygame.key.name(self.tasten[aktion][0]).upper()


def gamepad_ereignis(steuerungen, ereignis):
    """Ein neu eingestecktes Gamepad bekommt der erste Spieler, der noch keines hat."""
    if ereignis.type == pygame.JOYDEVICEADDED:
        pad = pygame.joystick.Joystick(ereignis.device_index)
        for steuerung in steuerungen:
            if steuerung.gamepad is None:
                steuerung.gamepad = pad
                break
    elif ereignis.type == pygame.JOYDEVICEREMOVED:
        for steuerung in steuerungen:
            if steuerung.gamepad is not None and steuerung.gamepad.get_instance_id() == ereignis.instance_id:
                steuerung.gamepad = None
