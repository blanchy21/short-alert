# Trade lessons

A note on every losing trade: what happened and why. **Rules stay unchanged until the weekly review**, so we judge
them on a week of trades rather than one loss. First review: **Saturday 14 November 2026** (covering 6–13 Nov).

## Losing trades

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

## Patterns to check at the review
- Losers were both shorted **while the coin was still pushing up**. Do winners show a deeper drop from the peak,
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
