.PHONY: notebook lint test artifacts artifacts-overview artifacts-by_operator export serve-export clean

RESULTS   := $(wildcard results/*.json)
TEMPLATES := $(wildcard templates/*.tex)
LIB       := $(wildcard lib/*.py)
NOTEBOOKS := $(filter-out notebook/__init__.py,$(wildcard notebook/*.py))

notebook:
	uv run marimo edit --watch ./notebook

lint:
	uv run ruff check .
	uv run mypy .

test:
	uv run pytest tests/

artifacts: artifacts-overview artifacts-by_operator

artifacts-overview: artifacts/overview/.stamp

artifacts/overview/.stamp: Makefile notebook/overview.py $(LIB) $(RESULTS) $(TEMPLATES)
	uv run python -m notebook.overview
	touch $@

artifacts-by_operator: artifacts/by_operator/.stamp

artifacts/by_operator/.stamp: Makefile notebook/by_operator.py $(LIB) $(RESULTS) $(TEMPLATES)
	uv run python -m notebook.by_operator
	touch $@

# overview and by_operator are static HTML, pair_comparison is WebAssembly (its controls need Python)
export: dist/.stamp

dist/.stamp: Makefile site/index.html $(NOTEBOOKS) $(LIB) $(RESULTS) $(TEMPLATES)
	rm -rf dist
	mkdir -p dist/overview dist/by_operator
	cp site/index.html dist/
	STATIC_EXPORT=1 uv run marimo export html notebook/overview.py -o dist/overview/index.html --no-include-code
	STATIC_EXPORT=1 uv run marimo export html notebook/by_operator.py -o dist/by_operator/index.html --no-include-code
	uv run marimo export html-wasm notebook/pair_comparison.py -o dist/pair_comparison --mode run
	mkdir -p dist/pair_comparison/public
	cp -r results templates dist/pair_comparison/public/
	cd dist/pair_comparison/public && find results templates -type f \( -name '*.json' -o -name '*.tex' \) | sort > manifest.txt
	touch $@

# WebAssembly builds must be served over localhost
serve-export: export
	cd dist && python3 -m http.server 8080

clean:
	rm -rf artifacts dist
