.PHONY: notebook lint artifacts export serve-export clean

RESULTS   := $(wildcard results/*.json)
TEMPLATES := $(wildcard templates/*.tex)
LIB       := $(wildcard lib/*.py)
NOTEBOOKS := $(filter-out notebook/__init__.py,$(wildcard notebook/*.py))

notebook:
	uv run marimo edit --watch ./notebook

lint:
	uv run ruff check .
	uv run mypy .

artifacts: artifacts/.stamp

artifacts/.stamp: notebook/overview.py $(LIB) $(RESULTS) $(TEMPLATES)
	uv run python -m notebook.overview
	touch $@

# Static WebAssembly build for GitHub Pages: one folder per notebook plus a landing page.
# Each notebook fetches results/ and templates/ from <site>/public/ at startup, so they
# are copied there with a manifest (a static host has no directory listing).
export: dist/.stamp

dist/.stamp: site/index.html $(NOTEBOOKS) $(LIB) $(RESULTS) $(TEMPLATES)
	rm -rf dist
	mkdir -p dist
	cp site/index.html dist/
	for nb in $(NOTEBOOKS); do \
		name=$$(basename $$nb .py); \
		uv run marimo export html-wasm $$nb -o dist/$$name --mode run; \
		mkdir -p dist/$$name/public; \
		cp -r results templates dist/$$name/public/; \
		(cd dist/$$name/public && find results templates -type f \( -name '*.json' -o -name '*.tex' \) | sort > manifest.txt); \
	done
	touch $@

# WebAssembly builds must be served over localhost
serve-export: export
	cd dist && python3 -m http.server 8080

clean:
	rm -rf artifacts dist
