# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "openpyxl",
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

    return Figure, Patch, mo, np, pd


@app.cell
def _():
    from lib.datasets import REGULAR_SUITES, SCALE_SUITES, Suite, suite_frames
    from lib.largerdfbench import load as load_largerdfbench
    from lib.stats import (
        ALPHA,
        SIGNIFICANCE_TESTS,
        compare,
        correct_times,
        matched_times_by_size,
        pooled,
        summary_table,
        verdict,
    )
    from lib.types import (
        EngineName,
        LargeRDFBenchCategory,
        LargeRDFBenchSourceSelection,
    )

    return (
        ALPHA,
        EngineName,
        LargeRDFBenchCategory,
        LargeRDFBenchSourceSelection,
        REGULAR_SUITES,
        SCALE_SUITES,
        SIGNIFICANCE_TESTS,
        Suite,
        compare,
        correct_times,
        load_largerdfbench,
        matched_times_by_size,
        pooled,
        suite_frames,
        summary_table,
        verdict,
    )


@app.cell
def _(REGULAR_SUITES, SCALE_SUITES, pd, pooled):
    regular_bfc, regular_specs = pooled(REGULAR_SUITES)
    scale_bfc, scale_specs = pooled(SCALE_SUITES)
    all_bfc = pd.concat([regular_bfc, scale_bfc], ignore_index=True)
    all_specs = pd.concat([regular_specs, scale_specs], ignore_index=True)
    return (
        all_bfc,
        all_specs,
        regular_bfc,
        regular_specs,
        scale_bfc,
        scale_specs,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Overview: BFC vs SPECS
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Tables
    """)
    return


@app.cell
def _(mo):
    def show_table(table):
        """The table with whole-millisecond timings; only the display is rounded."""
        return mo.ui.table(
            table,
            format_mapping={
                "Mean (ms)": "{:.0f}".format,
                "Median (ms)": "{:.0f}".format,
            },
            selection=None,
            show_download=False,
        )

    return (show_table,)


@app.cell
def _(all_bfc, all_specs, compare, mo, show_table, summary_table, verdict):
    all_table = summary_table(all_bfc, all_specs)
    all_p, all_faster = compare(all_bfc, all_specs)
    mo.vstack(
        [
            mo.md(f"### All suites (regular and scale), N = {len(all_bfc)} pairs"),
            show_table(all_table),
            mo.md(verdict(all_p, all_faster)),
        ]
    )
    return all_faster, all_p, all_table


@app.cell
def _(
    compare,
    mo,
    regular_bfc,
    regular_specs,
    show_table,
    summary_table,
    verdict,
):
    regular_table = summary_table(regular_bfc, regular_specs)
    regular_p, regular_faster = compare(regular_bfc, regular_specs)
    mo.vstack(
        [
            mo.md(f"### Regular suites (branching, operators, star, ucfq), N = {len(regular_bfc)} pairs"),
            show_table(regular_table),
            mo.md(verdict(regular_p, regular_faster)),
        ]
    )
    return regular_faster, regular_p


@app.cell
def _(compare, mo, scale_bfc, scale_specs, show_table, summary_table, verdict):
    scale_table = summary_table(scale_bfc, scale_specs)
    scale_p, scale_faster = compare(scale_bfc, scale_specs)
    mo.vstack(
        [
            mo.md(f"### Scale suites (sizes pooled), N = {len(scale_bfc)} pairs"),
            show_table(scale_table),
            mo.md(verdict(scale_p, scale_faster)),
        ]
    )
    return scale_faster, scale_p


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Plot functions
    """)
    return


@app.cell
def _(EngineName):
    COLORS = {EngineName.BFC: "#2a78d6", EngineName.SPECS: "#eb6834"}

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

    return COLORS, draw_violins, tidy


@app.cell
def _(EngineName, Figure, correct_times, draw_violins, tidy):
    def group_violins(bfc, specs):
        """One violin per engine over the timings of its correct pairs."""
        fig = Figure(layout="constrained")
        ax = fig.subplots()
        labels = []
        for position, (engine, df) in enumerate(
            ((EngineName.BFC, bfc), (EngineName.SPECS, specs)), start=1
        ):
            draw_violins(ax, engine, [correct_times(df)], [position])
            labels.append(f"{engine.value.upper()}\nn = {int(df['Correct'].sum())} correct")
        ax.set_xticks([1, 2], labels=labels)
        ax.set_yscale("log")
        ax.set_ylabel("Execution time (ms)")
        tidy(ax)
        return fig

    return (group_violins,)


@app.cell
def _(EngineName, matched_times_by_size, suite_frames):
    def scale_data(suite):
        """Per size, each engine's timings over the statements it answers correctly at every size."""
        engines = (EngineName.BFC, EngineName.SPECS)
        frames = suite_frames(suite)
        by_engine = {engine: matched_times_by_size(df) for engine, df in zip(engines, frames)}
        sizes = list(by_engine[EngineName.BFC])
        total = len(frames[0]) // len(sizes)
        timings = {
            engine: [[time for times in by_engine[engine][size] for time in times] for size in sizes]
            for engine in engines
        }
        statements = {engine: len(by_engine[engine][sizes[0]]) for engine in engines}
        return sizes, timings, statements, total

    def legend_label(engine, statements):
        return f"{engine.value.upper()} (n = {statements[engine]} correct at every size)"

    return legend_label, scale_data


@app.cell
def _(
    COLORS,
    EngineName,
    Figure,
    Patch,
    draw_violins,
    legend_label,
    scale_data,
    tidy,
):
    def size_figure(suite):
        """Violins per size."""
        sizes, timings, statements, _ = scale_data(suite)
        fig = Figure(layout="constrained")
        ax = fig.subplots()
        for engine, offset in ((EngineName.BFC, -0.2), (EngineName.SPECS, 0.2)):
            draw_violins(ax, engine, timings[engine], [i + offset for i in range(len(sizes))])
        ax.set_xticks(range(len(sizes)), labels=[str(size) for size in sizes])
        ax.set_xlabel("size N")
        ax.set_ylabel("Execution time (ms)")
        ax.set_yscale("log")
        ax.legend(
            handles=[
                Patch(color=COLORS[engine], label=legend_label(engine, statements))
                for engine in (EngineName.BFC, EngineName.SPECS)
            ],
            loc="upper left",
            frameon=False,
        )
        tidy(ax)
        return fig

    return (size_figure,)


@app.cell
def _(COLORS, EngineName, Figure, legend_label, np, scale_data, tidy):
    def growth_figure(suite):
        """Median time (inter-quartile band) against size, both axes linear."""
        sizes, timings, statements, _ = scale_data(suite)
        fig = Figure(layout="constrained")
        ax = fig.subplots()
        for engine in (EngineName.BFC, EngineName.SPECS):
            samples = [np.array(sample) for sample in timings[engine]]
            if any(sample.size == 0 for sample in samples):
                continue
            medians = [float(np.median(sample)) for sample in samples]
            low = [float(np.percentile(sample, 25)) for sample in samples]
            high = [float(np.percentile(sample, 75)) for sample in samples]
            ax.plot(
                sizes,
                medians,
                marker="o",
                markersize=3,
                color=COLORS[engine],
                label=legend_label(engine, statements),
            )
            ax.fill_between(sizes, low, high, color=COLORS[engine], alpha=0.2, linewidth=0)
        ax.set_xticks(sizes)
        ax.set_xlabel("size N")
        ax.set_ylabel("Execution time (ms)")
        ax.legend(loc="upper left", frameon=False)
        tidy(ax)
        return fig

    return (growth_figure,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Figures
    """)
    return


@app.cell
def _(all_bfc, all_faster, all_p, all_specs, group_violins, mo, verdict):
    fig_all = group_violins(all_bfc, all_specs)
    mo.vstack(
        [
            mo.md(f"### Execution time of BFC and SPECS on all suites, N = {len(all_bfc)} pairs"),
            fig_all,
            mo.md(verdict(all_p, all_faster)),
        ]
    )
    return


@app.cell
def _(
    group_violins,
    mo,
    regular_bfc,
    regular_faster,
    regular_p,
    regular_specs,
    verdict,
):
    fig_regular = group_violins(regular_bfc, regular_specs)
    mo.vstack(
        [
            mo.md(f"### Execution time of BFC and SPECS on the regular suites, N = {len(regular_bfc)} pairs"),
            fig_regular,
            mo.md(verdict(regular_p, regular_faster)),
        ]
    )
    return


@app.cell
def _(
    group_violins,
    mo,
    scale_bfc,
    scale_faster,
    scale_p,
    scale_specs,
    verdict,
):
    fig_scale = group_violins(scale_bfc, scale_specs)
    mo.vstack(
        [
            mo.md(f"### Execution time of BFC and SPECS on the scale suites, N = {len(scale_bfc)} pairs"),
            fig_scale,
            mo.md(verdict(scale_p, scale_faster)),
        ]
    )
    return


@app.cell(hide_code=True)
def _(Suite, mo, scale_data):
    _, _, _, _total = scale_data(Suite.BRANCHING_SCALE)
    mo.md(f"### Branching scale suite, {_total} pairs per size")
    return


@app.cell
def _(Suite, mo, size_figure):
    fig_branching_size = size_figure(Suite.BRANCHING_SCALE)
    mo.vstack(
        [
            mo.md("#### Execution time of BFC and SPECS on the branching scale suite, per size N"),
            fig_branching_size,
        ]
    )
    return


@app.cell
def _(Suite, growth_figure, mo):
    fig_branching_growth = growth_figure(Suite.BRANCHING_SCALE)
    mo.vstack(
        [
            mo.md("#### Median execution time of BFC and SPECS on the branching scale suite against size N"),
            fig_branching_growth,
        ]
    )
    return


@app.cell(hide_code=True)
def _(Suite, mo, scale_data):
    _, _, _, _total = scale_data(Suite.OPERATORS_SCALE)
    mo.md(f"### Chain scale suite, {_total} pairs per size")
    return


@app.cell
def _(Suite, mo, size_figure):
    fig_chain_size = size_figure(Suite.OPERATORS_SCALE)
    mo.vstack(
        [
            mo.md("#### Execution time of BFC and SPECS on the chain scale suite, per size N"),
            fig_chain_size,
        ]
    )
    return


@app.cell
def _(Suite, growth_figure, mo):
    fig_chain_growth = growth_figure(Suite.OPERATORS_SCALE)
    mo.vstack(
        [
            mo.md("#### Median execution time of BFC and SPECS on the chain scale suite against size N"),
            fig_chain_growth,
        ]
    )
    return


@app.cell(hide_code=True)
def _(Suite, mo, scale_data):
    _, _, _, _total = scale_data(Suite.STAR_SCALE)
    mo.md(f"### Star scale suite, {_total} pairs per size")
    return


@app.cell
def _(Suite, mo, size_figure):
    fig_star_size = size_figure(Suite.STAR_SCALE)
    mo.vstack(
        [
            mo.md("#### Execution time of BFC and SPECS on the star scale suite, per size N"),
            fig_star_size,
        ]
    )
    return


@app.cell
def _(Suite, growth_figure, mo):
    fig_star_growth = growth_figure(Suite.STAR_SCALE)
    mo.vstack(
        [
            mo.md("#### Median execution time of BFC and SPECS on the star scale suite against size N"),
            fig_star_growth,
        ]
    )
    return


@app.cell(hide_code=True)
def _(Suite, mo, scale_data):
    _, _, _, _total = scale_data(Suite.UCFQ_SCALE)
    mo.md(f"### UCFQ scale suite, {_total} pairs per size")
    return


@app.cell
def _(Suite, mo, size_figure):
    fig_ucfq_size = size_figure(Suite.UCFQ_SCALE)
    mo.vstack(
        [
            mo.md("#### Execution time of BFC and SPECS on the UCFQ scale suite, per size N"),
            fig_ucfq_size,
        ]
    )
    return


@app.cell
def _(Suite, growth_figure, mo):
    fig_ucfq_growth = growth_figure(Suite.UCFQ_SCALE)
    mo.vstack(
        [
            mo.md("#### Median execution time of BFC and SPECS on the UCFQ scale suite against size N"),
            fig_ucfq_growth,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Comparison with LargeRDFBench
    """)
    return


@app.cell
def _(
    LargeRDFBenchCategory,
    LargeRDFBenchSourceSelection,
    all_table,
    load_largerdfbench,
    mo,
    pd,
):
    _bfc_mean = all_table.loc[all_table["Engine"] == "BFC", "Mean (ms)"].item()

    _largerdfbench = load_largerdfbench()
    _correct = _largerdfbench[_largerdfbench["Complete"] & _largerdfbench["Time (ms)"].notna()]

    def _stat(category, selection):
        group = _correct[(_correct["Category"] == category) & (_correct["SourceSelection"] == selection)]
        times = group["Time (ms)"]
        return times.mean(), len(times)

    _AUTO = LargeRDFBenchSourceSelection.AUTOMATIC
    _SERVICE = LargeRDFBenchSourceSelection.EXPLICIT_SERVICE

    _rows = []
    for _category in LargeRDFBenchCategory:
        _auto_mean, _auto_n = _stat(_category, _AUTO)
        _service_mean, _service_n = _stat(_category, _SERVICE)
        _rows.append(
            {
                "Category": _category.value,
                "Automatic mean (ms)": _auto_mean,
                "Automatic n": _auto_n,
                "Automatic speedup vs BFC": _auto_mean / _bfc_mean,
                "Explicit SERVICE mean (ms)": _service_mean,
                "Explicit SERVICE n": _service_n,
                "Explicit SERVICE speedup vs BFC": _service_mean / _bfc_mean,
            }
        )

    _all_auto = _correct[_correct["SourceSelection"] == _AUTO]["Time (ms)"]
    _all_service = _correct[_correct["SourceSelection"] == _SERVICE]["Time (ms)"]
    _rows.append(
        {
            "Category": "All",
            "Automatic mean (ms)": _all_auto.mean(),
            "Automatic n": len(_all_auto),
            "Automatic speedup vs BFC": _all_auto.mean() / _bfc_mean,
            "Explicit SERVICE mean (ms)": _all_service.mean(),
            "Explicit SERVICE n": len(_all_service),
            "Explicit SERVICE speedup vs BFC": _all_service.mean() / _bfc_mean,
        }
    )
    largerdfbench_table = pd.DataFrame(_rows)

    from math import log2 as _log2

    _BLUE, _ORANGE = "42, 120, 214", "235, 104, 52"
    _SPEEDUP_COLUMNS = ("Automatic speedup vs BFC", "Explicit SERVICE speedup vs BFC")

    def _style_cell(row_id, column, value):
        if column not in _SPEEDUP_COLUMNS:
            return {}
        _strength = min(abs(_log2(value)) / 4, 1)
        _rgb = _BLUE if value > 1 else _ORANGE
        return {"backgroundColor": f"rgba({_rgb}, {0.15 + 0.55 * _strength:.2f})"}

    _gradient = (
        '<span style="display:inline-block;vertical-align:middle;font-size:0.85em">'
        '<span style="display:block;width:16em;height:0.9em;border-radius:2px;'
        f"background:linear-gradient(to right, rgba({_ORANGE}, 0.70), rgba({_ORANGE}, 0.15) 50%, "
        f'rgba({_BLUE}, 0.15) 50%, rgba({_BLUE}, 0.70))"></span>'
        '<span style="display:flex;justify-content:space-between;width:16em">'
        "<span>LargeRDFBench 16x+ faster</span><span>equal</span><span>BFC 16x+ faster</span></span></span>"
    )

    mo.vstack(
        [
            mo.md(f"### LargeRDFBench, speedup vs BFC's mean ({_bfc_mean:.0f} ms)"),
            mo.md(_gradient),
            mo.ui.table(
                largerdfbench_table,
                format_mapping={
                    "Automatic mean (ms)": "{:.0f}".format,
                    "Automatic speedup vs BFC": "{:.1f}".format,
                    "Explicit SERVICE mean (ms)": "{:.0f}".format,
                    "Explicit SERVICE speedup vs BFC": "{:.1f}".format,
                },
                selection=None,
                show_download=False,
                style_cell=_style_cell,
            ),
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
def _(ALPHA, SIGNIFICANCE_TESTS, pd):
    from string import Template as _Template

    class _LatexTemplate(_Template):
        # "@" so that LaTeX's "$" and "%" stay untouched in the template files.
        delimiter = "@"

    def latex_rows(table):
        lines = []
        for (
            engine, mean, median,
            correct, unknown, incorrect, timeouts, errors, out_of_memory,
        ) in table.itertuples(index=False):
            cells = [
                engine.upper(),
                f"{mean:.0f}", f"{median:.0f}",
                str(correct), str(unknown), str(incorrect),
                str(timeouts), str(errors), str(out_of_memory),
            ]
            lines.append("    " + " & ".join(cells) + r" \\")
        return "\n".join(lines)

    def latex_verdict(p_value, faster):
        if pd.isna(p_value):
            return "No comparison is possible, an engine has no correct pair."
        p_text = "p < 0.0001" if p_value < 1e-4 else f"p = {p_value:.4g}"
        test = (
            f"Wilcoxon signed-rank test with Hodges-Lehmann direction (Bonferroni-corrected "
            f"$\\alpha$ = {ALPHA:.4g} for {SIGNIFICANCE_TESTS} tests) on the pairs both engines "
            f"answered correctly"
        )
        if faster is None:
            return f"{test}: ${p_text}$, no significant difference."
        return f"{test}: ${p_text}$, {faster.value.upper()} is significantly faster."

    def render_table(name, table, n_pairs, p_value, faster):
        """Fill templates/table_<name>.tex, which holds the caption, label and layout."""
        from pathlib import Path

        template = _LatexTemplate(Path(f"templates/table_{name}.tex").read_text())
        return template.substitute(
            rows=latex_rows(table), n=n_pairs, verdict=latex_verdict(p_value, faster)
        )

    def markdown_table(title, table, n_pairs, verdict_text):
        columns = list(table.columns)
        lines = [
            f"**{title}, N = {n_pairs} pairs**",
            "",
            "| " + " | ".join(columns) + " |",
            "| --- " + "| ---: " * (len(columns) - 1) + "|",
        ]
        for (
            engine, mean, median,
            correct, unknown, incorrect, timeouts, errors, out_of_memory,
        ) in table.itertuples(index=False):
            cells = [
                engine.upper(),
                f"{mean:.0f}", f"{median:.0f}",
                str(correct), str(unknown), str(incorrect),
                str(timeouts), str(errors), str(out_of_memory),
            ]
            lines.append("| " + " | ".join(cells) + " |")
        return "\n".join([*lines, "", verdict_text, ""])

    def zip_bytes(files):
        import zipfile
        from io import BytesIO

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for name, data in files.items():
                archive.writestr(name, data)
        return buffer.getvalue()

    def write_files(files, directory="artifacts/overview"):
        from pathlib import Path

        out = Path(directory)
        out.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (out / name).write_bytes(data)

    return markdown_table, render_table, write_files, zip_bytes


@app.cell
def _(
    Suite,
    all_bfc,
    all_specs,
    compare,
    group_violins,
    growth_figure,
    markdown_table,
    regular_bfc,
    regular_specs,
    render_table,
    scale_bfc,
    scale_specs,
    size_figure,
    summary_table,
    verdict,
):
    def _svg_bytes(fig):
        from io import BytesIO

        buffer = BytesIO()
        fig.savefig(buffer, format="svg")
        return buffer.getvalue()

    _figures = {
        "all_suites": group_violins(all_bfc, all_specs),
        "regular_suites": group_violins(regular_bfc, regular_specs),
        "scale_suites": group_violins(scale_bfc, scale_specs),
    }
    for _suite, _name in (
        (Suite.BRANCHING_SCALE, "branching"),
        (Suite.OPERATORS_SCALE, "chain"),
        (Suite.STAR_SCALE, "star"),
        (Suite.UCFQ_SCALE, "ucfq"),
    ):
        _figures[f"{_name}_per_size"] = size_figure(_suite)
        _figures[f"{_name}_growth"] = growth_figure(_suite)

    artifacts = {}
    for _name, _figure in _figures.items():
        artifacts[f"{_name}.svg"] = _svg_bytes(_figure)

    for _name, _title, (_bfc, _specs) in (
        ("all", "All suites (regular and scale)", (all_bfc, all_specs)),
        ("regular", "Regular suites (branching, operators, star, ucfq)", (regular_bfc, regular_specs)),
        ("scale", "Scale suites (sizes pooled)", (scale_bfc, scale_specs)),
    ):
        _table = summary_table(_bfc, _specs)
        _p_value, _faster = compare(_bfc, _specs)
        _latex = render_table(_name, _table, len(_bfc), _p_value, _faster)
        _markdown = markdown_table(_title, _table, len(_bfc), verdict(_p_value, _faster))
        artifacts[f"table_{_name}.tex"] = _latex.encode()
        artifacts[f"table_{_name}.md"] = _markdown.encode()
    return (artifacts,)


@app.cell
def _(mo):
    write_button = mo.ui.run_button(label="Write artifacts to artifacts/overview/", full_width=True)
    return (write_button,)


@app.cell
def _(artifacts, mo, write_button, write_files, zip_bytes):
    _buttons = [mo.download(zip_bytes(artifacts), "artifacts.zip", label="Download all as .zip")]
    _status = []
    # Only a local session can also write each artifact to its own file, by the button or by
    # running the notebook as a script (`make artifacts`). A static page cannot write to a
    # folder (`make export` sets STATIC_EXPORT).
    from os import environ as _environ

    if _environ.get("STATIC_EXPORT") != "1":
        _buttons.insert(0, write_button)
        if write_button.value or mo.app_meta().mode == "script":
            write_files(artifacts)
            _status.append(mo.md(f"Wrote {len(artifacts)} files to `artifacts/overview/`."))
    mo.vstack([mo.vstack(_buttons, align="stretch"), *_status], align="center")
    return


if __name__ == "__main__":
    app.run()
