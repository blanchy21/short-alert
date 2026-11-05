#!/usr/bin/env python3
"""
Short Alert - hourly moon-dump short alerts for Hyperliquid (paper mode).

Uses moon_dump_monitor.py's scoring unchanged, plus the Short Seller rules:
  - score 55+ and NOT in the Day 2 bounce zone (peak > 24h ago)
  - "rolled over": peak at least 1h ago AND price at least 1% below the peak
  - BTC filter: no new shorts while BTC is above a rising 4h EMA21
  - stop = 1.5x ATR above entry, capped at 10%
  - one alert per coin per day, max hold 24h, paper day-stop at -$11.60

Sends Telegram alerts and keeps a paper-trade log in state/state.json.
Places NO orders.
"""

import json
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from moon_dump_monitor import (
    MIN_PUMP_PCT,
    MIN_VOLUME_USD,
    calc_24h_change,
    calc_atr,
    calc_ema,
    fetch_candles,
    fetch_meta_and_contexts,
    get_all_sr_levels,
    score_short_readiness,
)

# ---------------------------------------------------------------- settings
MIN_SCORE = 55
NEAR_MISS_SCORE = 45          # 45-54 gets logged as a near-miss
MIN_HOURS_SINCE_PEAK = 1
MAX_DROP_FROM_PEAK = -1.0     # price must be at least 1% below the peak
STOP_ATR_MULT = 1.5
MAX_STOP_PCT = 10.0
MAX_HOLD_HOURS = 24
RISK_PER_TRADE_USD = 1.16     # ~2% of the EUR50 (~$58) pot
DAILY_LOSS_LIMIT_USD = 11.60
BTC_EMA_PERIOD = 21           # on 4h candles
TALLY_HOUR_LOCAL = 21         # 21:00 Dublin
TZ = ZoneInfo("Europe/Dublin")

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state", "state.json")
HOUR_MS = 3_600_000


# ---------------------------------------------------------------- helpers
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def fmt(p: float) -> str:
    return f"{p:.6g}"


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    print("\n" + text + "\n")
    if not token or not chat_id:
        print("(Telegram not configured - message printed only)")
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=15,
        )
        if not r.ok:
            print(f"Telegram error {r.status_code}: {r.text[:200]}")
    except requests.RequestException as e:
        print(f"Telegram send failed: {e}")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"date": "", "alerted_today": [], "near_misses_today": {},
            "paper_pnl_today": 0.0, "last_tally_date": "", "open": [], "closed": []}


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    state["closed"] = state["closed"][-500:]
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def roll_day(state: dict, today: str) -> None:
    if state.get("date") != today:
        state["date"] = today
        state["alerted_today"] = []
        state["near_misses_today"] = {}
        state["paper_pnl_today"] = 0.0


# ---------------------------------------------------------------- BTC filter
def btc_filter() -> dict:
    candles = fetch_candles("BTC", "4h", 80)
    closes = [float(c["c"]) for c in candles] if isinstance(candles, list) else []
    if len(closes) < BTC_EMA_PERIOD + 2:
        # No data: fail safe and block new shorts
        return {"blocks": True, "note": "BTC data unavailable - blocking new shorts"}
    ema = calc_ema(closes, BTC_EMA_PERIOD)
    above, rising = closes[-1] > ema[-1], ema[-1] > ema[-2]
    blocks = above and rising
    trend = "uptrend (above rising 4h EMA)" if blocks else (
        "below 4h EMA" if not above else "above a flat/falling 4h EMA")
    return {"blocks": blocks, "price": closes[-1], "ema": ema[-1], "note": f"BTC {trend}"}


# ---------------------------------------------------------------- trade levels
def trade_levels(candles: list) -> dict:
    entry = float(candles[-1]["c"])
    atr = calc_atr(candles)
    stop = entry + STOP_ATR_MULT * atr if atr else entry * 1.02
    stop = min(stop, entry * (1 + MAX_STOP_PCT / 100))

    sr = get_all_sr_levels(candles)
    strong = [s for s in sr.get("supports", []) if s["strength"] >= 2 and s["price"] < entry]
    if strong:
        tp1, tp1_src = strong[0]["price"], strong[0]["type"]
    else:
        tp1, tp1_src = (entry - 2 * atr if atr else entry * 0.97), "2x ATR"
    resist = sr.get("resistances", [])
    return {
        "entry": entry, "stop": stop, "tp1": tp1, "tp1_src": tp1_src,
        "res_stop": resist[0]["price"] if resist else None,
        "risk_pct": (stop - entry) / entry * 100,
        "tp1_pct": (tp1 - entry) / entry * 100,
    }


# ---------------------------------------------------------------- paper trades
def update_open_trades(state: dict, marks: dict) -> list:
    """Close paper trades on stop / TP1 / 24h. Returns closing messages."""
    msgs, still_open = [], []
    now_ms = int(time.time() * 1000)
    for t in state["open"]:
        candles = fetch_candles(t["coin"], "1h", MAX_HOLD_HOURS + 2)
        time.sleep(0.08)
        exit_px, reason = None, None
        for c in candles if isinstance(candles, list) else []:
            if int(c["t"]) <= t["entry_ms"]:
                continue  # candle opened before entry - its range is pre-trade
            if float(c["h"]) >= t["stop"]:          # check stop first (conservative)
                exit_px, reason = t["stop"], "STOP"
                break
            if float(c["l"]) <= t["tp1"]:
                exit_px, reason = t["tp1"], "TP1"
                break
        mark = marks.get(t["coin"])
        if exit_px is None and mark is not None:
            if mark >= t["stop"]:
                exit_px, reason = t["stop"], "STOP"
            elif mark <= t["tp1"]:
                exit_px, reason = t["tp1"], "TP1"
            elif now_ms - t["entry_ms"] >= MAX_HOLD_HOURS * HOUR_MS:
                exit_px, reason = mark, "24h TIME EXIT"
        if exit_px is None:
            still_open.append(t)
            continue
        r_mult = (t["entry"] - exit_px) / (t["stop"] - t["entry"])
        pnl = r_mult * RISK_PER_TRADE_USD
        t.update({"exit": exit_px, "exit_reason": reason, "r": round(r_mult, 2),
                  "pnl_usd": round(pnl, 2), "exit_time": now_utc().isoformat()})
        state["closed"].append(t)
        state["paper_pnl_today"] = round(state["paper_pnl_today"] + pnl, 2)
        icon = "✅" if pnl > 0 else "❌"
        msgs.append(f"{icon} PAPER CLOSE {t['coin']} — {reason}\n"
                    f"Entry {fmt(t['entry'])} → exit {fmt(exit_px)} | {r_mult:+.2f}R ({pnl:+.2f} USD)")
    state["open"] = still_open
    return msgs


# ---------------------------------------------------------------- daily tally
def tally_message(state: dict) -> str:
    today = state["date"]
    closed_today = [t for t in state["closed"]
                    if datetime.fromisoformat(t["exit_time"]).astimezone(TZ).strftime("%Y-%m-%d") == today]
    wins = sum(1 for t in closed_today if t["pnl_usd"] > 0)
    lines = [f"📊 SHORT ALERT — daily tally {today}",
             f"Alerts today: {len(state['alerted_today'])} {', '.join(state['alerted_today'])}".rstrip(),
             f"Paper trades closed: {len(closed_today)} ({wins} won) | P&L {state['paper_pnl_today']:+.2f} USD",
             f"Still open: {len(state['open'])} {', '.join(t['coin'] for t in state['open'])}".rstrip()]
    if state["near_misses_today"]:
        nm = "; ".join(f"{c} ({why})" for c, why in list(state["near_misses_today"].items())[:8])
        lines.append(f"Near-misses: {nm}")
    allc = state["closed"]
    if allc:
        w = sum(1 for t in allc if t["pnl_usd"] > 0)
        tot = sum(t["pnl_usd"] for t in allc)
        avg_r = sum(t["r"] for t in allc) / len(allc)
        lines.append(f"Since start: {len(allc)} trades, {w}/{len(allc)} won, {tot:+.2f} USD, avg {avg_r:+.2f}R")
    return "\n".join(lines)


# ---------------------------------------------------------------- main
def main() -> None:
    state = load_state()
    local_now = now_utc().astimezone(TZ)
    today = local_now.strftime("%Y-%m-%d")
    roll_day(state, today)

    universe, ctxs = fetch_meta_and_contexts()
    marks, candidates = {}, []
    for meta, ctx in zip(universe, ctxs):
        if meta.get("isDelisted"):
            continue
        try:
            coin = meta["name"]
            mark = float(ctx.get("markPx") or 0)
            prev = float(ctx.get("prevDayPx") or 0)
            vol = float(ctx.get("dayNtlVlm") or 0)
            funding = float(ctx.get("funding") or 0)
        except (TypeError, ValueError):
            continue
        if mark <= 0:
            continue
        marks[coin] = mark
        # Cheap pre-filter on the exchange's 24h change; exact check on candles below
        if vol >= MIN_VOLUME_USD and prev > 0 and (mark - prev) / prev * 100 >= MIN_PUMP_PCT - 2:
            candidates.append({"coin": coin, "funding": funding})

    # 1. Manage open paper trades
    for m in update_open_trades(state, marks):
        send_telegram(m)

    # 2. Market filter
    btc = btc_filter()
    print(btc["note"])
    day_stopped = state["paper_pnl_today"] <= -DAILY_LOSS_LIMIT_USD
    open_coins = {t["coin"] for t in state["open"]}

    # 3. Score mooners
    for cand in candidates:
        coin = cand["coin"]
        candles = fetch_candles(coin, "1h", 168)
        time.sleep(0.08)
        if not isinstance(candles, list) or len(candles) < 50:
            continue
        chg = calc_24h_change(candles)
        if chg is None or chg < MIN_PUMP_PCT:
            continue
        sd = score_short_readiness(candles, cand["funding"])
        rolled = sd["hours_since_peak"] >= MIN_HOURS_SINCE_PEAK and sd["drop_from_peak"] <= MAX_DROP_FROM_PEAK
        score = sd["score"]

        block = None
        if sd["bounce_risk"] == "CRITICAL":
            block = "Day 2 zone"
        elif score < MIN_SCORE:
            block = f"score {score}"
        elif not rolled:
            block = f"not rolled over ({sd['hours_since_peak']}h, {sd['drop_from_peak']:+.1f}%)"
        elif btc["blocks"]:
            block = "BTC uptrend"
        elif coin in state["alerted_today"] or coin in open_coins:
            block = "already alerted today"
        elif day_stopped:
            block = "paper day-stop hit"

        print(f"{coin:<8} {chg:+6.1f}% score {score:>3} {sd['bounce_risk']:<8} -> {block or 'ALERT'}")

        if block:
            if score >= NEAR_MISS_SCORE and block not in ("already alerted today",):
                state["near_misses_today"].setdefault(coin, f"{score}, {block}")
            continue

        lv = trade_levels(candles)
        if lv["tp1"] >= lv["entry"]:
            continue
        grade = "A+" if score >= 70 else "A"
        sigs = "\n".join(f"• {s}" for s in sd["signals"][:6])
        res = f"\n(Old resistance stop: {fmt(lv['res_stop'])})" if lv["res_stop"] else ""
        send_telegram(
            f"🔻 SHORT SETUP — {coin} | {grade} | score {score}/100\n"
            f"24h: {chg:+.1f}% | peak {sd['hours_since_peak']}h ago ({sd['drop_from_peak']:+.1f}%)\n"
            f"Entry ~{fmt(lv['entry'])}\n"
            f"Stop {fmt(lv['stop'])} (+{lv['risk_pct']:.1f}%, 1.5x ATR)\n"
            f"TP1 {fmt(lv['tp1'])} ({lv['tp1_pct']:.1f}%, {lv['tp1_src']})\n"
            f"Exit within {sd['exit_window']} — bounce risk {sd['bounce_risk']}\n"
            f"Funding {cand['funding']*100:.4f}% | {btc['note']}\n"
            f"{sigs}{res}\n"
            f"(Paper trade logged — no order placed)"
        )
        state["alerted_today"].append(coin)
        state["open"].append({
            "coin": coin, "score": score, "entry": lv["entry"], "stop": lv["stop"],
            "tp1": lv["tp1"], "entry_ms": int(time.time() * 1000),
            "entry_time": now_utc().isoformat(), "change_24h": round(chg, 2),
        })

    # 4. Daily tally at 21:00 Dublin (or first run after, if a run was delayed)
    if local_now.hour >= TALLY_HOUR_LOCAL and state.get("last_tally_date") != today:
        send_telegram(tally_message(state))
        state["last_tally_date"] = today

    save_state(state)


if __name__ == "__main__":
    main()
