# Backtest results

12 Jul 2026 to 09 Nov 2026 (120 days), 177 Hyperliquid coins, hourly candles. R after fees; 1R = the loss if the stop hits. Generated 09 Nov 2026 by `backtest/backtest.py`.

| Rules | Trades | Win % | Avg R | Total R | Profit factor | Worst run (R) | Stopped % | 1st half R | 2nd half R |
|---|---|---|---|---|---|---|---|---|---|
| baseline (live rules) | 70 | 64% | +0.09 | +6.2 | 1.25 | -6.0 | 34% | +6.4 | -0.2 |
| rules 8-9 Nov (1% drop, ATR stop) | 157 | 50% | +0.03 | +5.4 | 1.07 | -25.2 | 49% | +15.7 | -10.3 |
| rules before 8 Nov fix | 173 | 61% | -0.07 | -12.9 | 0.81 | -28.9 | 39% | +12.4 | -25.4 |
| drop >= 1% (stop 2% above peak) | 146 | 60% | +0.08 | +11.5 | 1.21 | -18.9 | 35% | +15.5 | -4.0 |
| drop >= 5% from peak | 24 | 58% | +0.03 | +0.6 | 1.06 | -4.2 | 42% | +0.5 | +0.1 |
| close below 1h EMA9 | 5 | 100% | +0.63 | +3.2 | ∞ | 0.0 | 0% | +0.0 | +3.2 |
| no peak retest in last 3h | 31 | 61% | +0.01 | +0.2 | 1.02 | -4.4 | 29% | +2.1 | -1.9 |
| stop >= 1% above peak | 71 | 61% | +0.07 | +4.7 | 1.17 | -10.3 | 38% | +8.1 | -3.5 |
| ATR stop only (no peak floor) | 76 | 54% | +0.08 | +6.3 | 1.18 | -11.7 | 46% | +3.4 | +2.9 |
| score 50+ | 107 | 63% | +0.05 | +5.7 | 1.15 | -8.7 | 35% | +4.6 | +1.0 |
| score 60+ | 40 | 52% | -0.09 | -3.8 | 0.80 | -8.9 | 48% | +1.2 | -5.0 |
| EMA9 + stop 1% above peak | 6 | 67% | +0.31 | +1.9 | 2.59 | -1.0 | 17% | +0.0 | +1.9 |
| skip if TP1 < 0.75R | 42 | 60% | +0.15 | +6.3 | 1.36 | -6.2 | 40% | +2.5 | +3.8 |
| skip if TP1 < 1R | 23 | 43% | -0.07 | -1.7 | 0.87 | -5.1 | 57% | -0.4 | -1.3 |
| stop 2% above peak + TP1 >= 0.75R | 108 | 51% | +0.02 | +2.5 | 1.05 | -22.0 | 44% | +11.1 | -8.6 |

## How trades ended

| Rules | STOP | TP1 + STOP | TP1 + break-even | TP1 + TP2 | 24h exit |
|---|---|---|---|---|---|
| baseline (live rules) | 24 | 0 | 14 | 21 | 11 |
| rules 8-9 Nov (1% drop, ATR stop) | 77 | 0 | 21 | 45 | 14 |
| rules before 8 Nov fix | 67 | 0 | 53 | 50 | 3 |
| drop >= 1% (stop 2% above peak) | 51 | 0 | 21 | 46 | 28 |
| drop >= 5% from peak | 10 | 0 | 3 | 4 | 7 |
| close below 1h EMA9 | 0 | 0 | 0 | 4 | 1 |
| no peak retest in last 3h | 9 | 0 | 4 | 10 | 8 |
| stop >= 1% above peak | 27 | 0 | 14 | 21 | 9 |
| ATR stop only (no peak floor) | 35 | 0 | 12 | 21 | 8 |
| score 50+ | 37 | 0 | 18 | 32 | 20 |
| score 60+ | 19 | 0 | 7 | 8 | 6 |
| EMA9 + stop 1% above peak | 1 | 0 | 0 | 3 | 2 |
| skip if TP1 < 0.75R | 17 | 0 | 5 | 14 | 6 |
| skip if TP1 < 1R | 13 | 0 | 2 | 5 | 3 |
| stop 2% above peak + TP1 >= 0.75R | 48 | 0 | 12 | 31 | 17 |
