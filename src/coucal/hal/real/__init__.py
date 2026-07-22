"""Raspberry Pi hardware implementations of the HAL interfaces.

Deliberately stubbed until Phase 5 — all Phase 0–4 development happens on the
simulator. Each stub names the exact part it will drive so a future maintainer
knows what to wire. This is the ONLY package permitted to import hardware
libraries (RPi.GPIO, smbus2, spidev, the IT8951 driver, etc.).

Target hardware:
  time/pos   : u-blox NEO-M8N GPS (UART) + DS3231 RTC (I2C)
  display    : Waveshare 10.3" e-ink, IT8951 controller (SPI)
  power      : INA219 (I2C) telemetry; Witty Pi 4 power controller (I2C + GPIO)
  audio      : MAX98357A I2S DAC -> case-bonded exciter transducer
  automaton  : one servo/stepper channel (GPIO/PWM)
  button     : one debounced brass button (GPIO)
  watchdog   : BCM hardware watchdog (/dev/watchdog)
"""
