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
    import matplotlib.patches as mpatches
    import numpy as np
    import pandas as pd
    from matplotlib.figure import Figure
    from returns.unsafe import unsafe_perform_io
    from scipy.stats import mannwhitneyu

    return Figure, mannwhitneyu, mo, mpatches, np, pd, unsafe_perform_io


@app.cell
def _(mo):
    import sys
    from pathlib import Path

    is_web = sys.platform == "emscripten"
    if sys.platform == "emscripten":
        # Browser build (GitHub Pages): marimo packages lib/ itself, but the
        # results/ data has no checkout to read from, so fetch it from
        # <site>/public/ into the in-memory filesystem.
        from pyodide.http import open_url

        _base = str(mo.notebook_location() / "public")
        for _name in open_url(f"{_base}/manifest.txt").read().split():
            _target = Path(_name)
            _target.parent.mkdir(parents=True, exist_ok=True)
            _target.write_text(open_url(f"{_base}/{_name}").read())

    from lib.datasets import Suite, result_dataframe
    from lib.types import EngineName

    return EngineName, Suite, is_web, result_dataframe


@app.cell
def _(Suite, mo):
    dropdown = mo.ui.dropdown(
        options=[e.value for e in Suite], label="choose a suite", value=Suite.OPERATORS.value
    )
    log_scale = mo.ui.switch(label="log scale")
    return dropdown, log_scale


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Pair comparison: BFC vs SPECS
    """)
    return


@app.cell
def _(dropdown, log_scale, mo):
    mo.hstack([dropdown, log_scale], justify="start")
    return


@app.cell
def _(EngineName, Figure, is_web, mo, mpatches, pd):
    _ENGINE_COLORS = {
        EngineName.BFC: "#2a78d6",
        EngineName.SPECS: "#eb6834",
    }

    def figure_view(fig):
        if not is_web:
            return mo.mpl.interactive(fig)
        from io import BytesIO

        buffer = BytesIO()
        fig.savefig(buffer, format="svg")
        return mo.Html(
            "<style>.fig svg { max-width: 100%; height: auto; }</style>"
            f'<div class="fig">{buffer.getvalue().decode()}</div>'
        )

    def pooled_times(df):
        return [t for times in df["Times"] for t in times]

    def pair_labels(df):
        return [
            f"#{index} {family.label}" + ("" if pd.isna(scale) else f" ×{int(scale)}")
            for index, family, scale in zip(df["Index"], df["QueryFamily"], df["Scale"])
        ]

    def violin_figure(bfc, specs, title, log_scale):
        fig = Figure(figsize=(max(7, 1.1 * len(bfc) + 2), 4.5), layout="constrained")
        ax = fig.subplots()

        for engine, df, offset in (
            (EngineName.BFC, bfc, -0.2),
            (EngineName.SPECS, specs, 0.2),
        ):
            drawn = [
                (position + offset, list(times))
                for position, times in enumerate(df["Times"], start=1)
                if len(times) > 0
            ]
            if not drawn:
                continue
            positions, data = zip(*drawn)
            parts = ax.violinplot(list(data), positions=list(positions), widths=0.35, showmeans=True)
            for body in parts["bodies"]:
                body.set_facecolor(_ENGINE_COLORS[engine])
                body.set_edgecolor(_ENGINE_COLORS[engine])
                body.set_alpha(0.7)

        ax.set_xticks(range(1, len(bfc) + 1), labels=pair_labels(bfc), rotation=45, ha="right", fontsize=9)
        ax.set_ylabel("Execution time (ms)", fontsize=10)
        ax.set_title(title, fontsize=12)
        if log_scale:
            ax.set_yscale("log")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(
            handles=[
                mpatches.Patch(color=_ENGINE_COLORS[EngineName.BFC], label="bfc"),
                mpatches.Patch(color=_ENGINE_COLORS[EngineName.SPECS], label="specs"),
            ],
            loc="upper right",
            fontsize=9,
        )
        return fig

    return figure_view, pair_labels, pooled_times, violin_figure


@app.cell
def _(EngineName, Suite, dropdown, result_dataframe, unsafe_perform_io):
    suite = Suite(dropdown.value)
    bfc_df = unsafe_perform_io(result_dataframe(suite, EngineName.BFC).unwrap())
    specs_df = unsafe_perform_io(result_dataframe(suite, EngineName.SPECS).unwrap())
    return bfc_df, specs_df, suite


@app.cell
def _(bfc_df, mo):
    _operators = list(dict.fromkeys(bfc_df["Operator"]))
    operator_dropdown = mo.ui.dropdown(
        options={_operator.label: _operator for _operator in _operators},
        value=_operators[0].label,
        label="operator",
    )
    return (operator_dropdown,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Operator detail
    """)
    return


@app.cell
def _(
    bfc_df,
    figure_view,
    log_scale,
    mo,
    operator_dropdown,
    specs_df,
    violin_figure,
):
    _group = bfc_df[bfc_df["Operator"] == operator_dropdown.value]
    mo.vstack(
        [
            operator_dropdown,
            figure_view(
                violin_figure(
                    _group,
                    specs_df.loc[_group.index],
                    operator_dropdown.value.label,
                    log_scale.value,
                )
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Pairs

    Speedup > 1: BFC faster. Speedup < 1: SPECS faster.
    """)
    return


@app.cell
def _(bfc_df, mo, pair_labels, pd, specs_df):
    def _time_per_run(df):
        return df["Times"].map(lambda times: sum(times) / len(times) if len(times) > 0 else float("nan"))

    _failed = (
        bfc_df["Timeouts"] | bfc_df["Errors"] | bfc_df["OutOfMemory"]
        | specs_df["Timeouts"] | specs_df["Errors"] | specs_df["OutOfMemory"]
    )
    _speedup = (_time_per_run(specs_df) / _time_per_run(bfc_df)).where(~_failed)

    pairs_table = pd.DataFrame(
        {
            "Operator": bfc_df["Operator"].map(lambda operator: operator.label),
            "Pair": pair_labels(bfc_df),
            "BFC correct": bfc_df["Correct"].map({True: "Yes", False: "No"}),
            "SPECS correct": specs_df["Correct"].map({True: "Yes", False: "No"}),
            "Speedup, BFC vs SPECS (x)": _speedup.astype(float).round(2),
        }
    )

    from math import log2 as _log2

    _BLUE, _ORANGE = "42, 120, 214", "235, 104, 52"
    _GREEN, _RED, _AMBER, _GREY = "46, 160, 67", "218, 54, 51", "237, 161, 0", "128, 128, 128"

    def _style_cell(row_id, column, value):
        _pair_speedup = pairs_table["Speedup, BFC vs SPECS (x)"].iloc[int(row_id)]
        if column in ("BFC correct", "SPECS correct"):
            _outcome = (bfc_df if column == "BFC correct" else specs_df)["Outcome"].iloc[int(row_id)]
            _rgb = _GREEN if value == "Yes" else _AMBER if _outcome == "unknown" else _RED
            return {"backgroundColor": f"rgba({_rgb}, 0.25)"}
        if pd.isna(_pair_speedup):
            return {"backgroundColor": f"rgba({_GREY}, 0.15)", "color": "gray"}
        if column == "Speedup, BFC vs SPECS (x)":
            _strength = min(abs(_log2(value)) / 4, 1)
            _rgb = _BLUE if value > 1 else _ORANGE
            return {"backgroundColor": f"rgba({_rgb}, {0.15 + 0.55 * _strength:.2f})"}
        return {}

    def _swatch(rgb, text):
        return (
            f'<span style="display:inline-block;width:0.9em;height:0.9em;border-radius:2px;'
            f'background:rgba({rgb}, 0.6);margin:0 0.3em 0 1.2em;vertical-align:-0.1em"></span>{text}'
        )

    _gradient = (
        '<span style="display:inline-block;vertical-align:middle;font-size:0.85em">'
        '<span style="display:block;width:16em;height:0.9em;border-radius:2px;'
        f"background:linear-gradient(to right, rgba({_ORANGE}, 0.70), rgba({_ORANGE}, 0.15) 50%, "
        f'rgba({_BLUE}, 0.15) 50%, rgba({_BLUE}, 0.70))"></span>'
        '<span style="display:flex;justify-content:space-between;width:16em">'
        "<span>SPECS 16x+ faster</span><span>equal</span><span>BFC 16x+ faster</span></span></span>"
    )

    _legend = mo.md(
        _gradient
        + _swatch(_GREEN, "correct")
        + _swatch(_AMBER, "unknown")
        + _swatch(_RED, "incorrect, timeout or out of memory")
        + _swatch(_GREY, "no speedup: timeout, error or out of memory")
    )

    mo.vstack(
        [
            _legend,
            mo.ui.table(pairs_table, selection=None, page_size=15, style_cell=_style_cell),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Suite overview
    """)
    return


@app.cell
def _(bfc_df, mannwhitneyu, mo, np, pd, pooled_times, specs_df, suite):
    _bfc_times = pooled_times(bfc_df)
    _specs_times = pooled_times(specs_df)

    if len(_bfc_times) > 0 and len(_specs_times) > 0:
        _, _p_value = mannwhitneyu(_bfc_times, _specs_times, alternative="two-sided")
    else:
        _p_value = float("nan")

    _alpha = 0.05
    _p_text = "< 0.0001" if _p_value < 1e-4 else f"= {_p_value:.4g}"
    if pd.isna(_p_value):
        _conclusion = "Cannot compare: one engine has no timings."
    else:
        _medians = {"bfc": np.median(_bfc_times), "specs": np.median(_specs_times)}
        _faster = "bfc" if _medians["bfc"] < _medians["specs"] else "specs"
        _detail = f"median {_medians['bfc']:.0f} ms (bfc) vs {_medians['specs']:.0f} ms (specs)"
        if _p_value < _alpha:
            _conclusion = (
                f"The difference is **statistically significant** (p < {_alpha}): "
                f"**{_faster} is faster** ({_detail})."
            )
        else:
            _conclusion = (
                f"The difference is **not statistically significant** (p ≥ {_alpha}): "
                f"neither engine can be called faster ({_detail})."
            )

    summary = pd.DataFrame(
        [
            {
                "Engine": _engine,
                "Mean (ms)": np.mean(_times_) if _times_ else float("nan"),
                "Median (ms)": np.median(_times_) if _times_ else float("nan"),
                "Correct": int(_df["Correct"].sum()),
                "Unknown": int((_df["Outcome"] == "unknown").sum()),
                "Incorrect": int(_df["Incorrect"].sum()),
                "Timeouts": int(_df["Timeouts"].sum()),
                "Errors": int(_df["Errors"].sum()),
                "OutOfMemory": int(_df["OutOfMemory"].sum()),
            }
            for _engine, _df, _times_ in (
                ("bfc", bfc_df, _bfc_times),
                ("specs", specs_df, _specs_times),
            )
        ]
    )

    mo.vstack(
        [
            mo.ui.table(
                summary,
                format_mapping={"Mean (ms)": "{:.0f}".format, "Median (ms)": "{:.0f}".format},
                selection=None,
                show_download=False,
            ),
            mo.md(
                f"Suite `{suite.value}`, N = {len(bfc_df)} pairs. "
                f"Mann-Whitney U on all pooled timings: "
                f"p {_p_text}. {_conclusion}"
            ),
        ]
    )
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
