# Backtest results

11 Jul 2026 to 08 Nov 2026 (120 days), 177 Hyperliquid coins, hourly candles. R after fees; 1R = the loss if the stop hits. Generated 08 Nov 2026 by `backtest/backtest.py`.

| Rules | Trades | Win % | Avg R | Total R | Profit factor | Worst run (R) | Stopped % | 1st half R | 2nd half R |
|---|---|---|---|---|---|---|---|---|---|
| baseline (live rules) | 173 | 61% | -0.07 | -12.9 | 0.81 | -28.9 | 39% | +12.7 | -25.6 |
| drop >= 3% from peak | 78 | 67% | -0.06 | -4.4 | 0.84 | -9.5 | 33% | -0.7 | -3.6 |
| drop >= 5% from peak | 25 | 56% | -0.25 | -6.2 | 0.45 | -6.9 | 44% | +0.3 | -6.5 |
| close below 1h EMA9 | 6 | 67% | -0.06 | -0.3 | 0.84 | -2.1 | 33% | +0.0 | -0.3 |
| no peak retest in last 3h | 48 | 67% | -0.06 | -3.1 | 0.81 | -9.2 | 33% | +2.4 | -5.5 |
| stop >= 1% above peak | 173 | 62% | -0.09 | -15.5 | 0.76 | -31.7 | 36% | +12.8 | -28.3 |
| stop >= 2% above peak | 168 | 69% | -0.02 | -3.6 | 0.93 | -21.9 | 28% | +11.6 | -15.3 |
| score 50+ | 257 | 65% | -0.04 | -10.7 | 0.88 | -28.6 | 34% | +15.1 | -25.8 |
| score 60+ | 112 | 55% | -0.13 | -14.6 | 0.70 | -22.1 | 43% | +4.3 | -18.9 |
| drop >= 3% + stop 1% above peak | 76 | 72% | -0.05 | -3.8 | 0.82 | -7.8 | 26% | +0.5 | -4.4 |
| EMA9 + stop 1% above peak | 6 | 83% | +0.08 | +0.5 | 1.46 | -1.0 | 17% | +0.0 | +0.5 |
| skip if TP1 < 0.75R | 67 | 52% | +0.03 | +2.3 | 1.07 | -12.2 | 48% | +12.1 | -9.8 |
| skip if TP1 < 1R | 43 | 47% | -0.00 | -0.2 | 0.99 | -10.8 | 53% | +7.4 | -7.6 |
| drop >= 3% + stop 2% above peak | 76 | 76% | -0.03 | -2.3 | 0.87 | -5.5 | 22% | +0.7 | -3.0 |
| stop 2% above peak + TP1 >= 0.75R | 44 | 52% | +0.05 | +2.4 | 1.13 | -8.3 | 41% | +6.0 | -3.6 |

## How trades ended

| Rules | STOP | TP1 + break-even | TP1 + TP2 | 24h exit |
|---|---|---|---|---|
| baseline (live rules) | 67 | 53 | 50 | 3 |
| drop >= 3% from peak | 26 | 26 | 26 | 0 |
| drop >= 5% from peak | 11 | 7 | 7 | 0 |
| close below 1h EMA9 | 2 | 3 | 1 | 0 |
| no peak retest in last 3h | 16 | 15 | 17 | 0 |
| stop >= 1% above peak | 63 | 53 | 52 | 5 |
| stop >= 2% above peak | 47 | 56 | 53 | 12 |
| score 50+ | 88 | 89 | 74 | 6 |
| score 60+ | 48 | 27 | 34 | 3 |
| drop >= 3% + stop 1% above peak | 20 | 28 | 27 | 1 |
| EMA9 + stop 1% above peak | 1 | 4 | 1 | 0 |
| skip if TP1 < 0.75R | 32 | 11 | 20 | 4 |
| skip if TP1 < 1R | 23 | 4 | 11 | 5 |
| drop >= 3% + stop 2% above peak | 17 | 30 | 28 | 1 |
| stop 2% above peak + TP1 >= 0.75R | 18 | 7 | 12 | 7 |
