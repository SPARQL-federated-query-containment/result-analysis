# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "pandas",
#     "pydantic",
#     "returns",
#     "scipy",
# ]
# ///

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from matplotlib.figure import Figure
    from matplotlib.patches import Patch
    from returns.unsafe import unsafe_perform_io

    return Figure, Patch, mo, np, pd, unsafe_perform_io


@app.cell
def _():
    from lib.datasets import REGULAR_SUITES, SCALE_SUITES
    from lib.stats import (
        correct_times_by_operator,
        operator_table,
        outcomes_by_operator,
        pooled,
    )
    from lib.types import EngineName, Outcome

    return (
        EngineName,
        Outcome,
        REGULAR_SUITES,
        SCALE_SUITES,
        correct_times_by_operator,
        operator_table,
        outcomes_by_operator,
        pooled,
    )


@app.cell
def _(REGULAR_SUITES, SCALE_SUITES, pooled, unsafe_perform_io):
    all_bfc, all_specs = unsafe_perform_io(pooled(REGULAR_SUITES + SCALE_SUITES).unwrap())
    return all_bfc, all_specs


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # By operator: BFC vs SPECS
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Table
    """)
    return


@app.cell
def _(all_bfc, all_specs, mo, operator_table, pd):
    from math import log2 as _log2

    operator_frame = operator_table(all_bfc, all_specs)
    _BLUE, _ORANGE, _GREY = "42, 120, 214", "235, 104, 52", "128, 128, 128"
    _SPEEDUP = "Average speedup of BFC over SPECS"

    def _ms(value):
        return "-" if pd.isna(value) else f"{value:.0f}"

    def _speedup(value):
        return "-" if pd.isna(value) else f"{value:.1f}"

    def _style_cell(row_id, column, value):
        if pd.isna(operator_frame[_SPEEDUP].iloc[int(row_id)]):
            return {"backgroundColor": f"rgba({_GREY}, 0.15)", "color": "gray"}
        if column == _SPEEDUP:
            _strength = min(abs(_log2(value)) / 4, 1)
            _rgb = _BLUE if value > 1 else _ORANGE
            return {"backgroundColor": f"rgba({_rgb}, {0.15 + 0.55 * _strength:.2f})"}
        return {}

    _gradient = (
        '<span style="display:inline-block;vertical-align:middle;font-size:0.85em">'
        '<span style="display:block;width:16em;height:0.9em;border-radius:2px;'
        f"background:linear-gradient(to right, rgba({_ORANGE}, 0.70), rgba({_ORANGE}, 0.15) 50%, "
        f'rgba({_BLUE}, 0.15) 50%, rgba({_BLUE}, 0.70))"></span>'
        '<span style="display:flex;justify-content:space-between;width:16em">'
        "<span>SPECS 16x+ faster</span><span>equal</span><span>BFC 16x+ faster</span></span></span>"
    )
    _grey_swatch = (
        '<span style="display:inline-block;width:0.9em;height:0.9em;border-radius:2px;'
        f'background:rgba({_GREY}, 0.6);margin:0 0.3em 0 1.2em;vertical-align:-0.1em"></span>'
        "no speedup: no pair both engines answered correctly"
    )

    mo.vstack(
        [
            mo.md(f"### All suites pooled, N = {len(all_bfc)} pairs"),
            mo.md(
                "Speedup of BFC over SPECS = SPECS time / BFC time. "
                "Above 1: BFC faster. Below 1: SPECS faster."
            ),
            mo.md(_gradient + _grey_swatch),
            mo.ui.table(
                operator_frame,
                format_mapping={
                    "BFC median (ms)": _ms,
                    "SPECS median (ms)": _ms,
                    _SPEEDUP: _speedup,
                },
                selection=None,
                show_download=False,
                page_size=15,
                style_cell=_style_cell,
            ),
        ]
    )
    return (operator_frame,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Plot functions
    """)
    return


@app.cell
def _(EngineName, Outcome):
    COLORS = {EngineName.BFC: "#2a78d6", EngineName.SPECS: "#eb6834"}
    OUTCOME_COLORS = {
        Outcome.CORRECT: "#2ea043",
        Outcome.INCORRECT: "#da3633",
        Outcome.ERROR: "#7a1f1f",
        Outcome.UNKNOWN: "#eda100",
        Outcome.TIMEOUT: "#8c8c8c",
        Outcome.OUT_OF_MEMORY: "#7b5fbf",
    }

    def draw_violins(ax, engine, samples, positions):
        drawn = [(p, s) for p, s in zip(positions, samples) if len(s) > 0]
        if not drawn:
            return
        where, data = zip(*drawn)
        parts = ax.violinplot(
            list(data), positions=list(where), widths=0.35, showmedians=True, showextrema=False
        )
        for body in parts["bodies"]:
            body.set_facecolor(COLORS[engine])
            body.set_edgecolor(COLORS[engine])
            body.set_alpha(0.7)
        parts["cmedians"].set_color(COLORS[engine])

    def tidy(ax):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_axisbelow(True)
        ax.grid(True, alpha=0.3)

    return COLORS, OUTCOME_COLORS, draw_violins, tidy


@app.cell
def _(
    EngineName,
    Figure,
    OUTCOME_COLORS,
    Patch,
    np,
    outcomes_by_operator,
    tidy,
):
    def outcomes_figure(bfc, specs):
        """Per operator, a stacked bar of how BFC's pairs ended (upper) and SPECS's (lower)."""
        counts = {
            EngineName.BFC: outcomes_by_operator(bfc),
            EngineName.SPECS: outcomes_by_operator(specs),
        }
        operators = list(counts[EngineName.BFC].index)
        fig = Figure(figsize=(8, 9), layout="constrained")
        ax = fig.subplots()
        for engine, offset in ((EngineName.BFC, 0), (EngineName.SPECS, 1)):
            left = np.zeros(len(operators))
            for outcome in counts[engine].columns:
                widths = counts[engine][outcome].to_numpy()
                ax.barh(
                    [3 * i + offset for i in range(len(operators))],
                    widths,
                    left=left,
                    height=0.9,
                    color=OUTCOME_COLORS[outcome],
                )
                left += widths
        ax.set_yticks([3 * i + 0.5 for i in range(len(operators))], labels=[o.label for o in operators])
        ax.invert_yaxis()
        ax.set_xlabel("pairs")
        ax.legend(
            handles=[Patch(color=color, label=outcome.value) for outcome, color in OUTCOME_COLORS.items()],
            loc="upper right",
            frameon=False,
        )
        tidy(ax)
        return fig

    return (outcomes_figure,)


@app.cell
def _(
    COLORS,
    EngineName,
    Figure,
    Patch,
    correct_times_by_operator,
    draw_violins,
    tidy,
):
    def time_figure(bfc, specs):
        """Per operator, violins of the timings of each engine's correct pairs."""
        timings = {
            EngineName.BFC: correct_times_by_operator(bfc),
            EngineName.SPECS: correct_times_by_operator(specs),
        }
        operators = list(timings[EngineName.BFC])
        fig = Figure(figsize=(10, 5.5), layout="constrained")
        ax = fig.subplots()
        for engine, offset in ((EngineName.BFC, -0.2), (EngineName.SPECS, 0.2)):
            draw_violins(
                ax,
                engine,
                [timings[engine][operator] for operator in operators],
                [i + offset for i in range(len(operators))],
            )
        ax.set_xticks(range(len(operators)), labels=[o.label for o in operators], rotation=45, ha="right")
        ax.set_yscale("log")
        ax.set_ylabel("Execution time (ms)")
        ax.legend(
            handles=[Patch(color=COLORS[e], label=e.value.upper()) for e in (EngineName.BFC, EngineName.SPECS)],
            loc="upper right",
            frameon=False,
        )
        tidy(ax)
        return fig

    return (time_figure,)


@app.cell
def _(COLORS, EngineName, Figure, Patch, tidy):
    def speedup_figure(table):
        """Per operator where both engines have a correct pair, the average speedup of BFC over SPECS."""
        rows = table.dropna(subset=["Average speedup of BFC over SPECS"])
        speedups = rows["Average speedup of BFC over SPECS"].to_numpy()
        fig = Figure(figsize=(8, 5), layout="constrained")
        ax = fig.subplots()
        ax.barh(
            range(len(rows)),
            speedups - 1,
            left=1,
            color=[COLORS[EngineName.BFC] if s > 1 else COLORS[EngineName.SPECS] for s in speedups],
        )
        ax.axvline(1, color="black", linewidth=1)
        ax.set_xscale("log")
        ax.set_xticks([1, 2, 4, 8, 16])
        ax.xaxis.set_major_formatter("{x:g}")
        ax.minorticks_off()
        ax.set_yticks(range(len(rows)), labels=list(rows["Operator"]))
        ax.invert_yaxis()
        ax.set_xlabel("Average speedup of BFC over SPECS")
        ax.legend(
            handles=[
                Patch(color=COLORS[EngineName.BFC], label="BFC faster"),
                Patch(color=COLORS[EngineName.SPECS], label="SPECS faster"),
            ],
            loc="lower right",
            frameon=False,
        )
        tidy(ax)
        return fig

    return (speedup_figure,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Figures
    """)
    return


@app.cell
def _(all_bfc, all_specs, mo, outcomes_figure):
    fig_outcomes = outcomes_figure(all_bfc, all_specs)
    mo.vstack(
        [
            mo.md("### How the pairs of each operator ended, BFC (upper bar) and SPECS (lower bar), all suites"),
            fig_outcomes,
        ]
    )
    return


@app.cell
def _(all_bfc, all_specs, mo, time_figure):
    fig_time = time_figure(all_bfc, all_specs)
    mo.vstack(
        [
            mo.md("### Execution time of BFC and SPECS per operator, all suites"),
            fig_time,
        ]
    )
    return


@app.cell
def _(mo, operator_frame, speedup_figure):
    fig_speedup = speedup_figure(operator_frame)
    mo.vstack(
        [
            mo.md("### Average speedup of BFC over SPECS per operator, all suites"),
            fig_speedup,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Export artifacts
    """)
    return


@app.cell
def _(pd):
    from string import Template as _Template

    class _LatexTemplate(_Template):
        # "@" so that LaTeX's "$" and "%" stay untouched in the template file.
        delimiter = "@"

    def _cell(value, digits, missing="--"):
        return missing if pd.isna(value) else f"{value:.{digits}f}"

    def latex_rows(table):
        lines = []
        for (
            operator, pairs, bfc_ok, specs_ok, bfc_ms, specs_ms, speedup,
        ) in table.itertuples(index=False):
            cells = [
                operator, str(pairs), str(bfc_ok), str(specs_ok),
                _cell(bfc_ms, 0), _cell(specs_ms, 0),
                _cell(speedup, 1),
            ]
            lines.append("    " + " & ".join(cells) + r" \\")
        return "\n".join(lines)

    def render_table(table, n_pairs):
        """Fill templates/table_operator.tex, which holds the caption, label and layout."""
        from pathlib import Path

        template = _LatexTemplate(Path("templates/table_operator.tex").read_text())
        return template.substitute(rows=latex_rows(table), n=n_pairs)

    def markdown_table(table, n_pairs):
        lines = [
            f"**By operator, all suites pooled, N = {n_pairs} pairs**",
            "",
            "| " + " | ".join(table.columns) + " |",
            "| --- " + "| ---: " * (len(table.columns) - 1) + "|",
        ]
        for (
            operator, pairs, bfc_ok, specs_ok, bfc_ms, specs_ms, speedup,
        ) in table.itertuples(index=False):
            cells = [
                operator,
                str(pairs),
                str(bfc_ok),
                str(specs_ok),
                _cell(bfc_ms, 0, "-"),
                _cell(specs_ms, 0, "-"),
                _cell(speedup, 1, "-"),
            ]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join([*lines, ""])

    def zip_bytes(files):
        import zipfile
        from io import BytesIO

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        return buffer.getvalue()

    def write_files(files, directory="artifacts/by_operator"):
        from pathlib import Path

        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (out / name).write_bytes(data)

    return markdown_table, render_table, write_files, zip_bytes


@app.cell
def _(
    all_bfc,
    all_specs,
    markdown_table,
    operator_frame,
    outcomes_figure,
    render_table,
    speedup_figure,
    time_figure,
):
    def _svg_bytes(fig):
        from io import BytesIO

        buffer = BytesIO()
        fig.savefig(buffer, format="svg")
        return buffer.getvalue()

    artifacts = {
        "operator_outcomes.svg": _svg_bytes(outcomes_figure(all_bfc, all_specs)),
        "operator_time.svg": _svg_bytes(time_figure(all_bfc, all_specs)),
        "operator_speedup.svg": _svg_bytes(speedup_figure(operator_frame)),
        "table_operator.tex": render_table(operator_frame, len(all_bfc)).encode(),
        "table_operator.md": markdown_table(operator_frame, len(all_bfc)).encode(),
    }
    return (artifacts,)


@app.cell
def _(mo):
    write_button = mo.ui.run_button(label="Write artifacts to artifacts/by_operator/", full_width=True)
    return (write_button,)


@app.cell
def _(artifacts, mo, write_button, write_files, zip_bytes):
    from os import environ as _environ

    _buttons = [mo.download(zip_bytes(artifacts), "artifacts.zip", label="Download all as .zip")]
    _status = []
    # A static page (`make export` sets STATIC_EXPORT) cannot write files.
    if _environ.get("STATIC_EXPORT") != "1":
        _buttons.insert(0, write_button)
        if write_button.value or mo.app_meta().mode == "script":
            write_files(artifacts)
            _status.append(mo.md(f"Wrote {len(artifacts)} files to `artifacts/by_operator/`."))
    mo.vstack([mo.vstack(_buttons, align="stretch"), *_status], align="center")
    return


if __name__ == "__main__":
    app.run()
