.DEFAULT_GOAL := help

help: ## Zeigt Kommandos
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sed 's/:.*##/: /' | sort

setup: ## Poetry & Hooks
	@pipx install poetry || true
	@pipx install pre-commit || true
	@poetry install --with dev
	@pre-commit install

fix: ## Auto-Fixes
	@poetry run ruff check . --fix
	@poetry run black .

lint: ## Checks
	@poetry run ruff check .
	@poetry run black --check .
	@poetry run mypy src || true

test: ## Pytests + Coverage
	@poetry run pytest -q --maxfail=1 --disable-warnings --cov=./ --cov-report=term-missing

export: ## Baut alle Formate
	@full-export --format pdf,epub,docx || poetry run full-export --format pdf,epub,docx
