"""Simulator implementations of every HAL interface.

These fakes let the entire clock run on a desktop. The centrepiece is
``SimTimeline`` (see ``timeline.py``): a controllable virtual clock the simulator
GUI drives, so the almanac can be aged through years in minutes.
"""
