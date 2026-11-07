# Trade lessons

A note on every losing trade: what happened and why. **Rules stay unchanged until the weekly review**, so we judge
them on a week of trades rather than one loss. First review: **Saturday 14 November 2026** (covering 6–13 Nov).

## Losing trades

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
