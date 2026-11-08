# Backtest results

11 Jul 2026 to 08 Nov 2026 (120 days), 177 Hyperliquid coins, hourly candles. R after fees; 1R = the loss if the stop hits. Generated 08 Nov 2026 by `backtest/backtest.py`.

| Rules | Trades | Win % | Avg R | Total R | Profit factor | Worst run (R) | Stopped % | 1st half R | 2nd half R |
|---|---|---|---|---|---|---|---|---|---|
| baseline (live rules) | 157 | 50% | +0.03 | +5.4 | 1.07 | -25.2 | 49% | +15.7 | -10.3 |
| old exits (before 8 Nov fix) | 173 | 61% | -0.07 | -12.9 | 0.81 | -28.9 | 39% | +12.4 | -25.4 |
| drop >= 3% from peak | 76 | 54% | +0.08 | +6.3 | 1.18 | -11.7 | 46% | +3.4 | +2.9 |
| drop >= 5% from peak | 25 | 44% | -0.08 | -2.0 | 0.86 | -5.4 | 56% | +1.0 | -3.0 |
| close below 1h EMA9 | 6 | 50% | +0.06 | +0.3 | 1.11 | -3.1 | 50% | +0.0 | +0.3 |
| no peak retest in last 3h | 46 | 48% | -0.03 | -1.4 | 0.94 | -14.1 | 52% | +2.4 | -3.8 |
| stop >= 1% above peak | 149 | 54% | +0.03 | +4.5 | 1.07 | -24.3 | 44% | +17.0 | -12.5 |
| stop >= 2% above peak | 146 | 60% | +0.08 | +11.5 | 1.21 | -18.9 | 35% | +15.5 | -4.0 |
| score 50+ | 223 | 52% | +0.04 | +9.8 | 1.09 | -22.6 | 47% | +11.5 | -1.7 |
| score 60+ | 105 | 47% | -0.06 | -6.3 | 0.89 | -22.3 | 51% | +7.5 | -13.8 |
| drop >= 3% + stop 1% above peak | 71 | 61% | +0.07 | +4.7 | 1.17 | -10.3 | 38% | +8.1 | -3.5 |
| EMA9 + stop 1% above peak | 6 | 67% | +0.31 | +1.9 | 2.59 | -1.0 | 17% | +0.0 | +1.9 |
| skip if TP1 < 0.75R | 157 | 50% | +0.03 | +5.4 | 1.07 | -25.2 | 49% | +15.7 | -10.3 |
| skip if TP1 < 1R | 126 | 45% | -0.02 | -2.6 | 0.96 | -18.7 | 54% | +7.4 | -10.0 |
| drop >= 3% + stop 2% above peak | 70 | 64% | +0.09 | +6.2 | 1.25 | -6.0 | 34% | +6.4 | -0.2 |
| stop 2% above peak + TP1 >= 0.75R | 108 | 51% | +0.02 | +2.5 | 1.05 | -22.0 | 44% | +11.1 | -8.6 |

## How trades ended

| Rules | STOP | TP1 + STOP | TP1 + break-even | TP1 + TP2 | 24h exit |
|---|---|---|---|---|---|
| baseline (live rules) | 77 | 0 | 21 | 45 | 14 |
| old exits (before 8 Nov fix) | 67 | 0 | 53 | 50 | 3 |
| drop >= 3% from peak | 35 | 0 | 12 | 21 | 8 |
| drop >= 5% from peak | 14 | 0 | 2 | 4 | 5 |
| close below 1h EMA9 | 3 | 0 | 0 | 2 | 1 |
| no peak retest in last 3h | 24 | 0 | 3 | 14 | 5 |
| stop >= 1% above peak | 65 | 0 | 22 | 45 | 17 |
| stop >= 2% above peak | 51 | 0 | 21 | 46 | 28 |
| score 50+ | 104 | 0 | 30 | 65 | 24 |
| score 60+ | 54 | 0 | 13 | 27 | 11 |
| drop >= 3% + stop 1% above peak | 27 | 0 | 14 | 21 | 9 |
| EMA9 + stop 1% above peak | 1 | 0 | 0 | 3 | 2 |
| skip if TP1 < 0.75R | 77 | 0 | 21 | 45 | 14 |
| skip if TP1 < 1R | 68 | 0 | 13 | 31 | 14 |
| drop >= 3% + stop 2% above peak | 24 | 0 | 14 | 21 | 11 |
| stop 2% above peak + TP1 >= 0.75R | 48 | 0 | 12 | 31 | 17 |
