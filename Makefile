
all: lint test

test:
	uv run pytest --cov=shardproxy --cov-report=term --cov-report=html

lint:
	uv run ruff check
	uv run mypy -p shardproxy
	uv run mypy tests/*.py

sdist:
	uv build

fmt:
	uv run isort -q src/**/*.py tests/*.py *.py
	uv run ruff check --fix
	uv run ruff format

run: lint
	uv run ./demo.py

dox:
	@mkdir -p tmp
	uv run sphinx-build -b html -d tmp/doctrees doc tmp/html

