# ===== Makefile =====
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Tool configuration
PY ?= python3
POETRY ?= poetry
MDL_CLI_VER ?= 0.39.0
CODESPELL_IGNORE ?= .codespellignore

# Helper for markdownlint autofix
define _run_markdownlint_fix
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) --fix "**/*.md"; \
	else \
		echo "markdownlint: npx not found – please install npm (e.g. 'sudo apt install npm')" >&2; \
		exit 1; \
	fi
endef

.PHONY: help setup install update hooks fix format fix-all lint typecheck precommit \
        test test-fast \
        export export-all export-all-nc \
        ebook paperback hardcover \
        pdf docx markdown html \
        comic-html comic-pdf \
        clean clean-venv

# ----------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------

help: ## Show all available make targets
	@echo "Available targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort \
	  | awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------
# Environment Setup
# ----------------------------------------------------------------------

setup: ## Install Poetry, dev dependencies and pre-commit hooks
	@$(PY) -m pip install --user pipx || true
	@pipx install pre-commit || true
	@$(POETRY) install
	@$(POETRY) run pre-commit install

install: ## Install project dependencies
	@$(POETRY) install

update: ## Update dependencies
	@$(POETRY) update

hooks: ## Install or refresh pre-commit hooks
	@$(POETRY) run pre-commit install

# ----------------------------------------------------------------------
# Code Quality: Fix / Format / Lint
# ----------------------------------------------------------------------

fix: ## Run quick autofixes (Ruff + Black)
	@$(POETRY) run ruff check . --fix --unsafe-fixes
	@$(POETRY) run black .

format: ## Format all Python files using Black
	@$(POETRY) run black .

fix-all: ## Run all autofix tools (Ruff, Black, Codespell, Markdownlint)
	@$(POETRY) run ruff check . --fix --unsafe-fixes
	@$(POETRY) run black .
	@$(POETRY) run codespell --ignore-words=$(CODESPELL_IGNORE) --write-changes || \
		$(POETRY) run codespell --write-changes
	@$(call _run_markdownlint_fix)

lint: ## Run all linters (Ruff, Black check, Codespell, Markdownlint)
	@$(POETRY) run ruff check .
	@$(POETRY) run black --check .
	@$(POETRY) run codespell --ignore-words=$(CODESPELL_IGNORE) || \
		$(POETRY) run codespell
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) "**/*.md"; \
	else \
		echo "markdownlint: npx not found – please install npm" >&2; \
	fi

typecheck: ## Run MyPy type checks using pre-commit
	@$(POETRY) run pre-commit run mypy --all-files

precommit: ## Run all pre-commit hooks
	@$(POETRY) run pre-commit run -a

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

test: ## Run pytest with coverage
	@$(POETRY) run pytest -q --maxfail=1 --disable-warnings --cov=./ --cov-report=xml

test-fast: ## Run pytest without coverage (faster)
	@$(POETRY) run pytest -q --maxfail=1 --disable-warnings

# ----------------------------------------------------------------------
# Book Export Commands (backwards-compatible)
# ----------------------------------------------------------------------

# Legacy target "export" remains and now uses the new all-formats-with-cover shortcut
export: ## Export all formats WITH default cover
	@$(POETRY) run export-all-with-cover $(ARGS)

export-all: ## Export all formats WITH default cover (alias)
	@$(POETRY) run export-all-with-cover $(ARGS)

export-all-nc: ## Export all formats WITHOUT cover
	@$(POETRY) run export-all $(ARGS)

# Frequently used export flows
ebook: ## Export E-Book (EPUB, NOT EPUB2)
	@$(POETRY) run export-epub $(ARGS)

paperback: ## Export print version (paperback)
	@$(POETRY) run export-print-version-paperback $(ARGS)

hardcover: ## Export print version (hardcover)
	@$(POETRY) run export-print-version-hardcover $(ARGS)

# Single-format convenience targets
pdf: ## Export PDF
	@$(POETRY) run export-pdf $(ARGS)

docx: ## Export DOCX
	@$(POETRY) run export-docx $(ARGS)

markdown: ## Export Markdown
	@$(POETRY) run export-markdown $(ARGS)

html: ## Export HTML
	@$(POETRY) run export-html $(ARGS)

# Comic exports
comic-html: ## Export comic as HTML
	@$(POETRY) run export-comic-html $(ARGS)

comic-pdf: ## Export comic as PDF
	@$(POETRY) run export-comic-pdf $(ARGS)

# ----------------------------------------------------------------------
# Cleanup
# ----------------------------------------------------------------------

clean: ## Remove cache and build artifacts
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} + || true
	@rm -rf .mypy_cache .ruff_cache .coverage dist build coverage.xml || true

clean-venv: ## Remove Poetry virtualenv
	@$(POETRY) env remove --all || true

# ----------------------------------------------------------------------
# Project Initialization
# ----------------------------------------------------------------------

.PHONY: init-bp init-project

init-bp: ## Initialize a new book project using the template
	@$(POETRY) run init-bp $(ARGS)

# Backwards-compatible and short alias
init-project: init-bp ## Alias: initialize a new project
