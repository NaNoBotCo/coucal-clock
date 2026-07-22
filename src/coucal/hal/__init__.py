"""Hardware Abstraction Layer.

`interfaces.py` defines Protocols for every physical device. `real/` implements
them against the Raspberry Pi hardware; `sim/` implements them as desktop fakes.
`factory.build_hal(config)` returns the correct bundle based on ``COUCAL_HAL``.

Rule: no module outside `hal/real/` may import a hardware library.
"""
