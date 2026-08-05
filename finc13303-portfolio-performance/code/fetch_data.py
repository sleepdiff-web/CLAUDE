"""Download daily adjusted closes from Yahoo chart API -> monthly total returns."""
import json, os, time, urllib.request, ssl
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)          # repository sub-directory root
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

HOLDINGS = ["MSFT","GOOGL","AMZN","V","EQIX","ILMN","ROK","NEE","COST","ALB","SLB"]
BENCH    = ["^GSPC","^NDX","^IXIC","^DJI","^RUT","^VIX"]
SECTORS  = ["XLK","XLC","XLY","XLF","XLRE","XLV","XLI","XLU","XLP","XLB","XLE","QQQ","SPY","AGG","TLT","GLD"]
ALL = HOLDINGS + BENCH + SECTORS

P1 = int(pd.Timestamp("2010-12-01").timestamp())
P2 = int(pd.Timestamp("2023-01-15").timestamp())

def fetch(sym):
    url = (f"https://query2.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}"
           f"?period1={P1}&period2={P2}&interval=1d&events=div%2Csplit&includeAdjustedClose=true")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                j = json.loads(r.read().decode())
            res = j["chart"]["result"][0]
            ts = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert("America/New_York").normalize().tz_localize(None)
            ind = res["indicators"]
            if "adjclose" in ind:
                px = ind["adjclose"][0]["adjclose"]
            else:
                px = ind["quote"][0]["close"]
            s = pd.Series(px, index=ts, name=sym).astype(float)
            s = s[~s.index.duplicated(keep="last")].dropna()
            return s
        except Exception as e:
            print(f"  retry {sym} ({attempt+1}): {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed {sym}")

frames = {}
for sym in ALL:
    s = fetch(sym)
    frames[sym] = s
    print(f"{sym:8s} {s.index.min().date()} -> {s.index.max().date()}  n={len(s)}")
    time.sleep(0.6)

px = pd.DataFrame(frames).sort_index()
px.to_csv(os.path.join(DATA, "prices_daily.csv"))

# month-end
mpx = px.resample("ME").last()
mret = mpx.pct_change()
mret.to_csv(os.path.join(DATA, "returns_monthly.csv"))
print("\nMonthly returns 2017-2022 coverage:")
print(mret.loc["2017":"2022"].notna().sum())
