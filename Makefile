VERSION = $(shell uv version --short)
RXVERSION = $(shell echo $(VERSION) | sed 's/\./[.]/g')
TAG = v$(VERSION)
NEWS = NEWS.rst

all: lint test

test:
	uv run pytest --cov=shardproxy --cov-report=term --cov-report=html:tmp/htmlcov

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

clean:
	rm -rf src/*/__pycache__ tests/__pycache__
	rm -rf tmp/htmlcov .coverage tmp/doctrees tmp/html

xclean: clean
	rm -rf .mypy_cache .pytest_cache .ruff_cache .venv

checkver:
	@echo "Checking version"
	@grep -Eq '^\w+ v$(RXVERSION)\b' $(NEWS) \
	|| { echo "Version '$(VERSION)' not in $(NEWS)"; exit 1; }
	@echo "Checking git repo"
	@git diff --stat --exit-code || { echo "ERROR: Unclean repo"; exit 1; }

release: checkver
	git tag $(TAG)
	git push github $(TAG):$(TAG)

unrelease:
	git push github :$(TAG)
	git tag -d $(TAG)

shownote:
	@awk -v VER="v$(VERSION)" -f etc/note.awk $(NEWS) \
	| pandoc -f rst -t gfm --wrap=none

%.txt: %.in
	uv pip compile -q --generate-hashes -o $@ $<

uvlock: etc/requirements.uv.txt

