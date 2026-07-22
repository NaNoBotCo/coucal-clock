"""Coucal Clock — a ceremonial multi-tradition e-ink almanac clock.

The package is layered so the whole system runs on a desktop with no hardware:

    almanac / faces   pure functions of (civil_time, position, config)
    services          timebase, compositor, voice, steward, installer
    hal               interfaces.py (Protocols) + real/ (Pi) + sim/ (fakes)

Nothing above `hal` imports a hardware library.
"""

__version__ = "0.0.0"
