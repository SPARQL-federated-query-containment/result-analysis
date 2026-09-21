.PHONY: notebook lint export serve-export

notebook:
	mkdir -p notebook
	uv run marimo edit ./notebook

lint:
	uv run ruff check .
	uv run mypy .

# Static WebAssembly build for GitHub Pages.
NOTEBOOKS := $(filter-out notebook/__init__.py,$(wildcard notebook/*.py))

export:
	rm -rf dist
	mkdir -p dist
	cp site/index.html dist/
	for nb in $(NOTEBOOKS); do \
		name=$$(basename $$nb .py); \
		uv run marimo export html-wasm $$nb -o dist/$$name --mode run; \
		mkdir -p dist/$$name/public; \
		cp -r results dist/$$name/public/; \
		(cd dist/$$name/public && find results -type f -name '*.json' | sort > manifest.txt); \
	done

# WebAssembly builds must be served over localhost.
serve-export: export
	cd dist && python3 -m http.server 8080
