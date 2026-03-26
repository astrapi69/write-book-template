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
# Chapter Creation
# ----------------------------------------------------------------------

.PHONY: create-chapters create-next-chapter cc cnc

create-chapters: ## Create multiple new chapter files
	@$(POETRY) run create-chapters $(ARGS)

create-next-chapter: ## Create the next chapter file
	@$(POETRY) run create-chapters --total 1

cc: create-chapters ## Alias: create-chapters

cnc: create-next-chapter ## Alias: create-next-chapter

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
	@$(POETRY) run export-epub $(ARGS)

ebook-copy: ## Export E-Book and copy EPUB to ~/Downloads (or EPUB_DEST)
	@$(POETRY) run export-epub-safe --copy-epub-to $(or $(EPUB_DEST),~/Downloads) $(ARGS)

paperback: ## Export print version (paperback)
	@$(POETRY) run export-print-version-paperback $(ARGS)

paperback-copy: ## Export paperback and copy EPUB to ~/Downloads (or EPUB_DEST)
	@$(POETRY) run export-print-version-paperback-safe --copy-epub-to $(or $(EPUB_DEST),~/Downloads) $(ARGS)

hardcover: ## Export print version (hardcover)
	@$(POETRY) run export-print-version-hardcover $(ARGS)

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
# Safe/Draft Exports (skip image processing)
# ----------------------------------------------------------------------

.PHONY: ebook-safe pdf-safe docx-safe markdown-safe html-safe \
        paperback-safe hardcover-safe

ebook-safe: ## Quick draft EPUB (skip image steps)
	@$(POETRY) run export-epub-safe $(ARGS)

pdf-safe: ## Quick draft PDF (skip image steps)
	@$(POETRY) run export-pdf-safe $(ARGS)

docx-safe: ## Quick draft DOCX (skip image steps)
	@$(POETRY) run export-docx-safe $(ARGS)

markdown-safe: ## Quick draft Markdown (skip image steps)
	@$(POETRY) run export-markdown-safe $(ARGS)

html-safe: ## Quick draft HTML (skip image steps)
	@$(POETRY) run export-html-safe $(ARGS)

paperback-safe: ## Quick draft paperback (skip image steps)
	@$(POETRY) run export-pvps $(ARGS)

hardcover-safe: ## Quick draft hardcover (skip image steps)
	@$(POETRY) run export-pvhs $(ARGS)

# ----------------------------------------------------------------------
# Translation (DeepL)
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
# Translation (LMStudio - local)
# ----------------------------------------------------------------------

.PHONY: translate-lms translate-lms-en-de translate-lms-de-en \
        translate-lms-en-es translate-lms-en-fr

translate-lms: ## Translate manuscript via LMStudio
	@$(POETRY) run translate-book-lmstudio $(ARGS)

translate-lms-en-de: ## Translate English -> German (LMStudio)
	@$(POETRY) run translate-book-en-de

translate-lms-de-en: ## Translate German -> English (LMStudio)
	@$(POETRY) run translate-book-de-en

translate-lms-en-es: ## Translate English -> Spanish (LMStudio)
	@$(POETRY) run translate-book-en-es

translate-lms-en-fr: ## Translate English -> French (LMStudio)
	@$(POETRY) run translate-book-en-fr

# ----------------------------------------------------------------------
# Markdown Cleanup (manuscripta tools)
# ----------------------------------------------------------------------

.PHONY: fix-quotes fix-quotes-dry unbold-headers replace-emojis fix-bullets

fix-quotes: ## Fix German quotation marks in manuscript
	@$(POETRY) run fix-german-quotes $(ARGS)

fix-quotes-dry: ## Preview German quotation mark fixes
	@$(POETRY) run fix-german-quotes --dry-run $(ARGS)

unbold-headers: ## Remove bold markers from Markdown headers
	@$(POETRY) run unbold-md-headers $(ARGS)

replace-emojis: ## Replace emojis with text equivalents
	@$(POETRY) run replace-emojis $(ARGS)

fix-bullets: ## Fix broken Markdown bullet points
	@$(POETRY) run replace-md-bullet-points $(ARGS)

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
# Markdown Quality (individual tools)
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
# Quality & Hooks (combined)
# ----------------------------------------------------------------------

.PHONY: hooks fix lint precommit

hooks: ## Install or refresh pre-commit hooks
	@$(POETRY) run pre-commit install

fix: mdlint-fix codespell-fix ## Run all auto-fixes (markdownlint + codespell)

lint: mdlint codespell ## Run all linters (markdownlint + codespell)

precommit: ## Run all pre-commit hooks
	@$(POETRY) run pre-commit run -a
