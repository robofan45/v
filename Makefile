.PHONY: install run test clean

VENV    := .venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
APP     := $(VENV)/bin/resumeflow

# ── Install ──────────────────────────────────────────────────
install: $(VENV)/bin/activate
	@echo "✓ ResumeFlow installed. Run with:  make run"

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -e ".[dev]" --quiet
	@touch $(VENV)/bin/activate

# ── Run ──────────────────────────────────────────────────────
run: install
	$(APP)

# ── Test ─────────────────────────────────────────────────────
test: install
	QT_QPA_PLATFORM=offscreen $(PY) -m pytest -v

# ── Clean ────────────────────────────────────────────────────
clean:
	rm -rf $(VENV) build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."
