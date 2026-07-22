# systemd units (Phase 5)

The device runs each service under systemd on a read-only root. Units are finalized in
Phase 5 alongside the OS image; this file records the intended shape so the seam is
visible now.

| Unit | Service | Notes |
|------|---------|-------|
| `coucal-timebase.service` | `timebase` | GPS>RTC>NTP arbitration; disciplines DS3231. Starts first. |
| `coucal-compositor.service` | `compositor` | Renders faces; owns the e-ink refresh budget. |
| `coucal-voice.service` | `voice` | Dawn/dusk coucal + automaton; honors silence windows. |
| `coucal-steward.service` | `steward` | Power budget, load-shedding, watchdog feed, brownout shutdown. Uses `WatchdogSec=`. |
| `coucal-installer.service` | `installer` | One-shot, run by hand at install (GPS capture, heading, abbot config). |

Design intent: `steward` is the supervisor; a daily scheduled reboot runs at an
astronomically dead hour; `Type=notify` + `WatchdogSec=` give systemd its own liveness
layer on top of the BCM hardware watchdog.
