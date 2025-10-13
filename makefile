# ===== Makefile =====
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Versions / Settings
PY ?= python3
MDL_CLI_VER ?= 0.39.0
CODESPELL_IGNORE ?= .codespellignore

# ---- Helpers ----
define _run_markdownlint_fix
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) --fix "**/*.md"; \
	else \
		echo "markdownlint: npx nicht gefunden – bitte 'npm install -g npm' o.ä. installieren" >&2; \
		exit 1; \
	fi
endef

# ---- PHONY ----
.PHONY: help setup install update hooks fix format fix-all lint typecheck precommit test test-fast export clean clean-venv

help: ## Zeigt Kommandos
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' Makefile | sed 's/:.*##/: /' | sort

# --- Setup / Install ---
setup: ## Poetry & Hooks installieren + Projekt-Env aufsetzen
	@pipx install poetry || true
	@pipx install pre-commit || true
	@poetry config virtualenvs.in-project true
	@poetry install --with dev
	@poetry run pre-commit install

install: ## Dependencies installieren (mit dev)
	@poetry install --with dev

update: ## Dependencies updaten (mit dev)
	@poetry update --with dev

hooks: ## pre-commit Hooks (re)installieren
	@poetry run pre-commit install

# --- Code-Fixes / Format ---
fix: ## Schnelle Auto-Fixes (ruff+black)
	@poetry run ruff check . --fix --unsafe-fixes
	@poetry run black .

format: ## Nur Formatierung (black)
	@poetry run black .

fix-all: ## Alles automatisch fixen: ruff, black, codespell (write), markdownlint (fix)
	@poetry run ruff check . --fix --unsafe-fixes
	@poetry run black .
	@if [ -f "$(CODESPELL_IGNORE)" ]; then \
		poetry run codespell --ignore-words=$(CODESPELL_IGNORE) --write-changes; \
	else \
		poetry run codespell --write-changes; \
	fi
	@$(call _run_markdownlint_fix)

# --- Lint / Typing ---
lint: ## Lint-Checks (ruff/black check, codespell, markdownlint)
	@poetry run ruff check .
	@poetry run black --check .
	@if [ -f "$(CODESPELL_IGNORE)" ]; then \
		poetry run codespell --ignore-words=$(CODESPELL_IGNORE); \
	else \
		poetry run codespell; \
	fi
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) "**/*.md"; \
	else \
		echo "markdownlint: npx nicht gefunden – bitte 'npm install -g npm' o.ä. installieren" >&2; \
	fi

typecheck: ## Type-Check via pre-commit (nutzt Hook-Environment + Stubs)
	@poetry run pre-commit run mypy --all-files

precommit: ## Alle pre-commit Hooks ausführen
	@poetry run pre-commit run -a

# --- Tests ---
test: ## Pytests + Coverage XML
	@poetry run pytest -q --maxfail=1 --disable-warnings --cov=./ --cov-report=xml

test-fast: ## Schnelltests ohne Coverage
	@poetry run pytest -q --maxfail=1 --disable-warnings

# --- Projekt-spezifisch ---
export: ## Exportiert alle Formate (pdf, epub, docx)
	@poetry run full-export --format pdf,epub,docx

# --- Cleanup ---
clean: ## Aufräumen von Cache/Build-Artefakten
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} + || true
	@rm -rf .mypy_cache .ruff_cache .coverage dist build coverage.xml || true

clean-venv: ## Poetry-Umgebung entfernen (Neuaufsetzen via `make setup`)
	@poetry env remove --all || true
