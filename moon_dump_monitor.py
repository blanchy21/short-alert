#!/usr/bin/env python3
"""
Moon-Dump Monitor for Hyperliquid Perps
=========================================
Tracks tokens that had big % increases ("mooned") and monitors
whether they dump the following day. Short-sell opportunity scanner.

KEY FINDING: ~90% of mooners dump on Day 1, but ~79% BOUNCE on Day 2.
This means the short window is TIGHT - enter on rollover, exit within 12-24h.

Strategy:
1. Finds the top 10 biggest % gainers over the last 24h
2. Checks multi-day history: Day 1 dump rate AND Day 2 bounce rate
3. Scores each token for short entry readiness using momentum indicators
4. Calculates optimal exit window based on historical bounce timing
5. Flags when a mooner is rolling over (short signal)

Run: python3 moon_dump_monitor.py
"""

import requests
import json
import time
import os
import csv
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional

API_URL = "https://api.hyperliquid.xyz/info"
HISTORY_FILE = "moon_dump_history.csv"
TOP_N = 10  # Track top 10 mooners
MIN_PUMP_PCT = 5.0  # Minimum % gain to count as a "moon"
MIN_VOLUME_USD = 200000  # Filter illiquid garbage


# =============================================================================
# API FUNCTIONS
# =============================================================================

def fetch_meta_and_contexts() -> Tuple[List[Dict], List[Dict]]:
    payload = {"type": "metaAndAssetCtxs"}
    resp = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
    data = resp.json()
    return data[0]["universe"], data[1]


def fetch_candles(coin: str, interval: str = "1h", num_candles: int = 168) -> List[Dict]:
    end_time = int(time.time() * 1000)
    interval_ms = {
        "5m": 300000, "15m": 900000, "30m": 1800000,
        "1h": 3600000, "4h": 14400000, "1D": 86400000,
    }
    start_time = end_time - (interval_ms.get(interval, 3600000) * num_candles)
    payload = {
        "type": "candleSnapshot",
        "req": {"coin": coin, "interval": interval, "startTime": start_time, "endTime": end_time}
    }
    try:
        resp = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
        return resp.json()
    except:
        return []


# =============================================================================
# INDICATOR FUNCTIONS
# =============================================================================

def calc_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calc_ema(data: List[float], period: int) -> List[float]:
    if not data:
        return []
    result = [data[0]]
    mult = 2.0 / (period + 1)
    for i in range(1, len(data)):
        result.append((data[i] - result[-1]) * mult + result[-1])
    return result


def calc_macd(closes: List[float]) -> Tuple[float, float, float]:
    if len(closes) < 26:
        return 0, 0, 0
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]
    signal = calc_ema(macd_line, 9)
    histogram = macd_line[-1] - signal[-1]
    return macd_line[-1], signal[-1], histogram


def calc_stoch_rsi(closes: List[float], period: int = 14) -> Tuple[float, float]:
    if len(closes) < period + 14:
        return 50, 50
    rsi_values = []
    for i in range(period, len(closes)):
        rsi_values.append(calc_rsi(closes[:i + 1], period))
    if len(rsi_values) < 14:
        return 50, 50
    recent = rsi_values[-14:]
    min_rsi = min(recent)
    max_rsi = max(recent)
    if max_rsi == min_rsi:
        k = 50
    else:
        k = ((rsi_values[-1] - min_rsi) / (max_rsi - min_rsi)) * 100
    k_values = []
    for i in range(max(0, len(rsi_values) - 3), len(rsi_values)):
        mn = min(rsi_values[max(0, i - 13):i + 1])
        mx = max(rsi_values[max(0, i - 13):i + 1])
        k_values.append(((rsi_values[i] - mn) / (mx - mn)) * 100 if mx != mn else 50)
    d = sum(k_values) / len(k_values) if k_values else 50
    return k, d


def calc_bollinger_position(closes: List[float], period: int = 20) -> float:
    if len(closes) < period:
        return 0.5
    recent = closes[-period:]
    sma = sum(recent) / period
    std = (sum((x - sma) ** 2 for x in recent) / period) ** 0.5
    if std == 0:
        return 0.5
    upper = sma + 2 * std
    lower = sma - 2 * std
    return (closes[-1] - lower) / (upper - lower) if upper != lower else 0.5


def calc_atr(candles: List[Dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0
    trs = []
    for i in range(1, len(candles)):
        h = float(candles[i]["h"])
        l = float(candles[i]["l"])
        pc = float(candles[i - 1]["c"])
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-period:]) / period


# =============================================================================
# SUPPORT & RESISTANCE LEVELS
# =============================================================================

def calc_pivot_points(candles_1h: List[Dict], lookback: int = 24) -> Dict:
    """Classic pivot points from the last 24h session.
    R3/R2/R1/Pivot/S1/S2/S3 - used to identify key levels."""
    if not candles_1h or len(candles_1h) < lookback:
        return {}
    session = candles_1h[-lookback:]
    high = max(float(c["h"]) for c in session)
    low = min(float(c["l"]) for c in session)
    close = float(session[-1]["c"])
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)
    return {
        "R3": r3, "R2": r2, "R1": r1, "Pivot": pivot,
        "S1": s1, "S2": s2, "S3": s3,
        "high_24h": high, "low_24h": low,
    }


def calc_swing_levels(candles_1h: List[Dict], lookback: int = 72, window: int = 5) -> Dict:
    """Find swing highs and swing lows over the last N hours.
    A swing high = a candle high that is higher than `window` candles on each side.
    Returns the most recent/relevant levels."""
    if not candles_1h or len(candles_1h) < lookback:
        return {"swing_highs": [], "swing_lows": []}
    segment = candles_1h[-lookback:]
    swing_highs = []
    swing_lows = []
    for i in range(window, len(segment) - window):
        h = float(segment[i]["h"])
        l = float(segment[i]["l"])
        is_high = all(h >= float(segment[j]["h"]) for j in range(i - window, i + window + 1) if j != i)
        is_low = all(l <= float(segment[j]["l"]) for j in range(i - window, i + window + 1) if j != i)
        hrs_ago = len(segment) - 1 - i
        if is_high:
            swing_highs.append({"price": h, "hours_ago": hrs_ago})
        if is_low:
            swing_lows.append({"price": l, "hours_ago": hrs_ago})
    # Sort by recency
    swing_highs.sort(key=lambda x: x["hours_ago"])
    swing_lows.sort(key=lambda x: x["hours_ago"])
    return {"swing_highs": swing_highs[:5], "swing_lows": swing_lows[:5]}


def calc_fib_retracement(candles_1h: List[Dict], lookback: int = 72) -> Dict:
    """Fibonacci retracement levels from the recent pump's low to high.
    For shorts: retrace levels are where price might bounce (support).
    For entries: fib extensions above are resistance (short entry zones)."""
    if not candles_1h or len(candles_1h) < lookback:
        return {}
    segment = candles_1h[-lookback:]
    highs = [float(c["h"]) for c in segment]
    lows = [float(c["l"]) for c in segment]
    peak_idx = highs.index(max(highs))
    # Find the low BEFORE the peak (the pump start)
    pre_peak = segment[:peak_idx + 1] if peak_idx > 0 else segment[:1]
    swing_low = min(float(c["l"]) for c in pre_peak)
    swing_high = max(highs)
    diff = swing_high - swing_low
    if diff == 0:
        return {}
    return {
        "swing_high": swing_high,
        "swing_low": swing_low,
        "fib_236": swing_high - 0.236 * diff,
        "fib_382": swing_high - 0.382 * diff,
        "fib_500": swing_high - 0.500 * diff,
        "fib_618": swing_high - 0.618 * diff,
        "fib_786": swing_high - 0.786 * diff,
        "ext_1272": swing_high + 0.272 * diff,
        "ext_1618": swing_high + 0.618 * diff,
    }


def calc_ema_levels(candles_1h: List[Dict]) -> Dict:
    """Current EMA values as dynamic S/R."""
    if not candles_1h or len(candles_1h) < 55:
        return {}
    closes = [float(c["c"]) for c in candles_1h]
    ema9 = calc_ema(closes, 9)[-1]
    ema21 = calc_ema(closes, 21)[-1]
    ema55 = calc_ema(closes, 55)[-1]
    return {"EMA9": ema9, "EMA21": ema21, "EMA55": ema55}


def calc_vwap(candles_1h: List[Dict], lookback: int = 24) -> float:
    """Session VWAP over last 24h."""
    if not candles_1h or len(candles_1h) < lookback:
        return 0
    session = candles_1h[-lookback:]
    cum_vol = 0
    cum_vwap = 0
    for c in session:
        typical = (float(c["h"]) + float(c["l"]) + float(c["c"])) / 3
        vol = float(c["v"])
        cum_vol += vol
        cum_vwap += typical * vol
    return cum_vwap / cum_vol if cum_vol > 0 else 0


def get_all_sr_levels(candles_1h: List[Dict]) -> Dict:
    """Calculate all S/R levels for a coin. Returns a dict with all level types."""
    pivots = calc_pivot_points(candles_1h)
    swings = calc_swing_levels(candles_1h, lookback=96, window=4)
    fibs = calc_fib_retracement(candles_1h, lookback=96)
    emas = calc_ema_levels(candles_1h)
    vwap = calc_vwap(candles_1h)

    current_price = float(candles_1h[-1]["c"]) if candles_1h else 0

    # Build consolidated resistance levels (above price) - short entry zones
    resistances = []
    if pivots:
        for label in ["R1", "R2", "R3"]:
            if pivots[label] > current_price:
                resistances.append({"price": pivots[label], "type": f"Pivot {label}", "strength": 2})
        if pivots.get("high_24h", 0) > current_price:
            resistances.append({"price": pivots["high_24h"], "type": "24h High", "strength": 3})
    if fibs:
        if fibs.get("swing_high", 0) > current_price:
            resistances.append({"price": fibs["swing_high"], "type": "Pump Peak", "strength": 3})
        if fibs.get("ext_1272", 0) > current_price:
            resistances.append({"price": fibs["ext_1272"], "type": "Fib 1.272 ext", "strength": 1})
    for sh in swings.get("swing_highs", []):
        if sh["price"] > current_price * 1.001:  # slight buffer
            resistances.append({"price": sh["price"], "type": f"Swing High ({sh['hours_ago']}h)", "strength": 2})
    if emas:
        for label in ["EMA9", "EMA21", "EMA55"]:
            if emas[label] > current_price:
                resistances.append({"price": emas[label], "type": label, "strength": 1})

    # Build consolidated support levels (below price) - TP zones / close short zones
    supports = []
    if pivots:
        for label in ["S1", "S2", "S3"]:
            if pivots[label] < current_price:
                supports.append({"price": pivots[label], "type": f"Pivot {label}", "strength": 2})
        if pivots.get("low_24h", 0) < current_price:
            supports.append({"price": pivots["low_24h"], "type": "24h Low", "strength": 3})
    if fibs:
        for label, key in [("Fib 23.6%", "fib_236"), ("Fib 38.2%", "fib_382"),
                           ("Fib 50%", "fib_500"), ("Fib 61.8%", "fib_618"),
                           ("Fib 78.6%", "fib_786")]:
            if fibs.get(key, 0) < current_price:
                strength = 3 if "61.8" in label or "50" in label else 2
                supports.append({"price": fibs[key], "type": label, "strength": strength})
    for sl in swings.get("swing_lows", []):
        if sl["price"] < current_price * 0.999:
            supports.append({"price": sl["price"], "type": f"Swing Low ({sl['hours_ago']}h)", "strength": 2})
    if emas:
        for label in ["EMA9", "EMA21", "EMA55"]:
            if emas[label] < current_price:
                supports.append({"price": emas[label], "type": label, "strength": 1})
    if vwap and vwap < current_price:
        supports.append({"price": vwap, "type": "VWAP", "strength": 2})
    elif vwap and vwap > current_price:
        resistances.append({"price": vwap, "type": "VWAP", "strength": 2})

    # Sort: resistances ascending (nearest first), supports descending (nearest first)
    resistances.sort(key=lambda x: x["price"])
    supports.sort(key=lambda x: x["price"], reverse=True)

    # Cluster nearby levels (within 0.5% of each other)
    def cluster_levels(levels):
        if not levels:
            return levels
        clustered = [levels[0].copy()]
        for lv in levels[1:]:
            prev = clustered[-1]
            if abs(lv["price"] - prev["price"]) / prev["price"] < 0.005:
                # Merge: keep higher strength, note confluence
                if lv["strength"] > prev["strength"]:
                    clustered[-1]["price"] = lv["price"]
                clustered[-1]["strength"] = min(prev["strength"] + lv["strength"], 5)
                clustered[-1]["type"] += f" + {lv['type']}"
            else:
                clustered.append(lv.copy())
        return clustered

    resistances = cluster_levels(resistances)
    supports = cluster_levels(supports)

    return {
        "current_price": current_price,
        "resistances": resistances[:5],  # Top 5 nearest
        "supports": supports[:5],
        "pivots": pivots,
        "fibs": fibs,
        "vwap": vwap,
    }


def format_sr_display(sr: Dict, coin: str) -> str:
    """Format S/R levels for terminal display."""
    lines = []
    price = sr["current_price"]
    if not price:
        return "  No S/R data available"

    # Resistance (short entry / stop loss zones)
    lines.append(f"  RESISTANCE (short entry / stop loss zones):")
    if sr["resistances"]:
        for r in sr["resistances"][:4]:
            dist = ((r["price"] - price) / price) * 100
            stars = "*" * min(r["strength"], 5)
            lines.append(f"    ${r['price']:<12.5g} {dist:>+6.2f}%  {stars:<5} {r['type']}")
    else:
        lines.append(f"    Price is above all resistance - extreme territory")

    lines.append(f"  ---- PRICE NOW: ${price:<12.5g} ----")

    # Support (take profit / close short zones)
    lines.append(f"  SUPPORT (take profit / close short zones):")
    if sr["supports"]:
        for s in sr["supports"][:4]:
            dist = ((s["price"] - price) / price) * 100
            stars = "*" * min(s["strength"], 5)
            lines.append(f"    ${s['price']:<12.5g} {dist:>+6.2f}%  {stars:<5} {s['type']}")
    else:
        lines.append(f"    No support found - freefall territory")

    return "\n".join(lines)


# =============================================================================
# MULTI-DAY CHANGE FUNCTIONS
# =============================================================================

def calc_24h_change(candles_1h: List[Dict]) -> Optional[float]:
    if not candles_1h or len(candles_1h) < 24:
        return None
    price_now = float(candles_1h[-1]["c"])
    price_24h_ago = float(candles_1h[-24]["o"])
    if price_24h_ago == 0:
        return None
    return ((price_now - price_24h_ago) / price_24h_ago) * 100


def calc_period_change(candles_1h: List[Dict], start_offset: int, end_offset: int) -> Optional[float]:
    """Calculate % change between two hourly offsets from the end.
    e.g. start_offset=48, end_offset=24 = the 24h period from 48h ago to 24h ago."""
    if not candles_1h or len(candles_1h) < start_offset:
        return None
    start_idx = -start_offset
    end_idx = -end_offset if end_offset > 0 else len(candles_1h)
    price_start = float(candles_1h[start_idx]["o"])
    price_end = float(candles_1h[end_idx - 1]["c"]) if end_offset > 0 else float(candles_1h[-1]["c"])
    if price_start == 0:
        return None
    return ((price_end - price_start) / price_start) * 100


def find_pump_peak_hours(candles_1h: List[Dict], pump_window_start: int, pump_window_end: int) -> Optional[int]:
    """Find how many hours after pump start the price peaked.
    Returns hours from pump start to highest price."""
    if not candles_1h or len(candles_1h) < pump_window_start:
        return None
    start_idx = len(candles_1h) - pump_window_start
    end_idx = len(candles_1h) - pump_window_end if pump_window_end > 0 else len(candles_1h)
    segment = candles_1h[start_idx:end_idx]
    if not segment:
        return None
    peak_idx = max(range(len(segment)), key=lambda i: float(segment[i]["h"]))
    return peak_idx


# =============================================================================
# SHORT READINESS SCORING
# =============================================================================

def calc_hours_since_peak(candles_1h: List[Dict], lookback: int = 48) -> Tuple[int, float]:
    """How many hours ago was the local high? Returns (hours_ago, peak_price)."""
    if not candles_1h or len(candles_1h) < lookback:
        return 0, 0
    recent = candles_1h[-lookback:]
    peak_idx = max(range(len(recent)), key=lambda i: float(recent[i]["h"]))
    hours_ago = len(recent) - 1 - peak_idx
    peak_price = float(recent[peak_idx]["h"])
    return hours_ago, peak_price


def calc_drop_from_peak(candles_1h: List[Dict], lookback: int = 48) -> float:
    """% drop from recent peak to current price."""
    hours_ago, peak = calc_hours_since_peak(candles_1h, lookback)
    if peak == 0:
        return 0
    current = float(candles_1h[-1]["c"])
    return ((current - peak) / peak) * 100


def score_short_readiness(candles_1h: List[Dict], funding: float = 0) -> Dict:
    """
    Score how ready a token is to be shorted (0-100).
    Higher = better short opportunity.
    Factors in day-2 bounce risk for exit timing.
    """
    if not candles_1h or len(candles_1h) < 50:
        return {"score": 0, "signals": [], "rsi": 0, "macd_hist": 0,
                "exit_window": "N/A", "bounce_risk": "unknown"}

    closes = [float(c["c"]) for c in candles_1h]
    volumes = [float(c["v"]) for c in candles_1h]

    score = 0
    signals = []

    # --- ENTRY SIGNALS ---

    # 1. RSI overbought (max +20)
    rsi = calc_rsi(closes)
    if rsi > 80:
        score += 20
        signals.append(f"RSI extreme overbought ({rsi:.1f})")
    elif rsi > 70:
        score += 15
        signals.append(f"RSI overbought ({rsi:.1f})")
    elif rsi > 65:
        score += 8
        signals.append(f"RSI elevated ({rsi:.1f})")

    # 2. MACD histogram declining (max +20)
    _, _, hist = calc_macd(closes)
    _, _, hist_prev = calc_macd(closes[:-1])
    if hist < 0 and hist_prev > 0:
        score += 20
        signals.append("MACD histogram JUST flipped negative")
    elif hist < hist_prev and hist_prev > 0:
        score += 15
        signals.append("MACD histogram declining from positive")
    elif hist < hist_prev:
        score += 8
        signals.append("MACD histogram declining")

    # 3. Stochastic RSI overbought and crossing down (max +15)
    k, d = calc_stoch_rsi(closes)
    if k > 80 and k < d:
        score += 15
        signals.append(f"StochRSI bearish crossover in overbought ({k:.0f}/{d:.0f})")
    elif k > 80:
        score += 8
        signals.append(f"StochRSI overbought ({k:.0f})")

    # 4. Price at upper Bollinger Band (max +10)
    bb_pos = calc_bollinger_position(closes)
    if bb_pos > 0.95:
        score += 10
        signals.append(f"Price at upper BB ({bb_pos:.2f})")
    elif bb_pos > 0.85:
        score += 5
        signals.append(f"Price near upper BB ({bb_pos:.2f})")

    # 5. Bearish candle pattern (max +10)
    if len(closes) >= 4:
        last_red = closes[-1] < float(candles_1h[-1]["o"])
        prev_3_green = all(
            float(candles_1h[i]["c"]) > float(candles_1h[i]["o"])
            for i in range(-4, -1)
        )
        if last_red and prev_3_green:
            score += 10
            signals.append("Bearish reversal candle after 3 green")
        elif last_red:
            score += 3
            signals.append("Last candle red")

    # 6. Volume declining on up-move (max +10)
    if len(volumes) >= 6:
        vol_recent = sum(volumes[-3:]) / 3
        vol_prior = sum(volumes[-6:-3]) / 3
        if vol_recent < vol_prior * 0.7 and closes[-1] > closes[-6]:
            score += 10
            signals.append("Volume drying up on rally")
        elif vol_recent < vol_prior * 0.85:
            score += 5
            signals.append("Volume declining")

    # 7. EMA bearish cross (max +15)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    if len(ema9) >= 2 and len(ema21) >= 2:
        if ema9[-1] < ema21[-1] and ema9[-2] > ema21[-2]:
            score += 15
            signals.append("EMA 9/21 bearish cross!")
        elif ema9[-1] < ema21[-1]:
            score += 8
            signals.append("EMA 9 below 21")
        elif (ema9[-1] - ema21[-1]) < (ema9[-2] - ema21[-2]):
            score += 3
            signals.append("EMA 9/21 converging")

    # 8. Funding rate supports short (max +10)
    if funding > 0.01:
        score += 10
        signals.append(f"HIGH funding ({funding*100:.4f}%) - crowded longs")
    elif funding > 0.005:
        score += 5
        signals.append(f"Elevated funding ({funding*100:.4f}%) - longs paying")

    # --- EXIT TIMING / BOUNCE RISK ---
    hours_since_peak, peak_price = calc_hours_since_peak(candles_1h, 48)
    drop_from_peak = calc_drop_from_peak(candles_1h, 48)

    # Determine bounce risk level and exit window
    if hours_since_peak <= 6:
        bounce_risk = "LOW"
        exit_window = "18-24h"
        exit_note = "Fresh rollover. Full day-1 dump window ahead."
    elif hours_since_peak <= 12:
        bounce_risk = "LOW-MED"
        exit_window = "12-18h"
        exit_note = "Early dump phase. Good runway, take profit by tonight."
    elif hours_since_peak <= 18:
        bounce_risk = "MEDIUM"
        exit_window = "6-12h"
        exit_note = "Mid dump. Day-2 bounce approaching, tighten stop."
    elif hours_since_peak <= 24:
        bounce_risk = "HIGH"
        exit_window = "3-6h"
        exit_note = "Late day-1. Day-2 bounce imminent (79% bounce rate). Quick scalp only."
    else:
        bounce_risk = "CRITICAL"
        exit_window = "AVOID"
        exit_note = "Already in day-2 territory. 79% of mooners bounce here. DO NOT SHORT."
        score = max(score - 30, 0)  # Penalize score heavily
        signals.append("DAY-2 BOUNCE ZONE - high risk of reversal up")

    return {
        "score": min(score, 100),
        "signals": signals,
        "rsi": rsi,
        "macd_hist": hist,
        "stoch_k": k,
        "stoch_d": d,
        "bb_pos": bb_pos,
        "hours_since_peak": hours_since_peak,
        "drop_from_peak": drop_from_peak,
        "peak_price": peak_price,
        "bounce_risk": bounce_risk,
        "exit_window": exit_window,
        "exit_note": exit_note,
    }


# =============================================================================
# HISTORY TRACKING (now with multi-day data)
# =============================================================================

HISTORY_FIELDS = [
    "date", "coin", "pump_pct", "day1_pct", "day2_pct",
    "dumped_d1", "dumped_d2", "total_2d_pct", "rank"
]


def load_history() -> List[Dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    rows = []
    with open(HISTORY_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def save_history_row(row: Dict):
    exists = os.path.exists(HISTORY_FILE)
    with open(HISTORY_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def calc_dump_stats(history: List[Dict]) -> Dict:
    if not history:
        return {"total": 0, "d1_dumps": 0, "d1_pct": 0, "d2_dumps": 0,
                "d2_pct": 0, "d2_bounce": 0, "d2_bounce_pct": 0,
                "avg_d1_dump": 0, "avg_d2_change": 0}

    total = len(history)
    d1_dumps = 0
    d2_dumps = 0
    d2_bounces = 0
    d1_amounts = []
    d2_amounts = []

    for h in history:
        # Handle both old format (dumped/next_day_pct) and new format (dumped_d1/day1_pct)
        if "dumped_d1" in h:
            if h.get("dumped_d1") == "True":
                d1_dumps += 1
            d1_val = float(h.get("day1_pct", 0))
            d1_amounts.append(d1_val)
            if h.get("day2_pct", "") not in ("", "N/A"):
                d2_val = float(h["day2_pct"])
                d2_amounts.append(d2_val)
                if d2_val < 0:
                    d2_dumps += 1
                if h.get("dumped_d1") == "True" and d2_val > 0:
                    d2_bounces += 1
        elif "dumped" in h:
            # Legacy format
            if h.get("dumped") == "True":
                d1_dumps += 1
            d1_val = float(h.get("next_day_pct", 0))
            d1_amounts.append(d1_val)

    has_d2 = len(d2_amounts)

    return {
        "total": total,
        "d1_dumps": d1_dumps,
        "d1_pct": (d1_dumps / total * 100) if total > 0 else 0,
        "d2_total": has_d2,
        "d2_dumps": d2_dumps,
        "d2_pct": (d2_dumps / has_d2 * 100) if has_d2 > 0 else 0,
        "d2_bounces": d2_bounces,
        "d2_bounce_pct": (d2_bounces / has_d2 * 100) if has_d2 > 0 else 0,
        "avg_d1_dump": sum(d1_amounts) / len(d1_amounts) if d1_amounts else 0,
        "avg_d2_change": sum(d2_amounts) / len(d2_amounts) if d2_amounts else 0,
    }


# =============================================================================
# MAIN MONITOR
# =============================================================================

def run_monitor():
    print("\n" + "=" * 75)
    print("  MOON-DUMP MONITOR v2 - Hyperliquid Perps Short Scanner")
    print("  Strategy: Short mooners on Day 1 rollover, exit before Day 2 bounce")
    print("=" * 75)
    print(f"\n  Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Min pump threshold: {MIN_PUMP_PCT}%")
    print(f"  Tracking top {TOP_N} mooners")
    print(f"  Data: 7 days of 1h candles per coin\n")

    # Step 1: Get all markets
    print("  [1/5] Fetching market data...")
    universe, contexts = fetch_meta_and_contexts()

    markets = []
    for meta, ctx in zip(universe, contexts):
        coin = meta["name"]
        try:
            vol_24h = float(ctx.get("dayNtlVlm", 0))
            mark_px = float(ctx.get("markPx", 0))
            funding = float(ctx.get("funding", 0))
            oi = float(ctx.get("openInterest", 0))
        except:
            continue
        if vol_24h < MIN_VOLUME_USD:
            continue
        markets.append({
            "coin": coin, "vol_24h": vol_24h, "mark_px": mark_px,
            "funding": funding, "oi": oi,
        })

    print(f"        {len(markets)} markets above ${MIN_VOLUME_USD:,.0f} volume\n")

    # Step 2: Fetch 7 days of 1h candles
    print("  [2/5] Fetching 7-day candle data...")
    movers = []
    for i, m in enumerate(markets):
        candles = fetch_candles(m["coin"], "1h", 168)  # 7 days
        time.sleep(0.08)

        change_24h = calc_24h_change(candles)
        if change_24h is None:
            continue

        # Multi-day windows
        m["candles"] = candles
        m["change_24h"] = change_24h
        m["change_24_48"] = calc_period_change(candles, 48, 24)  # prev day
        m["change_48_72"] = calc_period_change(candles, 72, 48)  # 2 days ago
        m["change_72_96"] = calc_period_change(candles, 96, 72)  # 3 days ago
        movers.append(m)

        if (i + 1) % 25 == 0:
            print(f"        {i + 1}/{len(markets)}...")

    print(f"        Done. {len(movers)} markets with data.\n")

    # Step 3: Log multi-day history
    print("  [3/5] Updating history with multi-day verification...")

    history = load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    already_logged = {(h["date"], h["coin"]) for h in history}

    # Coins that pumped 48-72h ago: we can now verify Day 1 AND Day 2
    pumped_2d_ago = sorted(
        [m for m in movers if m.get("change_48_72") is not None and m["change_48_72"] >= MIN_PUMP_PCT],
        key=lambda x: x["change_48_72"], reverse=True,
    )[:TOP_N]

    new_logs = 0
    for rank, pm in enumerate(pumped_2d_ago, 1):
        key = (today, pm["coin"])
        if key not in already_logged:
            day1 = pm.get("change_24_48")
            day2 = pm.get("change_24h") if pm.get("change_24_48") is not None else None
            # day1 = 24-48h window (first day after pump)
            # But actually: pump was 48-72h ago, day1 after = 24-48h ago, day2 after = 0-24h ago
            d1 = pm.get("change_24_48", 0) or 0
            d2 = pm.get("change_24h", 0) or 0
            total_2d = ((1 + d1/100) * (1 + d2/100) - 1) * 100

            save_history_row({
                "date": today,
                "coin": pm["coin"],
                "pump_pct": f"{pm['change_48_72']:.2f}",
                "day1_pct": f"{d1:.2f}",
                "day2_pct": f"{d2:.2f}",
                "dumped_d1": str(d1 < 0),
                "dumped_d2": str(d2 < 0),
                "total_2d_pct": f"{total_2d:.2f}",
                "rank": rank,
            })
            new_logs += 1

    if new_logs:
        history = load_history()
    stats = calc_dump_stats(history)
    print(f"        Logged {new_logs} new multi-day record(s)\n")

    # Step 4: Score mooners for short readiness
    print("  [4/5] Scoring short candidates...")

    # Current top mooners
    movers.sort(key=lambda x: x["change_24h"], reverse=True)
    top_mooners = [m for m in movers if m["change_24h"] >= MIN_PUMP_PCT][:TOP_N]

    # Yesterday's mooners (for live dump check)
    prev_mooners = sorted(
        [m for m in movers if m.get("change_24_48") is not None and m["change_24_48"] >= MIN_PUMP_PCT],
        key=lambda x: x["change_24_48"], reverse=True,
    )[:TOP_N]

    print("  [5/5] Results\n")

    # =========================================================================
    # DISPLAY: Historical Stats (multi-day)
    # =========================================================================
    print("=" * 75)
    print("  HISTORICAL MOON-DUMP STATS (Multi-Day)")
    print("=" * 75)
    if stats["total"] > 0:
        print(f"  Total mooners tracked:        {stats['total']}")
        print(f"  Day 1 dump rate:              {stats['d1_dumps']}/{stats['total']} ({stats['d1_pct']:.0f}%)")
        print(f"  Avg Day 1 change:             {stats['avg_d1_dump']:+.2f}%")
        if stats["d2_total"] > 0:
            print(f"  Day 2 data points:            {stats['d2_total']}")
            print(f"  Day 2 dump rate:              {stats['d2_dumps']}/{stats['d2_total']} ({stats['d2_pct']:.0f}%)")
            print(f"  Day 2 BOUNCE rate:            {stats['d2_bounces']}/{stats['d2_total']} ({stats['d2_bounce_pct']:.0f}%) <<<")
            print(f"  Avg Day 2 change:             {stats['avg_d2_change']:+.2f}%")
        print()
        print("  TAKEAWAY: Short on Day 1 rollover. Take profit within 12-24h.")
        print("  Day 2 bounces hard. Don't hold shorts overnight into Day 2.")
    else:
        print("  No history yet. Run daily to build stats.")
        print("  Need 3 days of data for full Day 1 + Day 2 verification.")
    print()

    # =========================================================================
    # DISPLAY: 2-Day Ago Mooners - Full D1 + D2 Check
    # =========================================================================
    if pumped_2d_ago:
        print("=" * 75)
        print("  2-DAY-AGO MOONERS - FULL DAY 1 + DAY 2 RESULTS")
        print("  (Pumped 48-72h ago. Day 1 = 24-48h ago. Day 2 = last 24h)")
        print("=" * 75)
        print(f"  {'Coin':<10} {'Pump':>8} {'Day 1':>8} {'Day 2':>8} {'Net 2d':>8} {'D1':>7} {'D2':>8}")
        print(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*7} {'-'*8}")

        d1_count = 0
        d2_bounce = 0
        for pm in pumped_2d_ago:
            pump = pm.get("change_48_72", 0) or 0
            d1 = pm.get("change_24_48", 0) or 0
            d2 = pm.get("change_24h", 0) or 0
            net = ((1 + d1/100) * (1 + d2/100) - 1) * 100
            d1_v = "DUMP" if d1 < 0 else "UP"
            d2_v = "BOUNCE" if d1 < 0 and d2 > 0 else "DUMP" if d2 < 0 else "UP"
            if d1 < 0:
                d1_count += 1
            if d1 < 0 and d2 > 0:
                d2_bounce += 1
            print(f"  {pm['coin']:<10} {pump:>+7.1f}% {d1:>+7.1f}% {d2:>+7.1f}% {net:>+7.1f}% {d1_v:>7} {d2_v:>8}")

        total_2d = len(pumped_2d_ago)
        print(f"\n  Day 1 dumps: {d1_count}/{total_2d} ({d1_count/total_2d*100:.0f}%)")
        if d1_count > 0:
            print(f"  Day 2 bounced back: {d2_bounce}/{d1_count} ({d2_bounce/d1_count*100:.0f}%) of Day 1 dumpers")
        print()

    # =========================================================================
    # DISPLAY: Yesterday's Mooners - Day 1 Live Check
    # =========================================================================
    print("=" * 75)
    print("  YESTERDAY'S MOONERS - DAY 1 CHECK (live)")
    print("  (Pumped 24-48h ago. Current 24h = Day 1 result)")
    print("=" * 75)
    if prev_mooners:
        print(f"  {'Coin':<10} {'Pump':>8} {'Day 1':>8} {'Status':>10} {'Hrs from peak':>14}")
        print(f"  {'-'*10} {'-'*8} {'-'*8} {'-'*10} {'-'*14}")
        dumped_count = 0
        for pm in prev_mooners:
            prev = pm["change_24_48"]
            curr = pm["change_24h"]
            dumped = curr < 0
            if dumped:
                dumped_count += 1
            status = "DUMPED" if dumped else "HOLDING" if curr < prev * 0.3 else "PUMPING"
            hrs, _ = calc_hours_since_peak(pm["candles"], 48)
            print(f"  {pm['coin']:<10} {prev:>+7.1f}% {curr:>+7.1f}% {status:>10} {hrs:>10}h ago")
        print(f"\n  Day 1 dump rate: {dumped_count}/{len(prev_mooners)} ({dumped_count/len(prev_mooners)*100:.0f}%)")

        # Show nearest support for dumped coins (where to close shorts)
        dumped_coins = [pm for pm in prev_mooners if pm["change_24h"] < 0]
        if dumped_coins:
            print(f"\n  NEXT SUPPORT for dumped coins (close short here):")
            for pm in dumped_coins[:5]:
                sr = get_all_sr_levels(pm["candles"])
                price = sr.get("current_price", 0)
                sups = sr.get("supports", [])
                if sups:
                    nearest = sups[0]
                    dist = ((nearest["price"] - price) / price) * 100 if price else 0
                    print(f"    {pm['coin']:<10} price ${price:<10.5g} -> support ${nearest['price']:<10.5g} ({dist:+.1f}%) {nearest['type']}")
                else:
                    print(f"    {pm['coin']:<10} price ${price:<10.5g} -> no support found")
    else:
        print("  No tokens pumped >5% in the 24-48h window.")
    print()

    # =========================================================================
    # DISPLAY: Current Mooners + Short Scoring + Exit Timing
    # =========================================================================
    print("=" * 75)
    print("  CURRENT MOONERS - SHORT CANDIDATES + EXIT TIMING")
    print("  (Pumped >5% in last 24h)")
    print("=" * 75)

    if not top_mooners:
        print(f"  No tokens pumped >{MIN_PUMP_PCT}% in the last 24h.\n")
        save_results({}, stats, [], [], [])
        return

    results = []
    for m in top_mooners:
        sd = score_short_readiness(m["candles"], m["funding"])
        m.update(sd)
        m["sr_levels"] = get_all_sr_levels(m["candles"])
        results.append(m)

    results.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n  {'#':<3} {'Coin':<8} {'24h':>7} {'Score':>6} {'RSI':>5} {'BB':>5} "
          f"{'Peak ago':>8} {'Drop':>7} {'Bounce':>8} {'Exit':>8}")
    print(f"  {'-'*3} {'-'*8} {'-'*7} {'-'*6} {'-'*5} {'-'*5} "
          f"{'-'*8} {'-'*7} {'-'*8} {'-'*8}")

    for i, r in enumerate(results, 1):
        print(f"  {i:<3} {r['coin']:<8} {r['change_24h']:>+6.1f}% {r['score']:>4}/100 "
              f"{r['rsi']:>4.0f} {r['bb_pos']:>4.2f} "
              f"{r['hours_since_peak']:>5}h   {r['drop_from_peak']:>+6.1f}% "
              f"{r['bounce_risk']:>8} {r['exit_window']:>8}")

    # =========================================================================
    # DISPLAY: Detailed Short Recommendations
    # =========================================================================
    # =========================================================================
    # DISPLAY: S/R Levels for ALL current mooners (even low-scoring ones)
    # =========================================================================
    print("\n" + "=" * 75)
    print("  KEY SUPPORT & RESISTANCE LEVELS")
    print("  Resistance = short entry / stop loss zones")
    print("  Support = take profit / close short zones")
    print("=" * 75)
    for r in results:
        sr = r.get("sr_levels", {})
        if sr:
            print(f"\n  --- {r['coin']} (24h: {r['change_24h']:+.1f}% | Score: {r['score']}/100) ---")
            print(format_sr_display(sr, r["coin"]))

    # =========================================================================
    # DISPLAY: Detailed Short Recommendations
    # =========================================================================
    actionable = [r for r in results if r["score"] >= 35 and r["bounce_risk"] != "CRITICAL"]
    if actionable:
        print("\n" + "=" * 75)
        print("  SHORT TRADE SETUPS (with S/R levels)")
        print("=" * 75)
        for i, r in enumerate(actionable[:5], 1):
            grade = ("A+" if r["score"] >= 70 else "A" if r["score"] >= 55
                     else "B+" if r["score"] >= 45 else "B")
            atr = calc_atr(r["candles"])
            entry = float(r["candles"][-1]["c"])
            sr = r.get("sr_levels", {})

            # Use nearest resistance as stop loss if available, else ATR-based
            nearest_resist = sr["resistances"][0]["price"] if sr.get("resistances") else None
            if nearest_resist and nearest_resist > entry:
                stop = nearest_resist
                stop_source = f"nearest resistance ({sr['resistances'][0]['type']})"
            else:
                stop = entry + (1.5 * atr) if atr else entry * 1.02
                stop_source = "1.5x ATR"

            # Use nearest strong support as TP target if available
            strong_supports = [s for s in sr.get("supports", []) if s["strength"] >= 2]
            if strong_supports:
                tp1 = strong_supports[0]["price"]
                tp1_source = strong_supports[0]["type"]
                tp2 = strong_supports[1]["price"] if len(strong_supports) > 1 else entry - (3 * atr) if atr else entry * 0.955
                tp2_source = strong_supports[1]["type"] if len(strong_supports) > 1 else "3x ATR"
            else:
                tp1 = entry - (2 * atr) if atr else entry * 0.97
                tp1_source = "2x ATR"
                tp2 = entry - (3 * atr) if atr else entry * 0.955
                tp2_source = "3x ATR"

            risk_pct = ((stop - entry) / entry) * 100
            tp1_pct = ((tp1 - entry) / entry) * 100
            tp2_pct = ((tp2 - entry) / entry) * 100
            rr1 = abs(tp1_pct / risk_pct) if risk_pct != 0 else 0
            rr2 = abs(tp2_pct / risk_pct) if risk_pct != 0 else 0

            print(f"\n  #{i} {r['coin']} | Grade: {grade} | Score: {r['score']}/100")
            print(f"  {'='*60}")
            print(f"  Entry:        ${entry:<12.5g}  (current price)")
            print(f"  Stop loss:    ${stop:<12.5g}  (+{risk_pct:.1f}%) <- {stop_source}")
            print(f"  TP1:          ${tp1:<12.5g}  ({tp1_pct:.1f}%) <- {tp1_source} [{rr1:.1f}R]")
            print(f"  TP2:          ${tp2:<12.5g}  ({tp2_pct:.1f}%) <- {tp2_source} [{rr2:.1f}R]")
            print(f"  24h pump:     {r['change_24h']:+.1f}%")
            print(f"  Peak:         {r['hours_since_peak']}h ago (dropped {r['drop_from_peak']:+.1f}% since)")
            print(f"  Funding:      {r['funding']*100:.4f}%")
            print()
            print(f"  EXIT TIMING")
            print(f"  Bounce risk:  {r['bounce_risk']}")
            print(f"  Exit window:  {r['exit_window']}")
            print(f"  Note:         {r['exit_note']}")
            print()
            print(f"  KEY LEVELS:")
            if sr.get("resistances"):
                print(f"  Resistance (above - invalidation):")
                for rv in sr["resistances"][:3]:
                    d = ((rv["price"] - entry) / entry) * 100
                    print(f"    ${rv['price']:<12.5g} (+{d:.1f}%)  {rv['type']}")
            if sr.get("supports"):
                print(f"  Support (below - take profit here):")
                for sv in sr["supports"][:3]:
                    d = ((sv["price"] - entry) / entry) * 100
                    print(f"    ${sv['price']:<12.5g} ({d:.1f}%)  {sv['type']}")
            print()
            print(f"  SIGNALS:")
            for sig in r["signals"]:
                print(f"    - {sig}")

    # Warn about coins in day-2 bounce zone
    avoid = [r for r in results if r["bounce_risk"] == "CRITICAL"]
    if avoid:
        print("\n" + "=" * 75)
        print("  DO NOT SHORT - DAY 2 BOUNCE ZONE")
        print("  79% of mooners bounce on day 2. These peaked >24h ago.")
        print("=" * 75)
        for r in avoid:
            print(f"  {r['coin']:<10} peaked {r['hours_since_peak']}h ago | "
                  f"dropped {r['drop_from_peak']:+.1f}% | EXPECT BOUNCE")

    # =========================================================================
    # SAVE RESULTS
    # =========================================================================
    save_results(stats, stats, results, prev_mooners, pumped_2d_ago)


def save_results(output_stats, stats, results, prev_mooners, pumped_2d_ago):
    output = {
        "scan_time": datetime.now().isoformat(),
        "stats": stats,
        "current_mooners": [
            {
                "coin": r["coin"],
                "change_24h": r["change_24h"],
                "short_score": r["score"],
                "rsi": r["rsi"],
                "funding": r["funding"],
                "bounce_risk": r["bounce_risk"],
                "exit_window": r["exit_window"],
                "hours_since_peak": r["hours_since_peak"],
                "drop_from_peak": r["drop_from_peak"],
                "signals": r["signals"],
            }
            for r in results
        ],
        "yesterday_mooners": [
            {
                "coin": pm["coin"],
                "pump": pm.get("change_24_48", 0),
                "day1": pm["change_24h"],
                "dumped": pm["change_24h"] < 0,
            }
            for pm in prev_mooners
        ],
        "two_day_ago_mooners": [
            {
                "coin": pm["coin"],
                "pump": pm.get("change_48_72", 0),
                "day1": pm.get("change_24_48", 0),
                "day2": pm.get("change_24h", 0),
            }
            for pm in pumped_2d_ago
        ],
    }

    filename = f"moon_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to {filename}")
    print("\n" + "=" * 75)
    print("  Run daily to build moon-dump history.")
    print("  KEY RULE: Short Day 1 rollover. Exit before Day 2 bounce.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_monitor()
