"""Chart suite for the NDIF six-year performance presentation.

Palette: validated categorical/sequential/diverging slots (dataviz reference instance).
Surface: light (#fcfcfb). Thin marks, hairline recessive grid, selective direct labels.
"""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from scipy import stats
import statsmodels.api as sm

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)          # repository sub-directory root
DATA = os.path.join(BASE, "data")
CH = os.path.join(BASE, "charts")
os.makedirs(CH, exist_ok=True)

# ------------------------------------------------------------------ design tokens
SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK2      = "#52514e"
INK3      = "#86847e"
GRID      = "#e6e5e1"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
S5, S6, S7, S8 = "#e87ba4", "#008300", "#4a3aa7", "#e34948"
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
       "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
DIV_MID = "#f0efec"
BLUE_CMAP = LinearSegmentedColormap.from_list("seqblue", SEQ)
DIV_CMAP = LinearSegmentedColormap.from_list("divbr", ["#8f1f22", "#c2352f", "#e34948",
                                                      "#ef8b86", DIV_MID, "#86b6ef",
                                                      "#3987e5", "#256abf", "#0d366b"])

plt.rcParams.update({
    "font.family": "Lato", "font.size": 11.5,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.linewidth": 0.9,
    "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 10.5, "ytick.labelsize": 10.5,
    "grid.color": GRID, "grid.linewidth": 0.9, "grid.linestyle": "-",
    "axes.grid": True, "axes.grid.axis": "y", "axes.axisbelow": True,
    "legend.frameon": False, "legend.fontsize": 10.5,
    "lines.linewidth": 2.0, "lines.solid_capstyle": "round",
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.18,
})
PCT = FuncFormatter(lambda v, _: f"{v*100:,.0f}%")
PCT1 = FuncFormatter(lambda v, _: f"{v*100:,.1f}%")
USD = FuncFormatter(lambda v, _: f"${v/1e6:,.0f}m")

def esc(s):
    """Stop matplotlib treating paired '$' as mathtext."""
    return s.replace("$", r"\$")

def place_labels(fig, ax, items, pad=3.0):
    """Greedy non-overlapping annotation placement.

    items: list of dicts with x, y, text, color, and optional size/weight.
    Each label takes the first candidate offset that collides with neither an
    already-placed label nor any data point.
    """
    CAND = [(10, 0, "left", "center"), (-10, 0, "right", "center"),
            (0, 11, "center", "bottom"), (0, -11, "center", "top"),
            (9, 9, "left", "bottom"), (-9, 9, "right", "bottom"),
            (9, -9, "left", "top"), (-9, -9, "right", "top"),
            (20, 0, "left", "center"), (-20, 0, "right", "center"),
            (0, 21, "center", "bottom"), (0, -21, "center", "top"),
            (18, 14, "left", "bottom"), (-18, 14, "right", "bottom"),
            (18, -14, "left", "top"), (-18, -14, "right", "top")]
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    taken = []
    for it in items:
        px, py = ax.transData.transform(
            (float(ax.convert_xunits(it["x"])), float(ax.convert_yunits(it["y"]))))
        r = it.get("radius", 7.0)
        taken.append((px - r, py - r, px + r, py + r))
    order = sorted(range(len(items)), key=lambda i: -items[i].get("priority", 0))
    for i in order:
        it = items[i]
        best, best_ov = None, None
        for dx, dy, ha, va in CAND:
            ann = ax.annotate(esc(it["text"]), xy=(it["x"], it["y"]), xytext=(dx, dy),
                              textcoords="offset points", ha=ha, va=va,
                              color=it["color"], fontsize=it.get("size", 9.4),
                              fontweight=it.get("weight", "bold"), zorder=9)
            bb = ann.get_window_extent(rend)
            box = (bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)
            ab = ax.get_window_extent(rend)
            inside = box[0] >= ab.x0 - 2 and box[2] <= ab.x1 + 2 and \
                     box[1] >= ab.y0 - 2 and box[3] <= ab.y1 + 2
            ov = sum(max(0, min(box[2], t[2]) - max(box[0], t[0])) *
                     max(0, min(box[3], t[3]) - max(box[1], t[1])) for t in taken)
            if not inside:
                ov += 1e7
            if best_ov is None or ov < best_ov:
                best_ov, best = ov, (dx, dy, ha, va, box)
            ann.remove()
            if ov == 0:
                break
        dx, dy, ha, va, box = best
        ax.annotate(esc(it["text"]), xy=(it["x"], it["y"]), xytext=(dx, dy),
                    textcoords="offset points", ha=ha, va=va, color=it["color"],
                    fontsize=it.get("size", 9.4), fontweight=it.get("weight", "bold"),
                    zorder=9)
        taken.append(box)

def end_labels(ax, x_anchor, entries, x_text=None, min_gap_frac=0.062, fs=10.5):
    """Right-hand series labels, spread to a minimum vertical gap, with leaders."""
    lo, hi = ax.get_ylim()
    gap = (hi - lo) * min_gap_frac
    ent = sorted(entries, key=lambda e: e[0])
    ys = [e[0] for e in ent]
    for i in range(1, len(ys)):                       # push up
        ys[i] = max(ys[i], ys[i - 1] + gap)
    over = ys[-1] - (hi - gap * 0.5)
    if over > 0:
        ys = [y - over for y in ys]
    for i in range(len(ys) - 2, -1, -1):              # re-settle downward
        ys[i] = min(ys[i], ys[i + 1] - gap)
    xt = x_text if x_text is not None else x_anchor
    for (y0, text, color), y1 in zip(ent, ys):
        ax.annotate("", xy=(x_anchor, y0), xytext=(xt, y1), textcoords="data",
                    arrowprops=dict(arrowstyle="-", color=color, lw=1.0, alpha=0.55,
                                    shrinkA=4, shrinkB=2))
        ax.annotate(esc(text), xy=(xt, y1), xytext=(7, 0), textcoords="offset points",
                    color=color, fontsize=fs, fontweight="bold", va="center", ha="left")

def frame(ax, ygrid=True, xgrid=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID); ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)
    ax.grid(ygrid, axis="y"); ax.grid(xgrid, axis="x")

def title(ax, t, sub=None):
    ax.set_title(esc(t), loc="left", fontsize=15.5, fontweight="bold", color=INK,
                 pad=22 if sub else 12)
    if sub:
        ax.annotate(esc(sub), xy=(0, 1.012), xycoords="axes fraction", fontsize=11,
                    color=INK2, ha="left", va="bottom")

def save(fig, name):
    fig.savefig(os.path.join(CH, name))
    plt.close(fig)
    print("  wrote", name)

# ------------------------------------------------------------------------- data
SER = pd.read_csv(os.path.join(DATA, "series_monthly.csv"), index_col=0)
SER.index = pd.PeriodIndex(SER.index, freq="M")
STK = pd.read_csv(os.path.join(DATA, "stocks_monthly.csv"), index_col=0)
STK.index = pd.PeriodIndex(STK.index, freq="M")
ALLR = pd.read_csv(os.path.join(DATA, "all_monthly_returns.csv"), index_col=0)
ALLR.index = pd.PeriodIndex(ALLR.index, freq="M")
WP = pd.read_csv(os.path.join(DATA, "weight_path.csv"), index_col=0)
WP.index = pd.PeriodIndex(WP.index, freq="M")
FRONT = pd.read_csv(os.path.join(DATA, "frontier.csv"))
RES = json.load(open(os.path.join(DATA, "results.json")))
ANNUAL = pd.read_csv(os.path.join(DATA, "annual.csv"), index_col=0)

DATES = SER.index.to_timestamp(how="end")
N, Q, S = "NDIF", "NASDAQ-100 (QQQ)", "S&P 500 (SPY)"
TICK = list(STK.columns)
COMPANY = {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "V": "Visa",
           "EQIX": "Equinix", "ILMN": "Illumina", "ROK": "Rockwell", "NEE": "NextEra",
           "COST": "Costco", "ALB": "Albemarle", "SLB": "SLB"}
TIER = {"MSFT": 1, "GOOGL": 1, "AMZN": 1, "V": 2, "EQIX": 2, "ILMN": 2, "ROK": 2,
        "NEE": 3, "COST": 3, "ALB": 3, "SLB": 3}
TIER_C = {1: S1, 2: S2, 3: S3}
SECTOR_ETF = {"MSFT": "XLK", "GOOGL": "XLC", "AMZN": "XLY", "V": "XLF", "EQIX": "XLRE",
              "ILMN": "XLV", "ROK": "XLI", "NEE": "XLU", "COST": "XLP", "ALB": "XLB", "SLB": "XLE"}
GICS = {"MSFT": "Info Tech", "GOOGL": "Comm Svcs", "AMZN": "Cons Disc", "V": "Financials",
        "EQIX": "Real Estate", "ILMN": "Health Care", "ROK": "Industrials",
        "NEE": "Utilities", "COST": "Cons Staples", "ALB": "Materials", "SLB": "Energy"}

def wealth(s, base=100e6):
    return base * (1 + s).cumprod()

def dd(s):
    c = (1 + s).cumprod()
    return c / c.cummax() - 1

def endlabel(ax, x, y, text, color, dy=0, fs=11.5, weight="bold"):
    ax.annotate(esc(text), xy=(x, y), xytext=(8, dy), textcoords="offset points",
                color=color, fontsize=fs, fontweight=weight, va="center", ha="left")

# =============================================================== 01 growth of $100m
def c01():
    fig, ax = plt.subplots(figsize=(13.0, 4.6))
    ents = []
    for k, c, lw in [(N, S1, 2.6), (Q, S2, 2.0), (S, S3, 2.0)]:
        w = wealth(SER[k])
        ax.plot(DATES, w, color=c, lw=lw)
        ents.append((w.iloc[-1], f"{k.split(' (')[0]}   ${w.iloc[-1]/1e6:,.0f}m", c))
    ax.axhline(100e6, color=INK3, lw=0.9, zorder=1)
    ax.annotate("$100m mandate", xy=(DATES[2], 100e6), xytext=(0, -16),
                textcoords="offset points", color=INK3, fontsize=10)
    ax.yaxis.set_major_formatter(USD)
    ax.set_xlim(DATES[0], DATES[-1] + pd.Timedelta(days=760))
    ax.set_ylim(80e6, 390e6)
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2017, 2024)])
    ax.set_xticklabels(range(2017, 2024))
    frame(ax)
    end_labels(ax, DATES[-1], ents, x_text=DATES[-1] + pd.Timedelta(days=120), fs=11)
    title(ax, "A $100m mandate became $279m",
          "Growth of the initial mandate, Jan 2017 – Dec 2022 · monthly total returns, quarterly rebalanced")
    save(fig, "01_growth.png")

# ======================================================== 02 growth with event map
EVENTS = [
    ("2017-01", "DJIA tops\n20,000", 1),
    ("2017-12", "US tax reform\ncuts corporate rate", -1),
    ("2018-10", "Trade-war\nescalation", -1),
    ("2020-03", "COVID-19\ncrash", -1),
    ("2020-11", "Vaccine news\n+ stimulus", 1),
    ("2021-11", "Growth peak\nrates turn", 1),
    ("2022-06", "Fed hikes\n75bp; CPI 9.1%", -1),
]
def c02():
    """Events sit in a clean band above the series; leaders drop to the point."""
    fig, ax = plt.subplots(figsize=(11.6, 6.2))
    w = wealth(SER[N])
    ax.plot(DATES, w, color=S1, lw=2.6, zorder=3)
    ax.fill_between(DATES, 60e6, w, color=S1, alpha=0.07, zorder=1)
    ax.axhline(100e6, color=INK3, lw=0.9, zorder=2)
    lo, hi = 60e6, 560e6
    rows = [470e6, 408e6, 346e6]                    # three stagger heights in the band
    for i, (per, lab, _) in enumerate(EVENTS):
        p = pd.Period(per, "M")
        x = p.to_timestamp(how="end"); y = w.loc[p]
        yt = rows[i % 3]
        ax.annotate("", xy=(x, y), xytext=(x, yt - 8e6),
                    arrowprops=dict(arrowstyle="-", color=INK3, lw=0.9, alpha=0.55,
                                    shrinkA=0, shrinkB=6))
        ax.text(x, yt, esc(lab), fontsize=9.6, color=INK2, ha="center", va="bottom",
                linespacing=1.35)
        ax.plot([x], [y], "o", ms=8, color=S1, mec=SURFACE, mew=2, zorder=4)
    ax.set_ylim(lo, hi)
    ax.set_yticks([100e6, 200e6, 300e6])
    ax.yaxis.set_major_formatter(USD)
    ax.set_xlim(pd.Timestamp("2016-11-01"), pd.Timestamp("2023-03-01"))
    frame(ax)
    title(ax, "Six years, seven turning points",
          "NDIF cumulative wealth with the events that moved it")
    save(fig, "02_growth_events.png")

# ================================================================== 03 drawdowns
def c03():
    fig, ax = plt.subplots(figsize=(13.0, 4.6))
    for k, c, a in [(N, S1, 0.16), (Q, S2, 0.0), (S, S3, 0.0)]:
        d = dd(SER[k])
        ax.plot(DATES, d, color=c, lw=2.4 if k == N else 1.8)
        if a:
            ax.fill_between(DATES, 0, d, color=c, alpha=a)
    ax.axhline(0, color=INK3, lw=0.9)
    for k, c in [(N, S1), (Q, S2), (S, S3)]:
        d = dd(SER[k]); i = d.idxmin()
        ax.plot([i.to_timestamp(how="end")], [d.min()], "o", ms=9, color=c, mec=SURFACE, mew=2)
        ax.annotate(f"{k.split(' (')[0]}  {d.min()*100:,.1f}%",
                    xy=(i.to_timestamp(how="end"), d.min()), xytext=(6, -13 if k != Q else 4),
                    textcoords="offset points", color=c, fontsize=10.5, fontweight="bold")
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(-0.40, 0.045)
    frame(ax)
    ax.legend([Line2D([], [], color=S1, lw=2.4), Line2D([], [], color=S2, lw=1.8),
               Line2D([], [], color=S3, lw=1.8)],
              ["NDIF", "NASDAQ-100", "S&P 500"], loc="lower left", ncol=3)
    title(ax, "The fund fell less than its own benchmark",
          "Peak-to-trough drawdown from month-end closes")
    save(fig, "03_drawdown.png")

# ============================================================ 04 calendar returns
def c04():
    yrs = ANNUAL.index.astype(int)
    x = np.arange(len(yrs)); w = 0.26
    fig, ax = plt.subplots(figsize=(13.0, 4.6))
    for j, (k, c) in enumerate([(N, S1), (Q, S2), (S, S3)]):
        v = ANNUAL[k].values
        ax.bar(x + (j - 1) * w, v, w * 0.92, color=c, zorder=3)
        for xi, vi in zip(x + (j - 1) * w, v):
            ax.annotate(f"{vi*100:,.0f}", (xi, vi), textcoords="offset points",
                        xytext=(0, 5 if vi >= 0 else -14), ha="center",
                        fontsize=9.4, color=INK2, fontweight="bold")
    ax.axhline(0, color=INK2, lw=1.0)
    ax.set_xticks(x); ax.set_xticklabels(yrs)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(-0.42, 0.60)
    frame(ax)
    ax.legend([Patch(color=S1), Patch(color=S2), Patch(color=S3)],
              ["NDIF", "NASDAQ-100", "S&P 500"], loc="upper right", ncol=3)
    title(ax, "Beat the S&P 500 in five of six years",
          "Calendar-year total return (%)")
    save(fig, "04_annual_bars.png")

# ================================================================= 05 histogram
def c05():
    r = SER[N]
    st = RES["stats"][N]
    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    bins = np.arange(-0.14, 0.16, 0.01)
    ax.hist(r, bins=bins, color=S1, alpha=0.85, zorder=3, rwidth=0.9)
    xs = np.linspace(-0.15, 0.16, 400)
    ax.plot(xs, stats.norm.pdf(xs, r.mean(), r.std(ddof=1)) * len(r) * 0.01,
            color=INK2, lw=1.8, zorder=4)
    for v, lab, c in [(st["var95_hist"], "VaR 95%", S8), (st["cvar95_hist"], "CVaR 95%", "#8f1f22")]:
        ax.axvline(v, color=c, lw=1.8, zorder=5)
        ax.annotate(f"{lab}\n{v*100:,.1f}%", xy=(v, ax.get_ylim()[1] * 0.86),
                    xytext=(-6, 0), textcoords="offset points", color=c,
                    fontsize=10, fontweight="bold", ha="right")
    ax.axvline(r.mean(), color=S3, lw=1.8, zorder=5)
    ax.annotate(f"Mean\n{r.mean()*100:,.2f}%", xy=(r.mean(), ax.get_ylim()[1] * 0.86),
                xytext=(7, 0), textcoords="offset points", color=S3,
                fontsize=10, fontweight="bold")
    ax.xaxis.set_major_formatter(PCT)
    ax.set_ylabel("Months")
    frame(ax)
    ax.legend([Patch(color=S1), Line2D([], [], color=INK2, lw=1.8)],
              ["NDIF monthly returns", "Normal fit"], loc="upper left")
    title(ax, "Returns are close to normal, with a mild left tail",
          f"72 monthly observations · skew {st['skew']:.2f} · excess kurtosis {st['kurt']:.2f} · "
          f"Jarque–Bera p = {st['jb_p']:.2f} (normality not rejected)")
    save(fig, "05_histogram.png")

# ================================================================ 06 density plot
def c06():
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    xs = np.linspace(-0.22, 0.22, 500)
    for k, c in [(N, S1), (Q, S2), (S, S3)]:
        kde = stats.gaussian_kde(SER[k])
        ax.plot(xs, kde(xs), color=c, lw=2.3)
        ax.fill_between(xs, 0, kde(xs), color=c, alpha=0.07)
    ax.axvline(0, color=INK3, lw=0.9)
    ax.xaxis.set_major_formatter(PCT)
    ax.set_ylabel("Density"); ax.set_yticks([])
    frame(ax)
    ax.legend([Line2D([], [], color=S1, lw=2.3), Line2D([], [], color=S2, lw=2.3),
               Line2D([], [], color=S3, lw=2.3)], ["NDIF", "NASDAQ-100", "S&P 500"],
              loc="upper left")
    title(ax, "A tighter distribution than the NASDAQ-100",
          "Kernel density of monthly returns, 2017–2022")
    save(fig, "06_density.png")

# ==================================================================== 07 boxplot
def c07():
    keys = [N, Q, S, "60/40 (SPY/AGG)"]
    cols = [S1, S2, S3, S7]
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    bp = ax.boxplot([SER[k] for k in keys], vert=True, widths=0.45, patch_artist=True,
                    medianprops=dict(color=SURFACE, lw=2.2),
                    whiskerprops=dict(color=INK3, lw=1.2),
                    capprops=dict(color=INK3, lw=1.2),
                    flierprops=dict(marker="o", ms=6, mfc=INK3, mec="none", alpha=0.6))
    for p, c in zip(bp["boxes"], cols):
        p.set_facecolor(c); p.set_edgecolor("none"); p.set_alpha(0.9)
    for i, k in enumerate(keys, start=1):
        ax.plot([i], [SER[k].mean()], "D", ms=7, color=INK, mec=SURFACE, mew=1.5, zorder=5)
    ax.axhline(0, color=INK3, lw=0.9)
    ax.set_xticks(range(1, 5))
    ax.set_xticklabels(["NDIF", "NASDAQ-100", "S&P 500", "60/40"])
    ax.yaxis.set_major_formatter(PCT)
    frame(ax)
    ax.legend([Line2D([], [], marker="D", color="none", mfc=INK, ms=7)], ["Mean"],
              loc="lower right")
    title(ax, "Higher median, contained downside",
          "Distribution of monthly returns · box = interquartile range, line = median")
    save(fig, "07_box.png")

# =========================================================== 08 risk-return scatter
def c08():
    ss = RES["stock_stats"]; st = RES["stats"]
    fig, ax = plt.subplots(figsize=(11.4, 6.2))
    items = []
    for t in TICK:
        c = TIER_C[TIER[t]]
        r = np.sqrt(RES["weights_target"][t] * 3400 / np.pi)
        ax.scatter(ss[t]["vol"], ss[t]["cagr"], s=RES["weights_target"][t] * 3400,
                   color=c, alpha=0.82, edgecolor=SURFACE, linewidth=2, zorder=3)
        items.append(dict(x=ss[t]["vol"], y=ss[t]["cagr"], text=t, color=INK,
                          size=9.4, radius=r + 2, priority=RES["weights_target"][t]))
    for k, c, m, lab in [(N, S1, "*", "NDIF portfolio"), (Q, S2, "s", "NASDAQ-100"),
                         (S, S3, "s", "S&P 500")]:
        ax.scatter(st[k]["vol"], st[k]["cagr"], s=520 if m == "*" else 165, marker=m,
                   color=c, edgecolor=SURFACE, linewidth=2, zorder=6)
        items.append(dict(x=st[k]["vol"], y=st[k]["cagr"], text=lab, color=c,
                          size=11, radius=13, priority=10))
    ax.axhline(0, color=INK3, lw=0.9)
    ax.xaxis.set_major_formatter(PCT); ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel("Annualised volatility"); ax.set_ylabel("Annualised return (CAGR)")
    ax.set_xlim(0.13, 0.545); ax.set_ylim(-0.085, 0.315)
    frame(ax, xgrid=True)
    ax.legend([Line2D([], [], marker="o", color="none", mfc=S1, ms=11),
               Line2D([], [], marker="o", color="none", mfc=S2, ms=11),
               Line2D([], [], marker="o", color="none", mfc=S3, ms=11),
               Line2D([], [], marker="*", color="none", mfc=S1, ms=17),
               Line2D([], [], marker="s", color="none", mfc=S2, ms=10),
               Line2D([], [], marker="s", color="none", mfc=S3, ms=10)],
              ["Tier 1 — core engines", "Tier 2 — enablers", "Tier 3 — ballast",
               "NDIF portfolio", "NASDAQ-100", "S&P 500"],
              loc="lower left", ncol=2, columnspacing=1.6)
    title(ax, "Diversification did its job",
          "Risk vs return by holding, 2017–2022 · bubble area = target weight")
    place_labels(fig, ax, items)
    save(fig, "08_riskreturn.png")

# ============================================================ 09 correlation heatmap
def c09():
    C = STK.corr()
    fig, ax = plt.subplots(figsize=(8.6, 7.2))
    im = ax.imshow(C, cmap=BLUE_CMAP, vmin=0, vmax=1)
    ax.set_xticks(range(11)); ax.set_xticklabels(TICK, rotation=45, ha="right", fontsize=10)
    ax.set_yticks(range(11)); ax.set_yticklabels(TICK, fontsize=10)
    for i in range(11):
        for j in range(11):
            v = C.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8.6,
                    color=SURFACE if v > 0.62 else INK)
    ax.set_xticks(np.arange(-.5, 11, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 11, 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0); ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False, which="major")
    cb = fig.colorbar(im, ax=ax, fraction=0.036, pad=0.03)
    cb.set_label("Correlation of monthly returns", color=INK2, fontsize=10)
    cb.outline.set_visible(False); cb.ax.tick_params(length=0, labelsize=9.5)
    title(ax, "Genuine diversification inside the theme",
          f"Average pairwise correlation {(C.values[np.triu_indices(11,1)]).mean():.2f} · 2017–2022")
    save(fig, "09_corr.png")

# ============================================================ 10 seasonality heatmap
def c10():
    G = pd.DataFrame(RES["monthly_grid"]).astype(float)
    G.index = G.index.astype(int)
    G = G.sort_index()
    G.columns = [int(c) for c in G.columns]
    G = G[sorted(G.columns)]
    fig, ax = plt.subplots(figsize=(11.6, 4.6))
    vmax = np.nanmax(np.abs(G.values))
    im = ax.imshow(G.values, cmap=DIV_CMAP, norm=TwoSlopeNorm(0, -vmax, vmax), aspect="auto")
    ax.set_xticks(range(12))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                        "Sep", "Oct", "Nov", "Dec"], fontsize=10.5)
    ax.set_yticks(range(len(G))); ax.set_yticklabels(G.index, fontsize=11)
    for i in range(G.shape[0]):
        for j in range(12):
            v = G.values[i, j]
            ax.text(j, i, f"{v*100:,.1f}", ha="center", va="center", fontsize=9.2,
                    color=SURFACE if abs(v) > vmax * 0.55 else INK)
    ax.set_xticks(np.arange(-.5, 12, 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(G), 1), minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0); ax.tick_params(length=0)
    ax.grid(False, which="major")
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.015)
    cb.set_label("Monthly return", color=INK2, fontsize=10)
    cb.outline.set_visible(False)
    cb.ax.yaxis.set_major_formatter(PCT); cb.ax.tick_params(length=0, labelsize=9.5)
    title(ax, "Where the money was made and lost",
          "NDIF monthly return (%) by calendar month and year")
    save(fig, "10_seasonality.png")

# ============================================================= 11 month-of-year bar
def c11():
    ma = pd.DataFrame(RES["month_avg"])[N]
    ma.index = ma.index.astype(int)
    ma = ma.sort_index()
    cols = [S1 if v >= 0 else S8 for v in ma]
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    ax.bar(range(1, 13), ma.values, 0.62, color=cols, zorder=3)
    for i, v in zip(range(1, 13), ma.values):
        ax.annotate(f"{v*100:,.1f}%", (i, v), textcoords="offset points",
                    xytext=(0, 6 if v >= 0 else -16), ha="center", fontsize=9.6,
                    color=INK2, fontweight="bold")
    ax.axhline(0, color=INK2, lw=1.0)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                        "Sep", "Oct", "Nov", "Dec"])
    ax.yaxis.set_major_formatter(PCT1)
    ax.set_ylim(ma.min() * 1.55, ma.max() * 1.35)
    frame(ax)
    title(ax, "July was the fund's month; September its worst",
          "Average NDIF monthly return by calendar month, 2017–2022 · six observations per month")
    save(fig, "11_month_avg.png")

# =========================================================== 12 contribution bars
def c12():
    cs = pd.Series(RES["contrib"]).sort_values()
    fig, ax = plt.subplots(figsize=(11.2, 5.6))
    top3 = cs.nlargest(3).index; bot3 = cs.nsmallest(3).index
    cols = [S1 if t in top3 else (S2 if t in bot3 else "#b7d3f6") for t in cs.index]
    ax.barh(range(len(cs)), cs.values, 0.62, color=cols, zorder=3)
    for i, (t, v) in enumerate(cs.items()):
        ax.annotate(f"{v*100:,.1f} pts", (v, i), textcoords="offset points", xytext=(7, 0),
                    va="center", fontsize=10, color=INK2, fontweight="bold")
    ax.set_yticks(range(len(cs)))
    ax.set_yticklabels([f"{t}  ·  {COMPANY[t]}" for t in cs.index], fontsize=10.5)
    ax.xaxis.set_major_formatter(PCT)
    ax.set_xlim(0, cs.max() * 1.24)
    ax.set_xlabel("Contribution to the fund's 179.2% cumulative return")
    frame(ax, ygrid=False, xgrid=True)
    ax.legend([Patch(color=S1), Patch(color=S2)],
              ["Top 3 contributors", "Bottom 3 contributors"], loc="lower right")
    title(ax, "Microsoft alone delivered a quarter of the fund's return",
          "Compounded contribution to cumulative return by holding, 2017–2022")
    save(fig, "12_contribution.png")

# ================================================== 13 stock vs its sector benchmark
def c13():
    stot = pd.Series(RES["stock_total"]); etot = pd.Series(RES["etf_total"])
    order = stot.sort_values(ascending=False).index
    x = np.arange(len(order)); w = 0.38
    fig, ax = plt.subplots(figsize=(11.4, 5.4))
    ax.bar(x - w / 2, stot[order].values, w * 0.92, color=S1, zorder=3)
    ax.bar(x + w / 2, etot[order].values, w * 0.92, color=S2, zorder=3)
    for xi, t in zip(x, order):
        diff = stot[t] - etot[t]
        ax.annotate(f"{diff*100:+,.0f}", (xi, max(stot[t], etot[t])),
                    textcoords="offset points", xytext=(0, 7), ha="center",
                    fontsize=9.4, fontweight="bold", color=S1 if diff > 0 else S8)
    ax.axhline(0, color=INK2, lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{t}\n{GICS[t]}" for t in order], fontsize=9.2)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(-0.45, 3.8)
    frame(ax)
    ax.legend([Patch(color=S1), Patch(color=S2)],
              ["Our holding", "Its GICS sector ETF"], loc="upper right", ncol=2)
    title(ax, "Eight of eleven picks beat their own sector",
          "Cumulative total return 2017–2022 · labels show the stock's excess over its sector, in points")
    save(fig, "13_stock_vs_sector.png")

# ============================================================== 14 rolling 12m return
def c14():
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    for k, c, lw in [(N, S1, 2.4), (Q, S2, 1.8), (S, S3, 1.8)]:
        r12 = (1 + SER[k]).rolling(12).apply(np.prod, raw=True) - 1
        ax.plot(DATES, r12, color=c, lw=lw)
    ax.axhline(0, color=INK2, lw=1.0)
    ax.yaxis.set_major_formatter(PCT)
    frame(ax)
    ax.legend([Line2D([], [], color=S1, lw=2.4), Line2D([], [], color=S2, lw=1.8),
               Line2D([], [], color=S3, lw=1.8)], ["NDIF", "NASDAQ-100", "S&P 500"],
              loc="upper right", ncol=3)
    title(ax, "Rolling one-year returns",
          "Trailing 12-month total return · first observation Dec-2017")
    save(fig, "14_rolling12.png")

# ===================================================== 15/16 rolling alpha and beta
def roll_reg():
    y = SER[N] - ALLR["RF"]
    a, b = [], []
    for i in range(35, len(SER)):
        idx = SER.index[i - 35:i + 1]
        X = sm.add_constant(ALLR.loc[idx, ["Mkt-RF"]])
        f = sm.OLS(y.loc[idx], X).fit()
        a.append((1 + f.params["const"]) ** 12 - 1); b.append(f.params["Mkt-RF"])
    return pd.Series(a, index=SER.index[35:]), pd.Series(b, index=SER.index[35:])

def c15_16():
    a, b = roll_reg()
    d = a.index.to_timestamp(how="end")
    fig, ax = plt.subplots(figsize=(11.2, 4.6))
    ax.plot(d, a, color=S1, lw=2.4)
    ax.fill_between(d, 0, a, where=(a >= 0), color=S1, alpha=0.12)
    ax.fill_between(d, 0, a, where=(a < 0), color=S8, alpha=0.12)
    ax.axhline(0, color=INK2, lw=1.0)
    ax.yaxis.set_major_formatter(PCT)
    frame(ax)
    title(ax, "Alpha was persistent, not a single lucky year",
          "Rolling 36-month CAPM (Jensen's) alpha, annualised")
    save(fig, "15_rolling_alpha.png")

    fig, ax = plt.subplots(figsize=(11.2, 4.6))
    ax.plot(d, b, color=S7, lw=2.4)
    ax.axhline(1.0, color=INK3, lw=1.2)
    ax.annotate("Market beta = 1.0", xy=(d[1], 1.0), xytext=(0, 7),
                textcoords="offset points", color=INK3, fontsize=10)
    frame(ax)
    ax.set_ylim(0.85, 1.20)
    title(ax, "Beta stayed close to the market",
          "Rolling 36-month CAPM beta vs the Fama–French market factor")
    save(fig, "16_rolling_beta.png")

# ============================================================ 17 efficient frontier
def c17():
    ss = RES["stock_stats"]; st = RES["stats"]
    fig, ax = plt.subplots(figsize=(11.4, 6.2))
    # efficient branch only: from the minimum-variance point upward
    k_mv = int(FRONT["vol"].idxmin())
    EFF = FRONT.iloc[k_mv:]
    ax.plot(EFF["vol"], EFF["ret"], color=INK3, lw=1.8, zorder=2)
    items = []
    for t in TICK:
        ax.scatter(ss[t]["vol"], ss[t]["cagr"], s=46, color="#9ec5f4",
                   edgecolor=SURFACE, lw=1.4, zorder=3)
        items.append(dict(x=ss[t]["vol"], y=ss[t]["cagr"], text=t, color=INK3,
                          size=8.8, weight="normal", radius=6, priority=0))
    pts = [(N, "NDIF (as run)", S1, "*", 520),
           ("Equal weight (1/N)", "Equal weight 1/N", S3, "o", 165),
           ("MV optimised (ex-ante 2014-16)", "Mean–variance (2014–16 inputs)", S2, "D", 150),
           (Q, "NASDAQ-100", S7, "s", 150), (S, "S&P 500", S8, "s", 150)]
    for k, lab, c, m, s in pts:
        ax.scatter(st[k]["vol"], st[k]["cagr"], s=s, marker=m, color=c,
                   edgecolor=SURFACE, lw=2, zorder=6)
        items.append(dict(x=st[k]["vol"], y=st[k]["cagr"], text=lab, color=c,
                          size=10.5, radius=16, priority=10))
    items.append(dict(x=float(EFF["vol"].iloc[-1]), y=float(EFF["ret"].iloc[-1]),
                      text="Ex-post efficient frontier\n(same eleven stocks, long-only)",
                      color=INK3, size=10, weight="normal", radius=6, priority=6))
    ax.xaxis.set_major_formatter(PCT); ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel("Annualised volatility"); ax.set_ylabel("Annualised return")
    ax.set_xlim(0.12, 0.545); ax.set_ylim(-0.085, 0.315)
    frame(ax, xgrid=True)
    title(ax, "Close to efficient — and beaten only with hindsight",
          "Realised risk and return, 2017–2022, against the ex-post frontier of the same eleven stocks")
    place_labels(fig, ax, items)
    save(fig, "17_frontier.png")

# ============================================================== 18 factor loadings
def c18():
    reg = RES["reg"]["FF5"]
    facs = ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]
    labs = ["Market\n(Mkt-RF)", "Size\n(SMB)", "Value\n(HML)", "Profitability\n(RMW)", "Investment\n(CMA)"]
    vals = [reg[f] for f in facs]; ts = [reg[f + "_t"] for f in facs]
    cols = [S1 if abs(t) >= 1.96 else "#b7d3f6" for t in ts]
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    ax.bar(range(5), vals, 0.5, color=cols, zorder=3)
    for i, (v, t) in enumerate(zip(vals, ts)):
        star = "***" if abs(t) > 2.58 else ("**" if abs(t) > 1.96 else "")
        ax.annotate(f"{v:+.2f}{star}\nt = {t:,.1f}", (i, v), textcoords="offset points",
                    xytext=(0, 8 if v >= 0 else -30), ha="center", fontsize=10,
                    color=INK2, fontweight="bold")
    ax.axhline(0, color=INK2, lw=1.0)
    ax.set_xticks(range(5)); ax.set_xticklabels(labs, fontsize=10.5)
    ax.set_ylim(-0.45, 1.32)
    frame(ax)
    ax.legend([Patch(color=S1), Patch(color="#b7d3f6")],
              ["Statistically significant (|t| ≥ 1.96)", "Not significant"], loc="upper right")
    title(ax, "A large-cap growth fund with market beta of one",
          f"Fama–French five-factor loadings · R² = {reg['r2']:.2f} · "
          f"annualised alpha {reg['alpha_a']*100:,.1f}% (t = {reg['alpha_t']:,.2f})")
    save(fig, "18_factors.png")

# ================================================================ 19 up/down capture
def c19():
    st = RES["stats"]
    ks = [N, "Equal weight (1/N)", Q, "60/40 (SPY/AGG)"]
    labs = ["NDIF", "Equal weight", "NASDAQ-100", "60/40"]
    x = np.arange(len(ks)); w = 0.36
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    up = [st[k]["up_capture"] for k in ks]; dn = [st[k]["down_capture"] for k in ks]
    ax.bar(x - w / 2, up, w * 0.92, color=S1, zorder=3)
    ax.bar(x + w / 2, dn, w * 0.92, color=S2, zorder=3)
    for xi, u, d in zip(x, up, dn):
        ax.annotate(f"{u*100:,.0f}%", (xi - w / 2, u), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=10, color=INK2, fontweight="bold")
        ax.annotate(f"{d*100:,.0f}%", (xi + w / 2, d), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=10, color=INK2, fontweight="bold")
    ax.axhline(1.0, color=INK3, lw=1.2)
    ax.annotate("Market = 100%", xy=(x[-1] + 0.42, 1.0), xytext=(0, 6),
                textcoords="offset points", color=INK3, fontsize=9.6, ha="right")
    ax.set_xticks(x); ax.set_xticklabels(labs)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(0, 1.42)
    frame(ax)
    ax.legend([Patch(color=S1), Patch(color=S2)],
              ["Upside capture vs S&P 500", "Downside capture vs S&P 500"], loc="upper right")
    title(ax, "120% of the upside, 97% of the downside",
          "Geometric up/down capture against the S&P 500, 2017–2022")
    save(fig, "19_capture.png")

# ========================================================= 20 positive/negative months
def c20():
    st = RES["stats"]
    ks = [N, Q, S]; labs = ["NDIF", "NASDAQ-100", "S&P 500"]
    pos = [st[k]["n_pos"] for k in ks]; neg = [st[k]["n_neg"] for k in ks]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.8),
                                  gridspec_kw={"width_ratios": [1, 1], "wspace": 0.28})
    y = np.arange(3)
    ax.barh(y, pos, 0.5, color=S1, zorder=3)
    ax.barh(y, neg, 0.5, left=[p + 0.55 for p in pos], color=S8, zorder=3)
    for i, (p, n) in enumerate(zip(pos, neg)):
        ax.annotate(f"{p} up", (p / 2, i), ha="center", va="center", color=SURFACE,
                    fontsize=10.5, fontweight="bold")
        ax.annotate(f"{n} down", (p + n / 2, i), ha="center", va="center", color=SURFACE,
                    fontsize=10.5, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(labs); ax.invert_yaxis()
    ax.set_xlim(0, 74); ax.set_xlabel("Months out of 72")
    frame(ax, ygrid=False, xgrid=True)
    ax.set_title("Hit rate", loc="left", fontsize=13, fontweight="bold", color=INK, pad=10)

    ap = [st[k]["avg_pos"] for k in ks]; an = [st[k]["avg_neg"] for k in ks]
    x2 = np.arange(3); w = 0.36
    ax2.bar(x2 - w / 2, ap, w * 0.92, color=S1, zorder=3)
    ax2.bar(x2 + w / 2, an, w * 0.92, color=S8, zorder=3)
    for xi, a_, b_ in zip(x2, ap, an):
        ax2.annotate(f"{a_*100:,.1f}%", (xi - w / 2, a_), textcoords="offset points",
                     xytext=(0, 5), ha="center", fontsize=9.6, color=INK2, fontweight="bold")
        ax2.annotate(f"{b_*100:,.1f}%", (xi + w / 2, b_), textcoords="offset points",
                     xytext=(0, -15), ha="center", fontsize=9.6, color=INK2, fontweight="bold")
    ax2.axhline(0, color=INK2, lw=1.0)
    ax2.set_xticks(x2); ax2.set_xticklabels(labs)
    ax2.yaxis.set_major_formatter(PCT1); ax2.set_ylim(-0.085, 0.075)
    frame(ax2)
    ax2.set_title("Average up month vs average down month", loc="left", fontsize=13,
                  fontweight="bold", color=INK, pad=10)
    fig.suptitle("NDIF was positive in 50 of 72 months", x=0.005, y=1.035, ha="left",
                 fontsize=15.5, fontweight="bold", color=INK)
    save(fig, "20_posneg.png")

# ================================================================ 21 weight drift
def c21():
    """Weights stacked by conviction tier — three hues, not eleven."""
    tiers = {1: ["MSFT", "GOOGL", "AMZN"], 2: ["V", "EQIX", "ILMN", "ROK"],
             3: ["NEE", "COST", "ALB", "SLB"]}
    labs = ["Tier 1 — core engines", "Tier 2 — enablers", "Tier 3 — ballast"]
    cols = [S1, S2, S3]
    cum = (1 + STK).cumprod()
    w0 = pd.Series(RES["weights_target"])
    drift = (cum * w0).div((cum * w0).sum(axis=1), axis=0)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 4.9), sharey=True,
                                 gridspec_kw={"wspace": 0.06})
    for a, src, ttl in [(a1, drift, "Left to drift (no rebalancing)"),
                        (a2, WP, "As run (quarterly rebalancing)")]:
        bands = [src[tiers[t]].sum(axis=1) for t in (1, 2, 3)]
        a.stackplot(DATES, bands, colors=cols, edgecolor=SURFACE, lw=1.6)
        base = 0
        tgt = {1: 0.42, 2: 0.34, 3: 0.24}
        for ti, (b, lab, c) in enumerate(zip(bands, labs, cols), start=1):
            mid = base + b.iloc[len(b) // 2] / 2
            a.annotate(f"{lab}\ntarget {tgt[ti]*100:,.0f}%",
                       xy=(DATES[len(DATES) // 2], mid), ha="center", va="center",
                       color=SURFACE, fontsize=9.8, fontweight="bold", linespacing=1.4)
            base += b.iloc[len(b) // 2]
        a.set_ylim(0, 1); a.set_xlim(DATES[0], DATES[-1])
        a.yaxis.set_major_formatter(PCT)
        a.set_title(ttl, loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=8)
        frame(a); a.grid(False)
    fig.suptitle("Rebalancing kept the mandate honest", x=0.005, y=1.10, ha="left",
                 fontsize=15.5, fontweight="bold", color=INK)
    fig.text(0.005, 1.035, "Weight by conviction tier · left to drift, Tier 1 would have reached 48% of the book "
             "by end-2022; quarterly rebalancing held it near its 42% target", ha="left", fontsize=11, color=INK2)
    save(fig, "21_weight_drift.png")

# =================================================================== 22 VaR / CVaR
def c22():
    st = RES["stats"]
    ks = [N, Q, S, "60/40 (SPY/AGG)"]
    labs = ["NDIF", "NASDAQ-100", "S&P 500", "60/40"]
    metrics = [("var95_hist", "VaR 95% (historical)", S1),
               ("cvar95_hist", "CVaR 95% (expected shortfall)", S2),
               ("var99_hist", "VaR 99% (historical)", S3)]
    x = np.arange(len(ks)); w = 0.26
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    for j, (m, lab, c) in enumerate(metrics):
        v = [st[k][m] for k in ks]
        ax.bar(x + (j - 1) * w, v, w * 0.92, color=c, zorder=3)
        for xi, vi in zip(x + (j - 1) * w, v):
            ax.annotate(f"{vi*100:,.1f}", (xi, vi), textcoords="offset points",
                        xytext=(0, -15), ha="center", fontsize=9.4, color=INK2,
                        fontweight="bold")
    ax.axhline(0, color=INK2, lw=1.0)
    ax.set_xticks(x); ax.set_xticklabels(labs)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(-0.155, 0.012)
    frame(ax)
    ax.legend([Patch(color=c) for _, _, c in metrics], [l for _, l, _ in metrics],
              loc="lower left", ncol=1)
    title(ax, "Tail risk below the NASDAQ-100 on every measure",
          "One-month value-at-risk and expected shortfall, from the empirical distribution of 72 monthly returns")
    save(fig, "22_var.png")

# ======================================================= 23 cumulative excess return
def c23():
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    for k, c, lab in [(Q, S2, "vs NASDAQ-100"), (S, S3, "vs S&P 500")]:
        ex = (1 + SER[N]).cumprod() / (1 + SER[k]).cumprod() - 1
        ax.plot(DATES, ex, color=c, lw=2.3)
        endlabel(ax, DATES[-1], ex.iloc[-1], f"  {lab}\n  {ex.iloc[-1]*100:+,.0f} pts", c, fs=10.5)
    ax.axhline(0, color=INK2, lw=1.0)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_xlim(DATES[0], DATES[-1] + pd.Timedelta(days=430))
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2017, 2024)])
    ax.set_xticklabels(range(2017, 2024))
    frame(ax)
    title(ax, "The value-add compounded quietly, then paid off in 2022",
          "Cumulative relative performance of NDIF (ratio of wealth indices, rebased to zero)")
    save(fig, "23_relative.png")

# ================================================================= 24 the 2022 test
def c24():
    y22 = SER.loc["2022"]
    s22 = STK.loc["2022"]
    tot = {"NDIF": (1 + y22[N]).prod() - 1, "NASDAQ-100": (1 + y22[Q]).prod() - 1,
           "S&P 500": (1 + y22[S]).prod() - 1}
    st = pd.Series({t: (1 + s22[t]).prod() - 1 for t in TICK}).sort_values()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.6, 5.0),
                                 gridspec_kw={"width_ratios": [0.85, 1.15], "wspace": 0.3})
    ks = list(tot); vs = [tot[k] for k in ks]
    a1.bar(range(3), vs, 0.5, color=[S1, S2, S3], zorder=3)
    for i, v in enumerate(vs):
        a1.annotate(f"{v*100:,.1f}%", (i, v), textcoords="offset points", xytext=(0, -17),
                    ha="center", fontsize=11, color=INK2, fontweight="bold")
    a1.axhline(0, color=INK2, lw=1.0)
    a1.set_xticks(range(3)); a1.set_xticklabels(ks, fontsize=10.5)
    a1.yaxis.set_major_formatter(PCT); a1.set_ylim(-0.40, 0.03)
    frame(a1)
    a1.set_title("2022 total return", loc="left", fontsize=12.5, fontweight="bold",
                 color=INK, pad=8)
    cols = [S8 if v < 0 else S1 for v in st.values]
    a2.barh(range(len(st)), st.values, 0.6, color=cols, zorder=3)
    for i, (t, v) in enumerate(st.items()):
        inside = v < -0.13
        a2.annotate(f"{v*100:,.0f}%", (v, i), textcoords="offset points",
                    xytext=(8, 0) if v >= 0 or inside else (-8, 0), va="center",
                    ha="left" if (v >= 0 or inside) else "right",
                    fontsize=9.8, color=SURFACE if inside else INK2, fontweight="bold")
    a2.set_yticks(range(len(st))); a2.set_yticklabels(st.index, fontsize=10)
    a2.axvline(0, color=INK2, lw=1.0)
    a2.xaxis.set_major_formatter(PCT); a2.set_xlim(-0.62, 0.86)
    a2.set_xticks([-0.6, -0.4, -0.2, 0, 0.2, 0.4, 0.6])
    frame(a2, ygrid=False, xgrid=True)
    a2.set_title("2022 by holding — the ballast earned its place", loc="left",
                 fontsize=12.5, fontweight="bold", color=INK, pad=8)
    fig.suptitle("The 2022 stress test: down 22.5% against a NASDAQ down 32.6%",
                 x=0.005, y=1.04, ha="left", fontsize=15.5, fontweight="bold", color=INK)
    save(fig, "24_2022.png")

# ============================================================ 25 scenario realisation
def c25():
    fig, ax = plt.subplots(figsize=(13.0, 4.6))
    yrs = [2017, 2018, 2019, 2020, 2021, 2022]
    act = ANNUAL[N].values
    fc = [0.18, 0.18, 0.09, 0.18, 0.18, -0.04]           # ex-ante scenario labels
    lab = ["A", "A", "B", "A", "A", "C"]
    x = np.arange(6); w = 0.36
    ax.bar(x - w / 2, fc, w * 0.92, color="#b7d3f6", zorder=3)
    ax.bar(x + w / 2, act, w * 0.92, color=S1, zorder=3)
    for xi, f, a in zip(x, fc, act):
        ax.annotate(f"{f*100:,.0f}%", (xi - w / 2, f), textcoords="offset points",
                    xytext=(0, 6 if f >= 0 else -16), ha="center", fontsize=9.4,
                    color=INK2)
        ax.annotate(f"{a*100:,.0f}%", (xi + w / 2, a), textcoords="offset points",
                    xytext=(0, 6 if a >= 0 else -16), ha="center", fontsize=9.8,
                    color=INK2, fontweight="bold")
    ax.axhline(0, color=INK2, lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{y}\nScenario {l}" for y, l in zip(yrs, lab)], fontsize=10.5)
    ax.yaxis.set_major_formatter(PCT); ax.set_ylim(-0.34, 0.52)
    frame(ax)
    ax.legend([Patch(color="#b7d3f6"), Patch(color=S1)],
              ["2016 scenario return assumption", "Realised NDIF return"],
              loc="upper right", ncol=2)
    title(ax, "The scenarios were right about direction, conservative about size",
          "Ex-ante illustrative return for the scenario that actually occurred, versus what the fund delivered")
    save(fig, "25_scenario.png")

# ================================================================ 26 sector exposure
def c26():
    w0 = pd.Series(RES["weights_target"])
    order = ["MSFT", "GOOGL", "AMZN", "V", "EQIX", "ILMN", "ROK", "NEE", "COST", "ALB", "SLB"]
    cols = [S1, S1, S1, S2, S2, S2, S2, S3, S3, S3, S3]
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    wed, _ = ax.pie([w0[t] for t in order], colors=cols, startangle=90,
                    counterclock=False, wedgeprops=dict(width=0.42, edgecolor=SURFACE, lw=2.4))
    for wg, t in zip(wed, order):
        ang = np.deg2rad((wg.theta1 + wg.theta2) / 2)
        ax.annotate(f"{t}\n{w0[t]*100:,.0f}%", xy=(0.79 * np.cos(ang), 0.79 * np.sin(ang)),
                    ha="center", va="center", fontsize=9.6, color=INK, fontweight="bold")
    ax.text(0, 0.09, "11", ha="center", va="center", fontsize=34, fontweight="bold", color=INK)
    ax.text(0, -0.14, "GICS sectors\none holding each", ha="center", va="center",
            fontsize=10.5, color=INK2)
    ax.set_aspect("equal"); ax.axis("off")
    ax.legend([Patch(color=S1), Patch(color=S2), Patch(color=S3)],
              ["Tier 1 — core engines (42%)", "Tier 2 — enablers (34%)", "Tier 3 — ballast (24%)"],
              loc="lower center", ncol=1, bbox_to_anchor=(0.5, -0.11))
    ax.set_title("Target weights by conviction tier", loc="left", fontsize=15.5,
                 fontweight="bold", color=INK, pad=16)
    save(fig, "26_weights_donut.png")

# =================================================== 27 strategy variants comparison
def c27():
    ks = [(N, S1, 2.6), ("MV optimised (ex-ante 2014-16)", S2, 2.0),
          ("Equal weight (1/N)", S3, 2.0), ("NDIF (buy & hold)", S7, 2.0)]
    fig, ax = plt.subplots(figsize=(11.2, 5.4))
    ents = []
    for k, c, lw in ks:
        w = wealth(SER[k])
        ax.plot(DATES, w, color=c, lw=lw)
        short = {"NDIF": "NDIF (as run)", "MV optimised (ex-ante 2014-16)": "Mean–variance",
                 "Equal weight (1/N)": "Equal weight", "NDIF (buy & hold)": "Buy & hold"}[k]
        ents.append((w.iloc[-1], f"{short}   ${w.iloc[-1]/1e6:,.0f}m", c))
    ax.set_ylim(90e6, 395e6)
    ax.yaxis.set_major_formatter(USD)
    ax.set_xlim(DATES[0], DATES[-1] + pd.Timedelta(days=880))
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2017, 2024)])
    ax.set_xticklabels(range(2017, 2024))
    frame(ax)
    title(ax, "Would a model have done better? Marginally — and only on paper",
          "Growth of $100m under four construction rules, same eleven stocks")
    end_labels(ax, DATES[-1], ents, x_text=DATES[-1] + pd.Timedelta(days=150),
               min_gap_frac=0.075)
    save(fig, "27_variants.png")

# ==================================================================== 28 COVID test
def c28():
    idx = pd.period_range("2020-01", "2020-12", freq="M")
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    for k, c, lw in [(N, S1, 2.6), (Q, S2, 2.0), (S, S3, 2.0)]:
        w = (1 + SER.loc[idx, k]).cumprod() - 1
        ax.plot(idx.to_timestamp(how="end"), w, color=c, lw=lw, marker="o", ms=6,
                mec=SURFACE, mew=1.6)
        endlabel(ax, idx.to_timestamp(how="end")[-1], w.iloc[-1],
                 f"  {k.split(' (')[0]}\n  {w.iloc[-1]*100:+,.0f}%", c, fs=10)
    ax.axhline(0, color=INK2, lw=1.0)
    ax.axvspan(pd.Timestamp("2020-02-01"), pd.Timestamp("2020-03-31"),
               color=S8, alpha=0.07, zorder=1)
    ax.annotate("COVID-19 crash\nFeb–Mar 2020", xy=(pd.Timestamp("2020-03-01"), -0.16),
                ha="center", fontsize=10, color=INK2)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_xlim(pd.Timestamp("2020-01-01"), pd.Timestamp("2021-04-15"))
    frame(ax)
    title(ax, "Scenario C arrived in March 2020 — and the fund recovered by July",
          "Cumulative return through calendar 2020")
    save(fig, "28_covid.png")

# ================================================================= 29 metric radar
def c29():
    st = RES["stats"]
    labs = ["Return\n(CAGR)", "Sharpe", "Sortino", "Calmar", "Drawdown\nresilience",
            "Tail safety\n(1/|CVaR|)"]
    def vec(k):
        s = st[k]
        return np.array([s["cagr"], s["sharpe"], s["sortino"], s["calmar"],
                         1 / abs(s["max_dd"]), 1 / abs(s["cvar95_hist"])])
    V = {k: vec(k) for k in [N, Q, S]}
    M = np.vstack(list(V.values()))
    Vn = {k: v / M.max(axis=0) for k, v in V.items()}
    ang = np.linspace(0, 2 * np.pi, len(labs), endpoint=False).tolist()
    ang += ang[:1]
    fig, ax = plt.subplots(figsize=(7.6, 6.6), subplot_kw=dict(polar=True))
    for (k, v), c in zip(Vn.items(), [S1, S2, S3]):
        vv = v.tolist() + [v[0]]
        ax.plot(ang, vv, color=c, lw=2.2)
        ax.fill(ang, vv, color=c, alpha=0.10)
    ax.set_xticks(ang[:-1]); ax.set_xticklabels(labs, fontsize=10.5, color=INK2)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0]); ax.set_yticklabels([])
    ax.set_ylim(0, 1.08)
    ax.spines["polar"].set_color(GRID)
    ax.grid(color=GRID, lw=0.9)
    ax.set_facecolor(SURFACE)
    ax.legend([Line2D([], [], color=S1, lw=2.2), Line2D([], [], color=S2, lw=2.2),
               Line2D([], [], color=S3, lw=2.2)], ["NDIF", "NASDAQ-100", "S&P 500"],
              loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.14))
    fig.suptitle("Best on five of six risk-adjusted measures", x=0.02, y=1.06,
                 ha="left", fontsize=15.5, fontweight="bold", color=INK)
    fig.text(0.02, 1.005, "Each axis scaled to the best of the three · larger is better on every spoke",
             fontsize=11, color=INK2)
    save(fig, "29_radar.png")

# ============================================================= 30 rolling volatility
def c30():
    fig, ax = plt.subplots(figsize=(11.2, 4.6))
    for k, c, lw in [(N, S1, 2.4), (Q, S2, 1.8), (S, S3, 1.8)]:
        v = SER[k].rolling(12).std(ddof=1) * np.sqrt(12)
        ax.plot(DATES, v, color=c, lw=lw)
    ax.yaxis.set_major_formatter(PCT)
    frame(ax)
    ax.legend([Line2D([], [], color=S1, lw=2.4), Line2D([], [], color=S2, lw=1.8),
               Line2D([], [], color=S3, lw=1.8)], ["NDIF", "NASDAQ-100", "S&P 500"],
              loc="upper left", ncol=3)
    title(ax, "Volatility ran below the benchmark through the 2022 repricing",
          "Rolling 12-month annualised standard deviation of monthly returns")
    save(fig, "30_rolling_vol.png")

# ============================================================== 31 attribution bars
def c31():
    a = RES["attrib"]
    labs = ["Sector allocation\n(which sectors we tilted to)",
            "Security selection\n(the stocks we picked)",
            "Interaction"]
    vals = [a["allocation"], a["selection"], a["interaction"]]
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    cols = [S2, S1, S3]
    ax.bar(range(3), vals, 0.46, color=cols, zorder=3)
    for i, v in enumerate(vals):
        ax.annotate(f"{v*100:+,.1f} pts", (i, v), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=12, color=INK2, fontweight="bold")
    ax.axhline(0, color=INK2, lw=1.0)
    ax.set_xticks(range(3)); ax.set_xticklabels(labs, fontsize=10.5)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_ylim(0, 0.50)
    frame(ax)
    title(ax, "94% of the value-add came from stock picking, not sector bets",
          "Brinson–Fachler decomposition of active return against an equal-weight sector-ETF benchmark, "
          "summed over 72 months")
    save(fig, "31_attribution.png")

# ================================================================= 32 stock spaghetti
def c32():
    fig, ax = plt.subplots(figsize=(11.4, 5.6))
    cum = (1 + STK).cumprod()
    focus = {"MSFT": S1, "SLB": S8, "ILMN": S2, "NEE": S3}
    items = []
    for t in TICK:
        if t in focus:
            continue
        ax.plot(DATES, cum[t], color="#d5d4cf", lw=1.4, zorder=2)
        items.append(dict(x=DATES[-1], y=cum[t].iloc[-1], text=t, color=INK3,
                          size=9, weight="normal", radius=2, priority=0))
    for t, c in focus.items():
        ax.plot(DATES, cum[t], color=c, lw=2.6, zorder=4)
        items.append(dict(x=DATES[-1], y=cum[t].iloc[-1],
                          text=f"{t}  {(cum[t].iloc[-1]-1)*100:+,.0f}%", color=c,
                          size=10.5, radius=2, priority=10))
    ax.axhline(1.0, color=INK3, lw=0.9)
    ax.set_xlim(DATES[0], DATES[-1] + pd.Timedelta(days=700))
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2017, 2024)])
    ax.set_xticklabels(range(2017, 2024))
    ax.set_ylabel("Growth of $1")
    frame(ax)
    title(ax, "The dispersion inside an eleven-stock book",
          "Cumulative growth of $1 per holding, Jan 2017 – Dec 2022")
    place_labels(fig, ax, items)
    save(fig, "32_spaghetti.png")

# ================================================================= 33 fee waterfall
def c33():
    gross = RES["stats"][N]["cagr"]
    mgmt = 0.009
    hurdle = RES["stats"][Q]["cagr"]
    excess = max(gross - mgmt - hurdle, 0)
    perf = 0.10 * excess
    net = gross - mgmt - perf
    steps = [("Gross return", gross, S1), ("Management fee\n0.90%", -mgmt, S2),
             ("Performance fee\n10% over hurdle", -perf, S2), ("Net to investors", net, S3)]
    fig, ax = plt.subplots(figsize=(11.2, 5.0))
    run = 0
    for i, (lab, v, c) in enumerate(steps):
        if lab in ("Gross return", "Net to investors"):
            ax.bar(i, v, 0.5, color=c, zorder=3)
            ax.annotate(f"{v*100:,.2f}%", (i, v), textcoords="offset points", xytext=(0, 7),
                        ha="center", fontsize=11.5, color=INK2, fontweight="bold")
            run = v if lab == "Gross return" else run
        else:
            ax.bar(i, v, 0.5, bottom=run, color=c, zorder=3)
            ax.annotate(f"{v*100:,.2f}%", (i, run + v), textcoords="offset points",
                        xytext=(0, -17), ha="center", fontsize=11, color=INK2,
                        fontweight="bold")
            ax.plot([i - 0.25, i + 0.25], [run, run], color=INK3, lw=0.9)
            run += v
    ax.set_xticks(range(4)); ax.set_xticklabels([st_[0] for st_ in steps], fontsize=10.5)
    ax.yaxis.set_major_formatter(PCT); ax.set_ylim(0, 0.215)
    frame(ax)
    title(ax, f"After fees, investors kept {net*100:,.1f}% a year",
          f"Annualised gross-to-net bridge · hurdle = NASDAQ-100 at {hurdle*100:,.1f}% p.a., high-water mark applied")
    save(fig, "33_fees.png")
    return net

# ====================================================================== run them all
if __name__ == "__main__":
    for f in [c01, c02, c03, c04, c05, c06, c07, c08, c09, c10, c11, c12, c13,
              c14, c15_16, c17, c18, c19, c20, c21, c22, c23, c24, c25, c26,
              c27, c28, c29, c30, c31, c32, c33]:
        f()
    print("done")
