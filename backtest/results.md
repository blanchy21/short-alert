# Backtest results

17 Jul 2026 to 14 Nov 2026 (120 days), 177 Hyperliquid coins, hourly candles. R after fees; 1R = the loss if the stop hits. Generated 14 Nov 2026 by `backtest/backtest.py`.

| Rules | Trades | Win % | Avg R | Total R | Profit factor | Worst run (R) | Stopped % | 1st half R | 2nd half R |
|---|---|---|---|---|---|---|---|---|---|
| baseline (live rules) | 73 | 66% | +0.13 | +9.4 | 1.38 | -6.0 | 33% | +7.5 | +1.9 |
| rules 8-9 Nov (1% drop, ATR stop) | 164 | 52% | +0.07 | +10.8 | 1.14 | -25.2 | 47% | +16.8 | -6.0 |
| rules before 8 Nov fix | 181 | 62% | -0.06 | -10.9 | 0.84 | -28.9 | 37% | +12.0 | -22.9 |
| drop >= 1% (stop 2% above peak) | 153 | 61% | +0.10 | +16.0 | 1.29 | -18.9 | 33% | +17.2 | -1.3 |
| drop >= 1.5% (stop 2% above peak) | 131 | 59% | +0.05 | +6.2 | 1.13 | -18.5 | 35% | +10.6 | -4.4 |
| drop >= 2% (stop 2% above peak) | 110 | 60% | +0.09 | +10.3 | 1.27 | -11.6 | 32% | +10.8 | -0.5 |
| drop >= 5% from peak | 27 | 59% | +0.07 | +1.9 | 1.17 | -4.2 | 41% | +0.0 | +1.9 |
| close below 1h EMA9 | 5 | 100% | +0.63 | +3.2 | ∞ | 0.0 | 0% | +0.0 | +3.2 |
| no peak retest in last 3h | 31 | 61% | +0.01 | +0.2 | 1.02 | -4.4 | 29% | +1.1 | -0.9 |
| stop >= 1% above peak | 74 | 62% | +0.11 | +8.1 | 1.29 | -10.3 | 36% | +9.5 | -1.4 |
| ATR stop only (no peak floor) | 79 | 56% | +0.12 | +9.8 | 1.27 | -11.7 | 44% | +5.1 | +4.7 |
| score 50+ | 113 | 64% | +0.09 | +9.7 | 1.25 | -8.7 | 34% | +8.6 | +1.1 |
| score 60+ | 43 | 56% | -0.01 | -0.6 | 0.97 | -8.9 | 44% | +0.3 | -0.9 |
| EMA9 + stop 1% above peak | 6 | 67% | +0.31 | +1.9 | 2.59 | -1.0 | 17% | +0.0 | +1.9 |
| skip if TP1 < 0.75R | 44 | 64% | +0.24 | +10.5 | 1.65 | -6.2 | 36% | +4.1 | +6.4 |
| skip if TP1 < 1R | 23 | 48% | +0.03 | +0.7 | 1.06 | -5.1 | 52% | +0.2 | +0.5 |
| stop 2% above peak + TP1 >= 0.75R | 112 | 54% | +0.07 | +7.3 | 1.15 | -22.0 | 42% | +12.4 | -5.1 |

## How trades ended

| Rules | STOP | TP1 + STOP | TP1 + break-even | TP1 + TP2 | 24h exit |
|---|---|---|---|---|---|
| baseline (live rules) | 24 | 0 | 14 | 24 | 11 |
| rules 8-9 Nov (1% drop, ATR stop) | 77 | 0 | 22 | 49 | 16 |
| rules before 8 Nov fix | 67 | 0 | 57 | 54 | 3 |
| drop >= 1% (stop 2% above peak) | 51 | 0 | 22 | 50 | 30 |
| drop >= 1.5% (stop 2% above peak) | 46 | 0 | 18 | 42 | 25 |
| drop >= 2% (stop 2% above peak) | 35 | 0 | 16 | 36 | 23 |
| drop >= 5% from peak | 11 | 0 | 3 | 6 | 7 |
| close below 1h EMA9 | 0 | 0 | 0 | 4 | 1 |
| no peak retest in last 3h | 9 | 0 | 4 | 10 | 8 |
| stop >= 1% above peak | 27 | 0 | 14 | 24 | 9 |
| ATR stop only (no peak floor) | 35 | 0 | 12 | 24 | 8 |
| score 50+ | 38 | 0 | 18 | 37 | 20 |
| score 60+ | 19 | 0 | 7 | 11 | 6 |
| EMA9 + stop 1% above peak | 1 | 0 | 0 | 3 | 2 |
| skip if TP1 < 0.75R | 16 | 0 | 5 | 17 | 6 |
| skip if TP1 < 1R | 12 | 0 | 2 | 6 | 3 |
| stop 2% above peak + TP1 >= 0.75R | 47 | 0 | 12 | 34 | 19 |
