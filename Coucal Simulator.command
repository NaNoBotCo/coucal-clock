#!/bin/bash
# Double-click this file in Finder to open the Coucal Clock simulator.
# It needs no network and touches nothing outside this folder.

cd "$(dirname "$0")" || exit 1

VENV_PY=".venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "The environment isn't set up yet."
  echo "Run this once in Terminal, from this folder:"
  echo
  echo "    make install"
  echo
  read -r -p "Press return to close."
  exit 1
fi

echo "Starting the Coucal Clock simulator…"
echo "(Close the clock window, or press Ctrl-C here, to stop.)"
echo

PYTHONPATH=src "$VENV_PY" -m coucal.sim --config config/unit-01.toml
status=$?

if [ $status -ne 0 ]; then
  echo
  echo "The simulator exited with an error (code $status). The message above says why."
  read -r -p "Press return to close."
fi
