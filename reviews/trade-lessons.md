# Trade lessons

A note on every trade, winners and losers: what happened and why. **Rules stay unchanged until the weekly review**, so we judge
them on a week of trades rather than one loss. First review: **Saturday 14 November 2026** (covering 6–13 Nov).

## Losing trades

### USUAL — 9 Nov, live, −$1.60 (−1.07R)
- **Entry** 15:05 UTC at 0.01062, score 63, +6.2% in 24h. It was the last live trade before Paul paused live
  trading at 15:37.
- **Stop** 0.01088. The peak was 0.01083 (14:00 candle), so price was only **1.9% off the peak** and the stop sat
  just **0.46% above it**.
- **What happened:** the 15:00 candle ran on to 0.01097 on heavy volume (about 100k against 5–10k overnight) and
  took the stop at 15:35, filled at 0.01089. At 17:00 it was 0.01076, still above our entry: no reversal yet.
- **Why it lost:** the same pattern as W, MET and BIO. The pump was still running, and the stop sat just above
  the high. **The 9 Nov rule would have skipped it** (it was 1.9% off the peak, under the new 3% minimum).

### BIO — 9 Nov, live, −$1.65 (−1.15R)
- **Entry** 13:10 UTC at 0.020278, score 55 (just at the bar), +5.0% in 24h, bounce risk LOW, BTC below 4h EMA.
  Reasons: RSI 80.8, StochRSI bearish cross at 95/98, price at the upper Bollinger band, a red candle after 3 green.
- **Stop** 0.020745 (+2.3%, 1.5× ATR). The peak was 0.020529 at 11:00, so the stop sat only **1.05% above it**.
- **What happened:** price never went our way. The 13:00 candle pushed through the 11:00 high to 0.020829. The
  stop triggered at 13:51 and filled at about 0.020797, 0.25% worse than the trigger.
- **Why it lost:**
  1. **Not rolled over, again.** It was only 1.1% off a peak 2h old, the minimum our rule allows. The 11:00
     candle was a heavy-volume wick (about 53k against 2–5k normal) and 12:00 made a lower high, but price was
     still holding near the top, not falling.
  2. **The "+5%" was a recovery, not a pump.** BIO flushed −5% at 21:00 on 8 Nov (about 40k volume) and spent
     the morning climbing back. Shorting the top of a V-shaped recovery is weaker than shorting an exhausted pump.
  3. **The score was a one-scan spike.** 48 before entry, 55 at entry, 48 five minutes later, then 38.
  4. **The stop was just above an obvious high,** as with MET.
- **After the stop** (checked at 16:30): BIO peaked at **0.02093 at 13:55**, 0.89% above our stop and 3.2% above
  entry. It pushed again to 0.020865 at 15:15, then turned and fell to 0.020179 by 16:25, 0.5% below entry.
  TP1 (0.019796) hadn't been reached. A stop 2% above the 11:00 peak (0.020940) would have survived by just
  0.00001, but it would have needed a 3.3% stop. At the same $1.43 risk, that means a position about 30% smaller.
- **The backtest tweaks would have skipped it:** a 1.1% drop from the peak fails the "drop ≥3%" filter, and the
  stop was less than 2% above the peak.

### MERL — 8 Nov, live, −$0.09 (−0.07R): right call, nothing earned
- **Entry** 21:40 UTC at 0.031311, score 65, +5.4% in 24h, 4.6% off a peak 1h earlier. Stop 0.032301 (+3.2%).
- **TP1 was 0.031283, only 0.09% below entry** (Fib 23.6%), smaller than the 0.09% round-trip fees. A
  normal wiggle filled half the position within seconds, for about $0.02.
- **The break-even stop fired at once.** The 21:45 scan moved the stop to 0.03128 (0.1% below entry), but price
  had bounced to about 0.0314, *above* that level. A buy-stop below the market triggers immediately, so the other
  half closed at about 0.0314, a small loss after fees.
- **Then MERL did what we expected:** it fell to 0.03004 by 21:55, 4% below entry. TP2 (0.030917) would have
  filled within 10 minutes, for about +$0.24. The short was right; the exits threw it away.
- **Two faults to fix:**
  1. **TP1 can sit almost on top of entry.** Nothing sets a minimum distance. The backtest found the same
     problem: TP1 averages only about 0.6R.
  2. **The break-even stop can be placed below the market** when price has bounced after TP1. It then fires
     straight away. This is an execution bug rather than a strategy choice. The backtest models the same effect.
- **Fixed on 8 Nov** (at Paul's request, ahead of the review): TP1 must now be at least 0.75R below entry,
  and the break-even stop only goes in once price is 0.3% below it. With the new rule MERL's TP1 would have
  been 0.030291 (−3.3%), which it reached. In the 120-day backtest the change moved the total from −12.9R to
  **+5.4R** (first half +15.7R, second half −10.3R). It wins less often (50% against 61%), but wins are bigger.
  The worst losing run is still −25.2R.

### MET — 7 Nov, live, −$1.21 (−1.09R)
- **Entry** 11:10 UTC at 0.29372, score 63, +6.3% in 24h, bounce risk LOW. BTC below its 4h EMA.
- **Stop** 0.30156 (+2.7%, 1.5× ATR). The morning high was 0.30028, so the stop sat only **0.4% above it**.
- **What happened:** the best price in our favour was 0.29123 at 11:15, only 0.85% down. A heavy-volume candle
  (about 3× normal) bought that dip, and price climbed back to 0.298 by 11:30. A 13:00 wick to 0.304 took the
  stop, which filled at 0.30204, 0.16% worse than the trigger. MET was at 0.2969 at 13:20, still above our entry.
- **Why it lost:**
  1. **The pump hadn't finished.** The coin was 2.2% off its peak and had been holding a tight range for 3 hours.
     That passes our "rolled over" rule (1% below the peak, peak 1h+ ago), but it was sideways, not falling.
  2. **The stop sat just above an obvious high.** Retests and wicks through a fresh high are common, and the
     margin above it was only 0.4%.
  3. **The score jumped around.** MET scored about 50 earlier, 63 at entry and 43 at the exit. The 63 was one
     5-minute snapshot.
- **What went right:** the 25% margin cap held risk to 2% of the pot (not 10%), so the loss was small. The stop
  was on the exchange and filled with little slippage.

### W — 6 Nov, paper (before live), −$1.36 (−1.0R)
- **Entry** 14:20 UTC at 0.01137, score 65, +5.9% in 24h. It was stopped at 0.01160 within 20 minutes.
- **Why it lost:** the pump was still going. W reached +13.4% in 24h by 17:10, when the next W trade (live)
  went in higher and won at TP1 (+$1.03). The same pattern as MET: we shorted before the move was done.

(The live W safety-net close on 6 Nov, −$0.17, was an order-format bug, fixed the same day. It wasn't a
strategy loss.)

## Winning trades
Winners get a note too, so the review can see what a good setup looks like, not only what a bad one does.

### BOME, AVAX, MET — 9 Nov, paper (live paused), +1.33R / +1.11R / +1.27R
- **Entries** 16:05–16:15 UTC, scores 60 / 75 / 58, +6.1% / +9.0% / +10.8% in 24h. These were under the 8 Nov
  rules (TP1 at least 0.75R away), just before the 3% rule went in at 16:37.
- **All three reached TP2.** BOME and AVAX got there within 3 hours, and MET overnight. Starting stops were 2.4% /
  2.9% / 3.7% above entry.
- **What went right:** TP1 was far enough from entry to be worth having, and after TP1 the break-even stop sat
  below entry, so the second half ran to TP2. This is the pattern the 8 Nov exit fix was meant to produce. Before it
  (USUAL, W, ZEC on 6 Nov) winners closed at TP1 alone for only +0.3R to +0.6R.

### Earlier winners — 6 Nov
USUAL (paper, +0.30R), W (live, +0.58R) and ZEC (live, +0.34R) all hit TP1. W went in when the coin was +13.4%
on the day, after the paper W short at +5.9% had been stopped. The later entry, once the pump was further along,
won.

## Orders the exchange blocked

### SOPH — 10 Nov, live order rejected, logged as paper
- **Signal** 14:15 UTC at 0.001443, score 60, +16.8% in 24h. Stop 0.001531, TP1 0.001372, TP2 0.0013325.
- **Hyperliquid rejected the order:** "Cannot increase position when open interest is at cap." SOPH had hit the
  exchange's limit on open positions, so nobody could add to one. The bot logged a paper trade instead.
- **What happened next:** it dropped to 0.001387 (1.1% short of TP1), bounced to 0.00149, then fell to 0.00138 by
  about 17:30. Funding was −0.018%/h, just inside our −0.02% limit, so the coin was crowded with shorts.
- **Lessons:**
  1. An open-interest cap is an exchange limit, not a strategy fault. It tends to hit the most crowded coins,
     which are also the ones with the most squeeze risk.
  2. Paul asked whether to enter late, at 0.00138. By the rules it was too late: the score was down to 26 and the
     original stop was 10.9% away, against about 3.4% left to TP2.
- **For the review:** count how often the cap blocks an entry, and whether funding close to the limit goes with
  bigger moves against us. The bot doesn't record open interest yet.

## Rule change on 9 Nov (brought forward at Paul's request)
Four of five losers (W, MET, BIO, USUAL) were shorted while the pump was still running, with the stop just above the
peak. From 9 Nov the bot needs **price at least 3% below the peak** (was 1%) and puts the **stop at least 2% above
the peak** (on top of 1.5× ATR, still capped at 10%). Over 120 days this scored **70 trades, 64% won, +6.2R, worst
run −6.0R** (against 157 trades, +5.4R, worst run −25.2R before). It trades about half as often, and the second
half was flat (−0.2R), so it isn't proven. Judge it at the 14 Nov review. Live trading was paused at the time (Paul's
manual AMD long), so the first trades under it come once live is switched back on.

## Blocked-setup log (from 9 Nov evening, log only)
To judge the 3% rule, the bot now records every setup that scored 55+ and was stopped only by the rolled-over
rule. It places no order, sends no alert, and doesn't touch the pot or limits. Each one is followed like a paper
trade, twice: with the stop the old rules would have used (`r`) and with the new rule's wider stop (`r_new_stop`).
`old_rule_ok` is true when the rules before 9 Nov would have traded it. They sit in `state/state.json` under
`blocked_open` and `blocked_closed`, with a one-line summary in the daily tally. If the `old_rule_ok` ones add up
to a loss, the rule saved money; if they add up to a gain, it cost money.

The near-miss log now keeps each coin's **highest** score of the day (it used to keep the first).

## Break-even stop after TP1 (study, 10 Nov)
Paul asked how many trades that hit TP1 go on to TP2, and how many get stopped at break-even. Backtest, current
rules, 120 days: 43 of 70 trades hit TP1.
| After TP1 | Trades | Share | Average R |
|---|---|---|---|
| Reached TP2 | 21 | 49% | +0.88 |
| Stopped at break-even | 14 | 33% | +0.35 |
| Closed at 24h | 8 | 19% | +0.91 |

What the 14 break-even stops did next: only **3** went on to TP2 before the original stop, **5** went on up to the
original stop (break-even saved about 1R on each), and 6 did neither within 24h. Other stop levels after TP1, total R:
break-even +6.2R, stop at entry +0.25R +5.1R, stop halfway (+0.5R) +7.0R, original stop kept +6.7R. Those gaps are
within noise, and on the 8–9 Nov rules break-even came out best (+5.4R). **Verdict: keep break-even.** It doesn't cost
much, and it stops a TP1 winner turning into a loss. Real trades so far: ZEC and MERL closed at break-even (MERL from
the bug fixed 8 Nov); the 9 Nov paper trades BOME, AVAX and MET all reached TP2. Recheck with real trades at the review.

## Patterns to check at the review
- Losers (W, MET, BIO, USUAL) were all shorted **while the coin was still pushing up**. Do winners show a deeper drop from the peak,
  or a clear lower high, before entry?
- **Stop distance above the recent high:** compare winners and losers. Is 0.4% too tight?
- **Score at entry versus the score on the scans before and after:** do one-off spikes lose more often?
- **Near-misses (score 50–54):** how would they have done? That tells us whether 55 is the right bar.
- Win rate, average win against average loss (in R), and how often TP1, TP2, the break-even stop and the 24h
  close each happen.

## Running tally
| Date | Coin | Mode | Score | Result | R | P&L |
|---|---|---|---|---|---|---|
| 6 Nov | USUAL | paper | 55 | TP1 | +0.30 | +$0.28 |
| 6 Nov | W | paper | 65 | Stop | −1.00 | −$1.36 |
| 6 Nov | W | live | 55 | TP1 | +0.58 | +$1.03 |
| 6 Nov | ZEC | live | 58 | TP1 + break-even | +0.34 | +$0.86 |
| 7 Nov | MET | live | 63 | Stop | −1.09 | −$1.21 |
| 8 Nov | MERL | live | 65 | TP1 + break-even | −0.07 | −$0.09 |
| 9 Nov | BIO | live | 55 | Stop | −1.15 | −$1.65 |
| 9 Nov | USUAL | live | 63 | Stop | −1.07 | −$1.60 |
| 9 Nov | BOME | paper | 60 | TP1 + TP2 | +1.33 | +$1.38 |
| 9 Nov | AVAX | paper | 75 | TP1 + TP2 | +1.11 | +$2.32 |
| 9 Nov | MET | paper | 58 | TP1 + TP2 | +1.27 | +$2.03 |
| 10 Nov | SOPH | paper (order rejected, OI cap) | 60 | TP1 + TP2 | +1.03 | +$3.04 |

## Backtest (run 8 Nov 2026): 120 days, 177 coins

Full table: [backtest/results.md](../backtest/results.md). Every trade: `backtest/trades.csv`. Rerun with
`python backtest/backtest.py` (read-only; it places no orders).

**The live rules lost money over the 120 days:** 173 trades, 61% won, average −0.07R, total −12.9R after fees.
They made +12.7R from July to mid-September, then lost −25.6R from mid-September to November.

**Why:**
- A win is usually smaller than a loss. TP1 averages 2.2% from entry but the stop averages 3.8%, so TP1 is
  worth only about 0.6R. Stops average −1.03R, TP1 + break-even +0.21R, TP1 + TP2 +0.84R.
- Many stops come early: 32 of 67 hit within 2 hours. That's the MET pattern, shorting before the pump has finished.

**Tweaks tested** (total R; first half / second half):
| Change | Trades | Total R | Halves | Worst run | Note |
|---|---|---|---|---|---|
| Live rules | 173 | −12.9 | +12.7 / −25.6 | −28.9R | |
| Stop at least 2% above the peak | 168 | −3.6 | +11.6 / −15.3 | −21.9R | stops fall from 39% to 28% |
| Drop ≥ 3% from peak + stop 2% above peak | 76 | −2.3 | +0.7 / −3.0 | −5.5R | steadiest, 76% won |
| Skip if TP1 < 0.75R | 67 | +2.3 | +12.1 / −9.8 | −12.2R | only plus total, still lost in half 2 |
| Stop 2% above peak + TP1 ≥ 0.75R | 44 | +2.4 | +6.0 / −3.6 | −8.3R | |
| Score 60+ | 112 | −14.6 | +4.3 / −18.9 | −22.1R | worse: a higher score doesn't help |
| Score 50+ | 257 | −10.7 | +15.1 / −25.8 | −28.6R | about the same as 55 |

**What it means:** no version made money in both halves, so none is a proven fix. Every change that
helped did the same two things: **wait for a real drop (3%+) before shorting** and **put the stop
clear of the peak (2%+)**. Those cut losing streaks a lot (−28.9R down to −5.5R). The score threshold isn't
the problem.

**Limits:** hourly candles, not every 5 minutes; when stop and target are inside one candle the
stop counts first (only 3 trades affected); no funding history; only coins listed today.
