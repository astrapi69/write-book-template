# ===== Makefile =====
.DEFAULT_GOAL := help
SHELL := /bin/bash

# Tool configuration
POETRY ?= poetry
MDL_CLI_VER ?= 0.39.0
CODESPELL_IGNORE ?= .codespellignore
MANUSCRIPT ?= manuscript

# Helper for markdownlint autofix
define _run_markdownlint_fix
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) --fix "**/*.md"; \
	else \
		echo "markdownlint: npx not found - please install npm (e.g. 'sudo apt install npm')" >&2; \
		exit 1; \
	fi
endef

# ----------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------

.PHONY: help

help: ## Show all available make targets
	@echo "Available targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | sort \
	  | awk 'BEGIN {FS=":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------
# Environment Setup
# ----------------------------------------------------------------------

.PHONY: setup lock-install install update

setup: lock-install ## Install dependencies and initialize project
	@$(POETRY) run init-bp $(ARGS)

lock-install: ## Lock and install project dependencies
	@$(POETRY) lock
	@$(POETRY) install

install: ## Install project dependencies
	@$(POETRY) install

update: ## Update dependencies (including manuscripta)
	@$(POETRY) update

# ----------------------------------------------------------------------
# Project Initialization
# ----------------------------------------------------------------------

.PHONY: init-bp init-project

init-bp: lock-install ## Initialize a new book project using the template
	@$(POETRY) run init-bp $(ARGS)

init-project: init-bp ## Alias: initialize a new project

# ----------------------------------------------------------------------
# Book Export
# ----------------------------------------------------------------------

.PHONY: export export-all export-all-nc \
        ebook ebook-copy paperback paperback-copy hardcover hardcover-copy \
        pdf docx markdown html \
        comic-html comic-pdf audiobook

export: ## Export all formats WITH default cover
	@$(POETRY) run export-all-with-cover $(ARGS)

export-all: ## Export all formats WITH default cover (alias)
	@$(POETRY) run export-all-with-cover $(ARGS)

export-all-nc: ## Export all formats WITHOUT cover
	@$(POETRY) run export-all $(ARGS)

# Frequently used export flows
ebook: ## Export E-Book (EPUB)
	@$(POETRY) run export-epub-safe $(ARGS)

ebook-copy: ## Export E-Book and copy EPUB to ~/Downloads (or EPUB_DEST)
	@$(POETRY) run export-epub-safe --copy-epub-to $(or $(EPUB_DEST),~/Downloads) $(ARGS)

paperback: ## Export print version (paperback)
	@$(POETRY) run export-print-version-paperback-safe $(ARGS)

paperback-copy: ## Export paperback and copy EPUB to ~/Downloads (or EPUB_DEST)
	@$(POETRY) run export-print-version-paperback-safe --copy-epub-to $(or $(EPUB_DEST),~/Downloads) $(ARGS)

hardcover: ## Export print version (hardcover)
	@$(POETRY) run export-print-version-hardcover-safe $(ARGS)

hardcover-copy: ## Export hardcover and copy EPUB to ~/Downloads (or EPUB_DEST)
	@$(POETRY) run export-print-version-hardcover-safe --copy-epub-to $(or $(EPUB_DEST),~/Downloads) $(ARGS)

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

# Audiobook
audiobook: ## Generate audiobook from manuscript
	@$(POETRY) run manuscripta-audiobook $(ARGS)

# ----------------------------------------------------------------------
# Translation
# ----------------------------------------------------------------------

.PHONY: translate-de-en translate-en-de translate-en-es translate-de-es

translate-de-en: ## Translate manuscript German -> English (DeepL)
	@$(POETRY) run translate-de-en $(ARGS)

translate-en-de: ## Translate manuscript English -> German (DeepL)
	@$(POETRY) run translate-en-de $(ARGS)

translate-en-es: ## Translate manuscript English -> Spanish (DeepL)
	@$(POETRY) run translate-en-es $(ARGS)

translate-de-es: ## Translate manuscript German -> Spanish (DeepL)
	@$(POETRY) run translate-de-es $(ARGS)

# ----------------------------------------------------------------------
# Manuscript Tools (provided by manuscript-tools)
# ----------------------------------------------------------------------

.PHONY: ms-check ms-check-strict ms-sanitize ms-sanitize-dry \
        ms-quotes ms-quotes-dry ms-format ms-format-dry \
        ms-metrics ms-validate ms-validate-fix

ms-check: ## Manuscript: core style checks
	@$(POETRY) run ms-check $(MANUSCRIPT)

ms-check-strict: ## Manuscript: all checks (filler, passive, sentence length)
	@$(POETRY) run ms-check $(MANUSCRIPT) --strict

ms-sanitize: ## Manuscript: sanitize with backup
	@$(POETRY) run ms-sanitize $(MANUSCRIPT) --backup

ms-sanitize-dry: ## Manuscript: preview sanitization
	@$(POETRY) run ms-sanitize $(MANUSCRIPT) --dry-run

ms-quotes: ## Manuscript: fix German quotation marks
	@$(POETRY) run ms-quotes $(MANUSCRIPT)

ms-quotes-dry: ## Manuscript: preview quotation mark fixes
	@$(POETRY) run ms-quotes $(MANUSCRIPT) --dry-run

ms-format: ## Manuscript: fix broken bold/italic formatting
	@$(POETRY) run ms-format $(MANUSCRIPT)

ms-format-dry: ## Manuscript: preview formatting fixes
	@$(POETRY) run ms-format $(MANUSCRIPT) --dry-run

ms-metrics: ## Manuscript: word counts and readability
	@$(POETRY) run ms-metrics $(MANUSCRIPT)

ms-validate: ## Manuscript: full pipeline (sanitize + check + readability)
	@$(POETRY) run ms-validate $(MANUSCRIPT)

ms-validate-fix: ## Manuscript: full pipeline with auto-fix
	@$(POETRY) run ms-validate $(MANUSCRIPT) --fix

# ----------------------------------------------------------------------
# Markdown Quality
# ----------------------------------------------------------------------

.PHONY: mdlint mdlint-fix codespell codespell-fix

mdlint: ## Run markdownlint on all Markdown files
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) "**/*.md"; \
	else \
		echo "markdownlint: npx not found - please install npm" >&2; \
	fi

mdlint-fix: ## Run markdownlint with auto-fix
	@$(call _run_markdownlint_fix)

codespell: ## Run codespell on manuscript
	@$(POETRY) run codespell $(MANUSCRIPT) --ignore-words=$(CODESPELL_IGNORE)

codespell-fix: ## Run codespell with auto-fix
	@$(POETRY) run codespell $(MANUSCRIPT) --ignore-words=$(CODESPELL_IGNORE) --write-changes

# ----------------------------------------------------------------------
# Project Releases
# ----------------------------------------------------------------------

.PHONY: tag-message

tag-message: ## Interactive: Generate tag message file and (optionally) create tag
	@$(POETRY) run make-tag-message

# ----------------------------------------------------------------------
# Cleanup
# ----------------------------------------------------------------------

.PHONY: clean clean-venv clean-git-cache

clean: ## Remove output and cache artifacts
	@rm -rf output output_backup export.log || true
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} + || true
	@rm -rf .mypy_cache .ruff_cache .coverage coverage.xml || true

clean-venv: ## Remove Poetry virtualenv
	@$(POETRY) env remove --all || true

clean-git-cache: ## Remove the git cache
	@$(POETRY) run clean-git-cache $(ARGS)

# ----------------------------------------------------------------------
# Quality & Hooks
# ----------------------------------------------------------------------

.PHONY: hooks fix lint precommit

hooks: ## Install or refresh pre-commit hooks
	@$(POETRY) run pre-commit install

fix: ## Run all auto-fixes (markdownlint + codespell)
	@$(call _run_markdownlint_fix)
	@$(POETRY) run codespell $(MANUSCRIPT) --ignore-words=$(CODESPELL_IGNORE) --write-changes || true

lint: ## Run all linters (markdownlint + codespell)
	@if command -v npx >/dev/null 2>&1; then \
		npx --yes markdownlint-cli@$(MDL_CLI_VER) "**/*.md"; \
	else \
		echo "markdownlint: npx not found - please install npm" >&2; \
	fi
	@$(POETRY) run codespell $(MANUSCRIPT) --ignore-words=$(CODESPELL_IGNORE)

precommit: ## Run all pre-commit hooks
	@$(POETRY) run pre-commit run -a
