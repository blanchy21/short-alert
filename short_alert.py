#!/usr/bin/env python3
"""
Short Alert - hourly moon-dump short alerts for Hyperliquid (paper mode).

Uses moon_dump_monitor.py's scoring unchanged, plus the Short Seller rules:
  - score 55+ and NOT in the Day 2 bounce zone (peak > 24h ago)
  - "rolled over": peak at least 1h ago AND price at least 1% below the peak
  - BTC filter: no new shorts while BTC is above a rising 4h EMA21
  - stop = 1.5x ATR above entry, capped at 10%; TP1 no further than -20%
  - one alert per coin per day, max hold 24h
  - Grokbot sizing: risk up to 10% of the pot, margin <= 25% of the pot, <= 5x isolated,
    max 3 open shorts, total open risk + today's losses <= 20% of the day-start pot,
    daily stop at -20% of the day-start pot, BTC/ETH excluded

Sends Telegram alerts and keeps a trade log in state/state.json.

TRADING_MODE=paper (default): places NO orders, paper-trades only.
TRADING_MODE=live: places a real short on Hyperliquid with an exchange-side
stop-loss and TP1 (see hl_trader.py). Switching back to paper stops new live
trades; any live trades already open keep being managed until they close.
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
# Sizing and caps - matched to Grokbot's Short Seller
RISK_PCT_OF_POT = 10.0        # risk up to 10% of the pot per trade (loss if the stop hits)
MAX_MARGIN_PCT_OF_POT = 25.0  # each short uses at most a quarter of the pot as margin
MAX_LEVERAGE = 5              # isolated, stepped down so liquidation sits well beyond the stop
LIQ_BUFFER_MULT = 1.5         # liquidation at least 1.5x the stop distance away
MAX_OPEN_SHORTS = 3
MAX_TOTAL_RISK_PCT = 20.0     # open shorts at their stops + today's losses <= 20% of day-start pot
DAILY_LOSS_PCT = 20.0         # daily stop: 20% of the day-start pot
MAX_TP_PCT = 20.0             # take profit no further than 20% below entry
TP1_CLOSE_FRACTION = 0.5      # take half at TP1, the rest at TP2
BREAKEVEN_PCT = 0.1           # after TP1, stop moves to 0.1% below entry (covers both fees)
EXCLUDED_COINS = {"BTC", "ETH"}
MIN_FUNDING = -0.0002         # hourly rate (-0.02%/h); skip if more negative (shorts paying heavily)
PAPER_START_POT = 58.0        # paper mode's starting pot (USD)
LEGACY_RISK_USD = 1.16        # risk of trades logged before sizing changed
BTC_EMA_PERIOD = 21           # on 4h candles
TALLY_HOUR_LOCAL = 21         # 21:00 Dublin
TZ = ZoneInfo("Europe/Dublin")

TRADING_MODE = os.environ.get("TRADING_MODE", "paper").strip().lower()
LIVE = TRADING_MODE == "live"

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


def warn_once(state: dict, key: str, text: str) -> None:
    """Send a warning to Telegram at most once per Dublin day per key (scans run every 5 min)."""
    sent = state.setdefault("warned_today", {})
    if sent.get(key) == state.get("date"):
        print(text)
        return
    sent[key] = state.get("date")
    send_telegram(text)


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
        state["day_start_pot"] = None


# ---------------------------------------------------------------- sizing
def pick_leverage(stop_pct: float, coin_max_lev: int) -> int:
    """Highest leverage <= MAX_LEVERAGE whose liquidation is LIQ_BUFFER_MULT x beyond the stop."""
    coin_max_lev = max(1, int(coin_max_lev or MAX_LEVERAGE))
    mm = 1 / (2 * coin_max_lev)  # Hyperliquid maintenance margin ~ half the initial margin at max leverage
    for lev in range(min(MAX_LEVERAGE, coin_max_lev), 0, -1):
        if (1 / lev - mm) * 100 >= LIQ_BUFFER_MULT * stop_pct:
            return lev
    return 1


def size_trade(pot: float, day_start_pot: float, open_risk: float, loss_today: float,
               stop_pct: float, lev: int) -> dict:
    """Returns {notional, risk_usd, lev} or {'block': reason}."""
    room = MAX_TOTAL_RISK_PCT / 100 * day_start_pot - open_risk - loss_today
    risk = min(RISK_PCT_OF_POT / 100 * pot, room)
    if risk <= 0:
        return {"block": f"risk cap full (open ${open_risk:.2f} + losses ${loss_today:.2f})"}
    notional = min(risk / (stop_pct / 100), MAX_MARGIN_PCT_OF_POT / 100 * pot * lev)
    if notional < 10:
        return {"block": f"size ${notional:.2f} under $10 minimum"}
    return {"notional": round(notional, 2), "risk_usd": round(notional * stop_pct / 100, 2), "lev": lev}


def trade_risk(t: dict) -> float:
    return t.get("risk_usd", LEGACY_RISK_USD)


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
    if tp1 < entry * (1 - MAX_TP_PCT / 100):
        tp1, tp1_src = entry * (1 - MAX_TP_PCT / 100), f"-{MAX_TP_PCT:.0f}% cap"
    # TP2: next strong support below TP1 (at least 0.5% further), else twice TP1's distance
    deeper = [s for s in strong if s["price"] < tp1 * 0.995]
    if deeper:
        tp2, tp2_src = deeper[0]["price"], deeper[0]["type"]
    else:
        tp2, tp2_src = entry - 2 * (entry - tp1), "2x TP1 distance"
    if tp2 < entry * (1 - MAX_TP_PCT / 100):
        tp2, tp2_src = entry * (1 - MAX_TP_PCT / 100), f"-{MAX_TP_PCT:.0f}% cap"
    resist = sr.get("resistances", [])
    return {
        "entry": entry, "stop": stop, "tp1": tp1, "tp1_src": tp1_src,
        "tp2": tp2, "tp2_src": tp2_src, "tp2_pct": (tp2 - entry) / entry * 100,
        "res_stop": resist[0]["price"] if resist else None,
        "risk_pct": (stop - entry) / entry * 100,
        "tp1_pct": (tp1 - entry) / entry * 100,
    }


# ---------------------------------------------------------------- live trader
def get_trader():
    """Return a hl_trader.Trader, or (None, error text)."""
    try:
        from hl_trader import Trader
        return Trader(), None
    except Exception as e:  # missing keys, SDK, network...
        return None, str(e)


def breakeven_px(t: dict) -> float:
    return t["entry"] * (1 - BREAKEVEN_PCT / 100)


def classify_exit(t: dict, last_px: float) -> str:
    """Name the exit from where the final fill happened."""
    if t.get("tp2") and last_px <= t["tp2"] * 1.005:
        return "TP1 + TP2"
    if t.get("tp1_hit"):
        if last_px >= t["stop"] * 0.995:
            return "TP1 + break-even stop"
        return "TP1 + CLOSED"
    if last_px >= t["stop"] * 0.995:
        return "STOP"
    if last_px <= t["tp1"] * 1.005:
        return "TP1"
    return "CLOSED"


def manage_live_trade(t: dict, trader, marks: dict, now_ms: int):
    """Returns ("open", message|None) or ("closed", (exit_px, reason, pnl_usd))."""
    coin = t["coin"]
    pos = abs(trader.position(coin))
    if pos > 0:
        # TP1 filled (position shrank): move the stop to break-even for the rest
        if t.get("tp2") and not t.get("tp1_hit") and pos < t["size"] * 0.75:
            new_stop = trader.move_stop(coin, breakeven_px(t), t["tp2"])
            t.update(tp1_hit=True, stop=new_stop)
            return "open", (f"🎯 LIVE TP1 hit {coin} — {fmt(t['size'] - pos)} closed at ~{fmt(t['tp1'])}\n"
                            f"Stop moved to break-even {fmt(new_stop)} for the other {fmt(pos)} | "
                            f"TP2 {fmt(t['tp2'])}")
        if now_ms - t["entry_ms"] < MAX_HOLD_HOURS * HOUR_MS:
            return "open", None
        trader.close(coin)
        trader.wait_flat(coin)
        forced = "24h TIME EXIT" + (" (after TP1)" if t.get("tp1_hit") else "")
    else:
        trader.cancel_all(coin)  # leftover stop/TP order
        forced = None
    fills = trader.closing_fills(coin, t["entry_ms"])
    if fills is None:
        return "closed", (marks.get(coin, t["entry"]), forced or "CLOSED (no fills found)", 0.0)
    return "closed", (fills["exit"], forced or classify_exit(t, fills.get("last_px", fills["exit"])), fills["pnl_usd"])


def paper_path(t: dict, candles: list, mark, now_ms: int) -> dict:
    """Replay a paper trade from its entry. Stop is checked before targets in each candle (conservative)."""
    stop0 = t.get("stop0", t["stop"])
    f = TP1_CLOSE_FRACTION if t.get("tp2") else 1.0
    tp1_hit, stop = False, stop0
    bars = [(float(c["h"]), float(c["l"])) for c in (candles if isinstance(candles, list) else [])
            if int(c["t"]) > t["entry_ms"]]  # candles that opened before entry are pre-trade
    if mark is not None:
        bars.append((mark, mark))
    for h, l in bars:
        if not tp1_hit:
            if h >= stop:
                return {"tp1_hit": False, "stop": stop, "exit": stop, "reason": "STOP"}
            if l <= t["tp1"]:
                if f >= 1.0:
                    return {"tp1_hit": True, "stop": stop, "exit": t["tp1"], "reason": "TP1"}
                tp1_hit, stop = True, breakeven_px(t)
                continue  # rest is judged from the next bar
        else:
            if h >= stop:
                return {"tp1_hit": True, "stop": stop, "exit": stop, "reason": "TP1 + break-even stop"}
            if l <= t["tp2"]:
                return {"tp1_hit": True, "stop": stop, "exit": t["tp2"], "reason": "TP1 + TP2"}
    if now_ms - t["entry_ms"] >= MAX_HOLD_HOURS * HOUR_MS and mark is not None:
        return {"tp1_hit": tp1_hit, "stop": stop, "exit": mark,
                "reason": "24h TIME EXIT" + (" (after TP1)" if tp1_hit else "")}
    return {"tp1_hit": tp1_hit, "stop": stop, "exit": None, "reason": None}


def paper_r(t: dict, exit_px: float, tp1_hit: bool) -> float:
    stop0 = t.get("stop0", t["stop"])
    risk = stop0 - t["entry"]
    if t.get("tp2") and tp1_hit:
        f = TP1_CLOSE_FRACTION
        return (f * (t["entry"] - t["tp1"]) + (1 - f) * (t["entry"] - exit_px)) / risk
    return (t["entry"] - exit_px) / risk


# ---------------------------------------------------------------- open trades
def close_trade(state: dict, t: dict, exit_px: float, reason: str, pnl: float, r_mult: float, kind: str) -> str:
    t.update({"exit": exit_px, "exit_reason": reason, "r": round(r_mult, 2),
              "pnl_usd": round(pnl, 2), "exit_time": now_utc().isoformat()})
    state["closed"].append(t)
    state["paper_pnl_today"] = round(state["paper_pnl_today"] + pnl, 2)
    icon = "✅" if pnl > 0 else "❌"
    after = " after fees" if kind == "LIVE" else ""
    return (f"{icon} {kind} CLOSE {t['coin']} — {reason}\n"
            f"Entry {fmt(t['entry'])} → exit {fmt(exit_px)} | {r_mult:+.2f}R ({pnl:+.2f} USD{after})")


def update_open_trades(state: dict, marks: dict, trader) -> list:
    """Manage open trades: TP1 (half) + break-even stop, TP2, stop, 24h. Returns Telegram messages."""
    msgs, still_open = [], []
    now_ms = int(time.time() * 1000)
    for t in state["open"]:
        t.setdefault("stop0", t["stop"])
        if t.get("live"):
            if trader is None:
                still_open.append(t)
                msgs.append(f"⚠️ Can't check LIVE {t['coin']} trade - Hyperliquid connection failed")
                continue
            try:
                status, info = manage_live_trade(t, trader, marks, now_ms)
            except Exception as e:
                still_open.append(t)
                msgs.append(f"⚠️ Error managing LIVE {t['coin']} trade: {e}")
                continue
            if status == "open":
                still_open.append(t)
                if info:
                    msgs.append(info)
                continue
            exit_px, reason, pnl = info
            msgs.append(close_trade(state, t, exit_px, reason, pnl, pnl / trade_risk(t), "LIVE"))
            continue

        candles = fetch_candles(t["coin"], "1h", MAX_HOLD_HOURS + 2)
        time.sleep(0.08)
        res = paper_path(t, candles, marks.get(t["coin"]), now_ms)
        if res["tp1_hit"] and not t.get("tp1_hit") and t.get("tp2"):
            t.update(tp1_hit=True, stop=res["stop"])
            if res["exit"] is None:
                msgs.append(f"🎯 PAPER TP1 hit {t['coin']} — half closed at {fmt(t['tp1'])}\n"
                            f"Stop moved to break-even {fmt(res['stop'])} | TP2 {fmt(t['tp2'])}")
        if res["exit"] is None:
            still_open.append(t)
            continue
        r_mult = paper_r(t, res["exit"], res["tp1_hit"])
        msgs.append(close_trade(state, t, res["exit"], res["reason"], r_mult * trade_risk(t), r_mult, "PAPER"))
    state["open"] = still_open
    return msgs


# ---------------------------------------------------------------- daily tally
def tally_message(state: dict) -> str:
    today = state["date"]
    closed_today = [t for t in state["closed"]
                    if datetime.fromisoformat(t["exit_time"]).astimezone(TZ).strftime("%Y-%m-%d") == today]
    wins = sum(1 for t in closed_today if t["pnl_usd"] > 0)
    live_n = sum(1 for t in closed_today if t.get("live"))
    lines = [f"📊 SHORT ALERT — daily tally {today} | mode: {TRADING_MODE.upper()}",
             f"Alerts today: {len(state['alerted_today'])} {', '.join(state['alerted_today'])}".rstrip(),
             f"Trades closed: {len(closed_today)} ({live_n} live, {wins} won) | P&L {state['paper_pnl_today']:+.2f} USD",
             f"Pot at day start: ${state.get('day_start_pot') or 0:.2f}",
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
    marks, candidates, max_lev = {}, [], {}
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
        max_lev[coin] = meta.get("maxLeverage", MAX_LEVERAGE)
        if coin in EXCLUDED_COINS:
            continue
        # Cheap pre-filter on the exchange's 24h change; exact check on candles below
        if vol >= MIN_VOLUME_USD and prev > 0 and (mark - prev) / prev * 100 >= MIN_PUMP_PCT - 2:
            candidates.append({"coin": coin, "funding": funding})

    # 0. Hyperliquid connection (live mode, or live trades still open)
    trader, trader_err = None, None
    if LIVE or any(t.get("live") for t in state["open"]):
        trader, trader_err = get_trader()
        if trader_err:
            print(f"Hyperliquid connection failed: {trader_err}")
            if LIVE:
                warn_once(state, "connection", f"⚠️ LIVE mode but Hyperliquid connection failed: {trader_err}\n"
                                               f"New setups will be paper-traded until fixed. "
                                               f"(This warning is sent once a day.)")
    print(f"Mode: {TRADING_MODE}" + (f" ({trader.network})" if trader else ""))

    # 1. Manage open trades
    for m in update_open_trades(state, marks, trader):
        if m.startswith("⚠️"):
            warn_once(state, m.split("\n")[0][:60], m)  # repeat problems: once a day
        else:
            send_telegram(m)

    # 2. Pot, caps and market filter
    pot = None
    if LIVE and trader:
        try:
            pot = trader.pot()
        except Exception as e:
            warn_once(state, "pot", f"⚠️ Couldn't read Hyperliquid account value: {e}\nNew setups will be paper-traded.")
            trader = None
    if pot is None:
        pot = PAPER_START_POT + sum(t["pnl_usd"] for t in state["closed"] if not t.get("live"))
    if not state.get("day_start_pot"):
        state["day_start_pot"] = round(pot, 2)
    day_start_pot = state["day_start_pot"]
    loss_today = max(0.0, -state["paper_pnl_today"])
    day_stopped = loss_today >= DAILY_LOSS_PCT / 100 * day_start_pot
    open_coins = {t["coin"] for t in state["open"]}
    if LIVE and trader:
        try:
            open_coins |= trader.open_coins()  # includes positions opened elsewhere (e.g. by hand)
        except Exception as e:
            print(f"Couldn't read exchange positions: {e}")
    print(f"Pot ${pot:.2f} (day start ${day_start_pot:.2f}) | open shorts {len(open_coins)} | "
          f"today {state['paper_pnl_today']:+.2f}")

    btc = btc_filter()
    print(btc["note"])

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
            block = "already alerted/open today"
        elif cand["funding"] < MIN_FUNDING:
            block = f"funding {cand['funding']*100:.4f}%/h too negative"
        elif day_stopped:
            block = "day-stop hit"
        elif len(open_coins) >= MAX_OPEN_SHORTS:
            block = f"{MAX_OPEN_SHORTS} shorts already open"

        print(f"{coin:<8} {chg:+6.1f}% score {score:>3} {sd['bounce_risk']:<8} -> {block or 'ALERT'}")

        if block:
            if score >= NEAR_MISS_SCORE and block != "already alerted/open today":
                state["near_misses_today"].setdefault(coin, f"{score}, {block}")
            continue

        lv = trade_levels(candles)
        if lv["tp1"] >= lv["entry"]:
            continue

        open_risk = sum(trade_risk(t) for t in state["open"])
        sz = size_trade(pot, day_start_pot, open_risk, loss_today, lv["risk_pct"],
                        pick_leverage(lv["risk_pct"], max_lev.get(coin)))
        if "block" in sz:
            print(f"         -> skipped: {sz['block']}")
            state["near_misses_today"].setdefault(coin, f"{score}, {sz['block']}")
            continue

        live = None
        if LIVE and trader:
            try:
                live = trader.open_short(coin, sz["notional"], sz["lev"], lv["risk_pct"], -lv["tp1_pct"],
                                         -lv["tp2_pct"], TP1_CLOSE_FRACTION)
                lv.update(entry=live["entry"], stop=live["stop"], tp1=live["tp1"], tp2=live["tp2"])
                lv["risk_pct"] = (lv["stop"] - lv["entry"]) / lv["entry"] * 100
                lv["tp1_pct"] = (lv["tp1"] - lv["entry"]) / lv["entry"] * 100
                if lv["tp2"]:
                    lv["tp2_pct"] = (lv["tp2"] - lv["entry"]) / lv["entry"] * 100
                sz.update(notional=live["notional"], risk_usd=live["risk_usd"])
            except Exception as e:
                send_telegram(f"⚠️ LIVE order for {coin} not placed: {e}\nLogged as a paper trade instead.")
        size_line = (f"Size ${sz['notional']:.2f} at {sz['lev']}x isolated "
                     f"(margin ${sz['notional'] / sz['lev']:.2f}) | risk ${sz['risk_usd']:.2f} "
                     f"= {sz['risk_usd'] / pot * 100:.1f}% of ${pot:.2f} pot")
        if live:
            footer = (f"💰 LIVE SHORT OPEN on Hyperliquid{' TESTNET' if live['network'] == 'testnet' else ''}: "
                      f"{live['size']} {coin} — stop" + (" & TP orders placed" if not live.get("tp_error") else
                      f" placed, ⚠️ TP order REJECTED ({live['tp_error']}) — set it by hand or let stop/24h exit"))
        else:
            footer = "(Paper trade logged — no order placed)"

        if lv.get("tp2"):
            tp_lines = (f"TP1 {fmt(lv['tp1'])} ({lv['tp1_pct']:.1f}%, {lv['tp1_src']}) — close half, "
                        f"then stop to break-even\n"
                        f"TP2 {fmt(lv['tp2'])} ({lv['tp2_pct']:.1f}%, {lv['tp2_src']}) — the other half")
        else:
            tp_lines = f"TP1 {fmt(lv['tp1'])} ({lv['tp1_pct']:.1f}%, {lv['tp1_src']}) — whole position"
        grade = "A+" if score >= 70 else "A"
        sigs = "\n".join(f"• {s}" for s in sd["signals"][:6])
        res = f"\n(Old resistance stop: {fmt(lv['res_stop'])})" if lv["res_stop"] else ""
        send_telegram(
            f"🔻 SHORT SETUP — {coin} | {grade} | score {score}/100\n"
            f"24h: {chg:+.1f}% | peak {sd['hours_since_peak']}h ago ({sd['drop_from_peak']:+.1f}%)\n"
            f"Entry ~{fmt(lv['entry'])}\n"
            f"Stop {fmt(lv['stop'])} (+{lv['risk_pct']:.1f}%, 1.5x ATR)\n"
            f"{tp_lines}\n"
            f"Exit within {sd['exit_window']} — bounce risk {sd['bounce_risk']}\n"
            f"Funding {cand['funding']*100:.4f}% | {btc['note']}\n"
            f"{sigs}{res}\n"
            f"{size_line}\n"
            f"{footer}"
        )
        state["alerted_today"].append(coin)
        trade = {
            "coin": coin, "score": score, "entry": lv["entry"], "stop": lv["stop"],
            "tp1": lv["tp1"], "tp2": lv.get("tp2"), "stop0": lv["stop"], "entry_ms": int(time.time() * 1000),
            "entry_time": now_utc().isoformat(), "change_24h": round(chg, 2),
            "risk_usd": sz["risk_usd"], "notional": sz["notional"], "leverage": sz["lev"],
        }
        if live:
            trade.update(live=True, size=live["size"], network=live["network"])
        state["open"].append(trade)
        open_coins.add(coin)
        save_state(state)  # record a live position straight away

    # 4. Daily tally at 21:00 Dublin (or first run after, if a run was delayed)
    if local_now.hour >= TALLY_HOUR_LOCAL and state.get("last_tally_date") != today:
        send_telegram(tally_message(state))
        state["last_tally_date"] = today

    save_state(state)


if __name__ == "__main__":
    main()
