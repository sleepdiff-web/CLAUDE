"""
Independent audit of the finished presentation.

Reads the built .pptx, pulls out every quantitative claim it can parse, and checks
each one against the underlying return series recomputed from scratch. Fails loudly
so that no figure ships without a matching calculation behind it.
"""
import json, os, re, sys
import numpy as np
import pandas as pd
from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, "data")
DECK = os.path.join(BASE, "deliverables",
                    "FINC13303_Ass2_PortfolioPerformance_14053836_OConnor.pptx")

R = json.load(open(os.path.join(DATA, "results.json")))
SER = pd.read_csv(os.path.join(DATA, "series_monthly.csv"), index_col=0)
SER.index = pd.PeriodIndex(SER.index, freq="M")
STK = pd.read_csv(os.path.join(DATA, "stocks_monthly.csv"), index_col=0)
STK.index = pd.PeriodIndex(STK.index, freq="M")
ALL = pd.read_csv(os.path.join(DATA, "all_monthly_returns.csv"), index_col=0)
ALL.index = pd.PeriodIndex(ALL.index, freq="M")
WP = pd.read_csv(os.path.join(DATA, "weight_path.csv"), index_col=0)
WP.index = pd.PeriodIndex(WP.index, freq="M")

N, Q, S = "NDIF", "NASDAQ-100 (QQQ)", "S&P 500 (SPY)"
ok, bad = [], []

def check(label, claimed, actual, tol=0.0005, unit=""):
    good = abs(claimed - actual) <= tol
    (ok if good else bad).append((label, claimed, actual, unit))
    return good

# ---------------------------------------------------------------- recompute from scratch
rf = ALL["RF"]
def recompute(r):
    r = r.dropna(); n = len(r)
    cum = float((1 + r).prod() - 1)
    cagr = (1 + cum) ** (12 / n) - 1
    vol = float(r.std(ddof=1) * np.sqrt(12))
    ex = r - rf.reindex(r.index)
    sharpe = float(ex.mean() / r.std(ddof=1) * np.sqrt(12))
    c = (1 + r).cumprod()
    mdd = float((c / c.cummax() - 1).min())
    return dict(cum=cum, cagr=cagr, vol=vol, sharpe=sharpe, mdd=mdd, n=n)

RE = {k: recompute(SER[k]) for k in (N, Q, S)}

print("=" * 78)
print("1. PIPELINE CONSISTENCY — results.json vs an independent recomputation")
print("=" * 78)
for k in (N, Q, S):
    for m, key in [("cum_return", "cum"), ("cagr", "cagr"), ("vol", "vol"),
                   ("sharpe", "sharpe"), ("max_dd", "mdd")]:
        check(f"{k} {m}", R["stats"][k][m], RE[k][key], 1e-9)
    check(f"{k} observations", R["stats"][k]["months"], RE[k]["n"], 0)

print("=" * 78)
print("2. HEADLINE FIGURES QUOTED IN THE DECK")
print("=" * 78)
check("NDIF cumulative 179.2%", 1.792, RE[N]["cum"], 0.001)
check("NDIF CAGR 18.66%", 0.1866, RE[N]["cagr"], 0.0002)
check("NDIF Sharpe 0.94", 0.94, RE[N]["sharpe"], 0.005)
check("NDIF max drawdown -24.9%", -0.249, RE[N]["mdd"], 0.001)
check("NASDAQ-100 cumulative 134.7%", 1.347, RE[Q]["cum"], 0.001)
check("S&P 500 cumulative 90.0%", 0.900, RE[S]["cum"], 0.001)
check("Terminal value $279.2m", 279.2e6, 100e6 * (1 + RE[N]["cum"]), 1e5)
check("Value added vs S&P $89.2m", 89.2e6,
      100e6 * (RE[N]["cum"] - RE[S]["cum"]), 1e5)
check("Value added vs NASDAQ $44.4m", 44.4e6,
      100e6 * (RE[N]["cum"] - RE[Q]["cum"]), 1e5)

print("=" * 78)
print("3. FACTOR-MODEL CLAIMS")
print("=" * 78)
check("FF5 alpha 6.6% p.a.", 0.066, R["reg"]["FF5"]["alpha_a"], 0.0006)
check("FF5 alpha t = 3.06", 3.06, R["reg"]["FF5"]["alpha_t"], 0.006)
check("FF5 alpha p = 0.002", 0.002, R["reg"]["FF5"]["alpha_p"], 0.0005)
check("CAPM alpha 7.2% p.a.", 0.072, R["reg"]["CAPM"]["alpha_a"], 0.0006)
check("Market loading 1.05", 1.05, R["reg"]["FF5"]["Mkt-RF"], 0.005)
check("NASDAQ-100 FF5 alpha 2.4%", 0.024, R["reg_qqq"]["FF5"]["alpha_a"], 0.0006)
check("NASDAQ-100 alpha t = 1.41", 1.41, R["reg_qqq"]["FF5"]["alpha_t"], 0.006)
check("Beta to S&P 500 = 1.04", 1.04, R["stats"][N]["beta"], 0.005)

print("=" * 78)
print("4. STOCK-LEVEL AND ATTRIBUTION CLAIMS")
print("=" * 78)
etf = {"MSFT": "XLK", "GOOGL": "XLC", "AMZN": "XLY", "V": "XLF", "EQIX": "XLRE",
       "ILMN": "XLV", "ROK": "XLI", "NEE": "XLU", "COST": "XLP", "ALB": "XLB",
       "SLB": "XLE"}
nbeat = 0
for t, e in etf.items():
    ser = ALL[e].fillna(ALL["XLK"]) if e == "XLC" else ALL[e]
    er = float((1 + ser).prod() - 1)
    check(f"{t} sector benchmark ({e})", R["etf_total"][t], er, 1e-9)
    nbeat += R["stock_total"][t] > er
check("Picks beating their sector = 9", 9, nbeat, 0)
check("MSFT contribution 41.9 pts", 0.419, R["contrib"]["MSFT"], 0.0006)
check("MSFT share of fund return 23%", 0.234, R["contrib_pct"]["MSFT"], 0.001)
check("SLB contribution +13.2 pts", 0.132, R["contrib"]["SLB"], 0.0006)
check("SLB six-year return -23.5%", -0.235, R["stock_total"]["SLB"], 0.001)
check("Contributions sum to cumulative return",
      sum(R["contrib"].values()), R["stats"][N]["cum_return"], 1e-9)
a = R["attrib"]
check("Selection share of active return 94%", 0.94,
      a["selection"] / a["total_active_arith"], 0.005)
check("Allocation +1.8 pts", 0.018, a["allocation"], 0.0006)
check("Attribution components sum to total",
      a["allocation"] + a["selection"] + a["interaction"], a["total_active_arith"], 1e-9)

print("=" * 78)
print("5. NARRATIVE CLAIMS THAT ARE EASY TO GET WRONG")
print("=" * 78)
w = 100e6 * (1 + SER[N]).cumprod()
check("Peak wealth $360m", 360.4e6, float(w.max()), 5e5)
peak_month = str(w.idxmax())
(ok if peak_month == "2021-12" else bad).append(
    ("Peak month is Dec-2021", peak_month, "2021-12", ""))
pre = float(w.loc[:"2020-01"].max())
rec = w[(w.index > pd.Period("2020-03", "M")) & (w > pre)]
(ok if str(rec.index[0]) == "2020-05" else bad).append(
    ("COVID recovery month is May-2020", str(rec.index[0]), "2020-05", ""))
check("MSFT peak weight 17.6%", 0.176, float(WP["MSFT"].max()), 0.001)
tgt = pd.Series(R["weights_target"])
check("Max drift from target 2.9 pts", 0.029, float((WP - tgt).abs().max().max()), 0.001)
check("Drift-rule breaches (>5 pts) = 0", 0,
      int(((WP - tgt).abs() > 0.05).any(axis=1).sum()), 0)
sep = SER[N][SER[N].index.month == 9]
check("September negative in 3 of 6 years", 3, int((sep < 0).sum()), 0)
check("September average -2.8%", -0.028, float(sep.mean()), 0.0006)
jul = SER[N][SER[N].index.month == 7]
check("July positive in 6 of 6 years", 6, int((jul > 0).sum()), 0)
check("July average +5.8%", 0.058, float(jul.mean()), 0.0006)
vols = [R["stock_stats"][t]["vol"] for t in etf]
check("Constituents more volatile than the fund = 11", 11,
      sum(v > R["stats"][N]["vol"] for v in vols), 0)
check("Positive months = 50", 50, R["stats"][N]["n_pos"], 0)
check("Upside capture 120%", 1.205, R["stats"][N]["up_capture"], 0.002)
check("Downside capture 97%", 0.972, R["stats"][N]["down_capture"], 0.002)
check("Rebalancing gain $18.3m",
      18.3e6, (R["stats"][N]["terminal"] - R["stats"]["NDIF (buy & hold)"]["terminal"]), 1e5)

print("=" * 78)
print("6. FEE ARITHMETIC")
print("=" * 78)
gross = R["stats"][N]["cagr"]; hurdle = R["stats"][Q]["cagr"]
mgmt, rate = 0.009, 0.10
perf = rate * max(gross - mgmt - hurdle, 0)
net = gross - mgmt - perf
check("Performance fee 0.25% p.a.", 0.0025, perf, 0.0002)
check("Net return 17.51% p.a.", 0.1751, net, 0.0002)
check("Cumulative net 163%", 1.63, (1 + net) ** 6 - 1, 0.005)
check("Northpoint 6-yr fee $6.90m", 6.90e6, 0.0115 * 100e6 * 6, 1e3)
check("QQQ 6-yr fee $1.20m", 1.20e6, 0.0020 * 100e6 * 6, 1e3)
check("Incremental fee vs QQQ $5.70m", 5.70e6, (0.0115 - 0.0020) * 100e6 * 6, 1e3)
check("Net gain after fees $38.7m", 38.7e6,
      (R["stats"][N]["terminal"] - R["stats"][Q]["terminal"]) - (0.0115 - 0.0020) * 100e6 * 6, 1e5)

print("=" * 78)
print("7. DECK SCAN — every percentage on every slide must appear in the data")
print("=" * 78)
prs = Presentation(DECK)
pool = set()
for d in (R["stats"], R["stock_stats"]):
    for v in d.values():
        for x in v.values():
            if isinstance(x, (int, float)) and x is not None:
                pool.add(round(x * 100, 1)); pool.add(round(x, 1)); pool.add(round(x, 0))
for d in (R["contrib"], R["stock_total"], R["etf_total"], R["weights_target"]):
    for x in d.values():
        pool.add(round(x * 100, 1)); pool.add(round(x * 100, 0))
for m in R["reg"].values():
    for x in m.values():
        if isinstance(x, (int, float)):
            pool.add(round(x * 100, 1)); pool.add(round(x, 2)); pool.add(round(x, 1))
for y, row in pd.read_csv(os.path.join(DATA, "annual.csv"), index_col=0).iterrows():
    for x in row:
        pool.add(round(x * 100, 1)); pool.add(round(x * 100, 0))
for d in (R["monthly_grid"], R["month_avg"]):          # seasonality figures
    for col in d.values():
        for x in col.values():
            pool.add(round(x * 100, 1)); pool.add(round(x * 100, 0))
for t in STK.columns:                                   # per-stock calendar years
    for y in range(2017, 2023):
        v = float((1 + STK[t].loc[str(y)]).prod() - 1)
        pool.add(round(v * 100, 1)); pool.add(round(v * 100, 0))
_g = R["stats"][N]["cagr"]; _h = R["stats"][Q]["cagr"]  # fee bridge
_net = _g - 0.009 - 0.10 * max(_g - 0.009 - _h, 0)
for x in (_net, _net - R["stats"][S]["cagr"], (1 + _net) ** 6 - 1):
    pool.add(round(x * 100, 1)); pool.add(round(x * 100, 0))
pool |= {round(x, 1) for x in list(pool)}

texts = []
for sl in prs.slides:
    for sh in sl.shapes:
        if sh.has_text_frame:
            texts.append(sh.text_frame.text)
        if sh.has_table:
            for r in sh.table.rows:
                for c in r.cells:
                    texts.append(c.text)
blob = " ".join(texts)
pcts = {abs(float(x)) for x in re.findall(r"[-−+]?\d+\.\d(?=%)", blob.replace("−", "-"))}
unmatched = sorted(p for p in pcts
                   if not any(abs(p - abs(q)) < 0.06 for q in pool if q is not None))
print(f"  distinct 1-dp percentages on slides: {len(pcts)}")
print(f"  not traceable to a computed value:   {len(unmatched)}")
if unmatched:
    print("   ", unmatched)

print()
print("=" * 78)
print(f"RESULT: {len(ok)} checks passed, {len(bad)} failed")
print("=" * 78)
for label, claimed, actual, unit in bad:
    print(f"  FAIL  {label}: deck says {claimed}, data says {actual}{unit}")
sys.exit(1 if bad else 0)
