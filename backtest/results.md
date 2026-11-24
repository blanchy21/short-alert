# Backtest results

27 Jul 2026 to 24 Nov 2026 (120 days), 177 Hyperliquid coins, hourly candles. R after fees; 1R = the loss if the stop hits. Generated 24 Nov 2026 by `backtest/backtest.py`.

| Rules | Trades | Win % | Avg R | Total R | Profit factor | Worst run (R) | Stopped % | 1st half R | 2nd half R |
|---|---|---|---|---|---|---|---|---|---|
| baseline (live rules) | 117 | 59% | +0.08 | +8.8 | 1.21 | -11.6 | 33% | +1.9 | +6.9 |
| rules 8-9 Nov (1% drop, ATR stop) | 165 | 52% | +0.05 | +8.9 | 1.11 | -25.2 | 48% | -0.8 | +9.7 |
| rules before 8 Nov fix | 182 | 61% | -0.08 | -14.2 | 0.80 | -28.9 | 38% | -2.2 | -12.0 |
| drop >= 1% (stop 2% above peak) | 153 | 60% | +0.08 | +11.8 | 1.21 | -18.9 | 35% | +1.7 | +10.1 |
| drop >= 1.5% (stop 2% above peak) | 136 | 58% | +0.04 | +4.9 | 1.09 | -18.5 | 36% | -2.0 | +6.9 |
| drop >= 2% (stop 2% above peak) | 117 | 59% | +0.08 | +8.8 | 1.21 | -11.6 | 33% | +1.9 | +6.9 |
| drop >= 5% from peak | 29 | 59% | -0.02 | -0.4 | 0.96 | -4.2 | 41% | -3.4 | +2.9 |
| close below 1h EMA9 | 6 | 83% | +0.51 | +3.1 | 27.13 | -0.1 | 0% | +0.0 | +3.1 |
| no peak retest in last 3h | 43 | 60% | +0.03 | +1.1 | 1.07 | -5.5 | 30% | +1.4 | -0.3 |
| stop >= 1% above peak | 119 | 55% | +0.05 | +5.4 | 1.11 | -19.7 | 41% | +2.1 | +3.3 |
| ATR stop only (no peak floor) | 124 | 49% | +0.02 | +3.0 | 1.05 | -21.5 | 49% | -5.2 | +8.3 |
| score 50+ | 169 | 62% | +0.08 | +13.7 | 1.23 | -11.0 | 33% | -2.4 | +16.1 |
| score 60+ | 81 | 58% | +0.09 | +7.3 | 1.24 | -10.7 | 35% | -0.5 | +7.8 |
| EMA9 + stop 1% above peak | 6 | 67% | +0.31 | +1.9 | 2.59 | -1.0 | 17% | +0.0 | +1.9 |
| skip if TP1 < 0.75R | 73 | 58% | +0.17 | +12.2 | 1.42 | -12.1 | 37% | -0.4 | +12.6 |
| skip if TP1 < 1R | 42 | 48% | +0.11 | +4.6 | 1.22 | -4.2 | 45% | +0.2 | +4.3 |
| stop 2% above peak + TP1 >= 0.75R | 114 | 54% | +0.06 | +7.2 | 1.14 | -22.0 | 42% | -1.7 | +9.0 |
| max 2 open shorts | 97 | 61% | +0.09 | +8.5 | 1.24 | -11.1 | 33% | +0.1 | +8.4 |
| max 1 open short | 60 | 68% | +0.24 | +14.4 | 1.91 | -4.2 | 23% | +6.6 | +7.8 |
| close shorts if BTC +2% in 1h | 117 | 59% | +0.08 | +8.8 | 1.21 | -11.6 | 33% | +1.9 | +6.9 |
| close shorts if BTC +1.5% in 1h | 117 | 60% | +0.07 | +8.6 | 1.20 | -11.7 | 33% | +1.9 | +6.7 |
| BTC +2% in 1h: break-even if winning, else close | 117 | 59% | +0.08 | +8.8 | 1.21 | -11.6 | 33% | +1.9 | +6.9 |
| max 2 open + close if BTC +2% in 1h | 97 | 61% | +0.09 | +8.5 | 1.24 | -11.1 | 33% | +0.1 | +8.4 |

## How trades ended

| Rules | STOP | TP1 + STOP | TP1 + break-even | TP1 + TP2 | 24h exit | BTC spike exit |
|---|---|---|---|---|---|---|
| baseline (live rules) | 39 | 0 | 17 | 37 | 24 | 0 |
| rules 8-9 Nov (1% drop, ATR stop) | 79 | 0 | 23 | 48 | 15 | 0 |
| rules before 8 Nov fix | 70 | 0 | 57 | 52 | 3 | 0 |
| drop >= 1% (stop 2% above peak) | 53 | 0 | 23 | 47 | 30 | 0 |
| drop >= 1.5% (stop 2% above peak) | 49 | 0 | 19 | 42 | 26 | 0 |
| drop >= 2% (stop 2% above peak) | 39 | 0 | 17 | 37 | 24 | 0 |
| drop >= 5% from peak | 12 | 0 | 4 | 6 | 7 | 0 |
| close below 1h EMA9 | 0 | 0 | 0 | 4 | 2 | 0 |
| no peak retest in last 3h | 13 | 0 | 5 | 13 | 12 | 0 |
| stop >= 1% above peak | 49 | 0 | 16 | 37 | 17 | 0 |
| ATR stop only (no peak floor) | 61 | 0 | 14 | 37 | 12 | 0 |
| score 50+ | 55 | 0 | 25 | 57 | 32 | 0 |
| score 60+ | 28 | 0 | 11 | 25 | 17 | 0 |
| EMA9 + stop 1% above peak | 1 | 0 | 0 | 3 | 2 | 0 |
| skip if TP1 < 0.75R | 27 | 0 | 6 | 25 | 15 | 0 |
| skip if TP1 < 1R | 19 | 0 | 3 | 10 | 10 | 0 |
| stop 2% above peak + TP1 >= 0.75R | 48 | 0 | 13 | 34 | 19 | 0 |
| max 2 open shorts | 32 | 0 | 14 | 34 | 17 | 0 |
| max 1 open short | 14 | 0 | 12 | 23 | 11 | 0 |
| close shorts if BTC +2% in 1h | 39 | 0 | 17 | 37 | 24 | 0 |
| close shorts if BTC +1.5% in 1h | 39 | 0 | 17 | 37 | 22 | 2 |
| BTC +2% in 1h: break-even if winning, else close | 39 | 0 | 17 | 37 | 24 | 0 |
| max 2 open + close if BTC +2% in 1h | 32 | 0 | 14 | 34 | 17 | 0 |
