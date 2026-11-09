#!/usr/bin/env python3
"""
Backtest for Short Alert. Read-only: places no orders, touches no state, sends nothing.

Replays the last DAYS of Hyperliquid 1h candles hour by hour. At each hour it runs the
live scanner's own code (score_short_readiness and trade_levels from short_alert.py) on
the 168 candles a live scan would see, applies the live entry rules, then follows each
trade through the next 24 hourly candles.

Every rule variant is tested on the same data, so the differences come from the rules.

Usage:  python backtest/backtest.py [--days 120] [--refresh]
Writes: backtest/results.md (the summary) and backtest/trades.csv (every trade, every variant)

Limits, so the numbers aren't over-read:
  - Hourly, not every 5 minutes: entries happen at hourly closes, not mid-candle.
  - Inside one candle the stop is assumed to hit before any target (conservative,
    same as the live paper mode).
  - Funding isn't replayed (history isn't in the candles). In practice the funding score
    and the -0.02%/h filter rarely apply.
  - Only coins listed today are included (delisted coins are missing).
  - Results are in R (1R = the loss if the stop hits), after 0.09% round-trip taker fees.
    Per-trade sizing and the pot aren't simulated; caps on open trades are.
"""

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import short_alert as sa  # noqa: E402
from moon_dump_monitor import calc_atr, calc_ema, score_short_readiness  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
API = "https://api.hyperliquid.xyz/info"
HOUR = 3_600_000
WINDOW = 168                 # candles a live scan fetches
FEE_ROUND_TRIP = 0.0009      # 0.045% taker in and out

# ---------------------------------------------------------------- variants
# Each variant changes one thing from the live rules ("baseline").
BASE = dict(min_score=sa.MIN_SCORE, min_drop=abs(sa.MAX_DROP_FROM_PEAK), min_hours=sa.MIN_HOURS_SINCE_PEAK,
            below_ema9=False, no_retest_h=0, stop_peak_buffer=sa.STOP_ABOVE_PEAK_PCT, min_tp1_r=0.0,
            tp1_floor_r=sa.MIN_TP1_R, be_guard=True)
VARIANTS = {
    "baseline (live rules)":         {},
    "rules 8-9 Nov (1% drop, ATR stop)": dict(min_drop=1.0, stop_peak_buffer=None),
    "rules before 8 Nov fix":        dict(min_drop=1.0, stop_peak_buffer=None, tp1_floor_r=0.0, be_guard=False),
    "drop >= 1% (stop 2% above peak)": dict(min_drop=1.0),
    "drop >= 5% from peak":          dict(min_drop=5.0),
    "close below 1h EMA9":           dict(below_ema9=True),
    "no peak retest in last 3h":     dict(no_retest_h=3),
    "stop >= 1% above peak":         dict(stop_peak_buffer=1.0),
    "ATR stop only (no peak floor)": dict(stop_peak_buffer=None),
    "score 50+":                     dict(min_score=50),
    "score 60+":                     dict(min_score=60),
    "EMA9 + stop 1% above peak":     dict(min_drop=1.0, below_ema9=True, stop_peak_buffer=1.0),
    "skip if TP1 < 0.75R":           dict(min_tp1_r=0.75),
    "skip if TP1 < 1R":              dict(min_tp1_r=1.0),
    "stop 2% above peak + TP1 >= 0.75R": dict(min_drop=1.0, min_tp1_r=0.75),
}
MEMO = {}  # (coin, i) -> (score data, levels): the same for every variant


# ---------------------------------------------------------------- data
def post(body, tries=4):
    for i in range(tries):
        try:
            r = requests.post(API, json=body, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def candles(coin, start_ms, end_ms, refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{coin.replace('/', '_')}.json")
    if not refresh and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    data = post({"type": "candleSnapshot",
                 "req": {"coin": coin, "interval": "1h", "startTime": start_ms, "endTime": end_ms}})
    data = data if isinstance(data, list) else []
    with open(path, "w") as f:
        json.dump(data, f)
    time.sleep(0.15)
    return data


def btc_blocks_at(btc, i):
    """Live BTC filter at 1h candle i: 4h candles built from 1h, last 4h candle in progress."""
    bars = btc[max(0, i - 80 * 4):i + 1]
    closes, cur = [], None
    for c in bars:
        bucket = int(c["t"]) // (4 * HOUR)
        if bucket != cur:
            closes.append(float(c["c"]))
            cur = bucket
        else:
            closes[-1] = float(c["c"])
    if len(closes) < sa.BTC_EMA_PERIOD + 2:
        return True
    ema = calc_ema(closes, sa.BTC_EMA_PERIOD)
    return closes[-1] > ema[-1] and ema[-1] > ema[-2]


# ---------------------------------------------------------------- one setup
def setup_at(win, v, key):
    """Live entry rules on a 168-candle window ending now. Returns trade levels or None."""
    closes = [float(c["c"]) for c in win]
    if key not in MEMO:
        MEMO[key] = [score_short_readiness(win, 0.0), {}]
    sd = MEMO[key][0]
    if sd["bounce_risk"] == "CRITICAL" or sd["score"] < v["min_score"]:
        return None
    if sd["hours_since_peak"] < v["min_hours"] or sd["drop_from_peak"] > -v["min_drop"]:
        return None
    if v["below_ema9"] and closes[-1] >= calc_ema(closes, 9)[-1]:
        return None
    if v["no_retest_h"] and max(float(c["h"]) for c in win[-v["no_retest_h"]:]) >= sd["peak_price"] * 0.99:
        return None
    lk = ("lv", v["tp1_floor_r"])
    if lk not in MEMO[key][1]:
        saved, sa.MIN_TP1_R = sa.MIN_TP1_R, v["tp1_floor_r"]
        MEMO[key][1][lk] = sa.trade_levels(win)
        sa.MIN_TP1_R = saved
    lv = dict(MEMO[key][1][lk])
    if lv["tp1"] >= lv["entry"]:
        return None
    if v["stop_peak_buffer"] is not None:
        floor = sd["peak_price"] * (1 + v["stop_peak_buffer"] / 100)
        lv["stop"] = min(max(lv["stop"], floor), lv["entry"] * (1 + sa.MAX_STOP_PCT / 100))
        lv["risk_pct"] = (lv["stop"] - lv["entry"]) / lv["entry"] * 100
    if v["min_tp1_r"] and (lv["entry"] - lv["tp1"]) < v["min_tp1_r"] * (lv["stop"] - lv["entry"]):
        return None
    return {**lv, "score": sd["score"], "drop": sd["drop_from_peak"], "hours_since_peak": sd["hours_since_peak"]}


def follow(t, after, be_guard=True):
    """Same path as live paper mode: stop first in each candle, half at TP1, rest at TP2. After TP1 the
    stop moves to break-even once a candle closes clearly below it (be_guard=False: straight away, the old rule)."""
    entry, stop0, tp1, tp2 = t["entry"], t["stop"], t["tp1"], t["tp2"]
    be = entry * (1 - sa.BREAKEVEN_PCT / 100)
    ready = lambda px: (not be_guard) or px < be * (1 - sa.BREAKEVEN_MARGIN_PCT / 100)
    f = sa.TP1_CLOSE_FRACTION
    tp1_hit, stop, exit_px, reason, held = False, stop0, None, None, 0
    for c in after[:sa.MAX_HOLD_HOURS]:
        held += 1
        h, lo, cl = float(c["h"]), float(c["l"]), float(c["c"])
        if h >= stop:
            exit_px, reason = stop, (("TP1 + break-even" if stop < stop0 else "TP1 + STOP") if tp1_hit else "STOP")
            break
        if not tp1_hit and lo <= tp1:
            tp1_hit = True
            if lo <= tp2:   # both targets inside one candle
                exit_px, reason = tp2, "TP1 + TP2"
                break
            if ready(cl):
                stop = be
            continue
        if tp1_hit and lo <= tp2:
            exit_px, reason = tp2, "TP1 + TP2"
            break
        if tp1_hit and stop >= stop0 and ready(cl):
            stop = be
    if exit_px is None:
        if len(after) < sa.MAX_HOLD_HOURS:
            return None  # still open at the end of the data
        exit_px = float(after[sa.MAX_HOLD_HOURS - 1]["c"])
        reason = "24h exit" + (" after TP1" if tp1_hit else "")
    risk = stop0 - entry
    gain = (f * (entry - tp1) + (1 - f) * (entry - exit_px)) if tp1_hit else (entry - exit_px)
    r = (gain - FEE_ROUND_TRIP * entry) / risk
    worst = max(float(c["h"]) for c in after[:held]) if held else entry
    return {"exit": exit_px, "reason": reason, "r": r, "held_h": held,
            "stop_pct": risk / entry * 100, "max_against_pct": (worst / entry - 1) * 100}


# ---------------------------------------------------------------- run
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=120)
    ap.add_argument("--refresh", action="store_true", help="re-download candles")
    args = ap.parse_args()

    end_ms = (int(time.time() * 1000) // HOUR) * HOUR
    start_ms = end_ms - (args.days * 24 + WINDOW + 24) * HOUR
    universe = post({"type": "metaAndAssetCtxs"})[0]["universe"]
    coins = [m["name"] for m in universe if not m.get("isDelisted") and m["name"] not in sa.EXCLUDED_COINS]

    print(f"Loading 1h candles for {len(coins) + 1} coins ({args.days} days)...", flush=True)
    btc = candles("BTC", start_ms, end_ms, args.refresh)
    btc_idx = {int(c["t"]): i for i, c in enumerate(btc)}
    data = {}
    for n, coin in enumerate(coins, 1):
        cs = candles(coin, start_ms, end_ms, args.refresh)
        if len(cs) >= WINDOW + 24:
            data[coin] = cs
        if n % 50 == 0:
            print(f"  {n}/{len(coins)}", flush=True)

    first_test_ms = end_ms - args.days * 24 * HOUR
    # Scan points: each coin-hour where the live pre-filters pass (24h >= 5%, 24h volume >= $200k)
    scans = []  # (t_ms, coin, i)
    for coin, cs in data.items():
        for i in range(WINDOW - 1, len(cs)):
            t = int(cs[i]["t"])
            if t < first_test_ms:
                continue
            o24 = float(cs[i - 23]["o"])
            if o24 <= 0 or (float(cs[i]["c"]) / o24 - 1) * 100 < sa.MIN_PUMP_PCT:
                continue
            vol = sum(float(c["v"]) * float(c["c"]) for c in cs[i - 23:i + 1])
            if vol < sa.MIN_VOLUME_USD:
                continue
            scans.append((t, coin, i))
    scans.sort()
    print(f"{len(scans)} coin-hours up 5%+ to score", flush=True)

    # Score once per coin-hour (shared by variants that only differ in later rules)
    results, all_rows = {}, []
    for name, change in VARIANTS.items():
        v = {**BASE, **change}
        open_until = []                  # exit times of open trades
        traded = set()                   # (coin, Dublin date)
        trades = []
        for t, coin, i in scans:
            cs = data[coin]
            day = datetime.fromtimestamp(t / 1000, timezone.utc).astimezone(sa.TZ).strftime("%Y-%m-%d")
            if (coin, day) in traded:
                continue
            bi = btc_idx.get(t)
            if bi is None or btc_blocks_at(btc, bi):
                continue
            close_ms = t + HOUR          # the candle's close: entry time
            open_until = [x for x in open_until if x > close_ms]
            if len(open_until) >= sa.MAX_OPEN_SHORTS:
                continue
            s = setup_at(cs[i - WINDOW + 1:i + 1], v, (coin, i))
            if not s:
                continue
            out = follow(s, cs[i + 1:], v["be_guard"])
            if not out:
                continue
            traded.add((coin, day))
            open_until.append(close_ms + out["held_h"] * HOUR)
            row = {"variant": name, "coin": coin,
                   "entry_time": datetime.fromtimestamp(close_ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M"),
                   "score": s["score"], "drop_from_peak": round(s["drop"], 2),
                   "hours_since_peak": s["hours_since_peak"], "entry": s["entry"], "stop": s["stop"],
                   "tp1": s["tp1"], "tp2": s["tp2"], **{k: (round(x, 3) if isinstance(x, float) else x)
                                                       for k, x in out.items()}}
            trades.append(row)
        results[name] = trades
        all_rows += trades
        print(f"  {name:<34} {len(trades):>4} trades", flush=True)

    with open(os.path.join(HERE, "trades.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()) if all_rows else ["variant"])
        w.writeheader()
        w.writerows(all_rows)
    write_report(results, args.days, len(data), first_test_ms, end_ms)


def stats(trades):
    rs = [t["r"] for t in trades]
    if not rs:
        return None
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    eq, peak, dd = 0.0, 0.0, 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
    reasons = defaultdict(int)
    for t in trades:
        reasons[t["reason"].split(" after")[0]] += 1
    return {"n": len(rs), "win": len(wins) / len(rs) * 100, "avg": sum(rs) / len(rs), "total": sum(rs),
            "pf": (sum(wins) / -sum(losses)) if losses and sum(losses) < 0 else float("inf"),
            "dd": dd, "avg_win": sum(wins) / len(wins) if wins else 0,
            "avg_loss": sum(losses) / len(losses) if losses else 0,
            "stop_rate": reasons.get("STOP", 0) / len(rs) * 100, "reasons": dict(reasons)}


def write_report(results, days, n_coins, start_ms, end_ms):
    d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%d %b %Y")
    lines = [f"# Backtest results", "",
             f"{d(start_ms)} to {d(end_ms)} ({days} days), {n_coins} Hyperliquid coins, hourly candles. "
             f"R after fees; 1R = the loss if the stop hits. Generated {d(int(time.time() * 1000))} by "
             f"`backtest/backtest.py`.", "",
             "| Rules | Trades | Win % | Avg R | Total R | Profit factor | Worst run (R) | Stopped % | "
             "1st half R | 2nd half R |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    mid = datetime.fromtimestamp((start_ms + end_ms) / 2000, timezone.utc).strftime("%Y-%m-%d %H:%M")
    for name, trades in results.items():
        s = stats(trades)
        if not s:
            lines.append(f"| {name} | 0 | | | | | | | | |")
            continue
        pf = "∞" if s["pf"] == float("inf") else f"{s['pf']:.2f}"
        lines.append(f"| {name} | {s['n']} | {s['win']:.0f}% | {s['avg']:+.2f} | {s['total']:+.1f} | {pf} | "
                     f"{s['dd']:.1f} | {s['stop_rate']:.0f}% | "
                     f"{sum(t['r'] for t in trades if t['entry_time'] < mid):+.1f} | "
                     f"{sum(t['r'] for t in trades if t['entry_time'] >= mid):+.1f} |")
    lines += ["", "## How trades ended", "", "| Rules | " + " | ".join(
        ["STOP", "TP1 + STOP", "TP1 + break-even", "TP1 + TP2", "24h exit"]) + " |", "|---|---|---|---|---|---|"]
    for name, trades in results.items():
        s = stats(trades)
        if s:
            rs = s["reasons"]
            lines.append(f"| {name} | " + " | ".join(str(rs.get(k, 0)) for k in
                                                     ["STOP", "TP1 + STOP", "TP1 + break-even", "TP1 + TP2",
                                                      "24h exit"]) + " |")
    with open(os.path.join(HERE, "results.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
