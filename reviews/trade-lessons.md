# Trade lessons

A note on every trade, winners and losers: what happened and why. **Rules stay unchanged until the weekly review**, so we judge
them on a week of trades rather than one loss. First review: **Saturday 14 November 2026** (covering 6–13 Nov).

## Weekly review — 21 Nov 2026, written late on 24 Nov (17–23 Nov)

**Rules this week:**
- Drop at least 2% from a peak at least 1h old; stop at least 2% above the peak.
- Live from 17 Nov 23:35, after the paper week was cut short.

**Live: 11 trades, 8 won, +2.84R but −$2.21.**
- **18–21 Nov:** the 2% rule worked. 8 trades, 8 winners, +5.17R, +$12.34. Every one reached TP1, and none was stopped.
- **22–23 Nov:** 3 stops (ETHFI, JTO, NEAR) and one break-even (STBL), −2.33R, −$12.55.
  - All four were open while **BTC rose 59k → 61.6k (22 Nov) and then 61.3k → 64.6k in two hours (23 Nov 13:00–14:00)**.
  - JTO and NEAR were stopped at the same minute (14:01). STBL had already hit TP1, so the break-even stop saved it.
    STBL then ran +17%.
- **Why R is positive but dollars negative:** the winners averaged +0.65R, while the losers were −1.1R each. The stops
  also came when each trade risked more ($2.9–$5.2, against $1.4–$3.0 for most winners).

**Paper:** RUNE +0.71R (TP1 + TP2) and SOPH −0.04R (24h exit).

**Blocked-setup log, 16–23 Nov:** 39 setups scored 55+ but were blocked by the rolled-over rule. These figures don't
apply the slot or risk limits.

| Group | Setups | Won | Total R |
|---|---|---|---|
| Drop 1–2%, peak 1h+ (the 1% rule would have taken these) | 17 | 10 | +4.47 |
| — before 22 Nov | 12 | 9 | +7.12 |
| — 22 Nov on | 5 | 1 | −2.65 |
| — peak under 2h old | 8 | 4 | +1.99 |
| — peak 2h+ old | 9 | 6 | +2.48 |
| Under 1% drop, or peak under 1h old (blocked by any rule) | 22 | 10 | +0.91 |

- **What it means:** the 1% rule would have added about +4.5R this week. All of that came in the good stretch, and it
  would have lost too on 22–23 Nov.
- **No sign this week of the fresh-peak weakness:** the peak-under-2h group made +2.0R. This week doesn't repeat the
  backtest finding (−4.9R on 40 such trades), so the fresh-peak filter idea from 15 Nov stays unproven.

**Main lesson: the losses came from BTC, not from the drop rule.**
- The BTC filter only blocks *new* shorts while BTC is above a rising 4h EMA. It does nothing for shorts already
  open, and with up to 3 open shorts, one BTC spike can stop all of them at once (JTO and NEAR at 14:01 on 23 Nov).
- Repeat coins went both ways: ETHFI won on 19 Nov and was stopped on 22 Nov; SOPH, VVV and MEGA have also come back.
  There's no pattern yet.

**Recommendations, for Paul to decide (nothing changed yet):**
1. **Keep the 2% rule.** 8 of 8 won outside the BTC spike, and the 1% rule's extra trades would also have lost in it.
   The case for 1% is the +4.5R in the blocked log. The case against is the three live losses on 15–16 Nov.
2. **Backtest two ways to handle a BTC spike while shorts are open:**
   - **(a)** a maximum of 2 open shorts instead of 3 (the backtest already models slots);
   - **(b)** close open shorts, or move their stops to break-even, when BTC rises 2%+ within an hour.

   Only switch if the backtest shows a gain in both halves.
3. **Funding and OI:** nothing stood out this week. STBL at the 1.1M OI level and NEAR at 96M OI both lost to the same
   BTC move.

Next review: **Saturday 28 Nov.**

### Backtest of the BTC-spike protections (24 Nov, at Paul's request)
Fresh data, 27 Jul–24 Nov 2026 (120 days, 177 coins), live rules (2% drop, stop 2% above the peak). Full table:
[backtest/results.md](../backtest/results.md).

| Rules | Trades | Total R | Worst run | 1st / 2nd half |
|---|---|---|---|---|
| Live (3 open shorts max) | 117 | +8.8 | −11.6R | +1.9 / +6.9 |
| **Max 1 open short** | 60 | **+14.4** | **−4.2R** | +6.6 / +7.8 |
| Max 2 open shorts | 97 | +8.5 | −11.1R | +0.1 / +8.4 |
| Close shorts if BTC +2% in 1h | 117 | +8.8 | −11.6R | no change: never fired |
| Close shorts if BTC +1.5% in 1h | 117 | +8.6 | −11.7R | fired twice |
| BTC +2%: break-even if winning, else close | 117 | +8.8 | −11.6R | no change: never fired |

- **Max 1 open short is the clear winner.** It gives more total R, about a third of the worst run, and gains in both
  halves.
  - **Robustness check:** when several coins set up in the same hour, the backtest has to pick one. I reran it with
    three different picking orders. Max 1 still won every time:
    - total +14.4 / +13.3 / +10.0R, against +8.8 / +8.4 / +9.2R for the live rules;
    - worst run −4.2 / −2.6 / −5.2R, against −11.6 / −13.2 / −12.3R.
  - **Why it helps:** when several alts set up together, it's usually one broad alt or BTC move, and the extra shorts
    tend to lose together, as on 22–23 Nov.
- **Max 2 is no better than 3** (+8.5R, and down to +3.1R in one ordering).
- **A BTC-spike exit can't be judged on hourly candles.** BTC rose 2%+ within an hour only 12 times in 128 days. When
  the spike and the coin's stop fall in the same hour, the backtest counts the stop first, so the exit almost never
  fires. Testing it properly would need 5-minute data, and Hyperliquid only gives about 17 days of that. Leave it.
- **Trade-off:** max 1 takes about half as many trades. At 10% risk per trade, the extra R comes from skipping the
  shorts that lose together, not from more trades.
- **Caveat:** the backtest uses hourly candles, while the live bot scans every 5 minutes. It didn't take the live
  ETHFI, JTO or NEAR trades on 22 Nov (its BTC check, on hourly closes, blocked them), so it can't replay that exact
  day.

**Recommendation:** set `MAX_OPEN_SHORTS = 1`. Paul to decide; not changed yet.

## Weekly review — 14 Nov 2026 (6–14 Nov)

**Paul's concern:** the 3% rolled-over rule is stopping almost every trade. **The data agrees.**
- **Bot trades since the rule went in (9 Nov 16:37):** only 2 in 5 days, both SOPH and both paper (live was
  paused 11–14 Nov). One reached TP2 (+1.03R), one was stopped (−1.0R).
- **Blocked-setup log:** 27 setups scored 55+ and were stopped only by the 3% rule. The 19 that the old 1% rule
  would have traded won 12 of 19 for **+7.0R** with the old stop, **+7.9R** with the new wider stop. So far the
  3% rule has cost money, not saved it. (The log doesn't apply the open-shorts or risk limits, so the real figure
  would be a bit lower.) By drop size: 1–1.5% +4.6R (7), 1.5–2% +3.9R (7), 2–3% −1.5R (5).
- **Backtest rerun on fresh data** (17 Jul–14 Nov, 120 days):

| Rules | Trades | Win % | Total R | Worst run | 1st / 2nd half | Since 9 Nov |
|---|---|---|---|---|---|---|
| Live: 3% drop, stop 2% above peak | 73 | 66% | +9.4 | −6.0R | +7.5 / +1.9 | 4 trades, +2.2R |
| 2% drop, stop 2% above peak | 110 | 60% | +10.3 | −11.6R | +10.8 / −0.5 | 7 trades, +2.1R |
| 1.5% drop, stop 2% above peak | 131 | 59% | +6.2 | −18.5R | +10.6 / −4.4 | 9 trades, +4.0R |
| 1% drop, stop 2% above peak | 153 | 61% | +16.0 | −18.9R | +17.2 / −1.3 | 11 trades, +6.4R |

- **What it means:** the 3% rule is the steadiest (smallest losing run, both halves positive) but trades about
  once every two days. A 1% drop with the wider stop makes the most R and agrees with the blocked log, but its
  worst losing run is three times deeper. The 1.5% row doing worse than both 1% and 2% shows how noisy these
  numbers are: no version is proven better.
- **Other checks:**
  - Open interest: only 15 blocked setups have it. Rising OI did not go with losses (+4.5R on 5 against +2.1R on 10),
    far too few to use.
  - Break-even after TP1: still fine.
  - Funding near the limit: no new cases.
- **SOPH 13 Nov loser (paper, −1.0R, −$3.05):**
  - **Entry** 07:01 UTC at 0.001483, score 55. Price was 3.9% below the 06:00 high, peak 1h old, so it passed the
    3% rule. Funding was slightly positive and OI was falling (−2.7% in 1h).
  - **Stopped in 20 minutes** at 0.001575.
  - **Then SOPH ran another +40%** (0.00213 by 16:00) on volume about 50× normal. It was a multi-day pumper (it also
    ran on 10 Nov).
  - **Lesson:** a 3% intrahour dip in a coin with accelerating volume is not a top. The 3% rule doesn't protect
    against that.

**Decision (14 Nov, Paul):** change the drop-from-peak rule from 3% to **1%**, keeping the stop at least 2% above the
peak. Paul first picked 2%, then chose 1% because **total profit matters more to him than the depth of a losing
run**. It's the best total in the backtest (+16.0R against +10.3R for 2%), but it has a deeper worst run (−18.9R,
about −$57 at today's sizes). The blocked-setup log keeps running, but now only catches setups less than 1% off the
peak or with a peak under 1h old. Next review: Saturday 21 Nov.

## Live on the 2% rule, 18–23 Nov: trade notes
Live trades are listed by close time. Columns:
- **Peak / drop:** how old the peak was at entry, and how far price was below it.
- **TP1 R:** how far TP1 was, in R.
- **Best:** the best point in the trade, in R.

| Coin | Entry → exit (UTC) | Score | Peak / drop | TP1 R | Best | Result |
|---|---|---|---|---|---|---|
| RUNE (paper) | 17 Nov 15:31 → 18 Nov 14:10 | 61 | 2h / −2.0% | 0.64 | 1.12 | TP1 + TP2, +0.71R, +$2.24 |
| MELANIA | 18 Nov 05:01 → 19 Nov 05:05 | 56 | 2h / −8.1% | 0.43 | 0.24 | 24h exit, +0.19R, +$0.57 |
| SOPH (paper) | 18 Nov 09:05 → 19 Nov 09:10 | 60 | under 1h / −6.8% | 1.05 | 0.58 | 24h exit, −0.04R, −$0.08 |
| STRK | 19 Nov 10:01 → 10:50 | 58 | 1h / −2.5% | 0.48 | 0.87 | TP1 + TP2, +0.61R, +$1.42 |
| 2Z | 18 Nov 16:01 → 19 Nov 16:05 | 56 | 2h / −2.6% | 0.65 | 1.42 | TP1 + 24h exit, +0.89R, +$1.27 |
| SYRUP | 19 Nov 16:06 → 17:05 | 55 | 1h / −4.8% | 0.37 | 0.64 | TP1 + TP2, +0.45R, +$0.94 |
| ETHFI | 19 Nov 05:50 → 20:35 | 63 | 2h / −2.2% | 0.64 | 1.16 | TP1 + TP2, +0.80R, +$1.79 |
| USELESS | 19 Nov 10:51 → 21:35 | 61 | 4h / −3.2% | 0.75 | 1.18 | TP1 + TP2, +0.96R, +$1.58 |
| BLUR | 20 Nov 19:05 → 21 Nov 03:35 | 60 | 1h / −3.0% | 0.96 | 1.65 | TP1 + TP2, +1.06R, +$2.77 |
| ETHFI | 22 Nov 02:40 → 13:55 | 60 | 2h / −2.2% | 0.77 | 0.27 | **Stop, −1.15R, −$4.34** |
| STBL | 22 Nov 13:50 → 23 Nov 13:25 | 61 | 4h / −2.2% | 0.57 | 0.71 | TP1 + break-even, +0.22R, +$0.48 |
| JTO | 22 Nov 18:25 → 23 Nov 14:01 | 56 | 7h / −4.1% | 0.39 | 0.26 | **Stop, −1.03R, −$5.36** |
| NEAR | 22 Nov 18:31 → 23 Nov 14:01 | 56 | 5h / −1.9% | 1.02 | 0.49 | **Stop, −1.16R, −$3.33** |

- **Winners:**
  - Every live winner reached TP1 within hours, while BTC was flat to falling. Six hours after the exit, all were
    3–10% below our entry, so the shorts were right and the targets left money on the table.
  - TP1 was often close (0.37–0.65R), so the wins were small in R.
- **MELANIA:** a deep drop (−8.1%) put the stop 10% away, so TP1 was only 0.43R. It drifted sideways for 24h and
  made only +0.19R. Deep drops give poor reward for the risk.
- **ETHFI (22 Nov), stop:** entered at 02:40. BTC then ran from 58.9k to 61.6k between 06:00 and 12:00, and ETHFI was
  stopped at 13:55. It was the second ETHFI short in three days; the first won.
- **STBL:** TP1 filled. Then BTC's 23 Nov spike pushed it 3R against us, and the break-even stop closed the rest at no
  loss. STBL then ran +17%. **The break-even stop earned its keep.**
- **JTO and NEAR, stops:** both were opened on 22 Nov evening and both stopped at 14:01 on 23 Nov, when BTC jumped
  4.8% in two hours. These two losses are one event, not two separate bad calls.
  - NEAR ($96M OI) is a large coin that moves with BTC.
  - JTO had little volume ($11k/h). Six hours later both were back near entry (JTO +2.7%, NEAR −0.6%).
- **SOPH (paper):** shorted under an hour after a fresh spike, 6.8% below it, with funding strongly positive. It went
  0.87R against us, then came back to a flat 24h exit.

## Paper week on the 2% rule (16–17 Nov): 3 closed, +1.37R, +$6.50
Live trading was off (Paul's call after the CASHCAT loss), so all three were paper trades on the 2% rule. RUNE
(score 61, entry 0.55536, opened 17 Nov 15:31) was still open when live trading restarted on 17 Nov at 23:35. It stays
a paper trade to the end.

- **ICP: winner, +1.75R (+$7.16), 24h time exit after TP1.**
  - **Entry** 16 Nov 23:01 at 2.49, score 61, +11.5% in 24h. The peak (2.5686) was 1h old and price was 3.1% below it.
  - **What happened:** TP1 (2.267) filled. The rest was still in profit after 24h (low 2.216) and closed on the time limit.
  - **Lesson:** a fresh peak with a 3%+ drop works, the opposite of MEGA (fresh peak, 1.6% drop). It fits the
    15 Nov finding that a 2% drop matters most when the peak is fresh.
- **PURR: winner, +0.62R (+$1.28), TP1 + TP2.**
  - **Entry** 17 Nov 01:01 at 0.093603, score 56, +6.1% in 24h. The peak was 3h old and price was 2.3% below it.
  - **Funding was strongly positive** (+0.04%/h), so longs were paying shorts.
  - **What happened:** TP1 and TP2 filled by 09:20. Only a small win in R, because TP1 was close.
- **HMSTR: loser, −1.0R (−$1.94), stop.**
  - **Entry** 17 Nov 02:05 at 0.000143, score 63, only +5.2% in 24h. The peak was 3h old and price was 2.1% below it,
    just over the 2% line.
  - **What happened:** it barely went our way (low 0.000142, about 0.2R), then pushed back above the peak and took the
    stop at 12:15.
  - **Points to note:**
    - HMSTR's price moves in steps of 0.000001, which is 0.7% of the price. A "2% drop" is only three price steps,
      so the signal is coarse.
    - Its 24h move (+5.2%) was the smallest of the three.
- **Takeaway:** a small sample, but it points the same way as the backtest. Drops of 3%+ worked; a drop only just
  over 2% on a weak pump lost.

## Losing trades

**Decision (16 Nov, Paul):** after the two losses below, the drop rule goes back to **2%** (stop still at least 2% above
the peak). Trading is **paper only for the week** to 21 Nov. Paul's manual AMD long stays untouched: in paper mode the
bot doesn't even connect to Hyperliquid. At the 21 Nov review, judge the 2% rule on that week's paper trades
before going live again.

### CASHCAT — 16 Nov, live, −$8.38 (−1.01R): the last live trade before the paper week
- **Entry** 05:05 UTC at 0.044428, score 58, +7.5% in 24h. The peak (0.047519, 03:00 candle) was 2h old and price was
  **6.5% below it**, so it would have passed even the old 3% rule. **The drop rule wasn't the problem here.**
- **Stop** 0.048487 (2% above the peak), 9.1% away from entry. TP1 0.041649 was 0.68R away. (The 0.75R TP1 floor is
  applied before the stop is widened to the peak, as in the backtest, so the final ratio can fall below 0.75R.)
- **Other readings:** funding was **negative** (−0.009%/h, so shorts were paying), not far from the −0.02% limit.
  OI was $7.4M and falling (−2.4% in 1h).
- **What happened:** at best the trade was 0.26R in profit (low 0.04338 at 06:00). Then a **second pump wave** came:
  0.0466 at 08:00, then 0.0511 at 09:00 on $527k volume (about 4× the hours before). The stop hit at 09:35. CASHCAT
  went on to 0.0532 at 10:00 on $1M volume. The stop was right to get us out.
- **Why it lost:** the same story as SOPH on 13 Nov. A deep pullback in a coin that's still attracting volume isn't a
  top, and a second wave came within hours. It was the biggest loss in dollars so far ($8.38) because the risk was
  10% of a pot of about $83.
- **Checked, but no rule from it:** in the 2% backtest, neither wide stops (8%+ away: +3.9R) nor deep drops (5–8%:
  +1.3R) clearly lose. So this is a loss the rules accept, not a gap in them.
- **Watch at the review:** negative funding at entry (shorts paying), and volume picking up again in the hours after
  entry.

### 15 Nov: two live losses on the first day of the 1% rule (MEGA −$4.10, VVV −$3.77, −2.1R in all)
Both were live trades and both were stopped. **Neither would have been taken under the 3% rule**, so these are the
first real cost of the 14 Nov change. A losing run like this is what the backtest warned about (−18.9R worst run), and
two trades don't prove the rule wrong.

**MEGA, −$4.10 (−1.08R):**
- **Entry** 08:01 UTC at 0.048583, score 56, +8.5% in 24h. **The peak (0.049361, 07:00 candle) was only 1h old**, and
  price was only **1.6% off it**. Funding +0.00125%, OI $7.9M, flat (+0.3% in 1h).
- **What happened:** MEGA had made a higher high in every hour from 02:00 to 07:00. At best the trade was 0.33R in
  profit (low 0.04792); TP1 needed 0.98R. The 09:00 candle broke out to 0.05082 on the highest volume of the day
  ($312k against about $180k) and took the stop at 09:40, filled at 0.05069 (a little slippage past 0.05058).
- **After:** it topped at 0.0513 at 13:00, then drifted back to about 0.0499. That's still above our entry, so even
  holding on wouldn't have paid.
- **Lesson:** this is the USUAL/BIO pattern again: a fresh peak, a shallow dip and a trend still making higher highs.
  The backtest shows this group is the weak spot of the 1% rule (see recommendation below).

**VVV, −$3.77 (−1.02R):**
- **Entry** 13:01 UTC at 19.785, score 56, +10.0% in 24h. The peak (20.272) was 9h old and price was 2.4% below it,
  so it was a reasonable-looking setup. OI was large ($51M) and flat; funding +0.00125%.
- **What happened:** the trade moved the right way at first. The low was 19.253 at 15:00, 0.60R in profit; TP1 needed
  1.30R. Then VVV ground up all afternoon and evening with no single spike, broke the peak at about 16:00, and took
  the stop (20.674) at 23:05, filled at 20.677. It was in the trade 10 hours.
- **One warning sign:** at 09:00, 4h before entry, VVV had already gone back to 20.21, within 0.3% of the peak, on
  heavy volume ($1.26M). Buyers were still defending the highs.
- **Lesson:** a normal loss. The setup was fine on paper, but TP1 at 1.30R was a long way off for a $51M coin moving
  2–3% a day. Large, slow coins need a long time to reach TP1, which gives the trend time to resume.

**Recommendation (Paul to decide):** add one rule. **If the peak is under 2h old, require a 2% drop. Otherwise 1% is
enough.** In the 1% backtest (153 trades, 17 Jul–14 Nov):
| Group | Trades | Total R | 1st / 2nd half | Stopped |
|---|---|---|---|---|
| Peak under 2h old and drop under 2% (MEGA's type) | 40 | **−4.9R** | −2.9 / −2.0 | 48% |
| Everything else | 113 | **+20.9R** | +20.2 / +0.8 | 30% |
| All (the current rule) | 153 | +16.0R | +17.2 / −1.3 | 33% |

- **What the new rule changes:**
  - It cuts the one group that lost in both halves, which lifts total R and makes the 2nd half positive.
  - The worst run improves from −18.9R to −12.5R.
  - It keeps about three quarters of the trades.
  - It would have skipped MEGA. VVV would still have been taken.
- **Caveat:** these numbers come from re-slicing the existing trade list, not a full rerun. A full rerun would
  account for slots freed by skipped trades. Run it before switching.
- **Watch, but don't add a rule yet:** a retest of the peak (within 0.5%) in the 4 hours before entry, as VVV showed.
  The older "no retest in 3h" test was flat (+0.2R), so there isn't enough evidence for it.

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
  bigger moves against us. From the evening of 10 Nov the bot records funding, open interest (USD) and its 1h change
  on every trade and blocked setup, plus `order_error` when the exchange rejects an order. Log only.

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
- **(21 Nov) Fresh-peak filter:** decide whether to require a 2% drop when the peak is under 2h old (see 15 Nov
  losses). Do a full backtest rerun first.
- **(21 Nov) Second-wave pumps (SOPH 13 Nov, CASHCAT 16 Nov):** do losers have negative funding at entry, or volume
  rising again within 2h? Could a volume check in the hours after entry close those trades early?
- **(21 Nov) Slow, large coins:** do trades with TP1 over 1.2R or OI over $30M stop more often? (VVV, 15 Nov.)
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
| 13 Nov | SOPH | paper (live paused) | 55 | Stop | −1.00 | −$3.05 |
| 15 Nov | MEGA | live | 56 | Stop | −1.08 | −$4.10 |
| 15 Nov | VVV | live | 56 | Stop | −1.02 | −$3.77 |
| 16 Nov | CASHCAT | live | 58 | Stop | −1.01 | −$8.38 |
| 16 Nov | ICP | paper (2% rule) | 61 | TP1 + 24h exit | +1.75 | +$7.16 |
| 17 Nov | PURR | paper (2% rule) | 56 | TP1 + TP2 | +0.62 | +$1.28 |
| 17 Nov | HMSTR | paper (2% rule) | 63 | Stop | −1.00 | −$1.94 |
| 18 Nov | RUNE | paper | 61 | TP1 + TP2 | +0.71 | +$2.24 |
| 19 Nov | MELANIA | live | 56 | 24h exit | +0.19 | +$0.57 |
| 19 Nov | SOPH | paper | 60 | 24h exit | −0.04 | −$0.08 |
| 19 Nov | STRK | live | 58 | TP1 + TP2 | +0.61 | +$1.42 |
| 19 Nov | 2Z | live | 56 | TP1 + 24h exit | +0.89 | +$1.27 |
| 19 Nov | SYRUP | live | 55 | TP1 + TP2 | +0.45 | +$0.94 |
| 19 Nov | ETHFI | live | 63 | TP1 + TP2 | +0.80 | +$1.79 |
| 19 Nov | USELESS | live | 61 | TP1 + TP2 | +0.96 | +$1.58 |
| 21 Nov | BLUR | live | 60 | TP1 + TP2 | +1.06 | +$2.77 |
| 22 Nov | ETHFI | live | 60 | Stop | −1.15 | −$4.34 |
| 23 Nov | STBL | live | 61 | TP1 + break-even | +0.22 | +$0.48 |
| 23 Nov | JTO | live | 56 | Stop | −1.03 | −$5.36 |
| 23 Nov | NEAR | live | 56 | Stop | −1.16 | −$3.33 |

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
