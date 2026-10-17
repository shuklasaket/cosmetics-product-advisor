.PHONY: setup run check lock lint format typecheck test docs exports check-exports

UV ?= uv

setup:
	$(UV) sync --locked

run:
	$(UV) run --frozen streamlit run app.py

check: lock lint typecheck test docs check-exports

lock:
	$(UV) lock --check --offline

lint:
	$(UV) run --frozen ruff format --check .
	$(UV) run --frozen ruff check .

format:
	$(UV) run --frozen ruff format .
	$(UV) run --frozen ruff check --fix .

typecheck:
	$(UV) run --frozen mypy

test:
	$(UV) run --frozen pytest

docs:
	$(UV) run --frozen python -m scripts.check_docs

exports:
	$(UV) export --quiet --frozen --no-header --no-dev --no-emit-project --output-file requirements.txt
	$(UV) export --quiet --frozen --no-header --no-emit-project --output-file requirements-dev.txt

check-exports:
	$(UV) run --frozen python -m scripts.check_exports
