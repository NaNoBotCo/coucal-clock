# Coucal Clock — build & dev tasks.
# The device itself needs none of this at runtime; these are developer conveniences.
# The one exception that MUST work from the repo alone on a fresh OS image: `offline-install`.

# Pick a Python >= 3.11 (the project uses tomllib and datetime.UTC). A bare
# `python3` can resolve to macOS's /usr/bin/python3 3.9, which cannot run this code,
# so search explicit versions first. Override with: make PY=/path/to/python3.12
PY ?= $(shell for p in python3.13 python3.12 python3.11 python3; do \
	  command -v $$p >/dev/null 2>&1 && \
	  $$p -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null && \
	  { command -v $$p; break; }; done)

VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTHON := $(VENV)/bin/python

.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-18s\033[0m %s\n", $$1, $$2}'

$(VENV):
	@test -n "$(PY)" || { echo "No Python >= 3.11 found. Install one (macOS: brew install python@3.13)"; exit 1; }
	@echo "Using $(PY)"
	$(PY) -m venv $(VENV)

.PHONY: install
install: $(VENV)  ## Set up the workstation environment (simulator + tests)
	$(PIP) install --quiet --upgrade pip
	$(PIP) install -r requirements-dev.txt
	@echo
	@echo "Ready. Launch the simulator with:  make sim"
	@echo "(or double-click 'Coucal Simulator.command' in Finder)"

.PHONY: offline-install
offline-install: $(VENV)  ## Posterity check: install using ONLY vendor/wheels (no network)
	$(PIP) install --no-index --find-links vendor/wheels -e ".[dev]"

.PHONY: vendor
vendor: $(VENV)  ## Populate vendor/wheels from the pinned deps (run once, online)
	$(PIP) download -d vendor/wheels -e ".[dev]"

.PHONY: sim
sim: $(VENV)  ## Launch the desktop simulator (Tk window + time-warp)
	PYTHONPATH=src $(PYTHON) -m coucal.sim --config config/unit-01.toml

.PHONY: frame
frame: $(VENV)  ## Render one face to out/frame.png without opening a window
	PYTHONPATH=src $(PYTHON) -m coucal.app --config config/unit-01.toml --out out/frame.png

.PHONY: test
test: $(VENV)  ## Run all tests
	$(PYTHON) -m pytest

.PHONY: golden
golden: $(VENV)  ## Run only golden tests (published-value validation)
	$(PYTHON) -m pytest -m golden

.PHONY: lint
lint: $(VENV)  ## Lint + format check
	$(VENV)/bin/ruff check src tests
	$(VENV)/bin/ruff format --check src tests

.PHONY: manual
manual: $(VENV)  ## Render MAINTENANCE.md to the bilingual PDF (Phase 6)
	@echo "Phase 6 — not yet implemented"

.PHONY: image
image:  ## Build the read-only Raspberry Pi OS image (Phase 5)
	@echo "Phase 5 — not yet implemented"

.PHONY: clean
clean:  ## Remove venv and caches
	rm -rf $(VENV) .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
