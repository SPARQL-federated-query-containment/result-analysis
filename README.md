# result-analysis

Analysis of BFC and SPECS, two SPARQL query-containment checking engines,
compared on a shared benchmark of query pairs. Marimo notebooks turn the raw
results into tables and figures, exportable for a paper.

Deployed at https://sparql-federated-query-containment.github.io/result-analysis/.

## Notebooks

- `notebook/overview.py` — tables and figures over all suites, with
  significance tests and a comparison against LargeRDFBench.
- `notebook/by_operator.py` — correctness, execution time and speedup per
  operator, over all suites.
- `notebook/pair_comparison.py` — per-pair violin plots, speedup table and
  significance test for a chosen benchmark suite.

## Running it

```
make notebook   # edit the notebooks locally, with autoreload
make test       # run the unit tests
make lint       # ruff + mypy
make artifacts  # export each notebook's tables and figures to artifacts/
make export     # build the static site into dist/
```

`lib/` holds the shared loading and statistics code the notebooks import.

## Data

- `results/*.json` — BFC and SPECS's own results, one file per suite. See the
  `benchmark` and `benchmark-runner` projects for how they were produced.
- `results/largerdfbench/` — external reference data, used only by
  `overview.py`'s LargeRDFBench comparison. See its own
  `results/largerdfbench/README.md` for provenance and license.
