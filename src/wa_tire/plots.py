"""Chart functions; each returns a matplotlib Figure.

Tire and dealer sales differ in scale by ~20x, so both are indexed to their 2019 average = 100
on one axis (no dual axes). Palette: validated default categorical slots 1-2.
"""

import matplotlib.pyplot as plt
import pandas as pd

TIRE_COLOR = "#2a78d6"
NEWCAR_COLOR = "#eb6834"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
LABELS = {"tire": "Tire dealers (441320/441340)", "newcar": "New-car dealers (441110)"}
COLORS = {"tire": TIRE_COLOR, "newcar": NEWCAR_COLOR}


def _style(ax, title, ylabel):
    fig = ax.figure
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=12)
    ax.set_ylabel(ylabel, color=INK_2)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(colors=MUTED)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def _indexed(cq):
    """Quarterly real sales by series, indexed to 2019 average = 100."""
    s = cq.groupby(["quarter", "series"])["real_sales"].sum().unstack("series")
    base = s[s.index.str.startswith("2019")].mean()
    return s / base * 100


def _index_chart(cq, title):
    idx = _indexed(cq)
    x = pd.PeriodIndex(idx.index, freq="Q").to_timestamp()
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for series in ("tire", "newcar"):
        ax.plot(x, idx[series], color=COLORS[series], linewidth=2, label=LABELS[series])
        ax.annotate(f"{idx[series].iloc[-1]:.0f}", (x[-1], idx[series].iloc[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", color=INK_2, fontsize=9)
    ax.axhline(100, color=MUTED, linewidth=0.8, linestyle=":")
    ax.axvline(pd.Timestamp("2022-04-01"), color=MUTED, linewidth=0.8)
    ax.text(pd.Timestamp("2022-05-01"), ax.get_ylim()[1], "2022 NAICS", va="top", color=MUTED, fontsize=8)
    _style(ax, title, "Real taxable sales, 2019 avg = 100")
    ax.legend(frameon=False, loc="upper left", labelcolor=INK_2)
    fig.tight_layout()
    return fig


def statewide_index(cq):
    return _index_chart(cq, "Washington: real taxable sales, tire dealers vs new-car dealers (quarterly)")


def county_index(cq, county):
    return _index_chart(cq[cq["county"] == county], f"{county} County: real taxable sales (quarterly)")


def signal_scatter(ranked):
    """Residual (x) vs growth gap (y); top candidates highlighted and labelled."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    top = ranked["top_candidate"]
    ax.scatter(ranked.loc[~top, "residual_pct"] * 100, ranked.loc[~top, "growth_gap_log"] * 100,
               s=36, color=MUTED, edgecolor=SURFACE, linewidth=1.5, label="Other included counties")
    ax.scatter(ranked.loc[top, "residual_pct"] * 100, ranked.loc[top, "growth_gap_log"] * 100,
               s=64, color=TIRE_COLOR, edgecolor=SURFACE, linewidth=1.5, label="Top candidates (top quartile on both)")
    for _, r in ranked[top].iterrows():
        ax.annotate(r["county"], (r["residual_pct"] * 100, r["growth_gap_log"] * 100), xytext=(6, 4),
                    textcoords="offset points", color=INK, fontsize=9)
    ax.axhline(0, color=MUTED, linewidth=0.8)
    ax.axvline(0, color=MUTED, linewidth=0.8)
    _style(ax, "County signals: sales above expectation vs tire growth beyond dealer growth",
           "Growth gap since 2019 (log points x100)")
    ax.set_xlabel("Residual: actual vs expected real tire sales, recent years (%)", color=INK_2)
    ax.legend(frameon=False, loc="best", labelcolor=INK_2)
    fig.tight_layout()
    return fig
