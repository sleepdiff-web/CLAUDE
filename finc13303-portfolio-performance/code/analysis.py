"""
Northpoint Digital Innovation Fund (NDIF)
Six-year performance analytics, Jan 2017 - Dec 2022.

Inputs : returns_monthly.csv (Yahoo adjusted-close monthly total returns)
         ff5.zip / mom.zip   (Ken French Data Library)
Outputs: results.json, tables/*.csv, charts/*.png
"""
import io, json, os, warnings, zipfile
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats, optimize

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)          # repository sub-directory root
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)
os.makedirs(os.path.join(BASE, "charts"), exist_ok=True)

START, END = "2017-01-01", "2022-12-31"
FUND_AUM = 100_000_000

TICKERS = ["MSFT", "GOOGL", "AMZN", "V", "EQIX", "ILMN", "ROK", "NEE", "COST", "ALB", "SLB"]
WEIGHTS = pd.Series({"MSFT": .16, "GOOGL": .14, "AMZN": .12, "V": .10, "EQIX": .09,
                     "ILMN": .08, "ROK": .07, "NEE": .07, "COST": .06, "ALB": .06, "SLB": .05})
TIER = {"MSFT": 1, "GOOGL": 1, "AMZN": 1, "V": 2, "EQIX": 2, "ILMN": 2, "ROK": 2,
        "NEE": 3, "COST": 3, "ALB": 3, "SLB": 3}
COMPANY = {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon", "V": "Visa",
           "EQIX": "Equinix", "ILMN": "Illumina", "ROK": "Rockwell Automation",
           "NEE": "NextEra Energy", "COST": "Costco", "ALB": "Albemarle", "SLB": "SLB"}
GICS = {"MSFT": "Information Technology", "GOOGL": "Communication Services",
        "AMZN": "Consumer Discretionary", "V": "Financials", "EQIX": "Real Estate",
        "ILMN": "Health Care", "ROK": "Industrials", "NEE": "Utilities",
        "COST": "Consumer Staples", "ALB": "Materials", "SLB": "Energy"}
SECTOR_ETF = {"MSFT": "XLK", "GOOGL": "XLC", "AMZN": "XLY", "V": "XLF", "EQIX": "XLRE",
              "ILMN": "XLV", "ROK": "XLI", "NEE": "XLU", "COST": "XLP", "ALB": "XLB", "SLB": "XLE"}

# ----------------------------------------------------------------------------- data
raw = pd.read_csv(os.path.join(DATA, "returns_monthly.csv"), index_col=0, parse_dates=True)
raw.index = raw.index.to_period("M")

def ff_frame(zip_name, csv_name):
    txt = zipfile.ZipFile(os.path.join(DATA, zip_name)).read(csv_name).decode("latin1")
    rows, started = [], False
    for line in txt.splitlines():
        p = [x.strip() for x in line.split(",")]
        if len(p) < 2:
            if started:
                break
            continue
        if p[0].isdigit() and len(p[0]) == 6:
            started = True
            rows.append(p)
        elif started:
            break
        elif not p[0] and any(p[1:]):
            header = p
    df = pd.DataFrame(rows).set_index(0)
    df.index = pd.PeriodIndex(df.index, freq="M")
    df.columns = header[1:len(df.columns) + 1]
    return df.astype(float) / 100.0

ff5 = ff_frame("ff5.zip", "F-F_Research_Data_5_Factors_2x3.csv")
mom = ff_frame("mom.zip", "F-F_Momentum_Factor.csv")
mom.columns = ["MOM"]
FF = ff5.join(mom, how="left")

full = raw.join(FF, how="left")
R = full.loc[START:END]                       # 72 monthly observations
RF = R["RF"]
periods = R.index

# ------------------------------------------------------------------- portfolio build
def rebalanced(returns, w0, freq="Q"):
    """Drift within period, snap back to target at each period end."""
    w0 = w0.reindex(returns.columns).fillna(0.0)
    out, wpath = [], []
    w = w0.copy()
    for t in returns.index:
        r = returns.loc[t]
        wpath.append(w.copy())
        out.append(float((w * r).sum()))
        w = w * (1 + r)
        w = w / w.sum()
        if freq == "Q" and t.month % 3 == 0:
            w = w0.copy()
        elif freq == "M":
            w = w0.copy()
    return pd.Series(out, index=returns.index), pd.DataFrame(wpath, index=returns.index)

STK = R[TICKERS]
ndif, wpath = rebalanced(STK, WEIGHTS, "Q")
bh, wpath_bh = rebalanced(STK, WEIGHTS, None)
ew, _ = rebalanced(STK, pd.Series(1 / 11, index=TICKERS), "Q")

# mean-variance in-sample on the three years to Dec-2016 -> out-of-sample 2017-22
hist = raw.loc["2014-01":"2016-12", TICKERS]

def mv_weights(rets, rf_a=0.005, wmax=0.25, target="sharpe"):
    mu = rets.mean() * 12
    S = rets.cov() * 12
    n = len(mu)
    def neg_sharpe(w):
        return -((w @ mu - rf_a) / np.sqrt(w @ S @ w))
    def var(w):
        return w @ S @ w
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    bnds = [(0.0, wmax)] * n
    f = neg_sharpe if target == "sharpe" else var
    res = optimize.minimize(f, np.repeat(1 / n, n), bounds=bnds, constraints=cons,
                            method="SLSQP", options={"maxiter": 2000, "ftol": 1e-12})
    return pd.Series(res.x, index=mu.index).clip(lower=0).pipe(lambda s: s / s.sum())

W_MV = mv_weights(hist)                                   # ex-ante (honest, out-of-sample)
W_MV_IS = mv_weights(R[TICKERS])                          # ex-post perfect-foresight bound
mv, _ = rebalanced(STK, W_MV, "Q")
mv_is, _ = rebalanced(STK, W_MV_IS, "Q")

SER = pd.DataFrame({
    "NDIF": ndif,
    "NDIF (buy & hold)": bh,
    "Equal weight (1/N)": ew,
    "MV optimised (ex-ante 2014-16)": mv,
    "MV optimised (perfect foresight)": mv_is,
    "NASDAQ-100 (QQQ)": R["QQQ"],
    "S&P 500 (SPY)": R["SPY"],
    "60/40 (SPY/AGG)": 0.6 * R["SPY"] + 0.4 * R["AGG"],
})
BENCH_N, BENCH_S = "NASDAQ-100 (QQQ)", "S&P 500 (SPY)"

# ------------------------------------------------------------------------- analytics
def dd_series(r):
    return (1 + r).cumprod() / (1 + r).cumprod().cummax() - 1

def metrics(r, bench=None, rf=RF):
    r = r.dropna()
    n = len(r)
    ex = r - rf.reindex(r.index)
    cum = (1 + r).prod() - 1
    cagr = (1 + cum) ** (12 / n) - 1
    vol = r.std(ddof=1) * np.sqrt(12)
    dn = r[r < 0]
    dsd = np.sqrt((np.minimum(r - 0, 0) ** 2).mean()) * np.sqrt(12)
    dd = dd_series(r)
    mdd = dd.min()
    # drawdown duration (months from peak to recovery of worst episode)
    peak_idx = dd[dd == 0].index
    sharpe = ex.mean() / r.std(ddof=1) * np.sqrt(12)
    sortino = (r.mean() * 12 - rf.reindex(r.index).mean() * 12) / dsd if dsd > 0 else np.nan
    m = dict(
        months=n, cum_return=cum, cagr=cagr, vol=vol,
        best=r.max(), worst=r.min(), mean_m=r.mean(), median_m=r.median(),
        skew=stats.skew(r, bias=False), kurt=stats.kurtosis(r, fisher=True, bias=False),
        jb_p=stats.jarque_bera(r)[1],
        hit=(r > 0).mean(), n_pos=int((r > 0).sum()), n_neg=int((r < 0).sum()),
        avg_pos=r[r > 0].mean(), avg_neg=r[r < 0].mean(),
        downside_dev=dsd, max_dd=mdd,
        sharpe=sharpe, sortino=sortino,
        calmar=cagr / abs(mdd) if mdd else np.nan,
        var95_hist=np.percentile(r, 5), cvar95_hist=r[r <= np.percentile(r, 5)].mean(),
        var99_hist=np.percentile(r, 1), cvar99_hist=r[r <= np.percentile(r, 1)].mean(),
        var95_param=r.mean() + stats.norm.ppf(0.05) * r.std(ddof=1),
        terminal=FUND_AUM * (1 + cum),
    )
    z = stats.norm.ppf(0.05); S, K = m["skew"], m["kurt"]
    zcf = z + (z**2 - 1) * S / 6 + (z**3 - 3 * z) * K / 24 - (2 * z**3 - 5 * z) * S**2 / 36
    m["var95_cf"] = r.mean() + zcf * r.std(ddof=1)
    if bench is not None:
        b = bench.reindex(r.index)
        cov = np.cov(r, b, ddof=1)
        m["beta"] = cov[0, 1] / cov[1, 1]
        m["corr"] = np.corrcoef(r, b)[0, 1]
        m["treynor"] = (ex.mean() * 12) / m["beta"]
        te = (r - b).std(ddof=1) * np.sqrt(12)
        m["te"] = te
        m["info_ratio"] = ((r - b).mean() * 12) / te
        bm = b.std(ddof=1) * np.sqrt(12)
        m["m2"] = rf.mean() * 12 + m["sharpe"] * bm
        up, dnm = b > 0, b < 0
        m["up_capture"] = ((1 + r[up]).prod() ** (1 / up.sum()) - 1) / ((1 + b[up]).prod() ** (1 / up.sum()) - 1)
        m["down_capture"] = ((1 + r[dnm]).prod() ** (1 / dnm.sum()) - 1) / ((1 + b[dnm]).prod() ** (1 / dnm.sum()) - 1)
    return m

STATS = {k: metrics(SER[k], SER[BENCH_S]) for k in SER.columns}
STOCK_STATS = {t: metrics(STK[t], SER[BENCH_S]) for t in TICKERS}

# ------------------------------------------------------------------------ regressions
def factor_reg(r, model="CAPM"):
    y = (r - RF.reindex(r.index)).dropna()
    cols = {"CAPM": ["Mkt-RF"], "FF3": ["Mkt-RF", "SMB", "HML"],
            "FF5": ["Mkt-RF", "SMB", "HML", "RMW", "CMA"],
            "FF6": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "MOM"]}[model]
    X = sm.add_constant(R[cols].reindex(y.index))
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    out = {"model": model, "n": int(fit.nobs), "r2": fit.rsquared, "r2adj": fit.rsquared_adj,
           "alpha_m": fit.params["const"], "alpha_a": (1 + fit.params["const"]) ** 12 - 1,
           "alpha_t": fit.tvalues["const"], "alpha_p": fit.pvalues["const"]}
    for c in cols:
        out[c] = fit.params[c]; out[c + "_t"] = fit.tvalues[c]; out[c + "_p"] = fit.pvalues[c]
    return out

REG = {m: factor_reg(SER["NDIF"], m) for m in ["CAPM", "FF3", "FF5", "FF6"]}
REG_QQQ = {m: factor_reg(SER[BENCH_N], m) for m in ["CAPM", "FF5"]}
REG_STOCK = {t: factor_reg(STK[t], "CAPM") for t in TICKERS}
REG_STOCK5 = {t: factor_reg(STK[t], "FF5") for t in TICKERS}

# rolling 36-month CAPM alpha
roll_alpha, roll_beta = [], []
for i in range(35, len(SER)):
    w = SER["NDIF"].iloc[i - 35:i + 1]
    rr = factor_reg(w, "CAPM")
    roll_alpha.append(rr["alpha_a"]); roll_beta.append(rr["Mkt-RF"])
ROLL = pd.DataFrame({"alpha": roll_alpha, "beta": roll_beta}, index=SER.index[35:])

# ------------------------------------------------------------------ contribution/attrib
# geometric contribution: sum of w_t * r_t compounded through the path
contrib = pd.DataFrame({t: wpath[t] * STK[t] for t in TICKERS}, index=periods)
growth = (1 + SER["NDIF"]).cumprod().shift(1).fillna(1.0)
CONTRIB = (contrib.mul(growth, axis=0)).sum()          # $ contribution per $1 invested
CONTRIB_PCT = CONTRIB / CONTRIB.sum()

stock_total = (1 + STK).prod() - 1
etf_total = pd.Series({t: (1 + R[SECTOR_ETF[t]].dropna()).prod() - 1 for t in TICKERS})
etf_start = {t: R[SECTOR_ETF[t]].dropna().index[0] for t in TICKERS}

# Brinson-Fachler vs equal-weight sector-ETF benchmark (11 sectors, 1/11 each)
bench_w = pd.Series(1 / 11, index=TICKERS)
sect_r = pd.DataFrame({t: R[SECTOR_ETF[t]] for t in TICKERS}).reindex(periods)
sect_r["GOOGL"] = sect_r["GOOGL"].fillna(R["XLK"])      # XLC only from Jun-2018
bench_ret = (sect_r * bench_w).sum(axis=1)
alloc = ((wpath - bench_w) * (sect_r.sub(bench_ret, axis=0))).sum().sum()
selec = (bench_w * (STK - sect_r)).sum().sum()
inter = ((wpath - bench_w) * (STK - sect_r)).sum().sum()
ATTRIB = {"allocation": alloc, "selection": selec, "interaction": inter,
          "total_active_arith": alloc + selec + inter,
          "portfolio_arith": SER["NDIF"].sum(), "benchmark_arith": bench_ret.sum(),
          "sector_bench_cum": (1 + bench_ret).prod() - 1}

# -------------------------------------------------------------------------- seasonality
ANNUAL = SER.groupby(SER.index.year).apply(lambda g: (1 + g).prod() - 1)
ANNUAL.index.name = "year"
MONTHLY_GRID = pd.DataFrame(
    {y: SER["NDIF"][SER.index.year == y].values for y in range(2017, 2023)},
    index=range(1, 13)).T
MONTH_AVG = SER.groupby(SER.index.month).mean()
QTR = SER.groupby((SER.index.month - 1) // 3 + 1).apply(lambda g: (1 + g).prod() ** (1 / len(g)) - 1)

# ------------------------------------------------------------------- efficient frontier
mu_a = STK.mean() * 12
S_a = STK.cov() * 12
def frontier(n=60):
    tgts = np.linspace(mu_a.min(), mu_a.max(), n)
    pts = []
    for tg in tgts:
        cons = [{"type": "eq", "fun": lambda w: w.sum() - 1},
                {"type": "eq", "fun": lambda w, tg=tg: w @ mu_a - tg}]
        res = optimize.minimize(lambda w: w @ S_a @ w, np.repeat(1 / 11, 11),
                                bounds=[(0, 1)] * 11, constraints=cons, method="SLSQP")
        if res.success:
            pts.append((np.sqrt(res.fun), tg))
    return pd.DataFrame(pts, columns=["vol", "ret"])
FRONTIER = frontier()

# ------------------------------------------------------------------------------ output
def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, (np.floating, float)): return None if pd.isna(o) else float(o)
    if isinstance(o, (np.integer, int)): return int(o)
    return o

results = clean({
    "stats": STATS, "stock_stats": STOCK_STATS, "reg": REG, "reg_qqq": REG_QQQ,
    "reg_stock_capm": REG_STOCK, "reg_stock_ff5": REG_STOCK5,
    "contrib": CONTRIB.to_dict(), "contrib_pct": CONTRIB_PCT.to_dict(),
    "stock_total": stock_total.to_dict(), "etf_total": etf_total.to_dict(),
    "attrib": ATTRIB,
    "weights_target": WEIGHTS.to_dict(), "weights_mv": W_MV.to_dict(),
    "weights_mv_is": W_MV_IS.to_dict(),
    "annual": ANNUAL.to_dict(), "month_avg": MONTH_AVG.to_dict(),
    "monthly_grid": MONTHLY_GRID.to_dict(),
    "final_weights": wpath_bh.iloc[-1].to_dict(),
})
json.dump(results, open(os.path.join(DATA, "results.json"), "w"), indent=1)

SER.to_csv(os.path.join(DATA, "series_monthly.csv"))
STK.to_csv(os.path.join(DATA, "stocks_monthly.csv"))
wpath.to_csv(os.path.join(DATA, "weight_path.csv"))
pd.DataFrame(STATS).T.to_csv(os.path.join(DATA, "stats.csv"))
pd.DataFrame(STOCK_STATS).T.to_csv(os.path.join(DATA, "stock_stats.csv"))
pd.DataFrame(REG).T.to_csv(os.path.join(DATA, "regressions.csv"))
ANNUAL.to_csv(os.path.join(DATA, "annual.csv"))
FRONTIER.to_csv(os.path.join(DATA, "frontier.csv"), index=False)
R.to_csv(os.path.join(DATA, "all_monthly_returns.csv"))

# ---------------------------------------------------------------------------- console
pd.set_option("display.width", 200, "display.float_format", lambda x: f"{x:,.4f}")
print("\n=== HEADLINE ===")
hd = pd.DataFrame(STATS).T[["cum_return", "cagr", "vol", "sharpe", "sortino", "max_dd",
                            "beta", "info_ratio", "terminal"]]
print(hd)
print("\n=== NDIF DETAIL ===")
for k, v in STATS["NDIF"].items(): print(f"  {k:18s} {v}")
print("\n=== REGRESSIONS (NDIF) ===")
print(pd.DataFrame(REG).T)
print("\n=== ANNUAL ===")
print(ANNUAL.T)
print("\n=== CONTRIBUTION ===")
print(pd.DataFrame({"contrib_$per$1": CONTRIB, "share": CONTRIB_PCT,
                    "stock_total_ret": stock_total, "sector_etf_ret": etf_total}).sort_values("contrib_$per$1", ascending=False))
print("\n=== ATTRIBUTION ===", ATTRIB)
print("\n=== MV WEIGHTS (ex-ante) ===\n", W_MV.round(4))
print("\n=== STOCK STATS ===")
print(pd.DataFrame(STOCK_STATS).T[["cagr", "vol", "sharpe", "max_dd", "beta"]])
