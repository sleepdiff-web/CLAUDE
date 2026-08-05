"""Replace the deck's speaker notes with a version that fits a 25-minute delivery."""
import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)          # repository sub-directory root
DATA = os.path.join(BASE, "data")
NEW = [
# 0 — title
"""
Good morning, afternoon or evening, depending on where you're joining me from. I'm Callum
O'Connor, Portfolio Manager of the Northpoint Digital Innovation Fund.

Six years ago you gave this fund a hundred million dollars and one instruction: own the winners of
digital transformation across the whole economy, and do it with discipline. Today I'm closing the
book on that mandate.

The headline is on the right of your screen. That hundred million is now two hundred and
seventy-nine million — a hundred and seventy-nine per cent cumulative, or eighteen point seven per
cent a year, through a trade war, a pandemic, the fastest bear market in history, and the sharpest
rate shock in forty years.

Over the next twenty-five minutes I'll show you where that money came from, how much risk we took
to get it, whether it was skill or simply a rising market, and what I think you should do next.
""",
# 1 — agenda
"""
Six sections.

Where we started — the mandate, and whether we stuck to it. The economy — three regimes in six
years, and an honest mark against the scenarios we published in 2016. What the fund returned, and
how it behaved in the two moments that mattered. How much risk we took. Then the section I care
most about: was any of this skill? And finally the verdict, the fees, and my recommendation.

Questions at the end. There's a full appendix behind the deck with the workings.
""",
# 2 — exec summary
"""
The whole six years on one slide.

Top left: a hundred and seventy-nine per cent cumulative. The S&P 500 returned ninety over the same
window; the NASDAQ-100, our primary benchmark and the harder test, returned a hundred and
thirty-five. Annualised, eighteen point seven per cent against a target of eight to ten.

But look at the second row as much as the first. A Sharpe ratio of nought point nine four — the
highest of every comparator I tested. A maximum drawdown of minus twenty-four point nine per cent,
shallower than the NASDAQ-100's thirty-two point six. We didn't simply take more risk to get more
return.

And the number I'd draw your attention to above all: six point six per cent annualised alpha on a
five-factor model, t-statistic three point zero six. The probability that's luck is about two in a
thousand — with a beta of one, so it wasn't leverage either.

I'll earn every one of those claims.
""",
# 3 — mandate
"""
This is the contract, unedited, because the first test of a manager isn't performance — it's
whether the thing you bought is the thing you got.

An active, high-conviction thematic equity fund. The theme: digital transformation. Eleven
holdings, one per GICS sector — a pure technology fund would have been an easier story to sell, but
it would have failed the diversification requirement, and as you'll see, it would have hurt badly
in 2022.

Two hard constraints on the weights: a five per cent floor in every sector, and a sixteen per cent
cap on the largest position. Quarterly rebalancing with a five-point drift threshold.

And the target: eight to ten per cent net a year. Hold that number — I'm going to mark ourselves
against it at the end.
""",
# 4 — sectors donut
"""
The book, coloured by conviction tier.

Tier one: forty-two per cent in three platform companies where several parts of the thesis compound
at once. Microsoft at sixteen per cent was our largest position and our highest-conviction idea.

Tier two, thirty-four per cent: the enablers. Each monetises digitisation through one channel —
Visa is payments, Equinix is data centres, Illumina is genomics, Rockwell is factory automation.

Tier three, twenty-four per cent: ballast.

Now, the fourth point is the one I'd ask you to remember. For five of these six years, holding
Schlumberger at five per cent looked like a tax on the portfolio. I was asked repeatedly why we
didn't just drop the sector. We didn't, because the mandate said every sector keeps a floor. In
2022 that discipline is exactly what saved us.
""",
# 5 — rebalancing
"""
A short detour on process, because this is where funds quietly drift from their mandate.

On the left: what would have happened if we'd bought the eleven stocks and never touched them. Tier
one would have grown from forty-two per cent of the book to forty-eight, with Microsoft alone at
twenty-five per cent. You'd have ended up owning a concentrated mega-cap technology fund that no
longer resembled the mandate you signed.

On the right: what we actually did.

And look at the table. Rebalancing wasn't governance theatre — it was worth eighteen million
dollars. Two seventy-nine versus two sixty-one. One point three points a year of extra return, a
higher Sharpe, and a drawdown three points shallower — because rebalancing systematically trimmed
winners at highs and topped up laggards at lows.
""",
# 6 — events
"""
The whole six years in one line.

We opened in January 2017 with the Dow crossing twenty thousand. Through 2017 the fund returned
forty per cent, driven by the December tax reform and by cloud adoption accelerating exactly as
we'd argued.

2018 was our first hard year — the trade war escalated and the fourth quarter was brutal. We lost
nine point six per cent in October and nine point eight in December, and still finished up three
point seven while the S&P fell four and a half.

2019 was the recovery on the Fed's pivot to cutting. Then March 2020, which I'll come back to.

The peak is November 2021 at three hundred and sixty-one million dollars. That's also the month the
rate regime turned, and 2022 gave a chunk of it back.
""",
# 7 — macro
"""
Some economic narrative, because you're not paying me to read a line chart to you.

The first three years were broadly the world we said we expected — moderate growth, contained
inflation, a gradual Fed, and spending shifting steadily toward cloud, mobile and payments. 2018
was the exception: the trade war was a risk we'd flagged but sized wrongly.

The second three years are more interesting. If you go back to our 2016 Scenario C, we wrote — and
I quote — "another systemic disruption such as a global pandemic." We put twenty per cent on it.
It happened.

And here's the part we got right for the right reason. We argued that even in a recession, cloud
migration and payment digitisation continue, because they're cost-saving. COVID didn't slow our
theme. It accelerated it by years.

2022 tested the diversification rather than the theme. When the discount rate goes from zero to
four and a quarter, long-duration growth equity is repriced. There was nowhere to hide inside the
theme — only the ballast helped.
""",
# 8 — scenarios
"""
Something most managers avoid: holding up our own forecast and marking it against reality.

In 2016 we published three scenarios with explicit probabilities and returns. The pale bars are
what we said. The dark bars are what happened.

Two honest observations. We got the direction right in five of six years. But we were
systematically too conservative about magnitude in both directions — in 2017 we assumed eighteen
per cent and delivered forty; in 2019 we thought we were in a stagnation world worth nine and
delivered thirty-seven; and in 2022 we'd assumed a recession would cost four per cent, and it cost
twenty-two and a half.

The lesson: scenario frameworks are good at identifying which state of the world you're in, and
poor at telling you how violent it will be.
""",
# 9 — growth of $100m
"""
The most important chart in the deck.

Blue is the fund, orange the NASDAQ-100, green the S&P 500.

Three things. First, we're above the NASDAQ-100 for essentially the whole period, and the gap
widens rather than narrows. Second, look at where the lines separate most — the right-hand end, in
2022. On the way up we tracked the benchmark closely; on the way down we fell much less. That
asymmetry is the whole argument for the construction.

Third, the table. Against the S&P 500 — which any of you could have bought for nine basis points —
we added eighty-nine million dollars. Against the NASDAQ-100, the tougher test because it shares
our theme, forty-four million. Against a conventional sixty-forty, a hundred and twenty-seven
million.

I'm not going to pretend all of that is skill. Section five separates the two properly.
""",
# 10 — annual
"""
Annual returns.

The pattern to take away isn't the size of the good years — it's the shape of the bad ones. In a
bull market a technology-tilted fund is supposed to have good years; there's nothing clever about
that.

The interesting years are 2018 and 2022. In 2018 the S&P lost four point six per cent and the
NASDAQ-100 was flat; we made three point seven. In 2022 the S&P lost eighteen and the NASDAQ-100
lost thirty-two point six; we lost twenty-two and a half.

Now — we underperformed the S&P by four points that year, and I won't dress that up. A
technology-tilted fund should lag the broad market when growth de-rates. But against our own theme
benchmark we outperformed by ten full points.

The only year we lagged the NASDAQ-100 was 2020, because concentration was rewarded and our sector
floors held us back. That's the cost of diversification — and 2022 is where you got paid for it.
""",
# 11 — relative
"""
This strips out the market and shows only relative performance.

Against the S&P 500, in green, the line rises steadily. That's the theme working.

The orange line tells you something you won't get anywhere else. Against the NASDAQ-100 we were
roughly flat for the first four and a half years. We only decisively pulled ahead from November
2021.

Let me be direct about what that means. For most of this fund's life we did not beat our primary
benchmark — we tracked it. All of the outperformance against it was earned in the 2022 drawdown, by
falling less.

Some managers would present that as a weakness. I'd argue the opposite. Anyone can hold technology
stocks in a technology bull market. Capital preservation when the regime turns is the part that
requires an actual discipline — and 2022 is the year the fee earned itself.
""",
# 12 — drawdown
"""
Drawdown determines whether an investor stays in a fund, so let me address it directly.

Our worst peak-to-trough loss was twenty-four point nine per cent, from November 2021 to September
2022. The NASDAQ-100 lost thirty-two point six. The S&P lost twenty-three point nine.

So we sat between the two — worse than the broad market, materially better than our own benchmark.
For a fund with a deliberate technology tilt, that's the right place to be.

The Calmar ratio in the table is return per unit of maximum drawdown: nought point seven five for
us against nought point four seven for both indices. A sixty per cent improvement in return per
unit of worst-case pain.
""",
# 13 — COVID
"""
The first stress test.

February and March 2020 cost us twelve point six per cent. It felt considerably worse at the time,
because these are month-end figures.

Then look what happens. April 2020 was the best month in the fund's history at plus fourteen and a
half per cent. By July we were above the pre-COVID high, and 2020 finished up thirty-seven per
cent.

Two things worth saying. First, our 2016 document had literally named a global pandemic as a
Scenario C trigger. I'm not claiming we predicted COVID — I'm claiming that a framework which
forces you to name tail events stops you building a portfolio that only survives the base case.

Second, and more substantive: our core assumption was that digital transformation is cost-saving
and therefore continues in a recession. COVID tested that harder than anything we could have
designed, and the answer came back emphatically.
""",
# 14 — 2022
"""
The second stress test, and the more instructive one.

2022 was the sharpest tightening since 1981 — the Fed raised four hundred and twenty-five basis
points in a calendar year. When the discount rate moves that fast, long-duration growth equity gets
repriced, and there's no clever way around it.

We lost twenty-two and a half per cent. The NASDAQ-100 lost thirty-two point six.

The right-hand panel explains the ten-point difference. At the bottom: Amazon minus fifty, Illumina
minus forty-seven, Alphabet minus thirty-nine. Our thesis names were hit exactly as hard as you'd
expect.

Now look at the top. Schlumberger, plus eighty-one per cent. Visa down three. Albemarle down seven.

Schlumberger was, over six years, the worst holding in this fund. For five years it was the
position I was asked to justify most often. It was there for one reason: the mandate said every
sector gets a floor. In the worst year of the fund's life, that unloved five per cent returned
eighty-one per cent. That's what diversification is — and it's why the constraint was written into
the mandate rather than left to my discretion.
""",
# 15 — histogram
"""
The quantitative section. I want to start with the raw distribution, because a summary statistic
can hide a lot.

Seventy-two observations. Mean monthly return one point five nine per cent, median two point seven
three. The median well above the mean tells you immediately there's a left tail.

Skewness confirms it at minus nought point four seven — mild negative skew, normal for equities.
Excess kurtosis is essentially zero, so no fat tails. And Jarque-Bera returns a p-value of nought
point two eight, meaning we can't reject normality.

That matters practically: the parametric risk measures — standard deviation, Sharpe, normal-based
VaR — are trustworthy for this fund. That isn't true of every strategy.

Best month, April 2020, plus fourteen and a half. Worst, April 2022, minus twelve point one. Fifty
of seventy-two months positive.
""",
# 16 — scorecard
"""
The scorecard slide — the one I'd print out if you kept only one.

Read down the NDIF column against the benchmarks.

Sharpe: nought point nine four against nought point seven five and nought point six five. Sortino,
which penalises only downside volatility: one point five one against one point one eight — a bigger
improvement than on Sharpe, which tells you our volatility was disproportionately upside
volatility. Treynor highest. Calmar sixty per cent better than both indices.

Information ratio against the S&P is nought point nine eight. As a rule of thumb, above nought
point five over a multi-year period is good and above one is excellent.

And the last row, M-squared: if you levered this fund to exactly the S&P's volatility it would have
returned seventeen point two per cent a year against the index's eleven point three. A like-for-like
comparison, and a six-point gap.

Note also that we beat the naive equal-weight portfolio of the same eleven stocks on every one of
these. That's a famously hard benchmark to beat.
""",
# 17 — VaR
"""
Value-at-risk and expected shortfall — what your risk committees will ask for.

Our ninety-five per cent one-month VaR is minus eight point eight two per cent. In the worst month
in twenty we'd expect to lose at least that. On two hundred and seventy-nine million, a
twenty-four point six million dollar month.

Note the historical, parametric and Cornish-Fisher estimates all cluster between seven and nine per
cent — another confirmation the distribution is close to normal.

The number I'd actually watch is CVaR, because VaR only tells you the threshold, not how bad it
gets beyond it. Ours is minus ten point two per cent.

Compare the NASDAQ-100: essentially the same VaR threshold, but a worse CVaR and a worse
ninety-nine per cent VaR. Same threshold risk, thinner tail beyond it. Again, that's
diversification rather than anything clever in timing.
""",
# 18 — seasonality
"""
Seasonality — and I want to frame this carefully, because it's easy to over-read.

Blue is positive, red negative, intensity is magnitude.

July was our strongest month at plus five point eight per cent average, positive in all six years.
September was weakest at minus two point eight, negative in four of six.

But here's why I wouldn't build a strategy on it. Six observations per calendar month is nowhere
near enough to separate a real seasonal effect from noise — the standard error on any monthly mean
is over two per cent. Almost none of these differences would survive a significance test.

What the grid is genuinely useful for is the concentration of extremes. Look at the 2020 and 2022
rows. The best month in the fund's history and the worst sit within twenty-four months of each
other. That's the volatility regime we were managing through.
""",
# 19 — alpha
"""
This is the slide that answers the question you should be asking: was this skill, or did we simply
own high-beta growth stocks in a decade that rewarded them?

You answer that with a factor regression. Take the fund's excess return, regress it on known risk
factors, and see what's left over. That leftover is Jensen's alpha.

Start with the CAPM: alpha of seven point two per cent, t of two point one nine. But the CAPM only
controls for market risk, so a sceptic would say a growth tilt is doing the work.

Add size and value: five point nine per cent, t of two point eight three. Add profitability and
investment: six point six per cent, t of three point zero six, p-value nought point zero zero two.
With momentum, unchanged.

Ninety-two per cent of our variance is explained by the factors. The remaining six point six per
cent a year is not.

Now the bottom row — the one I'd spend most time on. I ran the same test on the NASDAQ-100 itself.
Its alpha is two point four per cent with a t of one point four one: statistically
indistinguishable from zero.

The benchmark's strong decade is fully explained by its factor exposures. Ours is not. That
difference is what you paid a management fee for.
""",
# 20 — factor loadings
"""
Those five coefficients describe the fund more honestly than any marketing document could.

Market loading, one point zero five — one-for-one with the market. Not levered.

Size, minus nought point two two and significant: large-cap. Value, minus nought point one nine and
significant: growth. Both correct and intended.

Profitability and investment are both small and insignificant. That's worth noting, because a
common criticism of "technology alpha" is that it's really a quality tilt in disguise. Here it
isn't.

Momentum is effectively zero — this wasn't a momentum-chasing strategy that would blow up on the
first reversal.

So: a large-cap growth fund with market-like beta, no leverage, no hidden factor bets. Precisely
the description in the mandate I showed you at the start.
""",
# 21 — rolling alpha
"""
One more robustness check, because a full-sample alpha can always be produced by a single
extraordinary year buried in the middle.

I've re-estimated the CAPM alpha on every rolling thirty-six-month window. The line never goes
below zero.

Alpha was earned in the growth years of 2017 to 2019, and in the very different windows dominated
by 2020's crash-and-recovery and 2022's rate shock.

There is a shape worth noticing, though. It declines through the middle of the sample and recovers
at the right. The middle windows are 2020 and 2021, when the NASDAQ-100 was extremely hard to beat.
The recovery at the right is 2022.

So the source of alpha changed character — security selection early, downside protection late.
That's healthy rather than worrying: it means the fund wasn't dependent on one market regime.
""",
# 22 — stock vs sector
"""
Let's get underneath the portfolio number, because ultimately you hired me to pick eleven stocks.

The fairest test isn't whether a pick went up. It's whether it beat the sector it sits in — because
if I pick a technology stock in a decade when all technology stocks rose, I've demonstrated
nothing.

Blue is the stock, orange is its sector ETF. Eight of eleven picks beat their sector.

The standouts: Microsoft beat the technology sector by a hundred and forty-two points — in our
largest position, which is the most valuable place to be right. NextEra beat utilities by a hundred
and forty-six. Alphabet beat communication services by a hundred and twenty-two.

The three misses: Illumina, where the thesis was right but the GRAIL acquisition destroyed value;
Amazon, which beat in absolute terms but lagged its sector; and Schlumberger, which lost money
against an energy sector that gained fifty-four per cent.

I own those three. But eight of eleven, weighted toward our largest positions, is why the portfolio
worked.
""",
# 23 — contribution
"""
How each holding's weight and return compounded into the total.

Microsoft contributed forty-one point nine points of the fund's hundred and seventy-nine. That's
twenty-three per cent of everything the fund made, from a sixteen per cent position. Sizing your
highest-conviction idea largest is the most consequential decision a manager makes, and this is
what it looks like when it goes right.

Alphabet twenty-two points, Albemarle twenty-one — the surprise, a six per cent materials position
riding the lithium and EV supply chain. Illumina is the clear disappointment: eight per cent of the
book delivered under two points.

But the panel on the right contains the most interesting finding in this review. Schlumberger lost
twenty-three and a half per cent over six years, and yet contributed a positive thirteen points.

How? Every quarter it fell, the rebalancing rule bought more at a lower price. Then in 2022 it
returned eighty-one per cent, and by then we owned considerably more shares. A losing stock made
money for this fund because of a mechanical process rule.
""",
# 24 — attribution
"""
Brinson attribution answers a specific question: how much came from being in the right sectors, and
how much from picking the right stocks within them?

To isolate that, I built a benchmark with exactly our sector coverage at neutral weights and no
stock selection — an equal-weight portfolio of the eleven sector ETFs. It returned eighty-five per
cent against our hundred and seventy-nine.

Allocation — our sector tilts — contributed one point eight points. Almost nothing. Selection
contributed forty-one point four. Interaction, one.

So ninety-four per cent of our active return came from security selection.

Why that matters for your decision: allocation skill is a macro forecasting call, and the evidence
that anyone repeats macro calls is weak. Selection skill is the output of a research process — you
can describe it, staff it and repeat it. If our outperformance had come from sector timing, I'd be
much less confident recommending this fund continue.
""",
# 25 — optimiser
"""
The obvious challenge to everything I've said is: fine, but a model could have done better. So I
tested it.

I took three years of data ending December 2016 — the information a manager genuinely had at launch
— fed it to a mean-variance optimiser, and ran the weights forward with the same rebalancing.

The result: nineteen point seven per cent a year against our eighteen point seven. So yes, it wins,
by a point a year.

But look at what it had to do. Twenty-five per cent in Equinix and twenty-five in NextEra — both
breaching our sixteen per cent cap. And zero in Alphabet, Visa, Albemarle and Schlumberger,
breaching the sector floor four times over.

The optimiser didn't beat our strategy. It declined to run it — it bought a better backtest by
discarding the constraints that, as we saw in 2022, protected you. And there's a known reason to
distrust it anyway: DeMiguel, Garlappi and Uppal showed in 2009 that naive equal weighting
frequently beats optimisation out of sample, because small input errors produce wildly concentrated
portfolios.

The last row is the humbling one. With perfect hindsight the best achievable was twenty-two point
nine per cent. We captured eighty-two per cent of a number nobody could have known.
""",
# 26 — capture
"""
If I had to reduce this whole presentation to two numbers, it would be these.

Upside capture of a hundred and twenty per cent: in months the S&P rose, we rose twenty per cent
more. Downside capture of ninety-seven: in months it fell, we fell slightly less.

That asymmetry is the engine of the result. You don't need to be right about market direction to
compound at eighteen per cent a year if you participate disproportionately in the good months and
proportionately in the bad ones.

Contrast the NASDAQ-100: a hundred and eighteen per cent of the upside — very similar — but a
hundred and eight per cent of the downside. More of the gains and more of the losses. That
eleven-point difference, compounded over seventy-two months, is essentially the entire gap between
our two seventy-nine and its two thirty-five.
""",
# 27 — objective scorecard
"""
The accountability slide. Ten commitments, marked against what happened.

We said eight to ten per cent net a year; we delivered seventeen and a half net. We said fifty-five
to seventy per cent cumulative; we delivered a hundred and sixty-one.

I'll be careful how I present that, because doubling your target isn't automatically a compliment
to the manager. Part of it is that this was an unusually strong period for our theme. The honest
framing: our central estimate was reasonable and our distribution around it was too narrow.

Then the process commitments, which matter as much. All eleven sectors held through all twenty-four
quarters. The sixteen per cent cap never breached at a rebalance date. Twenty-four rebalances
executed. The mid-life review delivered at the end of 2019.

Ten commitments. Four exceeded, six met, none missed.
""",
# 28 — fees
"""
Fees in full, because you're entitled to see the bridge.

Gross, the fund compounded at eighteen point seven per cent. The management fee is ninety basis
points, flat.

The performance fee is where the structure earns its keep. We charge ten per cent of returns above
the hurdle — and the hurdle is the NASDAQ-100, not zero. Because that benchmark itself returned
fifteen point three per cent a year, we only cleared it by two and a half points, so the
performance fee is twenty-five basis points rather than the one point eight per cent a
zero-hurdle fund would have taken.

Total load: one point one five per cent a year. Net to you, seventeen point five one per cent a
year, or a hundred and sixty-one per cent cumulative.

The honest alternative: a NASDAQ-100 ETF at twenty basis points would have returned two hundred and
thirty-five million. After paying us every dollar of fee, you're roughly forty million ahead of the
cheap passive option. That's the only fee test that matters, and we pass it.
""",
# 29 — recommendation
"""
So: should this fund continue?

My recommendation is yes, for three specific reasons rather than a general expression of
confidence.

First, the alpha is real and repeatable — six point six per cent a year that five established
factors can't explain, and ninety-four per cent of it from selection rather than sector timing.
Selection skill is a process; macro timing is a guess.

Second, the thesis isn't exhausted. Cloud is still a minority of enterprise IT spend, six years
after we argued it was early. 2022 repriced the multiple, not the demand.

Third, the construction discipline was tested by the two hardest events in twenty years and held.

But I'd be doing you a disservice if I asked for renewal without saying what I'd change.

We need wider tail-scenario assumptions — we said a recession would cost four per cent; it cost
twenty-two and a half. We need a valuation discipline on entry: Illumina was a correct thesis
bought with no margin of safety. And I'd ask you to consider raising the position cap from sixteen
to twenty per cent, because that cap forced us to trim Microsoft — our best decision — eleven
times. The sector floors I would leave entirely untouched, because those are what saved us.
""",
# 30 — thank you
"""
That's the review.

Three sentences: a hundred million became two hundred and seventy-nine million; we did it with less
drawdown than our own benchmark and a higher Sharpe than any comparator I could construct; and
after controlling for every standard risk factor, six point six per cent a year remains unexplained
by anything other than the decisions we made.

I recommend the fund continues, with the three mandate changes I've set out.

Happy to take questions — and there's a substantial appendix if you want to go deeper on the
methodology, the holdings or the regressions. Thank you for six years of patient capital.
""",
# --- appendix (spoken only if asked) -------------------------------------------
# 31 — A1
"""
This slide exists so anyone can reproduce every number in the deck.

Two points I'd flag. First, I've used QQQ and SPY rather than the raw index levels, because the raw
series are price-only. Comparing our dividend-inclusive return against a price-only index would
have flattered us by roughly two per cent a year. Using the ETFs makes it apples-to-apples, and
investable.

Second, these returns are gross of transaction costs and taxes. With twenty-four rebalances of
eleven liquid mega-caps, realistic round-trip costs are a few basis points a year — immaterial, but
I'd rather state it than have it discovered.
""",
# 32 — A2
"""
The complete metric table.

The comparison I'd encourage you to make is NDIF against equal weight, in the first two data
columns — a genuinely hard benchmark.

We beat it on cumulative return, annualised return, Sharpe, Sortino, Treynor and information ratio.
Equal weight beat us on maximum drawdown and Calmar, because it held less in the mega-caps that
fell hardest in 2022.

So conviction weighting added return and risk-adjusted return while costing a little on worst-case
drawdown. That's a fair characterisation of what active weighting bought you.
""",
# 33 — A3
"""
Every holding on the same basis as the portfolio.

The point I want to make is in the last two columns and the bottom row.

Only two individual holdings — Microsoft and NextEra — produced a statistically significant CAPM
alpha on their own. Everything else has a t-statistic below two.

But the portfolio's alpha has a t of two point one nine on the CAPM and three point zero six on the
five-factor. The portfolio is more significant than almost every stock in it.

That's not a paradox — it's diversification. Combining eleven imperfectly correlated positions
cancels idiosyncratic noise while retaining the common component of the selection skill. The signal
survives; much of the noise doesn't.
""",
# 34 — A4
"""
The full regression output.

Read across the alpha row: seven point two, five point nine, six point six, six point five. Stable
across specifications — an alpha that collapses when you add a factor was never alpha, it was an
unmeasured exposure.

Market loading between one and one point zero five in every model, always with a t above fifteen.

Size and value significantly negative throughout. Profitability, investment and momentum all
insignificant — a meaningful negative result, because it means our excess return isn't a repackaged
quality factor.

Adjusted R-squared runs from nought point eight seven to nought point nine one five. Newey-West
standard errors with four lags throughout, which is the conservative choice — ordinary OLS errors
would have produced higher t-statistics.
""",
# 35 — A5
"""
The correlation matrix.

Average pairwise correlation is nought point four zero, which for eleven stocks inside a single
theme is genuinely low.

The structure is intuitive. The three platforms cluster tightly — Microsoft and Alphabet at nought
point seven four. That's the concentration risk in tier one, and why the position cap mattered.

At the other end, the genuine diversifiers: NextEra against Schlumberger is minus nought point one
two — actually negatively correlated. That bottom-right corner is where the ballast lives, and
those low correlations produced the ten-point drawdown advantage in 2022.

It's also why the portfolio's volatility of nineteen per cent sits well below the average
constituent volatility of about twenty-nine.
""",
# 36 — A6
"""
The risk-return scatter, each bubble sized by target weight.

The most important feature is where the star sits — upper-left of almost every individual holding.

Only Microsoft, NextEra and Costco sit above the portfolio on return, all at comparable or higher
volatility. Meanwhile Schlumberger at forty-nine per cent volatility and Albemarle at forty-four
are far out to the right.

The portfolio has lower volatility than eight of its own eleven constituents. That's the argument
for diversification in one picture.
""",
# 37 — A7
"""
The ex-post efficient frontier from the eleven stocks we owned. Nobody could have known this in
advance — it exists only because we now know the answers.

The fund sits below and slightly right of it, which is where a real portfolio should sit. The
vertical distance is roughly four points of annual return: the cost of not having known the future.

What I find more informative is that the fund, equal weight and the ex-ante optimiser all cluster
in the same small region. Three different construction philosophies converged on nearly the same
outcome, which tells you the dominant driver was which eleven stocks we chose, not how we weighted
them.
""",
# 38 — A8
"""
Two supporting exhibits.

The box plot compares the four distributions directly. Our median is visibly higher than both
benchmarks, our interquartile range is tighter than the NASDAQ-100's, and our whisker extremes are
contained relative to it.

The lower chart shows dispersion across the eleven holdings. The range runs from minus twenty-four
per cent to plus three hundred and nineteen — in an eleven-stock portfolio, in a single theme, over
six years.

That dispersion is exactly why the position cap mattered. Had we been permitted a thirty per cent
position and chosen Illumina rather than Microsoft for it — and in 2016 the genomics thesis was
every bit as compelling as the cloud thesis — this would be a very different presentation.
""",
# 39 — A9
"""
Two stability checks.

Rolling thirty-six-month beta stays between about nought point nine seven and one point zero eight
for the entire sample. We didn't drift into higher-beta positioning as markets rose, which is a
common and destructive pattern in growth funds.

Rolling twelve-month volatility below shows the regime: calm through 2017, the COVID spike, a quiet
2021, then the sustained rise through 2022. Our line sits below the NASDAQ-100's for most of the
sample. Less total risk than our own benchmark, more return — which is the argument this entire
deck has been making.
""",
# 40 — A10
"""
Two pieces of supporting detail.

The chart is the month-of-year seasonality — July strongest, September weakest. Six observations per
month, so description rather than signal.

The table is the fee benchmarking. A passive S&P 500 ETF costs nine basis points and returned
ninety per cent. A NASDAQ-100 ETF costs twenty and returned a hundred and thirty-five. We cost one
point one five per cent all-in and returned a hundred and seventy-nine.

The arithmetic: we cost six point four million more than the NASDAQ ETF and delivered forty-four
million more in terminal value. A net gain of thirty-eight million after every dollar of fee.

I put this in the appendix deliberately — a manager should be prepared to defend a fee on request,
not only when it flatters them.
""",
# 41 — A11
"""
References and declarations.

The methodology follows the standard literature: Jensen for alpha, Sharpe, Sortino and Treynor for
the ratios, Fama and French for the factor models, Brinson for attribution, Markowitz for the
frontier, Newey and West for the standard-error correction.

On AI use: this assessment is classified as AI-Supported. I've declared the tools and, more
importantly, the division of labour. The analytical scope, the choice of benchmarks and models, the
interpretation of every result and the recommendation are mine. Every number traces back to a
reproducible calculation on primary market data, and the code and workbook accompany this
submission.
""",
]

p = os.path.join(HERE, "deck.py")
s = open(p).read()
pat = re.compile(r'notes\(s, """(.*?)""" *\)', re.S)
matches = list(pat.finditer(s))
assert len(matches) == len(NEW), f"{len(matches)} blocks vs {len(NEW)} replacements"
out, last = [], 0
for m, new in zip(matches, NEW):
    out.append(s[last:m.start()])
    out.append('notes(s, """\n' + new.strip() + '\n""")')
    last = m.end()
out.append(s[last:])
open(p, "w").write("".join(out))
words = sum(len(n.split()) for n in NEW)
main = sum(len(n.split()) for n in NEW[:31])
print(f"replaced {len(NEW)} note blocks")
print(f"main body: {main:,} words ≈ {main/150:.0f} min at 150 wpm")
print(f"appendix:  {words-main:,} words (spoken only on request)")
