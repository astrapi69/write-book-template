# ===== Makefile =====
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Versions / Config
PY ?= python3
MDL_CLI_VER ?= 0.39.0
CODESPELL_IGNORE ?= .codespellignore

# Helper for markdownlint
define _run_markdownlint_fix
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) --fix "**/*.md"; \
	else \
		echo "markdownlint: npx not found – please install npm (e.g. 'sudo apt install npm')" >&2; \
		exit 1; \
	fi
endef

.PHONY: help setup install update hooks fix format fix-all lint typecheck precommit test test-fast export clean clean-venv

# --- General ---

help: ## Show available commands
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' Makefile | sed 's/:.*##/: /' | sort

# --- Setup / Installation ---

setup: ## Install Poetry, pre-commit and all dev dependencies
	@pipx install poetry || true
	@pipx install pre-commit || true
	@poetry config virtualenvs.in-project true
	@poetry install --with dev
	@poetry run pre-commit install

install: ## Install dependencies (including dev)
	@poetry install --with dev

update: ## Update dependencies (including dev)
	@poetry update --with dev

hooks: ## Install or update pre-commit hooks
	@poetry run pre-commit install

# --- Auto-fixes / Formatting ---

fix: ## Quick fix with Ruff and Black
	@poetry run ruff check . --fix --unsafe-fixes
	@poetry run black .

format: ## Format code using Black only
	@poetry run black .

fix-all: ## Run all auto-fixes (Ruff, Black, Codespell, Markdownlint)
	@poetry run ruff check . --fix --unsafe-fixes
	@poetry run black .
	@if [ -f "$(CODESPELL_IGNORE)" ]; then \
		poetry run codespell --ignore-words=$(CODESPELL_IGNORE) --write-changes; \
	else \
		poetry run codespell --write-changes; \
	fi
	@$(call _run_markdownlint_fix)

# --- Linting / Type checking ---

lint: ## Run all linters (Ruff, Black check, Codespell, Markdownlint)
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
		echo "markdownlint: npx not found – please install npm" >&2; \
	fi

typecheck: ## Run MyPy type checks via pre-commit (ensures stub consistency)
	@poetry run pre-commit run mypy --all-files

precommit: ## Run all pre-commit hooks
	@poetry run pre-commit run -a

# --- Tests ---

test: ## Run Pytest with coverage
	@poetry run pytest -q --maxfail=1 --disable-warnings --cov=./ --cov-report=xml

test-fast: ## Run quick tests without coverage
	@poetry run pytest -q --maxfail=1 --disable-warnings

# --- Book / Export ---

export: ## Build all export formats (PDF, EPUB, DOCX)
	@poetry run full-export --format pdf,epub,docx

# --- Cleanup ---

clean: ## Remove cache and build artifacts
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} + || true
	@rm -rf .mypy_cache .ruff_cache .coverage dist build coverage.xml || true

clean-venv: ## Remove Poetry virtualenv (recreate via `make setup`)
	@poetry env remove --all || true
