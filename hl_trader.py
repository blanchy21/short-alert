"""
Hyperliquid order placement for Short Alert (live mode only).

Opens a market short, then places a reduce-only stop-loss and take-profit on the
exchange so they protect the position between hourly runs. Uses an API (agent)
wallet: it can trade but cannot withdraw.

Needs:
  HL_ACCOUNT_ADDRESS   your main Hyperliquid wallet address (0x...)
  HL_API_PRIVATE_KEY   the API wallet's private key
  HL_NETWORK           "mainnet" (default) or "testnet"
"""

import os
import time

import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

MIN_NOTIONAL_USD = 10.0      # Hyperliquid's minimum order value
ENTRY_SLIPPAGE = 0.01        # max 1% worse than mid on the market entry
LEVERAGE = 3                 # isolated; margin = notional / 3


class TraderError(Exception):
    pass


def _statuses(resp) -> list:
    if not isinstance(resp, dict) or resp.get("status") != "ok":
        raise TraderError(f"exchange rejected request: {resp}")
    return resp["response"]["data"]["statuses"]


class Trader:
    def __init__(self):
        addr = os.environ.get("HL_ACCOUNT_ADDRESS", "").strip()
        key = os.environ.get("HL_API_PRIVATE_KEY", "").strip()
        if not addr or not key:
            raise TraderError("HL_ACCOUNT_ADDRESS / HL_API_PRIVATE_KEY not set")
        self.network = os.environ.get("HL_NETWORK", "mainnet").strip().lower()
        url = constants.TESTNET_API_URL if self.network == "testnet" else constants.MAINNET_API_URL
        self.address = addr
        self.info = Info(url, skip_ws=True)
        self.exchange = Exchange(eth_account.Account.from_key(key), url, account_address=addr)

    # ------------------------------------------------------------ rounding
    def _sz_decimals(self, coin: str) -> int:
        return self.info.asset_to_sz_decimals[self.info.name_to_asset(coin)]

    def round_px(self, coin: str, px: float) -> float:
        # Perps: max 5 significant figures and max (6 - szDecimals) decimals
        return round(float(f"{px:.5g}"), 6 - self._sz_decimals(coin))

    def round_sz(self, coin: str, sz: float) -> float:
        return round(sz, self._sz_decimals(coin))

    # ------------------------------------------------------------ account
    def account_value(self) -> float:
        return float(self.info.user_state(self.address)["marginSummary"]["accountValue"])

    def position(self, coin: str) -> float:
        """Signed size (negative = short); 0 if flat."""
        for p in self.info.user_state(self.address)["assetPositions"]:
            if p["position"]["coin"] == coin:
                return float(p["position"]["szi"])
        return 0.0

    def mid(self, coin: str) -> float:
        return float(self.info.all_mids()[coin])

    def cancel_all(self, coin: str) -> None:
        for o in self.info.open_orders(self.address):
            if o["coin"] == coin:
                self.exchange.cancel(coin, o["oid"])

    # ------------------------------------------------------------ trading
    def open_short(self, coin: str, stop_pct: float, tp_pct: float, risk_usd: float) -> dict:
        """
        stop_pct: stop distance above entry in % (positive)
        tp_pct:   take-profit distance below entry in % (positive)
        Sizes the position so hitting the stop loses ~risk_usd.
        """
        if self.position(coin) != 0:
            raise TraderError(f"already have a {coin} position on the exchange")

        mid = self.mid(coin)
        sz = self.round_sz(coin, risk_usd / (mid * stop_pct / 100))
        if sz * mid < MIN_NOTIONAL_USD:
            raise TraderError(f"position ${sz * mid:.2f} is under Hyperliquid's ${MIN_NOTIONAL_USD:.0f} minimum "
                              f"(stop {stop_pct:.1f}% too wide for ${risk_usd:.2f} risk)")

        lev = self.exchange.update_leverage(LEVERAGE, coin, is_cross=False)
        if not isinstance(lev, dict) or lev.get("status") != "ok":
            raise TraderError(f"couldn't set {LEVERAGE}x isolated leverage: {lev}")

        st = _statuses(self.exchange.market_open(coin, False, sz, None, ENTRY_SLIPPAGE))[0]
        if "filled" not in st:
            raise TraderError(f"entry not filled: {st}")
        entry = float(st["filled"]["avgPx"])
        filled = float(st["filled"]["totalSz"])

        stop = self.round_px(coin, entry * (1 + stop_pct / 100))
        tp = self.round_px(coin, entry * (1 - tp_pct / 100))
        try:
            sl_st, tp_st = _statuses(self.exchange.bulk_orders([
                {"coin": coin, "is_buy": True, "sz": filled, "reduce_only": True,
                 "limit_px": self.round_px(coin, stop * 1.10),
                 "order_type": {"trigger": {"triggerPx": stop, "isMarket": True, "tpsl": "sl"}}},
                {"coin": coin, "is_buy": True, "sz": filled, "reduce_only": True,
                 "limit_px": self.round_px(coin, tp * 1.05),
                 "order_type": {"trigger": {"triggerPx": tp, "isMarket": True, "tpsl": "tp"}}},
            ], grouping="normalTpsl"))
            for s in (sl_st, tp_st):
                if "error" in s:
                    raise TraderError(f"stop/TP order rejected: {s['error']}")
        except Exception:
            # Never leave an unprotected position
            self.close(coin)
            raise

        return {"entry": entry, "size": filled, "stop": stop, "tp1": tp,
                "notional": round(entry * filled, 2), "network": self.network}

    def close(self, coin: str) -> None:
        self.cancel_all(coin)
        if self.position(coin) != 0:
            _statuses(self.exchange.market_close(coin))

    def closing_fills(self, coin: str, since_ms: int) -> dict | None:
        """Summarise fills that closed our short since entry (P&L after open+close fees); None if none yet."""
        fills = [f for f in self.info.user_fills_by_time(self.address, since_ms - 5000)
                 if f["coin"] == coin and f.get("dir") in ("Open Short", "Close Short")]
        closes = [f for f in fills if f["dir"] == "Close Short"]
        if not closes:
            return None
        sz = sum(float(f["sz"]) for f in closes)
        px = sum(float(f["px"]) * float(f["sz"]) for f in closes) / sz
        pnl = sum(float(f["closedPnl"]) for f in closes) - sum(float(f["fee"]) for f in fills)
        return {"exit": px, "pnl_usd": round(pnl, 2)}

    def wait_flat(self, coin: str, tries: int = 5) -> bool:
        for _ in range(tries):
            if self.position(coin) == 0:
                return True
            time.sleep(1)
        return False
