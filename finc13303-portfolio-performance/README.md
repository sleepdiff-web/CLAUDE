# FINC13-303 Assignment 2, Part 1 — Portfolio performance presentation

Northpoint Digital Innovation Fund (NDIF) — six-year performance review, January 2017 – December 2022.
Callum O'Connor · Student ID 14053836 · Bond University.

Everything here is generated from real market data by the scripts in `code/`. No figure in the deck
was written by hand.

## Deliverables

| File | What it is |
|---|---|
| `deliverables/FINC13303_Ass2_PortfolioPerformance_14053836_OConnor.pptx` | The presentation — 49 slides (37 main body + 12 appendix), 16:9, speaker notes on every slide |
| `deliverables/FINC13303_Ass2_PortfolioPerformance_14053836_OConnor.pdf` | The same deck as PDF (the mandatory slide submission) |
| `deliverables/FINC13303_Ass2_PresenterScript_14053836_OConnor.docx` | The speaker notes as a presenter script, with pacing and delivery guidance |
| `deliverables/FINC13303_Ass2_PerformanceWorkbook_14053836_OConnor.xlsx` | 11-sheet workbook: every table behind the deck plus the raw 72-month return series (the mandatory Excel/code submission) |

## Headline results

| Measure | NDIF | NASDAQ-100 | S&P 500 |
|---|---|---|---|
| Cumulative return | **+179.2%** | +134.7% | +90.0% |
| Annualised (CAGR) | **18.66%** | 15.28% | 11.29% |
| Annualised volatility | 19.06% | 20.21% | 17.09% |
| Sharpe ratio | **0.94** | 0.75 | 0.65 |
| Sortino ratio | **1.51** | 1.18 | 0.98 |
| Maximum drawdown | −24.9% | −32.6% | −23.9% |
| Beta vs S&P 500 | 1.04 | 1.10 | 1.00 |
| Information ratio | **0.98** | 0.54 | — |
| Terminal value on $100m | **$279.2m** | $234.7m | $190.0m |

Jensen's alpha, Fama–French five-factor: **+6.63% p.a., t = 3.06, p = 0.002** (Newey–West, 4 lags).
The same test applied to the NASDAQ-100 gives +2.4% p.a. with t = 1.41, which is not significant.
Brinson–Fachler attribution puts **94% of the active return in security selection** rather than
sector allocation. Nine of the eleven holdings beat their own GICS sector over the six years.

## Verification

`code/audit.py` is an independent check on the finished presentation. It opens the built `.pptx`,
recomputes the return, risk and regression figures from the monthly series without reference to
`results.json`, and asserts that every headline claim matches. It also scans every slide and table
for one-decimal percentages and fails if any of them cannot be traced to a computed value.

```
$ python audit.py
  distinct 1-dp percentages on slides: 140
  not traceable to a computed value:   0
  RESULT: 77 checks passed, 0 failed
```

Spot-checks against published index returns agree to within 4 basis points (SPY 2017–2022 by year,
QQQ 2017/2019/2022, MSFT and AMZN 2022).

One data treatment is worth stating plainly. XLC, the Communication Services sector ETF, did not
exist until June 2018, so its standalone six-year return covers only part of the sample. The
Communication Services sleeve is therefore spliced with XLK before that date, both in the
Brinson attribution and in the stock-versus-sector comparison, and the splice is disclosed on the
chart itself.

## Method

- **Portfolio** — the eleven target weights from the Assignment 1 mandate, drifting within each
  quarter and restored to target at every calendar quarter-end (24 rebalances).
- **Returns** — monthly total returns from dividend- and split-adjusted closing prices,
  72 observations per series.
- **Benchmarks** — NASDAQ-100 and S&P 500 total return, proxied by QQQ and SPY so that dividends are
  included; the raw `^NDX` and `^GSPC` index series are price-only and would flatter the fund.
- **Sector benchmarks** — the eleven SPDR GICS sector ETFs. XLC launched in June 2018, so XLK stands
  in for the Communication Services sleeve before that date.
- **Risk-free rate and factors** — Kenneth R. French Data Library (Mkt-RF, SMB, HML, RMW, CMA, MOM,
  RF), monthly US research series.
- **Regressions** — OLS with Newey–West HAC standard errors, four lags.
- **Optimisation** — SLSQP, long-only, maximum Sharpe, 25% position bound. The ex-ante case uses
  January 2014 – December 2016 as its in-sample window, so it only sees information a manager had at
  launch.
- **Excluded** — transaction costs, market impact, taxes and cash drag.

## Reproducing

```bash
pip install -r requirements-analysis.txt
cd code
python fetch_data.py     # downloads prices; writes prices_daily.csv + returns_monthly.csv
python analysis.py       # metrics, regressions, attribution -> results.json + tables/
python charts.py         # 33 charts -> charts/
python deck.py           # the .pptx (slide text and speaker notes both live here)
python workbook.py       # the .xlsx
python notes_doc.py      # the presenter script .docx
python audit.py          # re-checks every figure in the built deck against the data
```

## Design

The deck uses an editorial system rather than a stock presentation template: bone paper
(`#F6F3EC`), warm near-black ink, a deep pine field for the title and section pages, hairline rules
in place of boxes, and a narrow left rail carrying the folio and section marker. Headlines are set
in Georgia, body and data in Corbel; both ship with Office on Windows and macOS, so the file opens
as designed without embedding fonts. Chart titles live on the slide rather than inside the image,
so each headline is set once.

The categorical palette — pine-teal `#00736A`, terracotta `#C4551A`, violet `#8A6DAF`, ochre
`#9A6A00`, indigo `#4F6FB5`, oxblood `#8F2F1D` — was chosen by searching candidate hues against a
colour-vision-deficiency validator on this surface. The selected ordering clears every gate with no
contrast relief required: worst adjacent pair ΔE 10.0 under simulated CVD and 20.3 under normal
vision. Sequential encodings use a single-hue teal ramp; diverging encodings run teal to terracotta
through a warm neutral midpoint. Oxblood is reserved for losses and is never used as a series
identity.

## Note on scope

This covers **Part 1 only** — the portfolio performance presentation. Parts 2 (Investing for the
future) and 3 (Investopedia simulator report) are separate Word/PDF deliverables and are not in this
directory.

## Generative AI declaration

This assessment is classified AI-Supported. Generative AI was used to write the analysis code,
produce the visualisations, structure the deck and draft the speaker notes. The analytical scope,
the choice of benchmarks and factor models, the interpretation of results and the investment
recommendation are the author's. All market data was retrieved programmatically from primary
sources; every figure traces to a reproducible calculation. The presentation is delivered by the
author. A full declaration appears on slide A11 of the deck.
